from .pip_resolver import PipResolver
from .raw_resolver import RawResolver
from .zip_resolver import ZipResolver

_RESOLVERS = {
    "pip": PipResolver,
    "raw": RawResolver,
    "zip": ZipResolver,
}

def get_resolver_class(format_name):
    return _RESOLVERS.get(format_name)
