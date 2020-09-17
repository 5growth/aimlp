from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

# Define fs as an object with method "exists", which returns false,
# in order to correctly handle the fs.exists call when HDFS isn't available
def dummy_fs():
    return type("fsHandler", (object,), {"exists": lambda self: False})

def get_scoped_session(engine):
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)
