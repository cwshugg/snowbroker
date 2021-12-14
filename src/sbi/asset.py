# This module implements an interface for creating, modifying, loading, and
# saving "assets" - some sort of stock/fund/bond/whatever.
#
#   Connor Shugg

# Imports
import os
import sys
from datetime import datetime
import json

# Enable import from the main src directory
sbi_dpath = os.path.dirname(os.path.realpath(__file__))
src_dpath = os.path.dirname(sbi_dpath)
if src_dpath not in sys.path:
    sys.path.append(src_dpath)

# My imports
import sbi.config as config
import sbi.utils as utils
from sbi.utils import IR


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
    def json_parse(jdata: dict):
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
    #   quantity    The asset's quantity (amount owned)
    def __init__(self, name: str, symbol: str, quantity: float):
        self.name = name
        self.quantity = quantity
        self.symbol = symbol
        # set a few other fields to default values
        self.phistory = [] # price history: begins as an empty array
    
    # Used to iterate through an asset's price data points.
    def __iter__(self):
        for pdp in self.phistory:
            yield pdp
    
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
    
    # Used to retrieve the earliest (first) data point for the asset. Returns
    # None if none are present.
    def phistory_earliest(self):
        if len(self.phistory) == 0:
            return None
        return self.phistory[0]

    # Used to retrieve the latest price data point for the asset. Returns None
    # if none are present.
    def phistory_latest(self):
        phlen = len(self.phistory)
        if phlen == 0:
            return None
        return self.phistory[phlen - 1]
    
    # --------------------------- JSON Functions ---------------------------- #
    # Converts the object to JSON and returns it.
    def json_make(self) -> dict:
        # build an array of pdps, then make the json object
        pdps = []
        for pdp in self.phistory:
            pdps.append(pdp.json_make())
        return {"name": self.name, "symbol": self.symbol,
                "quantity": self.quantity, "phistory": pdps}

    # Attempts to parse a JSON object and return an Asset object.
    # Returns None on failure to parse anything.
    @staticmethod
    def json_parse(jdata: dict):
        # check the expected keys and types
        expect = [["name", str], ["symbol", str],
                  ["quantity", float], ["phistory", list]]
        if not utils.json_check_keys(jdata, expect):
            return None
        
        # otherwise, create the PDP object and load up the price history
        a = Asset(jdata["name"], jdata["symbol"], jdata["quantity"])
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
                return IR(False, msg="failed to parse JSON data as an asset (%s)" %
                          fpath)
            return IR(True, data=a)
        except Exception as e:
            return IR(False, msg="failed to parse string as JSON (%s): %s" %
                      (fpath, e))
    
    # ------------------------- Asset Computations -------------------------- #
    # Computes the asset's total value.
    def value(self) -> float:
        pdp = self.phistory_latest()
        if pdp == None:
            return 0.0
        return pdp.price * self.quantity


# ============================ Asset Group Class ============================ #
# A simple class used to contain a group of assets.
class AssetGroup:
    info_fname = "INFO.json" # class field - name of asset group info file

    # Constructor. Takes in a name for the asset group.
    def __init__(self, name: str):
        self.name = name
        self.assets = []    # array of asset objects
    
    # Used to return the length of the class.
    def __len__(self):
        return len(self.assets)
    
    # Used to iterate across the asset group's assets.
    def __iter__(self):
        for asset in self.assets:
            yield asset
    
    # ------------------------ Asset List Functions ------------------------- #
    # Searches the group for an asset with the same symbol. Returns the asset
    # on success and None on failure.
    def search(self, symbol: str) -> Asset:
        for a in self.assets:
            if a.symbol == symbol:
                return a
        return None

    # Appends a given asset to the asset group's internal list if it isn't
    # already present. If it IS already present, the asset's price history is
    # updated to hold the given asset's histories.
    def update(self, asset: Asset) -> IR:
        existing = self.search(asset.symbol)
        # if we already have the asset, we'll update its price history
        if existing != None:
            # try to append each price data point to the existing asset. The
            # 'phistory_append()' function will ensure pdps we already have are
            # NOT added to the list
            for pdp in asset:
                existing.phistory_append(pdp)
            return IR(True)

        # otherwise, we'll just append
        self.assets.append(asset)
        return IR(True)
    
    # --------------------------- JSON Functions ---------------------------- #
    # Converts the object to JSON and returns it.
    def json_make(self) -> dict:
        # first, build an array of assets in JSON form
        ajdata = []
        for asset in self.assets:
            ajdata.append(asset.json_make())
        # make and return the final JSON object
        return {"name": self.name, "assets": ajdata}

    # Attempts to parse a JSON object and return an AssetGroup object.
    # Returns None on failure to parse anything.
    @staticmethod
    def json_parse(jdata: dict):
        # check the expected keys and types
        expect = [["name", str], ["assets", list]]
        if not utils.json_check_keys(jdata, expect):
            return None
        
        # otherwise, create the asset group and load up the asset list
        ag = AssetGroup(jdata["name"])
        for a in jdata["assets"]:
            # attempt to parse the json, then add to the list
            asset = Asset.json_parse(a)
            if asset == None:
                return None
            ag.update(asset)
        return ag

    # --------------------- Asset Group Saving/Loading ---------------------- #
    # Takes in a file path and attempts to save the asset group as a JSON file.
    def save(self, fpath: str) -> IR:
        # make the JSON string
        jdata = self.json_make()
        jstr = json.dumps(jdata, indent=4)

        # attempt to open the file and write to it
        return utils.file_write_all(fpath, jstr)

    # Static method used to load in a new asset group from a given file.
    # Returns a new asset group on success.
    @staticmethod
    def load(fpath: str) -> IR:
        # make sure the file exists
        if not os.path.isfile(fpath):
            return IR(False, "failed to find file (%s)" % fpath)
        
        # attempt to read bytes from the file
        res = utils.file_read_all(fpath)
        if not res.success:
            return res
        
        # attempt to pasre the string as a json object
        try:
            jdata = json.loads(res.data)
            a = AssetGroup.json_parse(jdata)
            if a == None:
                return IR(False, msg="failed to parse JSON data as an asset (%s)" %
                          fpath)
            return IR(True, data=a)
        except Exception as e:
            return IR(False, msg="failed to parse string as JSON (%s): %s" %
                      (fpath, e))

    # ---------------------- Asset Group Computations ----------------------- #
    # Computes the total value of the asset group.
    def value(self) -> float:
        if len(self.assets) == 0:
            return 0.0
        # iterate through each asset and compute their values, adding to the sum
        ag_sum = 0.0
        for asset in self.assets:
            ag_sum += asset.value()
        return ag_sum
    
    # Computes how much of the total value each asset takes up and produces a
    # dictionary of symbol-to-percents.
    def percents(self) -> dict:
        # if we have no assets, return
        if len(self.assets) == 0:
            return {}
        # otherwise iterate through all assets and compute percents
        percents = {}
        total = self.value()
        for asset in self.assets:
            percents[asset.symbol] = asset.value() / total
        return percents
