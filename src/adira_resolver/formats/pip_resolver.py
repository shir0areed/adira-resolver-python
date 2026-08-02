import venv
from pathlib import Path

class PipResolverFromPipIndex:
    """
    PipIndex 用 resolver。
    fetch semantics:
        - output_path は venv のパス
        - server.fetch(output_path) は pip install を行う
        - server.fetch の返り値は None
    """

    def __init__(self, dep_id, identity, fmt_params, dest_root):
        self.dep_id = dep_id
        self.identity = identity
        self.fmt_params = fmt_params
        self.dest_root = Path(dest_root)

    def retrieve(self, server):
        """
        pre_fetch_process + fetch + post_fetch_process を統合したメソッド。

        1. venv を構築する（旧 pre）
        2. server.fetch(venv_path) を呼ぶ（旧 fetch）
        3. pip install は server が担当する（旧 post は不要）
        """

        # 1. venv を構築
        rel_path = self.fmt_params.get("venv_path", self.dep_id)
        venv_dir = self.dest_root / rel_path
        venv_dir.mkdir(parents=True, exist_ok=True)

        builder = venv.EnvBuilder(with_pip=True)
        builder.create(str(venv_dir))

        # 2. server.fetch を呼ぶ（pip install）
        server.fetch(self.identity, venv_dir)

        # 3. pip index 方式では post は不要
        return None
