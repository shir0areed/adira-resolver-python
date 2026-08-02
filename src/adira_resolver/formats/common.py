from adira_resolver.protocols.semantics import ServerSemantics

from .pip_resolver import PipResolver
from .native_resolver import NativeResolver

_RESOLVERS = {
    ("pip", ServerSemantics.PIP_INDEX): PipResolver,
    ("native", ServerSemantics.FILE): NativeResolver,
}

def get_resolver_class(fmt, protocol):
    return _RESOLVERS.get((fmt, protocol))
