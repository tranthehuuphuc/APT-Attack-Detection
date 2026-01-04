from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict

def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
