# Python module responsible for computing statistics over individual assets and
# asset groups. Useful for making strategic decisions.
#
#   Connor Shugg

# Imports
import os
import sys

# Enable import from the main src directory
sbi_dpath = os.path.dirname(os.path.realpath(__file__))
src_dpath = os.path.dirname(sbi_dpath)
if src_dpath not in sys.path:
    sys.path.append(src_dpath)

# My imports
from sbi.asset import Asset, AssetGroup, PriceDataPoint

# ========================== General Computations =========================== #
# Computes simple rate of return with a beginning and end value.
def ror(begin: float, end: float) -> float:
    begin = 0.00001 if begin == 0.0 else begin # avoid division by zero
    return round(((end - begin) / begin) * 100.0, 4)


# ======================== Asset-Specific Computations ====================== #
# Computes the latest price of a given asset and multiplies it by the asset's
# quantity. 0.0 is returned if no price history data is available.
def asset_value(a: Asset) -> float:
    pdp = a.phistory_latest()
    if pdp == None:
        return 0.0
    return pdp.price * a.quantity


# ======================== Asset Group Computations ========================= #
# Computes the sum of all assets' values (taking quantity into account).
# Any assets without price history are not taken into account.
def asset_group_value(ag: AssetGroup) -> float:
    if len(ag) == 0.0:
        return 0.0
    # iterate through each asset and compute their values, adding to the sum
    ag_sum = 0.0
    for asset in ag:
        ag_sum += asset_value(asset)
    return ag_sum
