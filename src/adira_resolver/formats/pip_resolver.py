import subprocess
import sys
import shutil
import os
from .base import BaseResolver
import logging
logger = logging.getLogger("adira_resolver.formats.pip")

class PipResolver(BaseResolver):
    def resolve(self):
        venv_rel = self.dep.get("pip", {}).get("venv_path") or self.config.get("formats", {}).get("pip", {}).get("venv_path") or self.dep_id
        venv_dir = self.dest_root / venv_rel
        venv_dir.mkdir(parents=True, exist_ok=True)

        # create venv
        import venv
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(str(venv_dir))
        python_bin = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
        # map identity to requirement specifier per spec
        artifact = self.dep.get("artifact", "")
        vendor = self.dep.get("vendor", "")
        version = self.dep.get("version", "")
        if vendor:
            raise RuntimeError("pip format: vendor must be empty per spec")
        if version.startswith((">", "<", "~", "==", ">=", "<=")):
            req = f"{artifact}{version}"
        elif version:
            req = f"{artifact}=={version}"
        else:
            req = artifact

        logger.info("Installing %s into venv %s", req, venv_dir)
        subprocess.check_call([str(python_bin), "-m", "pip", "install", req])
        logger.info("Installed %s", req)
