from __future__ import annotations
import argparse
from pathlib import Path
import logging

from src.common.logging import setup_logging
from src.common.config import load_yaml
from src.engine.megr_adapter import MEGRArgs, megr_train

log = logging.getLogger(__name__)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["cadets","theia","trace"], required=True)
    ap.add_argument("--experiment", choices=["DEMO","REALTIME"], default="DEMO")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--save", required=True)
    ap.add_argument("--configs", default="configs")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()

    setup_logging(args.log_level)
    ds_cfg = load_yaml(Path(args.configs)/"datasets.yaml")
    ds = ds_cfg["tc"][args.dataset]
    exp_rel = ds_cfg["experiments"]["demo"] if args.experiment == "DEMO" else ds_cfg["experiments"]["realtime"]
    exp_path = Path(ds["root"])/exp_rel

    rc = megr_train(MEGRArgs(dataset=ds["engine_name"], dataset_path=exp_path, epochs=args.epochs, save=Path(args.save), train=True))
    log.info("Engine train return code: %s", rc)

if __name__ == "__main__":
    main()
