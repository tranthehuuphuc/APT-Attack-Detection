from __future__ import annotations
from pathlib import Path
import logging
from src.engine.megr_adapter import MEGRArgs, megr_predict

log = logging.getLogger(__name__)

def run_predict(dataset_engine_name: str, experiment_path: Path, predict_file: str, checkpoint: Path, threshold: float = 0.5) -> int:
    args = MEGRArgs(
        dataset=dataset_engine_name,
        dataset_path=experiment_path,
        predict=True,
        predict_file=predict_file,
        load=checkpoint,
        threshold=threshold,
    )
    return megr_predict(args)
