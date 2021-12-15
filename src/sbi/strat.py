# This module defines the base class for all investing bot strategies I will
# implement.
#
#   Connor Shugg

# Imports
import os
import sys
import abc
import time
from datetime import datetime

# Enable import from the parent directory
sbi_dpath = os.path.dirname(os.path.realpath(__file__))
src_dpath = os.path.dirname(sbi_dpath)
if src_dpath not in sys.path:
    sys.path.append(src_dpath)

# My imports
import sbi.utils as utils
from sbi.utils import IR
from sbi.api import TradeAPI, TradeOrder, TradeOrderAction

# ============================= Strategy Class ============================== #
# Represents the base class for strategies.
class Strategy(abc.ABC):
    log_fname = "log.txt"

    # Constructor. Takes in the following:
    #   name        name of the strategy
    #   tick_rate   how often a single "tick" of the strategy occurs (seconds)
    def __init__(self, name: str, tick_rate: int):
        self.name = name
        self.tick_rate = tick_rate
        self.api = TradeAPI()
    
    # Initializes fies and other needed fields before the strategy can start
    # running. Strategy subclasses should override this method to add their own
    # init code, but be sure to invoke super().init() before its own code.
    # The 'config_fpath' is unused here, but may be by child strategy classes.
    def init(self, dpath: str, config_fpath=None) -> IR:
        # set up the working directory
        self.work_dpath = os.path.realpath(dpath)
        res = utils.dir_make(self.work_dpath, exists_ok=True)
        if not res.success:
            return res
        
        # with the directory created, we'll set up the log file
        self.log_fpath = os.path.join(self.work_dpath, Strategy.log_fname)
        res = utils.file_make(self.log_fpath, exists_ok=True)
        if not res.success:
            return res
        
        # attempt to load the API keys into memory
        res = self.api.load_keys()
        if not res.success:
            return res
        
        # log and return success
        self.log("initialized", reset=True)
        return IR(True)
    
    # Simple function used to sleep the calling thread the number of seconds in
    # the strategy's 'tick_rate' field. This should be used after a call to
    # 'tick()' to wait until it's time for the next tick
    def sleep(self) -> IR:
        time.sleep(self.tick_rate)
        return IR(True)

    # Abstract method that represents a single "tick" of the strategy. This is
    # where the strategy will come to life, observe the current assets in my
    # account, make decisions, and place orders on the market.
    # If any order or API calls fail, this tick will return early, and will
    # return false with an appropriate message.
    @abc.abstractmethod
    def tick(self) -> IR:
        pass

    # Writes a log out to the strategy's log file in its working directory. If
    # the 'reset' parameter is true, the log file will be emptied before the
    # given message is written to it. If 'no_stdout' is true, this will not
    # additionally write to stdout.
    def log(self, message: str, reset=False, no_stdout=False) -> IR:
        # create a prefix for the log
        prefix_name = utils.str_to_fname(self.name.lower())
        prefix_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = "[%s %s] " % (prefix_name, prefix_date)
        
        # attempt to append (or wipe-then-write) a new line to the file
        res = None
        if reset:
            res = utils.file_write_all(self.log_fpath, "%s%s\n" % (prefix, message))
        else:
            res = utils.file_append(self.log_fpath, "%s%s\n" % (prefix, message))
        
        # also write to stdout, if necessary
        if not no_stdout:
            prefix_stdout = "%s[%s%s %s%s%s]%s " % (utils.C_GRAY, utils.C_BLUE,
                            prefix_name, utils.C_GREEN, prefix_date, utils.C_GRAY,
                            utils.C_NONE)
            sys.stdout.write("%s%s\n" % (prefix_stdout, message))
        
        # return appropriately
        if not res.success:
            return res
        return IR(True)
