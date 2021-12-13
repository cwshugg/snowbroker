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
import sbi.utils as utils
from sbi.utils import IR

# Main strategy class.
class PBStrat(Strategy):
    # Overriden initialization function.
    def init(self, dpath: str) -> IR:
        super().init(dpath) # typical init stuff

        print("TODO: init")

    # The strategy's tick implementation.
    def tick(self) -> IR:
        print("TODO: tick")
