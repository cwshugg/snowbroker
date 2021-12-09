# General-purpose utility module.
#
#   Connor Shugg


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
        msg += "" if self.message == "" else ": %s" + self.message
        msg += " (data included)" if self.data != None else ""
        return msg


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