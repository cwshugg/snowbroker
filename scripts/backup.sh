#!/bin/bash
# Script to copy a given directory (used by strategies to store data) elsewhere
# (presumably to some location where it'll get saved).
# Backups are recurring, and this script runs forever.

# get the backup directory from the command-line args
if [ $# -lt 1 ]; then
    echo "Usage: $0 /path/to/source_dir /path/to/dest_dir"
    exit 1
fi
sdir=$1
ddir=$2

sleep_time=1800

# enter the backup look
while true; do
    ls -al ${sdir} > /dev/null
    ls -al ${ddir} > /dev/null
    # make sure both directories are valid
    if [ ! -d ${sdir} ]; then
        echo "Source directory (${sdir}) is not a directory."
        exit 1
    elif [ ! -d ${ddir} ]; then
        echo "Destination directory (${ddir}) is not a directory."
        exit 1
    fi

    # copy from one to another
    echo -e "[$(date)] backing up...\033[90m"
    cp -v -r ${sdir}/* ${ddir}/

    # sleep for a time
    echo -e "\033[0m[$(date)] going to sleep..."
    sleep ${sleep_time}
done

