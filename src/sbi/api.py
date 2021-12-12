# Python module responsible for send requests to the Alpaca web API to make
# order requests and perform other operations.
#
#   Connor Shugg

# Imports
import os
import requests
from datetime import datetime

# My imports
import config
import utils
from utils import IR
from asset import Asset, AssetGroup, PriceDataPoint

api_key = None          # API key for web requests - loaded in from file

# Main TradeAPI class. Defines functions used to make alpaca API calls to send
# and receive information.
class TradeAPI:
    # Constructor.
    def __init__(self):
        self.key_api = None     # web API key
        self.key_secret = None  # web secret key
    
    # ------------------------ Init/Helper Functions ------------------------ #
    # Used to load the API's keys from files. File paths are taken from the
    # config module.
    def load_keys(self) -> IR:
        # first, load the API key from disk
        api_fpath = os.path.join(config.key_dpath, config.key_api_fname)
        res = utils.file_read_all(api_fpath)
        if not res.success:
            return res
        self.key_api = res.data

        # next, load the secret key from disk
        secret_fpath = os.path.join(config.key_dpath, config.key_api_secret_fname)
        res = utils.file_read_all(secret_fpath)
        if not res.success:
            return res
        self.key_secret = res.data
        return IR(True)
    
    # Helper function used to build URL strings for API HTTP requests.
    def make_url(self, endpoint: str):
        fmt = "%s%s" if endpoint.startswith("/") else "%s/%s"
        return fmt % (config.api_url, endpoint)
    
    # Helper function for building a dictionary to hold HTTP headers for Alpaca
    # authentication (API keys)
    def make_headers(self):
        return {"APCA-API-KEY-ID": self.key_api,
                "APCA-API-SECRET-KEY": self.key_secret}
    
    # Helper function for attempting to parse JSON out of the server's resposne
    # body. Returns None if parsing failed.
    def extract_response_json(self, response: requests.Response) -> dict:
        try:
            return response.json()
        except Exception:
            return None

    # -------------------------- API HTTP Requests -------------------------- #
    # Pings alpaca and determines if the markets are currently open or not.
    def get_market_status(self) -> IR:
        # make the request and return on a non-200 response
        response = requests.get(self.make_url("/v2/clock"),
                                headers=self.make_headers())
        if response.status_code != 200:
            return IR(False, msg="did not receive 200 response code (%d)" %
                      response.status_code)
        
        # attempt to pull the JSON message body out
        jdata = self.extract_response_json(response)
        if jdata == None:
            return IR(False, msg="could not parse response body as JSON")
        
        # check for the correct keys, then return whether or not the markets
        # are open
        if not utils.json_check_keys(jdata, [["is_open", bool]]):
            return IR(False, msg="response JSON did not contain expected key(s)")
        return IR(True, data=jdata["is_open"])
    
    # Pings alpaca and retrieves all account positions. Returns an AssetGroup
    # on success.
    def get_assets(self) -> IR:
        response = requests.get(self.make_url("/v2/positions"),
                                headers=self.make_headers())
        if response.status_code != 200:
            return IR(False, msg="did not receive 200 response code (%d)" %
                      response.status_code)
        
        # extract JSON content
        jdata = self.extract_response_json(response)
        if jdata == None:
            return IR(False, msg="could not parse response body as JSON")
        
        # iterate through each entry in the JSON array and build assets
        ag = AssetGroup("fetched")
        for position in jdata:
            # make sure the appropriate keys are there
            expected = [["asset_id", str], ["symbol", str],
                        ["qty", str], ["current_price", str]]
            if not utils.json_check_keys(position, expected):
                return IR(False, msg="response JSON didn't have the expected keys")

            # attempt to convert the quantity to a float
            res = utils.str_to_float(position["qty"])
            if not res.success:
                return res
            quantity = res.data

            # attempt to convert the current price to a float
            res = utils.str_to_float(position["current_price"])
            if not res.success:
                return res
            price = res.data
            
            # create an asset object and add a single price data point to its
            # price history (with the price we just retrieved from the API).
            # Then, add the asset to the asset group
            name = position["asset_id"]
            symbol = position["symbol"]
            a = Asset(name, symbol, quantity)
            a.phistory_append(PriceDataPoint(price, datetime.now()))
            ag.append(a)
        return IR(True, data=ag)
