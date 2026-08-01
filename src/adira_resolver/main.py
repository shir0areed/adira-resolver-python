import argparse
import sys
import os
import logging
from .config import load_config
from .manifest import load_manifest_with_additions
from .protocols.common import get_server_class
from .formats.common import get_resolver_class

logger = logging.getLogger("adira_resolver")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def parse_args(argv):
    p = argparse.ArgumentParser(prog="adira-resolver", description="Resolve ADIRA manifest")
    p.add_argument("--config", "-c", default="./config.toml", help="Path to resolver config TOML")
    p.add_argument("--dest", "-d", default="adira_resolve", help="Resolve destination directory")
    p.add_argument("--dry-run", action="store_true", help="Show actions without performing them")
    p.add_argument("manifests", nargs=1, help="Path to manifest TOML (main file)")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    config = load_config(args.config)
    manifest = load_manifest_with_additions(args.manifests[0])
    os.makedirs(args.dest, exist_ok=True)

    # For each dependency, dispatch to format resolver
    for dep_id, dep in manifest["dependencies"].items():
        identity = {
            "vendor": dep.get("vendor"),
            "artifact": dep.get("artifact"),
            "version": dep.get("version"),
            "format": dep.get("format"),
        }

        fmt = identity.get("format")
        if not fmt:
            logger.error("Dependency %s has no format; skipping", dep_id)
            continue

        # merge formats.<fmt> defaults into dep.<fmt>
        fmt_defaults = manifest.get("formats", {}).get(fmt, {})
        dep_fmt_params = dep.get(fmt, {})
        fmt_params = fmt_defaults.copy()
        fmt_params.update(dep_fmt_params)

        logger.info("Resolving %s (format=%s)", dep_id, fmt)

        server_entries = config.get("formats", {}).get(fmt, [])
        if not isinstance(server_entries, list):
            logger.error("formats.%s must be an array of server configs", fmt)
            continue

        for server_cfg in server_entries:
            protocol = server_cfg.get("protocol")
            if not protocol:
                logger.error("Server entry for format %s has no 'protocol' field", fmt)
                continue

            protocol_params = server_cfg.get(protocol, {})

            resolver_cls = get_resolver_class(fmt, protocol)
            if resolver_cls is None:
                logger.error("No resolver for format '%s' with server '%s'", fmt, protocol)
                continue

            server_cls = get_server_class(protocol)
            if server_cls is None:
                logger.error("No server implementation for protocol '%s'", protocol)
                continue

            resolver = resolver_cls(dep_id, identity, fmt_params, args.dest)
            server = server_cls(protocol_params)

            if args.dry_run:
                logger.info("[dry-run] fetching %s from %s", identity, protocol_params)
            else:
                try:
                    with resolver.pre_fetch_process() as output_path:
                        server_ret = server.fetch(identity, output_path)
                        resolver.post_fetch_process(server_ret)
                    break  # 成功したら次の dependency へ
                except Exception as e:
                    logger.warning("Server %s failed for %s: %s", protocol, dep_id, e)
        else:
            logger.error("All servers failed for dependency %s", dep_id)

if __name__ == "__main__":
    main()
