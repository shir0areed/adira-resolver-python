import os

class RawResolver:
    def __init__(self, dep_id, identity, fmt_params, dest_root):
        self.dep_id = dep_id
        self.identity = identity
        self.fmt_params = fmt_params
        self.dest_root = dest_root

    def pre_fetch_process(self):
        """
        raw は「そのまま最終レイヤーに置く」ので、
        output_path は最終配置先のパスになる。
        """
        filename = self.fmt_params.get("filename", self.dep_id)
        output_path = os.path.join(self.dest_root, filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return output_path

    def post_fetch_process(self, server_ret):
        """
        raw は fetch したものがそのまま最終レイヤーなので何もしない。
        server_ret は oci_server.fetch の返り値（output_path）だが使わなくてもよい。
        """
        return
