# This module implements an interface for creating, modifying, loading, and
# saving "assets" - some sort of stock/fund/bond/whatever.
#
#   Connor Shugg

# Imports
from datetime import datetime
import json
import os

# My imports
import config
import utils
from utils import IR


# ========================= Price Data Point Class ========================== #
# Price data point. A simple class that keeps track of a single price value and
# pairs it with a time/date.
class PriceDataPoint:
    # Constructor: takes in the price and timestamp and saves it.
    def __init__(self, price: float, timestamp: datetime):
        self.price = price
        self.timestamp = timestamp
    
    # Returns the timestamp value in total seconds (as a float).
    def timestamp_total_seconds(self) -> float:
        return self.timestamp.timestamp()
        
    # --------------------------- JSON Functions ---------------------------- #
    # Converts the object to JSON and returns it.
    def json_make(self) -> dict:
        return {"price": self.price, "timestamp": self.timestamp_total_seconds()}

    # Attempts to parse a JSON object and return a PriceDataPoint object.
    # Returns None on failure.
    @staticmethod
    def json_parse(jdata):
        # check the expected keys and types
        expect = [["price", float], ["timestamp", float]]
        if not utils.json_check_keys(jdata, expect):
            return None
        
        # otherwise, create the PDP object
        return PriceDataPoint(jdata["price"],
                              datetime.fromtimestamp(jdata["timestamp"]))


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
    def phistory_append(self, pdp: PriceDataPoint) -> bool:
        # if our history is empty, append without question
        phlen = len(self.phistory)
        if phlen == 0:
            self.phistory.append(pdp)
            return True

        # otherwise, make sure the current pdp's timestamp is LATER than latest
        # one stored in our price history
        latest = self.phistory[phlen - 1]
        if pdp.timestamp_total_seconds() <= latest.timestamp_total_seconds():
            return False

        # if the price history is full, we'll remove the oldest entry
        if len(self.phistory) == config.asset_phistory_length:
            self.phistory.pop()
        self.phistory.append(pdp)
        return True
    
    # ------------------------ Computation Functions ------------------------ #
    # Computes the rate of return based on what's stored in the price history.
    # Rate of return is rounded to 4 digits.
    def compute_ror(self) -> float:
        # a simple formula for computing rate of return (as a percent) is:
        #   ((END_VALUE - BEGINNING_VALUE) / BEGINNING_VALUE) * 100

        # if we have NO price data points, return 0
        phlen = len(self.phistory)
        if phlen == 0:
            return 0.0
        # otherwise, get the earliest and most recent value and compute ROR
        begin = self.phistory[0].price
        end = self.phistory[phlen - 1].price
        begin = 0.00001 if begin == 0.0 else begin # prevent div-by-zero
        return round(((end - begin) / begin) * 100.0, 4)
    
    # --------------------------- JSON Functions ---------------------------- #
    # Converts the object to JSON and returns it.
    def json_make(self) -> dict:
        # build an array of pdps, then make the json object
        pdps = []
        for pdp in self.phistory:
            pdps.append(pdp.json_make())
        return {"name": self.name, "symbol": self.symbol,
                "phistory": pdps}

    # Attempts to parse a JSON object and return a PriceDataPoint object.
    # Returns None on failure to parse anything.
    @staticmethod
    def json_parse(jdata):
        # check the expected keys and types
        expect = [["name", str], ["symbol", str], ["phistory", list]]
        if not utils.json_check_keys(jdata, expect):
            return None
        
        # otherwise, create the PDP object and load up the price history
        a = Asset(jdata["name"], jdata["symbol"])
        for pdp in jdata["phistory"]:
            # parse the JSON and return on failure to parse
            pdp_obj = PriceDataPoint.json_parse(pdp)
            if pdp_obj == None:
                return None
            a.phistory_append(pdp_obj)
        return a

    # ------------------- Asset Saving/Loading Functions -------------------- #
    # Saves the asset to a file specified by 'fpath'.
    def save(self, fpath: str) -> IR:
        # make the JSON string
        jdata = self.json_make()
        if jdata == None:
            return IR(False, "failed to convert asset to JSON")
        jstr = json.dumps(jdata, indent=4)

        # attempt to open the file and write to it
        return utils.file_write_all(fpath, jstr)
    
    # Static method that attempts to load in and return an Asset from a file
    # created by a previous call to save().
    @staticmethod
    def load(fpath: str) -> IR:
        # first, verify the file exists
        if not os.path.isfile(fpath):
            return IR(False, "failed to find file (%s)" % fpath)
        
        # next, attempt to read bytes from the file
        res = utils.file_read_all(fpath)
        if not res.success:
            return res
        
        # attempt to pasre the string as a json object
        try:
            jdata = json.loads(res.data)
            a = Asset.json_parse(jdata)
            if a == None:
                return IR(False, "failed to parse JSON data as an asset")
            return IR(True, data=a)
        except Exception as e:
            return IR(False, "failed to parse string as JSON: %s" % e)
