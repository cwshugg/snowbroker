#!/bin/bash
# A simple script to set up a symlink pointing at the main python module for
# snowbanker.
#
#   Connor Shugg

# check for arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 /path/to/new/symlink"
    exit 1
fi

# get the correct file path and make sure we can find a "main.py" in the
# correct place
script_dir=$(realpath $(dirname $0))
snowbanker_dir=$(dirname ${script_dir})
main_fpath=${snowbanker_dir}/src/main.py
if [ ! -f ${main_fpath} ]; then
    echo "Error: couldn't find main python module at ${main_fpath}."
    exit 1
fi

# create a symlink
ln -s ${main_fpath} $1
