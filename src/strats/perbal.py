# This is the "percent balance" strategy. If my understanding of index funds is
# correct, this is effectively emulating an index fund.
# 
# It looks at all the assets in the account, and uses user-chosen percents of
# how much money the asset should make up. With these percents, at each tick,
# it looks at how far above/under each asset has gone in its percent, and makes
# buy/sell orders accordingly to set the percents back to what they were.
# This means assets that increased will have part of it sold, and that money
# will be used to invest in assets that decreased. Overall, hopefully it should
# increase.
#
# Thanks Dad for showing me how to do this manually on a spreadsheet. That's
# what got me thinking about writing this program.
#
#   Connor Shugg

# Imports
import os
import sys

# Enable import from the parent directory
strat_dpath = os.path.dirname(os.path.realpath(__file__))
src_dpath = os.path.dirname(strat_dpath)
if src_dpath not in sys.path:
    sys.path.append(src_dpath)

# My imports
from sbi.strat import Strategy
from sbi.asset import Asset, AssetGroup
import sbi.utils as utils
from sbi.utils import IR

# Main strategy class.
class PBStrat(Strategy):
    assets_fname = "assets.json"

    # Overriden initialization function. Takes in a percent profile config
    # file path (optional) to initialize the strategy's percent profile with.
    def init(self, dpath: str, pp_fpath=None) -> IR:
        # run the inherited init sequence first
        res = super().init(dpath)
        if not res.success:
            return res
        
        # get an updated version of our assets
        res = self.retrieve_assets()
        if not res.success:
            return res
        assets: AssetGroup = res.data

        # initialize the percent profile
        self.pp_init(assets, fpath=pp_fpath)
        return IR(True)

    # The strategy's tick implementation.
    def tick(self) -> IR:
        print("TODO: tick")
    
    # Function used to retrieve saved asset history from disk AND make an API
    # call to update it, if necessary. Returns an asset group on success.
    def retrieve_assets(self) -> IR:
        # first, attempt to load in previously-saved asset history
        asset_fpath = os.path.join(self.work_dpath, PBStrat.assets_fname)
        res = AssetGroup.load(asset_fpath)
        assets = None
        if res.success:
            assets: AssetGroup = res.data

        # next, use the API to get our current assets
        res = self.api.get_assets()
        if not res.success:
            return res
        new_assets: AssetGroup = res.data

        # update the old asset group, if it exists
        if assets != None:
            for a in new_assets:
                res = assets.update(a)
                if not res.success:
                    return res
        else:
            assets = new_assets
        
        # write the assets back out to disk, then return the group
        res = assets.save(asset_fpath)
        if not res.success:
            return res
        return IR(True, data=assets)
    
    # --------------------------- Percent Profile --------------------------- #
    # The "percent profile" is the makeup of assets and their respective
    # percentages this strategy will uphold. The strategy will come up with
    # default percentages (given the asset group we retrieved from an API call),
    # but the 'fpath' param can also be specified to load in specific
    # percentages.
    def pp_init(self, assets: AssetGroup, fpath=None) -> IR:
        self.pp = {}
        # if we were given a file path, we'll try to read it in and parse it as
        # a JSON dictionary
        if fpath != None:
            res = utils.file_read_all(fpath)
            if not res.success:
                return res
            jdata = utils.json_try_loads(res.data)
            if jdata == None:
                return IR(False, msg="failed to read file contents (%s) as JSON" % fpath)

            # take the dictionary we read and set up our percent profile with
            # each key being an asset symbol, expecting a float (percent) as
            # the key's value
            for key in jdata:
                if type(jdata[key]) != float:
                    return IR(False, "JSON data key '%s' has a bad value (%s)" %
                              (key, fpath))
                # we'll store the percent as a value between 0-1 internally
                self.pp[key] = jdata[key] / 100.0
            return IR(True)
        
        # at this point, we know a file path WASN'T given, so we'll instead try
        # to come up with some default percents given the asset group
        asset_total = float(len(assets))
        if asset_total == 0.0:
            return IR(False, "the given asset group was empty")
        # divide 100% by the number of assets - we'll default to a totally
        # equal split
        equal_percent = 1.0 / asset_total
        for asset in assets:
            self.pp[asset.symbol] = equal_percent
        return IR(True)
        

# TEST CODE
import json

s = PBStrat("Test Percent-Balance", 1)
res = s.init("/home/snowmiser/snowbanker/src/strats/pb")
print("INIT RESULT: %s" % res)
print("PERCENT PROFILE:\n%s" % json.dumps(s.pp))
