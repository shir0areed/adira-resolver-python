import os
import zipfile

class NativeResolver:
    def __init__(self, dep_id, identity, fmt_params, dest_root):
        self.dep_id = dep_id
        self.identity = identity
        self.fmt_params = fmt_params
        self.dest_root = dest_root

    def pre_fetch_process(self):
        """
        zip は「まず zip ファイルとして取得し、その後展開する」ので、
        output_path は zip ファイルの一時パスになる。
        """
        zip_name = self.fmt_params.get("zip_name", f"{self.dep_id}.zip")
        zip_path = os.path.join(self.dest_root, zip_name)
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        return zip_path

    def post_fetch_process(self, server_ret):
        """
        server_ret は oci_server.fetch の返り値（zip_path）とみなせる。
        zip を展開して最終レイヤーを作る。
        """
        zip_path = server_ret
        extract_dir = os.path.join(self.dest_root, self.dep_id)

        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
