import subprocess
from pathlib import Path
import logging
import venv

from .semantics import ServerSemantics

logger = logging.getLogger(__name__)

class IndexServer:
    def __init__(self, protocol_params):
        self.extra_index_url = protocol_params.get("extra_index_url")

    @staticmethod
    def get_server_semantics():
        return ServerSemantics.PIP_INDEX

    def build_requirement_specifier(self, identity):
        vendor = identity.get("vendor", "")
        artifact = identity["artifact"]
        version = identity.get("version", "")

        if vendor:
            raise RuntimeError("pip format: vendor は空でなければなりません")

        if not version:
            version_spec = ""
        elif version[0] in "<>!=":
            version_spec = version
        else:
            version_spec = f"=={version}"

        return artifact + version_spec

    def is_installed(self, venv_python: Path, identity: dict) -> bool:
        artifact = identity["artifact"]
        version = identity.get("version")

        code = (
            "from importlib.metadata import version as v, PackageNotFoundError\n"
            "import sys\n"
            "name = sys.argv[1]\n"
            "ver = sys.argv[2] if len(sys.argv) > 2 else None\n"
            "try:\n"
            "    installed = v(name)\n"
            "except PackageNotFoundError:\n"
            "    sys.exit(1)\n"
            "if ver and installed != ver:\n"
            "    sys.exit(1)\n"
            "sys.exit(0)\n"
        )

        cmd = [str(venv_python), "-c", code, artifact]
        if version:
            cmd.append(version)

        result = subprocess.call(cmd)
        return result == 0

    def fetch(self, identity, output_path, dry_run=False):
        """
        pip フォーマット仕様書に従い、
        output_path（venv）内に pip install を行う。
        """
        venv_dir = Path(output_path)

        if dry_run:
            logger.info("[dry-run] installing %s into %s", identity, venv_dir)
            return None

        # venv を構築（pip入り）
        builder = venv.EnvBuilder(with_pip=True)
        context = builder.ensure_directories(str(venv_dir))

        # 仕様書通り、venv_python = context.env_exe
        venv_python = Path(context.env_exe)

        if self.is_installed(venv_python, identity):
            logger.info("Already installed (fast-skip): %s", identity)
            return None

        # identity → Requirement Specifier に変換
        requirement = self.build_requirement_specifier(identity)

        # pip install コマンドを構築
        cmd = [str(venv_python), "-m", "pip", "install", requirement]

        if self.extra_index_url:
            cmd.extend(["--extra-index-url", self.extra_index_url])

        subprocess.check_call(cmd)

        return None
