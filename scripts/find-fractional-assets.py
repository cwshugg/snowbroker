#!/usr/bin/python3
# A script to parse through a JSON file returned from a /v2/assets request to
# locate assets that are fractional.
#
#   Connor Shugg

# Imports
import sys
import requests
import time

# Globals
alpaca_url = "https://paper-api.alpaca.markets"
alpaca_api_key_fpath = "/home/snowmiser/snowbanker/keys/alpaca_paper_api.key"
alpaca_secret_key_fpath = "/home/snowmiser/snowbanker/keys/alpaca_paper_secret.key"
alpaca_headers = {"APCA-API-KEY-ID": None,
                  "APCA-API-SECRET-KEY": None}

# Main function.
def main():    
    # read keys from the given file paths
    key_api = ""
    key_secret = ""
    global alpaca_api_key_fpath, alpaca_secret_key_fpath
    with open(alpaca_api_key_fpath, "r") as fp:
        key_api = fp.read()
    with open(alpaca_secret_key_fpath, "r") as fp:
        key_secret = fp.read()

    # build the headers
    global alpaca_headers
    alpaca_headers["APCA-API-KEY-ID"] = key_api
    alpaca_headers["APCA-API-SECRET-KEY"] = key_secret

    # first make a request to the assets endpoint to get all asset IDs
    res = requests.get(alpaca_url + "/v2/assets",
                       headers=alpaca_headers)
    if res.status_code != 200:
        sys.stderr.write("Got response: %d" % res.status_code)
        sys.exit(2)

    # try to parse the json data
    jdata = res.json()

    # next iterate through each entry and look for the correct field that
    # specifies whether or not the entry is fractionable
    for asset in jdata:
        # if the asset isn't fractionable, we don't care
        if not asset["fractionable"]:
            continue
        # print the symbol
        print(asset["symbol"])

# Runner code.
if __name__ == "__main__":
    main()
