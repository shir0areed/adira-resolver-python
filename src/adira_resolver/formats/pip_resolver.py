import venv
from pathlib import Path

class PipResolverFromPipIndex:
    def __init__(self, dep_id, identity, fmt_params, dest_root):
        self.dep_id = dep_id
        self.identity = identity
        self.fmt_params = fmt_params
        self.dest_root = Path(dest_root)

    def pre_fetch_process(self):
        """
        venv を構築し、そのパスを output_path として返す。
        IndexServer.fetch が pip install を行う。
        """
        rel_path = self.fmt_params.get("venv_path", self.dep_id)
        venv_dir = self.dest_root / rel_path
        venv_dir.mkdir(parents=True, exist_ok=True)

        builder = venv.EnvBuilder(with_pip=True)
        builder.create(str(venv_dir))

        return venv_dir  # IndexServer.fetch の output_path になる

    def post_fetch_process(self, server_ret):
        """
        pip index 方式では post は何もしない。
        pip install は IndexServer が担当する。
        """
        return None
