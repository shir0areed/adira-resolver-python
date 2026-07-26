import zipfile
import shutil
from pathlib import Path
from .base import BaseResolver
import logging
logger = logging.getLogger("adira_resolver.formats.zip")

class ZipResolver(BaseResolver):
    def resolve(self):
        dst_root = self.config.get("formats", {}).get("zip", {}).get("dst_root") or self.dep.get("zip", {}).get("dst") or "."
        zip_dst_root = self.config.get("formats", {}).get("zip", {}).get("zip_dst_root", "zip")
        dst_dir = Path(self.dest_root) / dst_root / (self.dep.get("zip", {}).get("dst") or self.dep_id)
        dst_dir.mkdir(parents=True, exist_ok=True)

        # fetch archive
        reference = self.dep.get("ref") or self.dep.get("artifact") or self.dep_id
        tmp_zip = Path(self.dest_root) / zip_dst_root / f"{self.dep_id}.zip"
        tmp_zip.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_server.fetch(reference, str(tmp_zip))

        # save archive (already saved) and extract
        strip_root = bool(self.dep.get("zip", {}).get("strip_root", False))
        with zipfile.ZipFile(tmp_zip, "r") as z:
            namelist = z.namelist()
            if strip_root:
                # check that top-level entries are a single directory
                top_dirs = set(p.split("/")[0] for p in namelist if p)
                if len(top_dirs) != 1:
                    raise RuntimeError("zip.strip_root=True but archive root is not a single directory")
                # extract members under that single dir into dst_dir
                root = list(top_dirs)[0] + "/"
                members = [m for m in namelist if m.startswith(root)]
                for m in members:
                    target = Path(dst_dir) / Path(m[len(root):])
                    if m.endswith("/"):
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with z.open(m) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
            else:
                z.extractall(path=dst_dir)
        logger.info("Extracted zip to %s (archive saved at %s)", dst_dir, tmp_zip)
