from adira_resolver.protocols.semantics import ServerSemantics

from .pip_resolver import PipResolverFromPipIndex
from .native_resolver import NativeResolverFromFile

_RESOLVERS = {
    ("pip", ServerSemantics.PIP_INDEX): PipResolverFromPipIndex,
    ("native", ServerSemantics.FILE): NativeResolverFromFile,
}

def get_resolver_class(fmt, protocol):
    return _RESOLVERS.get((fmt, protocol))
