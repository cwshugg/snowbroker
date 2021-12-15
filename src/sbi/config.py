# Python module dedicated to reading in snowbanker configuration files.
#
#   Connor Shugg

# Imports
import os
import sys
import json

# Enable import from the main src directory
sbi_dpath = os.path.dirname(os.path.realpath(__file__))
src_dpath = os.path.dirname(sbi_dpath)
if src_dpath not in sys.path:
    sys.path.append(src_dpath)

# My imports
import sbi.utils as utils
from sbi.utils import IR

# ============================= Config Globals ============================== #
# Web API globals
api_url = "https://paper-api.alpaca.markets"        # alpaca API url

# Key file globals
key_dpath = "/home/snowmiser/snowbanker/keys"
key_api_fname = "alpaca_paper_api.key"              # alpaca API key
key_api_secret_fname = "alpaca_paper_secret.key"    # alpaca secret key

# Asset-related globals
asset_phistory_length = 100 # how many data points to keep for price history

# Strategy globals
strat_name = None
strat_tick_rate = 0
strat_work_dpath = None
strat_config_fpath = None


# ============================ Config Functions ============================= #
# Helper function that initializes globals for API config settings.
def config_init_api(jdata: dict) -> IR:
    # make sure all the necessary entries are present
    expected = [["url", str]]
    if not utils.json_check_keys(jdata, expected):
        return IR(False, msg="missing or invalid API config settings")
    
    # set up all globals
    global api_url
    api_url = jdata["url"]
    return IR(True)

# Initializes global key-related settings.
def config_init_keys(jdata: dict) -> IR:
    # make sure all the necessary entries are present
    expected = [["dpath", str], ["api_fname", str], ["secret_fname", str]]
    if not utils.json_check_keys(jdata, expected):
        return IR(False, msg="missing or invalid key config settings")
    
    # set key-related globals
    global key_dpath, key_api_fname, key_secret_fname
    key_dpath = jdata["dpath"]
    key_api_fname = jdata["api_fname"]
    key_secret_fname = jdata["secret_fname"]
    return IR(True)

# Initializes global asset-related settings.
def config_init_assets(jdata: dict) -> IR:
    # make sure all the necessary entries are present
    expected = [["phistory_length", int]]
    if not utils.json_check_keys(jdata, expected):
        return IR(False, msg="missing or invalid asset config settings")

    # set asset-related globals
    global asset_phistory_length
    asset_phistory_length = jdata["phistory_length"]
    return IR(True)

# Initializes global strategy-related settings.
def config_init_strat(jdata: dict) -> IR:
    # make sure all keys are present
    expected = [["name", str], ["tick_rate", int],
                ["work_dpath", str], ["config_fpath", str]]
    if not utils.json_check_keys(jdata, expected):
        return IR(False, msg="missing or invalid strategy config settings")
    
    # set strategy-related globals
    global strat_name, strat_tick_rate, strat_work_dpath, strat_config_fpath
    strat_name = jdata["name"].lower()
    strat_tick_rate = jdata["tick_rate"]
    strat_work_dpath = jdata["work_dpath"]
    strat_config_fpath = jdata["config_fpath"]
    return IR(True)

# Initializes the globa configuration settings, given a path to a snowbanker
# configuration JSON file.
def config_init(fpath: str) -> IR:
    # read the entire file into memory (shouldn't be too big)
    res = utils.file_read_all(fpath)
    if not res.success:
        return res
    
    # attempt to parse it as JSON
    data = None
    try:
        data = json.loads(res.data)
    except Exception as e:
        return IR(False, msg="failed to convert file content (%s) to JSON: %s" %
                  (fpath, e))
    
    # make checks for all the necessary keys
    expected = [["api", dict], ["keys", dict], ["assets", dict]]
    if not utils.json_check_keys(data, expected):
        return res(False, msg="failed to find all necessary config entries (%s): %s" %
                   (fpath, expected))

    # set up an array of expected keys, each with their own sub-data and their
    # own handler functions. Then, iterate through each and hope we get back
    # successes from each. Otherwise, there was something missing/wrong in the
    # config file
    sub_handlers = [
        ["api", config_init_api],
        ["keys", config_init_keys],
        ["assets", config_init_assets],
        ["strat", config_init_strat]
    ]
    for sub in sub_handlers:
        res = sub[1](data[sub[0]])
        if not res.success:
            return IR(False, msg="failed to read config['%s']: %s" %
                      (sub[0], res.message))
    return IR(True)
