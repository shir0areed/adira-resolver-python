from .pip_resolver import PipResolver
from .raw_resolver import RawResolver
from .zip_resolver import ZipResolver

_RESOLVERS = {
    ("pip", "index"): PipResolver,
    ("raw", "oci"): RawResolver,
    ("zip", "oci"): ZipResolver,
}

def get_resolver_class(fmt, protocol):
    return _RESOLVERS.get((fmt, protocol))
