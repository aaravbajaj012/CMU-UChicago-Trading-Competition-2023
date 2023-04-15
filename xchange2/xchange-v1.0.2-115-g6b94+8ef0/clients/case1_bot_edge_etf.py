#!/usr/bin/env python

from collections import defaultdict
from typing import DefaultDict, Dict, List
from utc_bot import UTCBot, start_bot
import math
import proto.utc_bot as pb
import betterproto
import asyncio
import re

DAYS_IN_MONTH = 21
DAYS_IN_YEAR = 252
INTEREST_RATE = 0.02
NUM_FUTURES = 14
TICK_SIZE = 0.01
CARRYING_COST = 0.10
FUTURE_CODES = [chr(ord('A') + i) for i in range(NUM_FUTURES)] # Suffix of monthly future code
CONTRACTS = ['SBL'] +  ['LBS' + c for c in FUTURE_CODES] + ['LLL']

MOVING_AVG_WINDOW = 20

MIN_EDGE = 0.10
FADE = 0.01
SLACK = 0.10
NUM_LEVELS = 4

LEVEL_SPREAD = 0.02

ORDER_SIZE = 60

LEVELS_ENABLED = True

# 2023: m = 1.7838804404379633  b = 54.849618905657714
# 2024: m = 1.60005651307329  b = 54.890769908266975
# 2025: m = 1.4162325857086162  b = 54.931920910876244
# 2026: m = 1.2324086583439426  b = 54.973071913485505
WEATHER_TO_PRICE_M = 1.7838804404379633
WEATHER_TO_PRICE_B = 54.849618905657714

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

        #Competition event messages
        if kind == "generic_msg":
            msg = update.generic_msg.message
            print(type(msg))
            
            # Used for API DO NOT TOUCH
            if 'trade_etf' in msg:
                self.etf_suffix = msg.split(' ')[1]
                
            # Updates current weather
            if "Weather" in msg:
                weather = float(re.findall("\d+\.\d+", msg)[0])
                self._weather_log_PS.append(self._weather_log_PS[-1] + weather)
                self._weather_log.append(weather)
                for asset in CONTRACTS:
                    self._fair_price[asset] = self.calculate_future_fair_price_weighted(asset, WEIGHTS)
                
            # Updates date
            if "Day" in msg:
                self._day = int(re.findall("\d+", msg)[0])
                            
            # Updates positions if unknown message (probably etf swap)
            else:
                resp = await self.get_positions()
                if resp.ok:
                    self.positions = resp.positions

         
        elif kind == "market_snapshot_msg":
            for asset in CONTRACTS:
                book = update.market_snapshot_msg.books[asset]
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

        self._ask_order_px: Dict[str, float] = defaultdict(
            lambda: 0
        )

        self._bid_order_qty: Dict[str, int] = defaultdict(
            lambda: 0
        )
        
        self._ask_order_qty: Dict[str, int] = defaultdict(
            lambda: 0
        )
        
        self.bid_id: Dict[str, str] = defaultdict(
            lambda: ""
        )

        self._ask_id: Dict[str, str] = defaultdict(
            lambda: ""
        )


        ### TODO Recording fair price for each asset
        self._fair_price: DefaultDict[str, float] = defaultdict(
            lambda: 55
        )

        self._bid_levels: DefaultDict[str, List[str]] = defaultdict(
            lambda: [str(i) for i in range(NUM_LEVELS)]
        )

        self._ask_levels: DefaultDict[str, List[str]] = defaultdict(
            lambda: [str(i+NUM_LEVELS) for i in range(NUM_LEVELS)]
        )

        
        ### List of weather reports
        self._weather_log = []
        self._weather_log_PS = [0]
        
        
        await asyncio.sleep(.1)
        
        # Starts market making for each asset
        # for asset in CONTRACTS:
        #     asyncio.create_task(self.make_market_asset(asset))


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
        if self._fair_price[asset] - self._best_bid[asset] < MIN_EDGE:
            return MIN_EDGE
        elif self._fair_price[asset] - self._best_bid[asset] > (MIN_EDGE + SLACK):
            return MIN_EDGE + SLACK
        else:
            return self._fair_price[asset] - self._best_bid[asset] - 0.01
        
    def calculate_ask_edge(self, asset):
        if self._best_ask[asset] - self._fair_price[asset] < MIN_EDGE:
            return MIN_EDGE
        elif self._best_ask[asset] - self._fair_price[asset] > (MIN_EDGE + SLACK):
            return MIN_EDGE + SLACK
        else:
            return self._best_ask[asset] - self._fair_price[asset] - 0.01

    async def place_levels(self, asset: str, bid_px: float, ask_px : float):
        for i in range(1, NUM_LEVELS+1):

            r = await self.modify_order(
                order_id=self._bid_levels[asset][i-1],
                asset_code = asset,
                order_type = pb.OrderSpecType.LIMIT,
                order_side = pb.OrderSpecSide.BID,
                qty = ORDER_SIZE,
                price = round_nearest(bid_px - i * LEVEL_SPREAD)
            )

            self._bid_levels[asset][i-1] = r.order_id

            r = await self.modify_order(
                order_id=self._ask_levels[asset][i-1],
                asset_code = asset,
                order_type = pb.OrderSpecType.LIMIT,
                order_side = pb.OrderSpecSide.ASK,
                qty = ORDER_SIZE,
                price = round_nearest(ask_px + i * LEVEL_SPREAD)
            )

            self._ask_levels[asset][i-1] = r.order_id

        
    async def make_market_asset(self, asset: str):

        while self.days_to_expiry(asset) >= 0:
            await asyncio.sleep(.1)
            # if days_to_expiry > 1:
                # get the fair price
                # get the current position size
                # get the faded fair price
                # calculate edge around faded fair price using edge/slack/penny in
                # place order pair and levels (make sure to do it in right order)
                
                # update the relevant variables 
                # - update current market bid ask prices
                # - update new levels
        
            # elif days_to_expiry == 1:
            #  - close our current open positions
            #     - if you have a long position:
            #         - (if best market future bid price > current market soybean bid price) (sell futures)
            #         - (else sell soybean)
            #     - else: (short positions)
            #         - 
            #  - cancel current orders for that asset

            # else: (<= 0)
            # - clear all soybean positions 
            
       
        

def round_nearest(x):
    return round(round(x / 0.01) * 0.01, 2)             


if __name__ == "__main__":
    start_bot(Case1Bot)
