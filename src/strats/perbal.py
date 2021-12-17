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
from datetime import datetime

# Enable import from the parent directory
strat_dpath = os.path.dirname(os.path.realpath(__file__))
src_dpath = os.path.dirname(strat_dpath)
if src_dpath not in sys.path:
    sys.path.append(src_dpath)

# My imports
from sbi.strat import Strategy
from sbi.asset import Asset, AssetGroup
import sbi.utils as utils
from sbi.utils import IR, float_to_str_dollar, float_to_str_maybe_round
from sbi.api import TradeOrder, TradeOrderAction

# Main strategy class.
class PBStrat(Strategy):
    assets_fname = "assets.json"
    last_order_time_fname = "last_order_time.txt"

    # Overriden initialization function. Takes in a percent profile config
    # file path (optional) to initialize the strategy's percent profile with.
    def init(self, dpath: str, config_fpath=None) -> IR:
        pp_fpath = config_fpath
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
        res = self.pp_init(assets, fpath=pp_fpath)
        if not res.success:
            return res

        # initialize some defaults and return
        self.last_order_time = 0.0      # last order time, in seconds
        self.order_rate = 24.0 * 3600.0 # number of seconds between orders
        return IR(True)

    # The strategy's tick implementation.
    def tick(self) -> IR:
        # if the markets are closed, don't bother doing anything
        if not self.api.get_market_status():
            self.log("markets are closed. Skipping this tick.")
            return IR(True)
        
        # load the last order time from a file
        res = self.last_order_time_load()
        now = datetime.now()
        time_diff = None
        time_str = "(unknown)"
        if not res.success:
            self.last_order_time = None
        else:
            self.last_order_time = res.data
            time_diff = now.timestamp() - res.data.timestamp()
            time_str = "%f seconds ago" % time_diff
        self.log("last order time: %s" % time_str)
        
        # retrieve latest asset information
        res = self.retrieve_assets()
        if not res.success:
            self.log("failed to retrieve assets: %s. Skipping this tick." % res.message)
            return res
        assets: AssetGroup = res.data
        assets_len = len(assets)
        # if we don't actually have any assets, we can't do anything
        if assets_len == 0:
            self.log("no assets found. Skipping this tick.")
            return IR(True)

        # collect only the assets in the big asset group that this strategy
        # actually cares about. Compute the total percent, out of 100, of our
        # percent profile, that's represented
        assets_wca = AssetGroup("strat assets") # "assets we care about"
        assets_wca_percent = 0.0
        if len(self.pp) == 0:
            # if we weren't actually given a percent profile, we'll create it
            # on the fly, right now, based on what assets we have.
            self.log("no percent profile specified. "
                     "Taking ALL assets into account.")
            assets_wca = assets
            assets_wca_percent = 100.0
            self.pp = {}
            for asset in assets:
                self.pp[asset.symbol] = 100.0 / float(assets_len)
        else:
            for asset in assets:
                if asset.symbol in self.pp:
                    assets_wca.update(asset)
                    assets_wca_percent += self.pp[asset.symbol]

        self.log("retrieved latest asset information:")
        assets_wca_len = len(assets_wca)
        i = 0
        for asset in assets_wca:
            prefix = utils.STAB_TREE2
            if i == assets_wca_len - 1:
                prefix = utils.STAB_TREE1
            
            # get the latest price
            pdp = asset.phistory_latest()
            price_str = "(no history)"
            if pdp != None:
                price_str = utils.float_to_str_dollar(pdp.price)
            # write to the log
            self.log("%s%-8s %s (x%s) = %s" % (prefix, asset.symbol, price_str,
                     utils.float_to_str_maybe_round(asset.quantity),
                     utils.float_to_str_dollar(asset.value())))
            i += 1
        self.log("percent profile total representation: %s%%" %
                 utils.float_to_str_maybe_round(assets_wca_percent * 100.0))
        # compute and log the total value of the assets
        assets_wca_value = assets_wca.value()
        self.log("total value: %s" % utils.float_to_str_dollar(assets_wca_value))
        
        # if the last order time is within the order time, don't proceed
        if time_diff != None and time_diff < self.order_rate:
            self.log("the last order was made too recently. "
                     "Skipping this tick.")
            return IR(True)

        # if we have ONE or ZERO assets represented, don't do anything
        if assets_wca_len == 0:
            self.log("no assets that are a part of the percent profile are "
                     "actually owned. This strategy won't do anything.")
            return IR(True)
        elif assets_wca_len == 1:
            self.log("only one asset that's a part of the percent profile is "
                     "actually owned. This strategy won't do anything.")
            return IR(True)

        # determine the percents each asset takes up in the total represented
        # amount. We'll also use this loop to compute what orders to place for
        # each asset
        assets_wca_percs = assets_wca.percents()
        orders = []
        i = 0
        for asset in assets_wca:
            val = asset.value()
            prefix1 = utils.STAB_TREE2
            prefix2 = utils.STAB_TREE3
            if i == assets_wca_len - 1:
                prefix1 = utils.STAB_TREE1
                prefix2 = utils.STAB
            
            # extract the percent it makes up and compute a difference
            sym = asset.symbol
            p = assets_wca_percs[sym]
            should_be_p = (self.pp[sym] / assets_wca_percent)
            price_diff = (should_be_p * assets_wca_value) - val

            # log it!
            self.log("%s%-8s %s%% of the total value (should be: %s%%)" %
                     (prefix1, sym, float_to_str_maybe_round(p * 100.0),
                      float_to_str_maybe_round(should_be_p * 100.0)))

            # set up a trade order we want to make
            oaction = None
            if price_diff < 0.0:
                oaction = TradeOrderAction.SELL
            elif price_diff > 0.0:
                oaction = TradeOrderAction.BUY
            if oaction != None:
                order = TradeOrder(sym, oaction, abs(price_diff))
                orders.append(order)
                # log the order we're going to make
                self.log("%sorder: %s %s" % (prefix2 + utils.STAB_TREE1,
                        "BUY" if oaction == TradeOrderAction.BUY else "SELL",
                        float_to_str_dollar(abs(price_diff))))
            i += 1
        
        # update the last order time, then make all the orders
        self.last_order_time_save(datetime.now())
        for order in orders:
            res = self.api.send_order(order)
            # handle the success or failure by printing a message
            if not res.success:
                self.log("%sorder failed%s for %s: %s" %
                         (utils.C_RED, utils.C_NONE, order.symbol, res.message))
            else:
                oid = res.data.id
                self.log("%sorder succeeded%s for %s: [id: %s]" %
                         (utils.C_GREEN, utils.C_NONE, order.symbol, oid))
        
        # return success
        return IR(True)
    
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
        
        # if there's an asset loaded from disk that's not longer present in
        # our account, according to the API, remove it from the asset group
        # before returning
        i = 0
        for a in assets:
            prefix = utils.STAB_TREE2
            if i == len(assets) - 1:
                prefix = utils.STAB_TREE1
            # search the API assets for the one stored in disk
            asset: Asset = new_assets.search(a.symbol)
            if asset == None:
                self.log("%sfound asset %s stored on disk, but no longer "
                         "present on the account. Ignoring." %
                         (prefix, a.symbol))
                assets.remove(a.symbol)

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
            percent_total = 0.0
            for key in jdata:
                if type(jdata[key]) != float:
                    return IR(False, msg="JSON data key '%s' has a bad value (%s)" %
                              (key, fpath))
                # we'll store the percent as a value between 0-1 internally
                self.pp[key] = jdata[key] / 100.0
                percent_total += jdata[key]
            # if the percents we loaded in don't total up to exactly 100.0,
            # we've got an issue
            if percent_total != 100.0:
                return IR(False, msg="file percentages total to %f, not 100.0 (%s)" %
                          (percent_total, fpath))
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
    
    # --------------------------- Last Order Time --------------------------- #
    # Saves the last order time to a file for future reference.
    def last_order_time_save(self, otime: datetime) -> IR:
        fpath = os.path.join(self.work_dpath, PBStrat.last_order_time_fname)
        return utils.file_write_all(fpath, str(otime.timestamp()))
    
    def last_order_time_load(self) -> IR:
        fpath = os.path.join(self.work_dpath, PBStrat.last_order_time_fname)
        # load the file contents
        res = utils.file_read_all(fpath)
        if not res.success:
            return res
        # attempt to decode as a float
        try:
            seconds = float(res.data)
            return IR(True, data=datetime.fromtimestamp(seconds))
        except Exception as e:
            return IR(False, msg="failed to read contents as float (%s): %s" %
                      (fpath, e))

        

# # TEST CODE
# import json

# s = PBStrat("Test Percent-Balance", 3600)
# res = s.init("/home/snowmiser/snowbanker/src/strats/pb",
#              pp_fpath="/home/snowmiser/snowbanker/src/strats/perbal_config.json")
# print("INIT RESULT: %s" % res)
# print("PERCENT PROFILE:\n%s" % json.dumps(s.pp))
# s.tick()
