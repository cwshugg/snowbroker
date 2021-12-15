#!/usr/bin/python3
# This module defines the main function and command-line interface for the
# snowbanker. From here, users can select the strategy they wish to use, any
# configuration files, then start the selected strategy, making its periodic
# ticks.
#
#   Connor Shugg

# Imports
import sys
import getopt

# My imports
import sbi.utils as utils
import sbi.config as config
import strats.perbal

# Globals
strats = {
    "perbal": strats.perbal.PBStrat
}

# ========================== Command-Line Options =========================== #
# Handles the -h argument.
def options_handle_help(arg: str):
    help()
    sys.exit(0)

# Handles the -c argument.
def options_handle_config(arg: str):
    # attempt to initialize configurations with the given file path
    res = config.config_init(arg)
    if not res.success:
        utils.eprint("Failed to load configurations: %s" % res.message)
        sys.exit(1)
    
    # take the strategy name and ensure it's a valid one
    global strats
    if config.strat_name in strats:
        sys.stdout.write("Selected strategy: %s%s%s.\n" %
                         (utils.C_BLUE, config.strat_name, utils.C_NONE))
    else:
        sys.stdout.write("Invalid strategy name: %s%s%s. "
                         "Available strategies are:\n" %
                         (utils.C_RED, config.strat_name, utils.C_NONE))
        # print all available strategy names, then exit
        i = 0
        strats_len = len(strats)
        for key in strats:
            prefix = utils.STAB_TREE2
            if i == strats_len - 1:
                prefix = utils.STAB_TREE1
            sys.stdout.write("%s%s\n" % (prefix, key))
            i += 1
        sys.exit(1)

# Global options dictionary
options = [
    {"short": "h", "long": "help", "arg": None,
     "description": "Displays this help menu.",
     "handler": options_handle_help},
    {"short": "c", "long": "config", "arg": "/path/to/config.json",
     "description": "Used to select a snowbanker configuration file.",
     "handler": options_handle_config},
]


# ======================= Option Handling & Help Menu ======================= #
# Used to initialize the command-line options. Returns the following:
#   [opt_str, opt_long_str_array]
# These can be directly passed into getopt()
def options_init() -> list:
    # build an array of command-line arguments, and a command-line argument
    # string for the call to getopt()
    opt_longstr_array = []
    opt_str = ""
    global options
    for opt in options:
        # add to the option string
        opt_str += opt["short"]
        if opt["arg"] != None:
            opt_str += ":"
        
        # add to the array
        long_str = opt["long"]
        long_str = long_str + "=" if opt["arg"] != None else long_str
        opt_longstr_array.append(long_str)
    return [opt_str, opt_longstr_array]

# Takes the return value from options_init() and handles the given command-line
# arguments accordingly.
def options_handle(getopt_str: str, getopt_long_str_array: list):
    try:
        # try to parse the arguments
        opts, args = getopt.getopt(sys.argv[1:], getopt_str,
                                   getopt_long_str_array)
        # iterate through all arguments
        global options
        for opt, arg in opts:   # iterate through given arguments
            opt = opt.replace("-", "")
            for aop in options:  # iterate again through availabe options
                # if the current option matches one in our list of options
                if opt in (aop["short"], aop["long"]):
                    aop["handler"](arg)
    except getopt.GetoptError:
        help()
        sys.exit(1)

# Function to display a help menu.
def help():
    sys.stdout.write("%sSnowbanker%s: the automated stock trading system.\n" %
                     (utils.C_BLUE, utils.C_NONE))
    sys.stdout.write("Usage: %s%s -c /path/to/config.json [OPTIONS]%s\n" %
                     (utils.C_GRAY, sys.argv[0], utils.C_NONE))
    sys.stdout.write("Select a configuration file to begin.\n")
    sys.stdout.write("\nCommand-Line Options:\n")
    # print all command-line options
    global options
    i = 0
    options_len = len(options)
    for opt in options:
        prefix = utils.STAB_TREE2
        if i == options_len - 1:
            prefix = utils.STAB_TREE1
        # write the line
        sys.stdout.write("%s%s-%s / --%-8s %-24s%s %s\n" %
                         (prefix, utils.C_GRAY, opt["short"],
                          opt["long"],
                          " " if opt["arg"] == None else opt["arg"],
                          utils.C_NONE, opt["description"]))
        i += 1


# ============================== Main Function ============================== #
# Main function.
def main():
    # if no args are given, print out the help menu
    if len(sys.argv) < 2:
        help()
        sys.exit(0)
    
    # extract command-line arguments and process them
    opt_info = options_init()
    options_handle(opt_info[0], opt_info[1])

    # if no strategy was selected (meaning no config file was given in the
    # command-line arguments), complain and exit
    if config.strat_name == None:
        sys.stdout.write("No configuration file specified. Exiting.\n")
        sys.exit(1)
    
    # get the strategy class and initialize it, based on the name
    global strats
    strat_class = strats[config.strat_name]
    name = "%s-%d" % (config.strat_name, config.strat_tick_rate)
    strat = strat_class(name, config.strat_tick_rate)

    # invoke the strategy's init() function, optionally passing in the
    # config file path specific to the strategy
    strat.init(config.strat_work_dpath,
               config_fpath=config.strat_config_fpath)
    

# Runner code
if __name__ == "__main__":
    main()
