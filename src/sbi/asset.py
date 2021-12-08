# This module implements an interface for creating, modifying, loading, and
# saving "assets" - some sort of stock/fund/bond/whatever.
#
#   Connor Shugg

# Imports
from datetime import datetime
import json
import config


# ========================= Price Data Point Class ========================== #
# Price data point. A simple class that keeps track of a single price value and
# pairs it with a time/date.
class PriceDataPoint:
    # Constructor: takes in the price and timestamp and saves it.
    def __init__(self, price: float, timestamp: datetime):
        self.price = price
        self.timestamp = timestamp
    
    # Returns the timestamp value in total seconds (as a float).
    def timestamp_total_seconds(self):
        return self.timestamp.timestamp()


# ============================ Main Asset Class ============================= #
# Main asset class.
class Asset:
    # Constructor. Takes in the following fields:
    #   name        The asset's name
    #   symbol      The asset's official market symbol
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        # set a few other fields to default values
        self.phistory = [] # price history: begins as an empty array
    
    # ----------------------- Price History Functions ----------------------- #
    # Appends a single price data point to the asset's price history. If the
    # asset's price history is full, the oldest data point will be evicted.
    # Returns true on a successful append and false otherwise.
    def phistory_append(self, pdp: PriceDataPoint):
        # if our history is empty, append without question
        phlen = len(self.phistory)
        if phlen == 0:
            self.phistory.append(pdp)

        # otherwise, make sure the current pdp's timestamp is LATER than latest
        # one stored in our price history
        latest = self.phistory[phlen - 1]
        if pdp.timestamp_total_seconds() <= latest.timestamp_total_seconds():
            return False

        # if the price history is full, we'll remove the oldest entry
        if len(self.phistory) == config.asset_phistory_length:
            self.phistory.pop()
        self.phistory.append(pdp)
    
    # ------------------------ Computation Functions ------------------------ #
    # Computes the rate of return based on what's stored in the price history.
    def compute_ror(self):
        # TODO
        pass

    # ------------------- Asset Saving/Loading Functions -------------------- #
    # Saves the asset to a file specified by 'fpath'.
    def save(self, fpath: str):
        # TODO - write to JSON file
        pass
    
    # Static method that attempts to load in and return an Asset from a file
    # created by a previous call to save(). Returns None on failure and an
    # Asset object on success.
    @staticmethod
    def load(fpath: str):
        # TODO - load from JSON file
        pass
