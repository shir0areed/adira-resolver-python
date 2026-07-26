import subprocess

class PipResolver:
    def __init__(self, dep_id, identity, fmt_params, dest_root):
        self.dep_id = dep_id
        self.identity = identity
        self.fmt_params = fmt_params
        self.dest_root = dest_root

    def pre_fetch_process(self):
        """
        pip index 方式では server.fetch は何もしないので、
        output_path は使わない。None を返しておけば十分。
        """
        return None

    def post_fetch_process(self, server_ret):
        """
        実際の取得と展開は pip install が担当する。
        identity からパッケージ名などを取り出して pip を叩く。
        """
        pkg = self.identity.get("artifact") or self.dep_id
        extra_index = self.fmt_params.get("extra_index_url")

        cmd = ["pip", "install", pkg]
        if extra_index:
            cmd.extend(["--extra-index-url", extra_index])

        subprocess.check_call(cmd)
