import os
import shutil
from pathlib import Path
from .base import BaseResolver
import logging
logger = logging.getLogger("adira_resolver.formats.raw")

class RawResolver(BaseResolver):
    def resolve(self):
        dst_root = self.config.get("formats", {}).get("raw", {}).get("dst_root") or self.dep.get("raw", {}).get("dst") or "."
        dst_dir = Path(self.dest_root) / dst_root / (self.dep.get("raw", {}).get("dst") or self.dep_id)
        dst_dir.mkdir(parents=True, exist_ok=True)

        # identity mapping: artifact reference may be provided in dep (e.g., dep['ref'])
        reference = self.dep.get("ref") or self.dep.get("artifact") or self.dep_id
        # download to temp file then extract/copy as-is
        tmp_path = Path(self.dest_root) / f"{self.dep_id}.download"
        self.artifact_server.fetch(reference, str(tmp_path))
        # if it's an archive but format is raw, we just place the file
        final_path = dst_dir / tmp_path.name
        shutil.move(str(tmp_path), final_path)
        logger.info("Placed raw artifact at %s", final_path)
