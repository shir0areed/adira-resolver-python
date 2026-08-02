import argparse
import hashlib
import sys
from pathlib import Path
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
    p.add_argument("--dest", "-d", help="Resolve destination directory")
    p.add_argument("--dry-run", action="store_true", help="Show actions without performing them")
    p.add_argument("manifests", nargs=1, help="Path to manifest TOML (main file)")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    config = load_config(args.config)
    manifest = load_manifest_with_additions(args.manifests[0])

    # -----------------------------
    # retrieval_dir の仕様に基づく処理
    # -----------------------------
    manifest_file = Path(args.manifests[0]).resolve()
    manifest_dir = manifest_file.parent

    manifest_retrieval_dir = manifest.get("retrieval_dir")
    default_parent = config.get("default_retrieval_dir_parent")

    # Case 1: manifest が retrieval_dir を指定している
    if manifest_retrieval_dir is not None:
        if args.dest:
            logger.error(
                "Manifest specifies retrieval_dir='%s', but --dest was also provided. "
                "When retrieval_dir is present, --dest must NOT be used.",
                manifest_retrieval_dir
            )
            sys.exit(1)

        dest_dir = (manifest_dir / manifest_retrieval_dir).resolve()

    # Case 2: manifest が retrieval_dir を指定していないが --dest がある
    elif args.dest:
        dest_dir = Path(args.dest).resolve()

    # Case 3: manifest が retrieval_dir を指定しておらず、--dest もない
    else:
        if not default_parent:
            logger.error(
                "Neither manifest.retrieval_dir nor --dest is specified, "
                "and config has no default_retrieval_dir_parent."
            )
            sys.exit(1)

        parent = Path(default_parent).resolve()
        parent.mkdir(parents=True, exist_ok=True)

        # manifest の絶対パスをハッシュ化して決定的なディレクトリ名を生成
        h = hashlib.sha256(str(manifest_file).encode("utf-8")).hexdigest()
        unique_name = f"adira_resolve_{h[:12]}"

        dest_dir = parent / unique_name

    logger.info("Using retrieval_dir: %s", dest_dir)
    
    if not args.dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

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

            server_cls = get_server_class(protocol)
            if server_cls is None:
                logger.error("No server implementation for protocol '%s'", protocol)
                continue

            resolver_cls = get_resolver_class(fmt, server_cls.get_server_semantics())
            if resolver_cls is None:
                logger.error("No resolver for format '%s' with server '%s'", fmt, protocol)
                continue

            resolver = resolver_cls(dep_id, identity, fmt_params, dest_dir)
            server = server_cls(protocol_params)

            try:
                resolver.retrieve(server, args.dry_run)
                if not args.dry_run:
                    break  # 成功したら次の dependency へ
            except Exception as e:
                logger.warning("Server %s failed for %s: %s", protocol, dep_id, e)
        else:
            logger.error("All servers failed for dependency %s", dep_id)

    logger.info("Retrieval completed. Final retrieval_dir: %s", dest_dir)

if __name__ == "__main__":
    main()
