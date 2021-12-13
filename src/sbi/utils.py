# General-purpose utility module.
#
#   Connor Shugg

# Imports
import os
import pathlib

# ========================= Error-Related Utilities ========================= #
# IR = "Internal Result". A simple class used to pair a success/failure flag
# with a message and some data.
class IR:
    # Constructor.
    def __init__(self, result: bool, msg="", data=None):
        self.success = result
        self.message = msg
        self.data = data

    # Converts the result to a readable string. Great for debugging.
    def __str__(self):
        msg = "Success" if self.success else "Failure"
        msg += "" if self.message == "" else ": %s" % self.message
        msg += " (data: %s)" % self.data if self.data != None else ""
        return msg


# ============================ String Utilities ============================= #
# Attempts to convert a string to a float.
def str_to_float(string: str) -> IR:
    try:
        return IR(True, data=float(string))
    except Exception as e:
        return IR(False, msg="couldn't convert string '%s' to float: %s" %
                  (string, e))


# ========================= File-Related Utilities ========================== #
# Takes in a file path and attempts to read the entire file into memory.
def file_read_all(fpath: str) -> IR:
    try:
        fp = open(fpath, "r")
        data = fp.read()
        fp.close()
        return IR(True, data=data)
    except Exception as e:
        return IR(False, "failed to read from file (%s): %s" % (e, fpath))

# Attempts to write the given string out to a file.
def file_write_all(fpath: str, string: str) -> IR:
    try:
        fp = open(fpath, "w")
        fp.write(string)
        fp.close()
    except Exception as e:
        return IR(False, "failed to write to file (%s): %s" %
                  (fpath, e))
    return IR(True)

# Attempts to append a string to the end of a file.
def file_append(fpath: str, string: str) -> IR:
    try:
        fp = open(fpath, "a")
        fp.write(string)
        fp.close()
    except Exception as e:
        return IR(False, "failed to append to file (%s): %s" %
                  (fpath, e))
    return IR(True)

# Attempts to make an empty file at the given path. If 'exists_ok' is set to
# true, then a success is also returned if the file already exists.
def file_make(fpath: str, exists_ok=False) -> IR:
    # if the file path is actually a directory, return
    if os.path.isdir(fpath):
        return IR(False, msg="the given path (%s) is a directory" % fpath)
    # if the file already exists, return
    if os.path.isfile(fpath):
        if exists_ok:
            return IR(True)
        return IR(False, msg="the given directory (%s) already exists" % fpath)
    
    # otherwise, try to create the file
    try:
        pathlib.Path(fpath).touch()
    except Exception as e:
        return IR(False, "failed to create file (%s): %s" % (fpath, e))
    return IR(True)

# Helper function that attempts to create a directory at the given path and
# returns an internal result on success. If 'exists_ok' is set to true, then a
# success is also returned if the directory already exists.
def dir_make(dpath: str, exists_ok=False) -> IR:
    # if the directory path is actually a file, return
    if os.path.isfile(dpath):
        return IR(False, msg="the given path (%s) is a file" % dpath)
    # if the directory already exists, return
    if os.path.isdir(dpath):
        if exists_ok:
            return IR(True)
        return IR(False, msg="the given directory (%s) already exists" % dpath)
    
    # otherwise, we'll try to make the directory
    try:
        os.mkdir(dpath)
    except Exception as e:
        return IR(False, msg="failed to create directory (%s): %s" % (dpath, e))
    return IR(True)


# Helper function to convert a string into a file name. Returns the string.
def str_to_fname(string: str, extension="") -> str:
    fname = "_".join(string.split())    # replace all whitespace with "_"
    fname = fname.replace("/", "-")     # replace forward slash
    fname = fname.replace("\\", "-")    # replace backward slash
    extension = ".%s" % extension if extension != "" else ""
    return "%s%s" % (fname, extension)


# ============================= JSON Utilities ============================== #
# Takes in JSON data and an array structured like so:
#   [["key1", type1], ["key2", type2], ...]
# And ensures each key is present in the JSON data, and each key has the right
# data type. If any check fails, false is returned. Otherwise true is returned.
def json_check_keys(jdata: dict, expected: list):
    for e in expected:
        if e[0] not in jdata or type(jdata[e[0]]) != e[1]:
            return False
    return True