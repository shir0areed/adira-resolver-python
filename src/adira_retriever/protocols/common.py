from .oci_server import OCIServer
from .index_server import IndexServer

_SERVER_TABLE = {
    "oci": OCIServer,
    "index": IndexServer,
}

def get_server_class(protocol):
    return _SERVER_TABLE.get(protocol)
