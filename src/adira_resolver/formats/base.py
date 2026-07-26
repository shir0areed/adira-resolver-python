import abc
import logging
from pathlib import Path

logger = logging.getLogger("adira_resolver.formats.base")

class BaseResolver(abc.ABC):
    def __init__(self, dep_id, dep, dest_root, artifact_server, config):
        self.dep_id = dep_id
        self.dep = dep
        self.dest_root = Path(dest_root)
        self.artifact_server = artifact_server
        self.config = config

    @abc.abstractmethod
    def resolve(self):
        raise NotImplementedError

    def dry_run(self):
        logger.info("Dry run: would resolve %s with params: %s", self.dep_id, self.dep)
