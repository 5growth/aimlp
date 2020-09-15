# Define fs as an object with method "exists", which returns false,
# in order to correctly handle the fs.exists call when HDFS isn't available
def dummy_fs():
    return type("fsHandler", (object,), {"exists": lambda self: False})
