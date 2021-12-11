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
                return IR(False, msg="failed to parse JSON data as an asset (%s)" %
                          fpath)
            return IR(True, data=a)
        except Exception as e:
            return IR(False, msg="failed to parse string as JSON (%s): %s" %
                      (fpath, e))


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
    
    # ------------------------ Asset List Functions ------------------------- #
    # Appends a given asset to the asset group's internal list.
    def append(self, asset: Asset) -> IR:
        self.assets.append(asset)

    # --------------------- Asset Group Saving/Loading ---------------------- #
    # Takes in a path specifying a new directory to be created. This directory
    # will be created, and each asset will be saved into the directory.
    def save(self, dpath: str) -> IR:
        # if the given path points to a file, return
        if os.path.isfile(dpath):
            return IR(False, msg="the given path (%s) is a file" % dpath)
        # if the directory doesn't exist, create it
        if not os.path.exists(dpath):
            try:
                os.mkdir(dpath)
            except Exception as e:
                return IR(False, msg="failed to create directory (%s): %s" %
                          (dpath, e))
        
        # save a small JSON file containing information about the asset group
        jdata = {"name": self.name}
        res = utils.file_write_all(os.path.join(dpath, AssetGroup.info_fname),
                                   json.dumps(jdata))
        if not res.success:
            return res

        # for each asset, build a file path string and save it to a JSON file
        fpaths = []
        for asset in self.assets:
            # build a file path, but account for collisions in file names
            sym = asset.symbol.lower()
            fpath = os.path.join(dpath, utils.str_to_fname(sym, "json"))
            count = 1
            while fpath in fpaths:
                fname = utils.str_to_fname("%s-%d" % (sym, count), "json")
                fpath = os.path.join(dpath, fname)
                count += 1
            fpaths.append(fpath)
            print("FPATH: %s" % fpath)

            res = asset.save(fpath)
            # on some sort of saving error, return it
            if not res.success:
                return res
        return IR(True)

    # Static method used to load in a new asset group from a given directory.
    # Returns a new asset group on success.
    @staticmethod
    def load(dpath: str) -> IR:
        # if the path doesn't exist or isn't a directory, return
        if not os.path.isdir(dpath):
            return IR(False, msg="the given path (%s) is not a directory" % dpath)

        # otherwise, attempt to access the information JSON file within to
        # learn the asset group's name
        ifpath = os.path.join(dpath, AssetGroup.info_fname)
        res = utils.file_read_all(ifpath)
        if not res.success:
            return res
        ag = None
        try:
            # attempt to convert to JSON and parse out a few fields
            jdata = json.loads(res.data)
            ag = AssetGroup(jdata["name"])
        except Exception as e:
            return IR(False, "failed to parse info file (%s): %s" % (ifpath, e))

        # otherwise we'll iterate through the directory's files
        for root, dirs, files in os.walk(dpath):
            for fname in files:
                # skip any non-JSON files, or the info file
                if not fname.endswith(".json") or fname == AssetGroup.info_fname:
                    continue
                # otherwise, attempt to load it in as an asset
                res = Asset.load(os.path.join(root, fname))
                if not res.success:
                    return res
                # add the asset to the asset group's list
                ag.append(res.data)
        return IR(True, data=ag)
