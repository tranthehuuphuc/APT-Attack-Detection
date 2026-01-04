from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from src.engine.runner import EngineSpec, run_engine

DEFAULT_ENGINE_ROOT = Path("src/engine/graph_matcher/engine_repo")
DEFAULT_ENGINE_ENTRY = Path("src/main.py")  # relative to engine root

def _dataset_path_arg(p: Path) -> str:
    s = str(p)
    return s if s.endswith("/") else s + "/"

@dataclass(frozen=True)
class MEGRArgs:
    dataset: str               # e.g., DARPA_CADETS
    dataset_path: Path         # experiments/<DEMO|REALTIME>/
    gnn_operator: str = "rgcn"
    threshold: float = 0.5
    epochs: int = 50
    save: Optional[Path] = None
    load: Optional[Path] = None
    predict_file: Optional[str] = None
    predict: bool = False
    train: bool = False

def megr_train(args: MEGRArgs, engine_root: Path = DEFAULT_ENGINE_ROOT) -> int:
    spec = EngineSpec(root=engine_root, entry=engine_root/DEFAULT_ENGINE_ENTRY)
    cli: list[str] = [
        "--dataset", args.dataset,
        "--dataset-path", _dataset_path_arg(args.dataset_path),
        "--gnn-operator", args.gnn_operator,
        "--epochs", str(args.epochs),
        "--train",
    ]
    if args.save:
        cli += ["--save", str(args.save)]
    return run_engine(spec, cli)

def megr_predict(args: MEGRArgs, engine_root: Path = DEFAULT_ENGINE_ROOT) -> int:
    if not args.load or not args.predict_file:
        raise ValueError("Predict requires load checkpoint and predict_file")
    spec = EngineSpec(root=engine_root, entry=engine_root/DEFAULT_ENGINE_ENTRY)
    cli: list[str] = [
        "--dataset", args.dataset,
        "--dataset-path", _dataset_path_arg(args.dataset_path),
        "--gnn-operator", args.gnn_operator,
        "--predict",
        "--predict-file", args.predict_file,
        "--threshold", str(args.threshold),
        "--load", str(args.load),
    ]
    return run_engine(spec, cli)
