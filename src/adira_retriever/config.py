import tomllib
from pathlib import Path

def load_config(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with p.open("rb") as f:
        cfg = tomllib.load(f)
    # minimal normalization
    return cfg
