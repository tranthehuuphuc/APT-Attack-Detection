from __future__ import annotations
import argparse
from pathlib import Path
import logging
import time

from src.common.logging import setup_logging
from src.common.config import load_yaml
from src.common.io import read_jsonl
from src.pipeline.hunting.provenance import WindowedProvenanceGraph
from src.pipeline.hunting.seeding import find_seeds
from src.pipeline.hunting.extractor import k_hop_subgraph
from src.pipeline.hunting.export_megr import to_megr_data_list, save_prediction_pt
from src.pipeline.hunting.predictor import run_predict

log = logging.getLogger(__name__)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["cadets","theia","trace"], required=True)
    ap.add_argument("--experiment", choices=["DEMO","REALTIME"], default="REALTIME")
    ap.add_argument("--events", default="runs/events/events.jsonl")
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--query-name", default="qg")
    ap.add_argument("--cti-seeds", default="runs/cti/seeds.json", help="Path to CTI seeds.json produced by pipeline.agent")
    ap.add_argument("--configs", default="configs")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()

    setup_logging(args.log_level)
    ds_cfg = load_yaml(Path(args.configs)/"datasets.yaml")
    hunt_cfg = load_yaml(Path(args.configs)/"hunting.yaml")
    ds = ds_cfg["tc"][args.dataset]
    exp_rel = ds_cfg["experiments"]["realtime"] if args.experiment == "REALTIME" else ds_cfg["experiments"]["demo"]
    exp_path = Path(ds["root"])/exp_rel

    pg = WindowedProvenanceGraph(window_seconds=int(hunt_cfg["window_seconds"]), max_nodes=int(hunt_cfg["max_nodes"]))
    events_path = Path(args.events)
    if not events_path.exists():
        raise FileNotFoundError(events_path)

    # ingest all events (replay-style). For realtime, run this in a loop or tail.
    for ev in read_jsonl(events_path):
        pg.ingest(ev)

    seeds = find_seeds(pg.g, query_name=args.query_name, cti_seeds_path=args.cti_seeds)
    sub = k_hop_subgraph(pg.g, seeds, k=int(hunt_cfg["k_hop"]))
    g_name = args.query_name

    predict_file = f"{args.query_name}_in_realtime_{int(time.time())}.pt"
    out_pt = exp_path/"raw/torch_prediction"/predict_file
    data_list = to_megr_data_list(sub, g_name=g_name)
    save_prediction_pt(out_pt, data_list)
    log.info("Wrote prediction graph: %s", out_pt)

    rc = run_predict(ds["engine_name"], exp_path, predict_file, Path(args.checkpoint))
    log.info("Engine predict return code: %s", rc)

if __name__ == "__main__":
    main()
