#!/usr/bin/env python

from collections import defaultdict
from typing import DefaultDict, Dict, List
from utc_bot import UTCBot, start_bot
import math
import proto.utc_bot as pb
import betterproto
import asyncio
import re
import time
import json
import sys

# Constants

DAYS_IN_MONTH = 21
DAYS_IN_YEAR = 252
INTEREST_RATE = 0.02
NUM_FUTURES = 14
TICK_SIZE = 0.01
CARRYING_COST = 0.10
FUTURE_CODES = [chr(ord('A') + i) for i in range(NUM_FUTURES)] # Suffix of monthly future code
FUTURES = ['LBS' + c for c in FUTURE_CODES]
CONTRACTS = ['SBL'] +  FUTURES + ['LLL']

EPSILON = 0.0001


MOVING_AVG_WINDOW = 20
MIN_EDGE = 0.10
FADE = 0.20
SLACK = 0.10
NUM_LEVELS = 4
LEVEL_SPREAD = 1.10
ORDER_SIZE = 60
LEVELS_ENABLED = True

WEATHER_TO_PRICE_M = 1.7838804404379633
WEATHER_TO_PRICE_B = 54.849618905657714
# 2023: m = 1.7838804404379633  b = 54.849618905657714
# 2024: m = 1.60005651307329  b = 54.890769908266975
# 2025: m = 1.4162325857086162  b = 54.931920910876244
# 2026: m = 1.2324086583439426  b = 54.973071913485505


# TUNE Weights
WEIGHTS = {"WEATHER_FAIR": 0.3, "SOYBEAN_MARKET" : 0.4, "FUTURES_MARKET" : 0.3}


class Case1Bot(UTCBot):
    """
    An example bot
    """
    etf_suffix = ''
    async def create_etf(self, qty: int):
        '''
        Creates qty amount the ETF basket
        DO NOT CHANGE
        '''
        if len(self.etf_suffix) == 0:
            return pb.SwapResponse(False, "Unsure of swap")
        return await self.swap("create_etf_" + self.etf_suffix, qty)

    async def redeem_etf(self, qty: int):
        '''
        Redeems qty amount the ETF basket
        DO NOT CHANGE
        '''
        if len(self.etf_suffix) == 0:
            return pb.SwapResponse(False, "Unsure of swap")
        return await self.swap("redeem_etf_" + self.etf_suffix, qty) 
    
    def days_to_expiry(self, asset):
        '''
        Calculates days to expiry for the future
        '''
        future = ord(asset[-1]) - ord('A')
        expiry = 21 * (future + 1)
        return expiry - self._day

    async def handle_exchange_update(self, update: pb.FeedMessage):
        '''
        Handles exchange updates
        '''

        kind, _ = betterproto.which_one_of(update, "msg")

        msg = None

        #Competition event messages
        if kind == "generic_msg":
            msg = update.generic_msg.message
            
            # Used for API DO NOT TOUCH
            if 'trade_etf' in msg:
                self.etf_suffix = msg.split(' ')[1]
                
            # Updates current weather
            if "Weather" in msg:
                weather = float(re.findall("\d+\.\d+", msg)[0])
                self._weather_log_PS.append(self._weather_log_PS[-1] + weather)
                self._weather_log.append(weather)

                for asset in FUTURES:
                    self._fair_price[asset] = self.calculate_future_fair_price_weighted(asset, WEIGHTS)

            # Updates date
            if "Day" in msg:
                self._day = int(re.findall("\d+", msg)[0])

 
        elif kind == "market_snapshot_msg":
            for asset in CONTRACTS:
                book = update.market_snapshot_msg.books[asset]
                if not (len(book.bids) == 0 or len(book.asks) == 0):
                    self._best_bid[asset] = float(book.bids[0].px)
                    self._best_ask[asset] = float(book.asks[0].px)
                    self._best_bid_qty[asset] = int(book.bids[0].qty)
                    self._best_ask_qty[asset] = int(book.asks[0].qty)

                # arbitrage where future > soybeans + carrying cost * days to expiry (buy soybeans and short future)
                #    best future bid > best soybean ask + CC * N AND both "bests" are not self trades => 
                #        ask at best futures bid, bid at best soybeans ask
                #        (quantity = min (best futures bid qty, best soybeans ask qty))
                #    else do nothing

                # arbitrage where future < soybeans (buy future and short soybeans)
                #    best future ask < best soybean bid AND both "bests" are not self trades => 
                #        bid at best future ask, ask at best soybeans bid
                #        (quantity = min(best futures ask qty, best soybeans bid qty)) 

        elif kind == "fill_msg":
            resp = await self.get_positions()
            if resp.ok:
                self.positions = resp.positions

        elif kind == "order_cancelled_msg":
            msg = update.order_cancelled_msg.message

        elif kind == "request_failed_msg":
            msg = update.request_failed_msg.message


    async def handle_round_started(self):
        ### Current day
        self._day = 0
        ### Best Bid in the order book
        self._best_bid: Dict[str, float] = defaultdict(
            lambda: 55
        )

        self._best_bid_qty: Dict[str, int] = defaultdict(
            lambda: 0
        )

        ### Best Ask in the order book
        self._best_ask: Dict[str, float] = defaultdict(
            lambda: 55
        )
        

        self._best_ask_qty: Dict[str, int] = defaultdict(
            lambda: 0
        )

        self._bid_order_px: Dict[str, float] = defaultdict(
            lambda: 0
        )

        self._bid_order_qty: Dict[str, int] = defaultdict(
            lambda: 0
        )

        self.bid_id: Dict[str, str] = defaultdict(
            lambda: ""
        )

        self._ask_order_px: Dict[str, float] = defaultdict(
            lambda: 0
        )

        self._ask_order_qty: Dict[str, int] = defaultdict(
            lambda: 0
        )
        
        self._ask_id: Dict[str, str] = defaultdict(
            lambda: ""
        )

        self._bid_levels: DefaultDict[str, List[str]] = defaultdict(
            lambda: [str(i) for i in range(NUM_LEVELS)]
        )

        self._ask_levels: DefaultDict[str, List[str]] = defaultdict(
            lambda: [str(i+NUM_LEVELS) for i in range(NUM_LEVELS)]
        )

        self._fair_price: DefaultDict[str, float] = defaultdict(
            lambda: 55
        )

        
        ### List of weather reports
        self._weather_log = []
        self._weather_log_PS = [0]
        
        
        await asyncio.sleep(.1)
        
        # Starts market making for each future
        for asset in FUTURES:
            asyncio.create_task(self.make_market_asset(asset))


    def calculate_soybean_fair_price(self):
        wl_len = len(self._weather_log_PS)

        avg_weather_idx = 0

        if wl_len <= (MOVING_AVG_WINDOW + 1):
            avg_weather_idx = self._weather_log_PS[-1] / (wl_len - 1)
        else:
            avg_weather_idx = (self._weather_log_PS[-1] - self._weather_log_PS[-1 - MOVING_AVG_WINDOW]) / MOVING_AVG_WINDOW
        
        # map avg_weather_idx to soybean price
        return WEATHER_TO_PRICE_M * avg_weather_idx + WEATHER_TO_PRICE_B

    def calculate_future_fair_price_with_SB_fair(self, asset, soybean_fair):
        return soybean_fair * (1 + INTEREST_RATE * (self.days_to_expiry(asset) / DAYS_IN_YEAR))

    def calculate_future_market_price(self, asset):
        return (self._best_bid[asset] + self._best_ask[asset]) / 2.0
    
    # weights[0] -- weather
    # weights[1] -- soybean market
    # weights[2] -- futures market
    def calculate_future_fair_price_weighted(self, asset, weights):
        soybean_weather_price = self.calculate_soybean_fair_price()
        soybean_market_price = (self._best_bid['SBL'] + self._best_ask['SBL']) / 2.0

        future_weather_fp = self.calculate_future_fair_price_with_SB_fair(asset, soybean_weather_price)
        future_SB_market_fp = self.calculate_future_fair_price_with_SB_fair(asset, soybean_market_price)
        future_market_fp =  self.calculate_future_market_price(asset)

        return weights["WEATHER_FAIR"] * future_weather_fp + weights["SOYBEAN_MARKET"] * future_SB_market_fp + weights["FUTURES_MARKET"] * future_market_fp

    def calculate_bid_edge(self, asset):
        isOurs = (self._best_bid[asset] - self._bid_order_px[asset]) < EPSILON
        diff = self._fair_price[asset] - self._best_bid[asset]
        if diff < MIN_EDGE:
            if isOurs:
                return diff
            else:
                return MIN_EDGE
        elif diff > (MIN_EDGE + SLACK):
            return MIN_EDGE + SLACK
        else:
            if isOurs:
                return diff
            else:
                return diff - 0.01
        
    def calculate_ask_edge(self, asset):
        isOurs = (self._ask_order_px[asset] - self._best_ask[asset]) < EPSILON
        diff = self._best_ask[asset] - self._fair_price[asset]
        if diff < MIN_EDGE:
            if isOurs:
                return diff
            else:
                return MIN_EDGE
        elif diff > (MIN_EDGE + SLACK):
            return MIN_EDGE + SLACK
        else:
            if isOurs:
                return diff
            else:
                return diff - 0.01

    async def place_ask_levels(self, asset: str, ask_px : float):
        for i in range(1, NUM_LEVELS + 1):
            r = await self.modify_order(
                order_id=self._ask_levels[asset][i-1],
                asset_code = asset,
                order_type = pb.OrderSpecType.LIMIT,
                order_side = pb.OrderSpecSide.ASK,
                qty = ORDER_SIZE,
                price = round_nearest(ask_px + i * LEVEL_SPREAD)
            )

            self._ask_levels[asset][i-1] = r.order_id

    async def place_bid_levels(self, asset: str, bid_px: float):
        for i in range(1, NUM_LEVELS + 1):
            r = await self.modify_order(
                order_id=self._bid_levels[asset][i-1],
                asset_code = asset,
                order_type = pb.OrderSpecType.LIMIT,
                order_side = pb.OrderSpecSide.BID,
                qty = ORDER_SIZE,
                price = round_nearest(bid_px - i * LEVEL_SPREAD)
            )

            self._bid_levels[asset][i-1] = r.order_id


    def fade(self, asset):
        return FADE * self.positions[asset]
        
    async def make_market_asset(self, asset: str):

        while self.days_to_expiry(asset) >= 0:

            if self.days_to_expiry(asset) > 1:
                # get the fair price
                fair_px =  self._fair_price[asset]

                # get the faded fair price
                faded_fair_px = fair_px - self.fade(asset)

                # calculate edge around faded fair price using edge/slack/penny in
                bid_edge = self.calculate_bid_edge(asset)
                ask_edge = self.calculate_ask_edge(asset)

                # place order pair and levels (make sure to do it in right order)
                order_bid = round_nearest(faded_fair_px - bid_edge)
                order_ask = round_nearest(faded_fair_px + ask_edge)

                # if our new bid is higher than our current ask, 
                #   then update all the ask levels
                #   then update the ask order
                #   then update the bid order
                #   then update the bid levels
                if order_bid > self._best_ask[asset]:
                    await self.place_ask_levels(asset, order_ask)

                    r = await self.modify_order(
                        order_id=self.ask_id[asset],
                        asset_code = asset,
                        order_type = pb.OrderSpecType.LIMIT,
                        order_side = pb.OrderSpecSide.ASK,
                        qty = ORDER_SIZE,
                        price = order_ask
                    )
                    self.ask_id[asset] = r.order_id
                    
                    r = await self.modify_order(
                        order_id=self.bid_id[asset],
                        asset_code = asset,
                        order_type = pb.OrderSpecType.LIMIT,
                        order_side = pb.OrderSpecSide.BID,
                        qty = ORDER_SIZE,
                        price = order_bid
                    )
                    self.bid_id[asset] = r.order_id

                    await self.place_bid_levels(asset, order_bid)

                # if our new ask is lower than our current bid,
                #   then update all the bid levels
                #   then update the bid order
                #   then update the ask order
                #   then update the ask levels
                elif order_ask < self._best_bid[asset]:
                    await self.place_bid_levels(asset, order_bid)

                    r = await self.modify_order(
                        order_id=self.bid_id[asset],
                        asset_code = asset,
                        order_type = pb.OrderSpecType.LIMIT,
                        order_side = pb.OrderSpecSide.BID,
                        qty = ORDER_SIZE,
                        price = order_bid
                    )
                    self.bid_id[asset] = r.order_id

                    r = await self.modify_order(
                        order_id=self.ask_id[asset],
                        asset_code = asset,
                        order_type = pb.OrderSpecType.LIMIT,
                        order_side = pb.OrderSpecSide.ASK,
                        qty = ORDER_SIZE,
                        price = order_ask
                    )
                    self.ask_id[asset] = r.order_id

                    await self.place_ask_levels(asset, order_ask)
                else:
                    # if we are here, then we are in the middle of the spread
                    #   so we need to update the bid and ask orders
                    #   then update the bid and ask levels
                    r = await self.modify_order(
                        order_id=self.bid_id[asset],
                        asset_code = asset,
                        order_type = pb.OrderSpecType.LIMIT,
                        order_side = pb.OrderSpecSide.BID,
                        qty = ORDER_SIZE,
                        price = order_bid
                    )
                    self.bid_id[asset] = r.order_id

                    r = await self.modify_order(
                        order_id=self.ask_id[asset],
                        asset_code = asset,
                        order_type = pb.OrderSpecType.LIMIT,
                        order_side = pb.OrderSpecSide.ASK,
                        qty = ORDER_SIZE,
                        price = order_ask
                    )
                    self.ask_id[asset] = r.order_id

                    await self.place_bid_levels(asset, order_bid)
                    await self.place_ask_levels(asset, order_ask)

                
                self._best_bid[asset] = order_bid
                self._best_ask[asset] = order_ask
                
        
            elif self.days_to_expiry(asset) == 1:
                # cancel all orders
                #  - close our current open positions
                #     - if you have a long position:
                #         - (if best market future bid price > current market soybean bid price) (sell futures)
                #         - (else sell soybean)
                #     - else: (short positions)
                #         -  (if best market future ask price < current market soybean ask price) (buy futures)
                #         - (else buy soybean)


                # cancel all orders
                r = await self.cancel_orders(self.bid_id[asset])
                r = await self.cancel_orders(self.ask_id[asset])
                for i in range(1, NUM_LEVELS+1):
                    r = await self.cancel_orders(self._bid_levels[asset][i-1])
                    r = await self.cancel_orders(self._ask_levels[asset][i-1])

                # long on future, so sell
                if self.positions[asset] > 0:
                    if self._best_bid[asset] > self._best_bid['SBL']:
                        r = await self.place_order(
                            asset_code = asset,
                            order_type = pb.OrderSpecType.MARKET,
                            order_side = pb.OrderSpecSide.ASK,
                            qty = self.positions[asset]
                        )
                    else:
                        r = await self.place_order(
                            asset_code = 'SBL',
                            order_type = pb.OrderSpecType.MARKET,
                            order_side = pb.OrderSpecSide.ASK,
                            qty = self.positions[asset]
                        )

                # short on future, so buy
                elif self.positions[asset] < 0:
                    if self._best_ask[asset] < self._best_ask['SBL']:
                        r = await self.place_order(
                            asset_code = asset,
                            order_type = pb.OrderSpecType.MARKET,
                            order_side = pb.OrderSpecSide.BID,
                            qty = abs(self.positions[asset])
                        )
                    else:
                        r = await self.place_order(
                            asset_code = 'SBL',
                            order_type = pb.OrderSpecType.MARKET,
                            order_side = pb.OrderSpecSide.BID,
                            qty = abs(self.positions[asset])
                        )

            else:
                # - clear all soybean positions 
                if self.positions[asset] > 0:
                    r = await self.place_order(
                        asset_code = asset,
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.ASK,
                        qty = self.positions[asset]
                    )
                elif self.positions[asset] < 0:
                    r = await self.place_order(
                        asset_code = asset,
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.BID,
                        qty = abs(self.positions[asset])
                    )
       
        

def round_nearest(x):
    return round(round(x / 0.01) * 0.01, 2)             


if __name__ == "__main__":
    # read the first argument from the command line
    #   - this is the name of the config file
    #   - if no argument is given, then do nothing

    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        with open(config_file) as f:
            config = json.load(f)

            # using the config, update all of the following variables
                # MOVING_AVG_WINDOW = 20
                # MIN_EDGE = 0.10
                # FADE = 0.20
                # SLACK = 0.10
                # NUM_LEVELS = 4
                # LEVEL_SPREAD = 1.10
                # ORDER_SIZE = 60
                # LEVELS_ENABLED = True

                # WEATHER_TO_PRICE_M = 1.7838804404379633
                # WEATHER_TO_PRICE_B = 54.849618905657714

            MOVING_AVG_WINDOW = config['moving_avg_window']
            MIN_EDGE = config['min_edge']
            FADE = config['fade']
            SLACK = config['slack']
            NUM_LEVELS = config['num_levels']
            LEVEL_SPREAD = config['level_spread']
            ORDER_SIZE = config['order_size']
            LEVELS_ENABLED = config['levels_enabled']

            WEATHER_TO_PRICE_M = config['weather_to_price_m']
            WEATHER_TO_PRICE_B = config['weather_to_price_b']

            bot = Case1Bot()
            


    start_bot(Case1Bot)
