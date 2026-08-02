from adira_retriever.protocols.semantics import ServerSemantics

from .pip_resolver import *
from .native_resolver import *

_RESOLVERS = {
    ("pip", ServerSemantics.PIP_INDEX): PipResolverFromPipIndex,
    ("native", ServerSemantics.FILE): NativeResolverFromFile,
}

def get_resolver_class(fmt, protocol):
    return _RESOLVERS.get((fmt, protocol))
