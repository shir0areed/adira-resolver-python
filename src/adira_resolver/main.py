import argparse
import sys
import os
import logging
from .config import load_config
from .manifest import load_manifest_with_additions
from .artifact_server import ArtifactServerFactory
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
        fmt = dep.get("format")
        if not fmt:
            logger.error("Dependency %s has no format; skipping", dep_id)
            continue

        logger.info("Resolving %s (format=%s)", dep_id, fmt)
        resolver_cls = get_resolver_class(fmt)
        if resolver_cls is None:
            logger.error("No resolver for format '%s' (dependency %s)", fmt, dep_id)
            continue

        # create artifact server client for this format
        server_cfg = config.get("formats", {}).get(fmt, {})
        artifact_server = ArtifactServerFactory.create(fmt, server_cfg)

        resolver = resolver_cls(dep_id=dep_id, dep=dep, dest_root=args.dest, artifact_server=artifact_server, config=config)
        if args.dry_run:
            resolver.dry_run()
        else:
            try:
                resolver.resolve()
            except Exception as e:
                logger.exception("Failed to resolve %s: %s", dep_id, e)

if __name__ == "__main__":
    main()
