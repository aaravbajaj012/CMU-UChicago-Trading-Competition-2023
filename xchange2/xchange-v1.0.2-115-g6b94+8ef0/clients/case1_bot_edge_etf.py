#!/usr/bin/env python

from collections import defaultdict
import time
from typing import DefaultDict, Dict, Tuple
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
FUTURE_CODES = [chr(ord('A') + i) for i in range(NUM_FUTURES)] # Suffix of monthly future code
CONTRACTS = ['SBL'] +  ['LBS' + c for c in FUTURE_CODES] + ['LLL']


MIN_EDGE = 0.10
FADE = 0.01
SLACK = 0.10
NUM_LEVELS = 5
LEVELS = [i * (MIN_EDGE + SLACK) for i in range(1, NUM_LEVELS + 1)]


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
        return self._day - expiry

    async def handle_exchange_update(self, update: pb.FeedMessage):
        '''
        Handles exchange updates
        '''
        kind, _ = betterproto.which_one_of(update, "msg")
        #Competition event messages
        if kind == "generic_msg":
            msg = update.generic_msg.message
            
            # Used for API DO NOT TOUCH
            if 'trade_etf' in msg:
                self.etf_suffix = msg.split(' ')[1]
                
            # Updates current weather
            if "Weather" in update.generic_msg.message:
                msg = update.generic_msg.message
                weather = float(re.findall("\d+\.\d+", msg)[0])
                self._weather_log.append(weather)
                for asset in CONTRACTS:
                    await self.calculate_fair_price(asset)
                #print(time.time(), "Weather:", weather)
                #print("_________________________")
                
            # Updates date
            if "Day" in update.generic_msg.message:
                self._day = int(re.findall("\d+", msg)[0])
                #print("Day:", self._day, "Positions:", self.positions)
                #print("Positions: ", self.positions)
                #print("_________________________")
                            
            # Updates positions if unknown message (probably etf swap)
            else:
                resp = await self.get_positions()
                if resp.ok:
                    self.positions = resp.positions

                    
        elif kind == "MarketSnapshotMessage":
            for asset in CONTRACTS:
                book = update.market_snapshot_msg.books[asset]
                self._best_bid[asset] = float(book.bids[0].px)
                self._best_ask[asset] = float(book.asks[0].px)
                self._best_bid_qty[asset] = int(book.bids[0].qty)
                self._best_ask_qty[asset] = int(book.asks[0].qty)
            


    async def handle_round_started(self):
        ### Current day
        self._day = 0
        ### Best Bid in the order book
        self._best_bid: Dict[str, float] = defaultdict(
            lambda: 0
        )

        self._best_bid_qty: Dict[str, int] = defaultdict(
            lambda: 0
        )

        ### Best Ask in the order book
        self._best_ask: Dict[str, float] = defaultdict(
            lambda: 0
        )

        self._best_ask_qty: Dict[str, int] = defaultdict(
            lambda: 0
        )

        ### Order book for market making
        self.__orders: DefaultDict[str, Tuple[str, float]] = defaultdict(
            lambda: ("", 0)
        )

        self._bid_orders: DefaultDict[str, Tuple[str, float]] = defaultdict(
            lambda: ("", 0)
        )

        self._ask_orders: DefaultDict[str, Tuple[str, float]] = defaultdict(
            lambda: ("", 0)
        )

        ### TODO Recording fair price for each asset
        self._fair_price: DefaultDict[str, float] = defaultdict(
            lambda: 55
        )
        ### TODO spread fair price for each asset
        self._spread: DefaultDict[str, float] = defaultdict(
            lambda: MIN_EDGE
        )

        ### TODO order size for market making positions
        self._quantity: DefaultDict[str, int] = defaultdict(
            lambda: 1
        )
        
        ### List of weather reports
        self._weather_log = []
        
        await asyncio.sleep(.1)
        ###
        ### TODO START ASYNC FUNCTIONS HERE
        ###
        #asyncio.create_task(self.example_redeem_etf())
        
        # Starts market making for each asset
        for asset in CONTRACTS:
            asyncio.create_task(self.make_market_asset(asset))

    # This is an example of creating and redeeming etfs
    # You can remove this in your actual bots.
    async def example_redeem_etf(self):
        while True:
            redeem_resp = await self.redeem_etf(1)
            create_resp = await self.create_etf(5)
            await asyncio.sleep(1)


    ### Helpful ideas
    async def calculate_risk_exposure(self):
        pass
    
    # CHANGE FOR OUR FAIR PRICE MODEL
    async def calculate_fair_price(self, asset):
        #print("Calculating fair price for", asset)
        self._fair_price[asset] = (self._best_bid[asset] + self._best_ask[asset]) / 2
        if self._fair_price[asset] < 25:
            self._fair_price[asset] = 55

    async def calculate_bid_edge(self, asset):
        if self._fair_price[asset] - self._best_bid[asset] < MIN_EDGE:
            return MIN_EDGE
        elif self._fair_price[asset] - self._best_bid[asset] > (MIN_EDGE + SLACK):
            return MIN_EDGE + SLACK
        else:
            return self._fair_price[asset] - self._best_bid[asset] - 0.01
        
    async def calculate_ask_edge(self, asset):
        if self._best_ask[asset] - self._fair_price[asset] < MIN_EDGE:
            return MIN_EDGE
        elif self._best_ask[asset] - self._fair_price[asset] > (MIN_EDGE + SLACK):
            return MIN_EDGE + SLACK
        else:
            return self._best_ask[asset] - self._fair_price[asset] - 0.01
        
    async def find_arbitrage(self):
        # calculate bid price of ETF
        # calculate fair value of underlying assets that compose ETF
        # calculate the most recently expiring future
        month = (self._day-1) // 21 + 1
        contract1 = CONTRACTS[month + 1]
        contract2 = CONTRACTS[month + 2]
        contract3 = CONTRACTS[month + 3]
        if self._best_ask["LLL"] < 5 * self._best_bid[contract1] + 3 * self._best_bid[contract2] + 2 * self._best_bid[contract3]:
            minETFQty = min(self._best_ask_qty["LLL"], self._best_bid_qty[contract1], self._best_bid_qty[contract2], self._best_bid_qty[contract3])
            r1 = await self.place_order(
                        asset_code = "LLL",
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.BID,
                        qty = minETFQty
                    )
            #self.__orders["LLL"] = (r1.order_id, r1.order_price)
            r2 = await self.place_order(
                        asset_code = contract1,
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.ASK,
                        qty = minETFQty * 5
                    )
            r3 = await self.place_order(
                        asset_code = contract2,
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.ASK,
                        qty = minETFQty * 3
                    )
            r4 = await self.place_order(
                        asset_code = contract3,
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.ASK,
                        qty = minETFQty * 2
                    )
            
            self.redeem_etf(minETFQty)
        elif self._best_bid["LLL"] > 5 * self._best_ask[contract1] + 3 * self._best_ask[contract2] + 2 * self._best_ask[contract3]:
            minETFQty = min(self._best_bid_qty["LLL"], self._best_ask_qty[contract1], self._best_ask_qty[contract2], self._best_ask_qty[contract3])
            r1 = await self.place_order(
                        asset_code = "LLL",
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.ASK,
                        qty = minETFQty
                    )
            #self.__orders["LLL"] = (r1.order_id, r1.order_price)
            r2 = await self.place_order(
                        asset_code = contract1,
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.BID,
                        qty = minETFQty * 5
                    )
            r3 = await self.place_order(
                        asset_code = contract2,
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.BID,
                        qty = minETFQty * 3
                    )
            r4 = await self.place_order(
                        asset_code = contract3,
                        order_type = pb.OrderSpecType.MARKET,
                        order_side = pb.OrderSpecSide.BID,
                        qty = minETFQty * 2
                    )
            self.create_etf(minETFQty)
            

        
    async def make_market_asset(self, asset: str):
        while self.days_to_expiry(asset) > 0:
            ## Old prices
            ub_oid, ub_price = self.__orders["underlying_bid_{}".format(asset)]
            ua_oid, ua_price = self.__orders["underlying_ask_{}".format(asset)]
            
            bid_edge = await self.calculate_bid_edge(asset)
            ask_edge = await self.calculate_ask_edge(asset)
            bid_px = self._fair_price[asset] - bid_edge
            ask_px = self._fair_price[asset] + ask_edge
            
            # If the underlying price moved first, adjust the ask first to avoid self-trades
            if (bid_px + ask_px) > (ua_price + ub_price):
                order = ["ask", "bid"]
            else:
                order = ["bid", "ask"]

            for d in order:
                if d == "bid":
                    order_id = ub_oid
                    order_side = pb.OrderSpecSide.BID
                    order_px = bid_px
                else:
                    order_id = ua_oid
                    order_side = pb.OrderSpecSide.ASK
                    order_px = ask_px

                r = await self.modify_order(
                        order_id = order_id,
                        asset_code = asset,
                        order_type = pb.OrderSpecType.LIMIT,
                        order_side = order_side,
                        qty = self._quantity[asset],
                        px = round_nearest(order_px, TICK_SIZE), 
                    )
                self.__orders[f"underlying_{d}_{asset}"] = (r.order_id, order_px)
                print(f"Modified {d} order for {asset} to {order_px} on day {self._day} at {r.order_id}")                
        

def round_nearest(x, a):
    return round(round(x / a) * a, -int(math.floor(math.log10(a))))             



if __name__ == "__main__":
    start_bot(Case1Bot)
