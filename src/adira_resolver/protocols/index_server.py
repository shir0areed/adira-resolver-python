import subprocess
from pathlib import Path
import venv

class IndexServer:
    def __init__(self, protocol_params):
        self.extra_index_url = protocol_params.get("extra_index_url")

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

    def fetch(self, identity, output_path):
        """
        pip フォーマット仕様書に従い、
        output_path（venv）内に pip install を行う。
        """
        venv_dir = Path(output_path)

        # venv を構築（pip入り）
        builder = venv.EnvBuilder(with_pip=True)
        context = builder.ensure_directories(str(venv_dir))

        # 仕様書通り、venv_python = context.env_exe
        venv_python = Path(context.env_exe)

        # identity → Requirement Specifier に変換
        requirement = self.build_requirement_specifier(identity)

        # pip install コマンドを構築
        cmd = [str(venv_python), "-m", "pip", "install", requirement]

        if self.extra_index_url:
            cmd.extend(["--extra-index-url", self.extra_index_url])

        subprocess.check_call(cmd)

        return None
