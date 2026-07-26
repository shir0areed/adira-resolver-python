import requests
import os

class OCIServer:
    def __init__(self, protocol_params):
        # protocol_params = {"base_url": "..."}
        self.base_url = protocol_params.get("base_url")

    def fetch(self, identity, output_path):
        """
        identity: {"vendor", "artifact", "version", "format"}
        output_path: ファイルを書き出すパス（zip/raw 共通）
        """
        vendor = identity.get("vendor")
        artifact = identity.get("artifact")
        version = identity.get("version")
        fmt = identity.get("format")

        url = f"{self.base_url.rstrip('/')}/{vendor}/{artifact}/{version}/{fmt}"
        resp = requests.get(url)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)

        return output_path
