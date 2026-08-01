from .pip_resolver import PipResolver
from .native_resolver import NativeResolver

_RESOLVERS = {
    ("pip", "index"): PipResolver,
    ("native", "oci"): NativeResolver,
}

def get_resolver_class(fmt, protocol):
    return _RESOLVERS.get((fmt, protocol))
