from pathlib import Path
import requests

from .semantics import ServerSemantics

class OCIServer:
    def __init__(self, protocol_params):
        self.base_url = protocol_params.get("base_url").rstrip("/")

    def _hex(self, s: str) -> str:
        return s.encode("utf-8").hex()

    @staticmethod
    def get_server_semantics():
        return ServerSemantics.FILE

    def fetch(self, identity, output_dir: Path):
        """
        identity: {"vendor", "artifact", "version", "format"}
        output_dir: フォルダ（ここに blob をファイル名で保存する）
        version は retriever 側で解決済み
        """
        vendor = identity.get("vendor", "")
        artifact = identity["artifact"]
        version = identity["version"]

        vendor_hex = self._hex(vendor) if vendor else ""
        artifact_hex = self._hex(artifact)

        # --- Step 1: manifest を取得 ---
        if vendor_hex:
            manifest_url = f"{self.base_url}/v2/{vendor_hex}/{artifact_hex}/manifests/{version}"
        else:
            manifest_url = f"{self.base_url}/v2/{artifact_hex}/manifests/{version}"

        manifest_resp = requests.get(manifest_url)
        manifest_resp.raise_for_status()
        manifest = manifest_resp.json()

        layers = manifest.get("layers", [])
        if not layers:
            raise RuntimeError("Manifest has no layers")

        layer = layers[0]
        digest = layer["digest"]

        # ★ ファイル名は OCI annotations から取得
        filename = layer.get("annotations", {}).get(
            "org.opencontainers.image.title",
            "artifact.bin"
        )

        # --- Step 2: blob を取得 ---
        if vendor_hex:
            blob_url = f"{self.base_url}/v2/{vendor_hex}/{artifact_hex}/blobs/{digest}"
        else:
            blob_url = f"{self.base_url}/v2/{artifact_hex}/blobs/{digest}"

        blob_resp = requests.get(blob_url)
        blob_resp.raise_for_status()

        # --- Step 3: フォルダ内にファイル名で保存 ---
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / filename

        output_path.write_bytes(blob_resp.content)

        return output_path
