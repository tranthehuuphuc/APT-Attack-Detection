from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Optional, Sequence

@dataclass(frozen=True)
class EngineSpec:
    root: Path
    entry: Path

def run_engine(spec: EngineSpec, args: Sequence[str], env: Optional[dict[str, str]] = None) -> int:
    cmd = [sys.executable, str(spec.entry), *args]
    proc = subprocess.run(cmd, cwd=str(spec.root), env=env)
    return int(proc.returncode)
