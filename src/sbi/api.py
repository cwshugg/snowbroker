# Python module responsible for send requests to the Alpaca web API to make
# order requests and perform other operations.
#
#   Connor Shugg

# Imports
import os
import requests
from datetime import datetime
from enum import Enum

# My imports
import config
import utils
from utils import IR
from asset import Asset, AssetGroup, PriceDataPoint
import stats

api_key = None          # API key for web requests - loaded in from file


# =============================== Order Class =============================== #
# Enum for specifying WHAT to do in an order.
class TradeOrderAction(Enum):
    BUY = 0
    SELL = 1

# The order class is used to represent a single order submitted to alpaca for
# processing.
class TradeOrder:
    # Constructor. Takes in the following parameters:
    #   symbol          The symbol representing what stock/thing we want
    #   action          The order action to take (enum). Either BUY or SELL
    # With optional parameters:
    #   order_id        The order ID number, if any
    #   value           The order dollar value, if any
    # As of right now, the default type is a market day order (completed at the
    # current market price, and is attempted to be filled during the current
    # day's normal market operating hours. If it's not filled that day, it is
    # cancelled).
    # If no value is given, the value will be computed from the given asset.
    def __init__(self, symbol: str, action: TradeOrderAction,
                 value: float, order_id=None):
        self.symbol = symbol
        self.action = action
        self.value = value
        self.id = order_id
    
    # --------------------------- JSON Functions ---------------------------- #
    # Converts the order into JSON readable by the Alpaca API.
    def json_make(self):
        action_str = "buy" if self.action == TradeOrderAction.BUY else "sell"

        # finally, construct and return the dictionary
        jdata = {
            "symbol": self.symbol,                      # asset symbol
            "notional": self.value,                     # dollar amount
            "side": action_str,                         # action, as a string
            "type": "market",                           # order type, as string
            "time_in_force": "day"                      # time to complete
        }
        if self.id != None:
            jdata["id"] = self.id
        return jdata
    
    # Takes in decoded JSON and attempts to build a TradeOrder object from it.
    @staticmethod
    def json_parse(jdata: dict):
        # check the expected keys and types
        expect = [["symbol", str], ["notional", str], ["side", str],
                  ["type", str], ["time_in_force", str], ["id", str]]
        if not utils.json_check_keys(jdata, expect):
            return None
        
        # try to convert the "notional" field into a float
        res = utils.str_to_float(jdata["notional"])
        if not res.success:
            return res
        val = res.data
        
        # otherwise, build the order object and return it (the asset object
        # will be somewhat incomplete)
        action = TradeOrderAction.BUY if jdata["side"] == "buy" else TradeOrderAction.SELL
        return TradeOrder(jdata["symbol"], action,
                          order_id=jdata["id"],
                          value=val)
    

# ================================ API Class ================================ #
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
    # https://alpaca.markets/docs/api-documentation/api-v2/clock/
    def get_market_status(self) -> IR:
        # make the request and return on a non-200 response
        response = requests.get(self.make_url("/v2/clock"),
                                headers=self.make_headers())
        if response.status_code != 200:
            return IR(False, msg="received status: %d" % response.status_code)
        
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
    # https://alpaca.markets/docs/api-documentation/api-v2/positions/
    def get_assets(self) -> IR:
        response = requests.get(self.make_url("/v2/positions"), headers=self.make_headers())
        if response.status_code != 200:
            return IR(False, msg="received status: %d" % response.status_code)
        
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

    # Pings alpaca for a summary of pending orders we've placed in the past.
    # If the optional 'order_id'' field is set, only that specific order will
    # be asked for.
    # https://alpaca.markets/docs/api-documentation/api-v2/orders/
    def get_orders(self, order_id=None) -> IR:
        # if the ID is set, we'll request just a single order
        url = self.make_url("/v2/orders")
        if order_id != None:
            url += "/%s" % order_id
        
        # make the HTTP request
        response = requests.get(self.make_url("/v2/orders"), headers=self.make_headers())
        if response.status_code != 200:
            return IR(False, msg="received status: %d" % response.status_code)
        
        # extract JSON content
        jdata = self.extract_response_json(response)
        if jdata == None:
            return IR(False, msg="could not parse response body as JSON")
        return IR(True, data=jdata)
    
    # Used to submit an order to the Alpaca API. Returns a new TradeOrder upon
    # a successful submission.
    def send_order(self, order: TradeOrder) -> IR:
        # send the response with the JSON data
        response = requests.post(self.make_url("/v2/orders"),
                                 headers=self.make_headers(),
                                 json=order.json_make())
        if response.status_code != 200:
            return IR(False, msg="received status: %d" % response.status_code)
        
        # extract JSON content and attempt to parse an order from it
        jdata = self.extract_response_json(response)
        if jdata == None:
            return IR(False, msg="could not parse response body as JSON")
        print("ORDER RESPONSE:\n%s" % json.dumps(jdata, indent=4))
        returned_order = TradeOrder.json_parse(jdata)
        if returned_order == None:
            return IR(False, msg="failed to convert JSON to TradeOrder")
        return IR(True, data=returned_order)
    
    # Attempts to cancel an order, given the order ID.
    def cancel_order(self, order_id: str) -> IR:
        pass
