import tomllib
from pathlib import Path
import logging
logger = logging.getLogger("adira_resolver.manifest")

def load_manifest_with_additions(main_manifest_path):
    main_path = Path(main_manifest_path)
    if not main_path.exists():
        raise FileNotFoundError(main_manifest_path)
    base_dir = main_path.parent

    with main_path.open("rb") as f:
        main = tomllib.load(f)

    # find additional files: any TOML files under same dir or subdirs that contain only [dependencies]
    # simple heuristic: files with 'dependencies' top-level key and no other top-level keys
    merged_deps = dict(main.get("dependencies", {}))
    for p in base_dir.rglob("*.toml"):
        if p.resolve() == main_path.resolve():
            continue
        try:
            with p.open("rb") as f:
                doc = tomllib.load(f)
        except Exception:
            continue
        if set(doc.keys()) == {"dependencies"}:
            for k, v in doc["dependencies"].items():
                if k in merged_deps:
                    raise ValueError(f"Dependency id conflict for {k} in {p}")
                merged_deps[k] = v
                logger.info("Merged dependency %s from %s", k, p)
    main["dependencies"] = merged_deps
    return main
