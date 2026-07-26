import requests
import logging
from urllib.parse import urljoin

logger = logging.getLogger("adira_resolver.artifact_server")

class ArtifactServerFactory:
    @staticmethod
    def create(format_name, server_cfg):
        # server_cfg is a dict from config file for this format
        if format_name in ("raw", "zip"):
            return OCIReferrerArtifactServer(server_cfg)
        elif format_name == "pip":
            return PyPIArtifactServer(server_cfg)
        else:
            return GenericHTTPArtifactServer(server_cfg)

class GenericHTTPArtifactServer:
    def __init__(self, cfg):
        self.cfg = cfg or {}
        self.base_url = self.cfg.get("base_url")

    def fetch(self, reference, dest_path):
        if not self.base_url:
            raise RuntimeError("No base_url configured for generic server")
        url = urljoin(self.base_url.rstrip("/") + "/", reference.lstrip("/"))
        logger.info("Downloading %s -> %s", url, dest_path)
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return dest_path

class OCIReferrerArtifactServer(GenericHTTPArtifactServer):
    """
    Minimal support for OCI distribution: assume 'reference' is an OCI descriptor or path.
    Real-world: integrate with ORAS or OCI registry client. Here we provide a simple HTTP GET
    to base_url + reference, and a hook for future ORAS integration.
    """
    def fetch(self, reference, dest_path):
        # reference may be like "repo/artifact:tag" or a path; config may provide 'pull_url_template'
        pull_template = self.cfg.get("pull_url_template")
        if pull_template:
            url = pull_template.format(reference=reference)
        else:
            url = self.base_url.rstrip("/") + "/" + reference
        logger.info("OCI fetch %s -> %s", url, dest_path)
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return dest_path

class PyPIArtifactServer:
    def __init__(self, cfg):
        self.cfg = cfg or {}
        self.index_url = self.cfg.get("index_url")  # optional
