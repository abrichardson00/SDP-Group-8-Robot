# System modules
from datetime import datetime

# 3rd party modules
from flask import make_response, abort, send_file


def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


