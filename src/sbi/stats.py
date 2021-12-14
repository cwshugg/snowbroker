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
