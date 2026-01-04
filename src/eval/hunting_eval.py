from __future__ import annotations
"""
Hunting Pipeline Evaluation Module

Metrics:
- Detection latency
- Graph size and complexity
- Alert precision/recall
- False positive rate
"""

import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class HuntingMetrics:
    """Metrics for hunting pipeline execution"""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Graph metrics
    num_events: int = 0
    num_nodes: int = 0
    num_edges: int = 0
    num_seeds: int = 0
    subgraph_nodes: int = 0
    subgraph_edges: int = 0
    
    # Detection metrics
    alerts_generated: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    # Performance
    event_ingestion_time: float = 0.0
    seeding_time: float = 0.0
    extraction_time: float = 0.0
    prediction_time: float = 0.0
    
    @property
    def total_time(self) -> float:
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def events_per_second(self) -> float:
        if self.event_ingestion_time == 0:
            return 0.0
        return self.num_events / self.event_ingestion_time
    
    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def false_positive_rate(self) -> float:
        total_negatives = self.false_positives + (self.alerts_generated - self.true_positives)
        if total_negatives == 0:
            return 0.0
        return self.false_positives / total_negatives


class HuntingEvaluator:
    """Evaluator for hunting pipeline"""
    
    def __init__(self):
        self.metrics = HuntingMetrics()
        self.runs: List[HuntingMetrics] = []
    
    def start_run(self):
        """Start a new evaluation run"""
        self.metrics = HuntingMetrics()
    
    def end_run(self):
        """End current run and save metrics"""
        self.metrics.end_time = time.time()
        self.runs.append(self.metrics)
    
    def record_graph_stats(self, num_nodes: int, num_edges: int):
        """Record provenance graph statistics"""
        self.metrics.num_nodes = num_nodes
        self.metrics.num_edges = num_edges
    
    def record_seeds(self, num_seeds: int):
        """Record number of seed nodes found"""
        self.metrics.num_seeds = num_seeds
    
    def record_subgraph(self, num_nodes: int, num_edges: int):
        """Record extracted subgraph statistics"""
        self.metrics.subgraph_nodes = num_nodes
        self.metrics.subgraph_edges = num_edges
    
    def record_alerts(self, num_alerts: int):
        """Record number of alerts generated"""
        self.metrics.alerts_generated = num_alerts
    
    def record_ground_truth(self, true_positives: int, false_positives: int, false_negatives: int):
        """Record ground truth labels for evaluation"""
        self.metrics.true_positives = true_positives
        self.metrics.false_positives = false_positives
        self.metrics.false_negatives = false_negatives
    
    def get_summary(self) -> Dict:
        """Get summary of all runs"""
        if not self.runs:
            return {"error": "No runs completed"}
        
        return {
            "total_runs": len(self.runs),
            "average_latency": sum(r.total_time for r in self.runs) / len(self.runs),
            "average_events": sum(r.num_events for r in self.runs) / len(self.runs),
            "average_throughput": sum(r.events_per_second for r in self.runs) / len(self.runs),
            "average_precision": sum(r.precision for r in self.runs) / len(self.runs),
            "average_recall": sum(r.recall for r in self.runs) / len(self.runs),
            "average_f1": sum(r.f1 for r in self.runs) / len(self.runs),
            "average_fpr": sum(r.false_positive_rate for r in self.runs) / len(self.runs),
        }


def analyze_graph_complexity(graph_dict: Dict) -> Dict:
    """Analyze provenance graph complexity
    
    Args:
        graph_dict: NetworkX graph as dict (from nx.node_link_data)
    
    Returns:
        Complexity metrics
    """
    nodes = graph_dict.get("nodes", [])
    edges = graph_dict.get("links", [])
    
    # Node type distribution
    from collections import Counter
    node_types = Counter(n.get("ntype", "unknown") for n in nodes)
    
    # Edge type distribution  
    edge_types = Counter(e.get("etype", "unknown") for e in edges)
    
    # Degree distribution (simplified)
    in_degree = Counter()
    out_degree = Counter()
    for edge in edges:
        out_degree[edge["source"]] += 1
        in_degree[edge["target"]] += 1
    
    return {
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "node_types": dict(node_types),
        "edge_types": dict(edge_types),
        "avg_in_degree": sum(in_degree.values()) / len(nodes) if nodes else 0,
        "avg_out_degree": sum(out_degree.values()) / len(nodes) if nodes else 0,
        "max_in_degree": max(in_degree.values()) if in_degree else 0,
        "max_out_degree": max(out_degree.values()) if out_degree else 0,
    }


def evaluate_detection_accuracy(
    predictions: List[Dict],
    ground_truth: List[Dict],
    score_threshold: float = 0.5
) -> Dict:
    """Evaluate detection accuracy
    
    Args:
        predictions: List of predictions with scores
        ground_truth: List of ground truth labels
        score_threshold: Threshold for positive prediction
        
    Returns:
        Accuracy metrics
    """
    # Convert predictions to binary based on threshold
    pred_positives = set(
        p["node_id"] for p in predictions 
        if p.get("score", 0) >= score_threshold
    )
    
    gt_positives = set(g["node_id"] for g in ground_truth if g.get("is_malicious", False))
    gt_negatives = set(g["node_id"] for g in ground_truth if not g.get("is_malicious", False))
    
    tp = len(pred_positives & gt_positives)
    fp = len(pred_positives & gt_negatives)
    fn = len(gt_positives - pred_positives)
    tn = len(gt_negatives - pred_positives)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    
    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": accuracy,
        "threshold": score_threshold,
    }


def benchmark_hunting_latency(
    events_file: Path,
    num_trials: int = 10
) -> Dict:
    """Benchmark hunting pipeline latency
    
    Args:
        events_file: Path to events JSONL
        num_trials: Number of trials to run
        
    Returns:
        Latency statistics
    """
    latencies = []
    
    for _ in range(num_trials):
        start = time.time()
        
        # Simulate hunting pipeline stages
        # (In real implementation, call actual pipeline)
        from src.common.io import read_jsonl
        from src.pipeline.hunting.provenance import WindowedProvenanceGraph
        
        pg = WindowedProvenanceGraph()
        for ev in read_jsonl(events_file):
            pg.ingest(ev)
        
        latency = time.time() - start
        latencies.append(latency)
    
    return {
        "mean_latency": sum(latencies) / len(latencies),
        "min_latency": min(latencies),
        "max_latency": max(latencies),
        "median_latency": sorted(latencies)[len(latencies) // 2],
        "trials": num_trials,
    }


def print_hunting_report(metrics: HuntingMetrics):
    """Pretty print hunting evaluation report"""
    print("=" * 60)
    print("HUNTING PIPELINE EVALUATION REPORT")
    print("=" * 60)
    
    print("\nPERFORMANCE METRICS:")
    print(f"  Total Time: {metrics.total_time:.3f}s")
    print(f"  Event Ingestion: {metrics.event_ingestion_time:.3f}s")
    print(f"  Seeding: {metrics.seeding_time:.3f}s")
    print(f"  Extraction: {metrics.extraction_time:.3f}s")
    print(f"  Prediction: {metrics.prediction_time:.3f}s")
    print(f"  Throughput: {metrics.events_per_second:.2f} events/sec")
    
    print("\nGRAPH STATISTICS:")
    print(f"  Events Processed: {metrics.num_events}")
    print(f"  Graph Nodes: {metrics.num_nodes}")
    print(f"  Graph Edges: {metrics.num_edges}")
    print(f"  Seed Nodes: {metrics.num_seeds}")
    print(f"  Subgraph Nodes: {metrics.subgraph_nodes}")
    print(f"  Subgraph Edges: {metrics.subgraph_edges}")
    
    print("\nDETECTION METRICS:")
    print(f"  Alerts Generated: {metrics.alerts_generated}")
    if metrics.true_positives + metrics.false_positives > 0:
        print(f"  True Positives: {metrics.true_positives}")
        print(f"  False Positives: {metrics.false_positives}")
        print(f"  False Negatives: {metrics.false_negatives}")
        print(f"  Precision: {metrics.precision:.3f}")
        print(f"  Recall: {metrics.recall:.3f}")
        print(f"  F1 Score: {metrics.f1:.3f}")
        print(f"  FPR: {metrics.false_positive_rate:.3f}")
    else:
        print("  (No ground truth available)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import argparse
    
    ap = argparse.ArgumentParser(description="Evaluate Hunting Pipeline performance")
    ap.add_argument("--events", required=True, help="Path to events JSONL")
    ap.add_argument("--predictions", help="Path to predictions JSON")
    ap.add_argument("--ground-truth", help="Path to ground truth JSON")
    ap.add_argument("--benchmark-trials", type=int, default=10)
    ap.add_argument("--output", help="Output JSON file for results")
    args = ap.parse_args()
    
    results = {}
    
    # Benchmark latency
    if Path(args.events).exists():
        print("Running latency benchmark...")
        results["latency"] = benchmark_hunting_latency(
            Path(args.events),
            num_trials=args.benchmark_trials
        )
        print(f"Mean latency: {results['latency']['mean_latency']:.3f}s")
    
    # Evaluate accuracy
    if args.predictions and args.ground_truth:
        predictions = json.loads(Path(args.predictions).read_text())
        ground_truth = json.loads(Path(args.ground_truth).read_text())
        
        results["accuracy"] = evaluate_detection_accuracy(predictions, ground_truth)
        print(f"\nAccuracy: {results['accuracy']['accuracy']:.3f}")
        print(f"F1 Score: {results['accuracy']['f1_score']:.3f}")
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2))
        print(f"\nResults saved to: {output_path}")
