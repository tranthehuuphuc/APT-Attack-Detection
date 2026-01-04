from __future__ import annotations
"""
CTI Agent Evaluation Module

Metrics:
- Technique extraction precision/recall
- Indicator extraction accuracy  
- Confidence calibration
- MITRE ATT&CK coverage
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class EvalMetrics:
    """Evaluation metrics for CTI Agent"""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
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


def load_seeds(seeds_path: Path) -> Dict:
    """Load CTI seeds.json"""
    if not seeds_path.exists():
        raise FileNotFoundError(f"Seeds file not found: {seeds_path}")
    return json.loads(seeds_path.read_text())


def load_ground_truth(gt_path: Path) -> Dict:
    """Load ground truth annotations
    
    Expected format:
    {
        "techniques": [{"technique_id": "T1059", ...}],
        "indicators": [{"type": "file_path", "value": "/tmp/malware", ...}]
    }
    """
    if not gt_path.exists():
        log.warning(f"Ground truth not found: {gt_path}")
        return {"techniques": [], "indicators": []}
    return json.loads(gt_path.read_text())


def evaluate_techniques(
    predicted: List[Dict], 
    ground_truth: List[Dict],
    confidence_threshold: float = 0.35
) -> Tuple[EvalMetrics, Dict]:
    """Evaluate technique extraction"""
    
    # Filter by confidence
    predicted_filtered = [
        t for t in predicted 
        if t.get("confidence", 0) >= confidence_threshold
    ]
    
    pred_ids = set(t.get("technique_id") for t in predicted_filtered)
    gt_ids = set(t.get("technique_id") for t in ground_truth)
    
    metrics = EvalMetrics()
    metrics.true_positives = len(pred_ids & gt_ids)
    metrics.false_positives = len(pred_ids - gt_ids)
    metrics.false_negatives = len(gt_ids - pred_ids)
    
    # Detailed analysis
    details = {
        "correct": list(pred_ids & gt_ids),
        "incorrect": list(pred_ids - gt_ids),
        "missed": list(gt_ids - pred_ids),
        "total_predicted": len(pred_ids),
        "total_ground_truth": len(gt_ids),
    }
    
    return metrics, details


def evaluate_indicators(
    predicted: List[Dict],
    ground_truth: List[Dict]
) -> Tuple[EvalMetrics, Dict]:
    """Evaluate indicator extraction"""
    
    def indicator_key(ind: Dict) -> Tuple[str, str]:
        return (ind.get("type", ""), ind.get("value", "").lower())
    
    pred_set = set(indicator_key(i) for i in predicted)
    gt_set = set(indicator_key(i) for i in ground_truth)
    
    metrics = EvalMetrics()
    metrics.true_positives = len(pred_set & gt_set)
    metrics.false_positives = len(pred_set - gt_set)
    metrics.false_negatives = len(gt_set - pred_set)
    
    details = {
        "correct": list(pred_set & gt_set),
        "incorrect": list(pred_set - gt_set),
        "missed": list(gt_set - pred_set),
        "type_distribution": Counter(i.get("type") for i in predicted),
    }
    
    return metrics, details


def analyze_confidence_calibration(techniques: List[Dict]) -> Dict:
    """Analyze confidence score calibration"""
    if not techniques:
        return {}
    
    confidences = [t.get("confidence", 0) for t in techniques]
    
    # Bin by confidence ranges
    bins = defaultdict(list)
    for t in techniques:
        conf = t.get("confidence", 0)
        if conf < 0.3:
            bins["low"].append(t)
        elif conf < 0.6:
            bins["medium"].append(t)
        elif conf < 0.8:
            bins["high"].append(t)
        else:
            bins["very_high"].append(t)
    
    return {
        "mean": sum(confidences) / len(confidences),
        "median": sorted(confidences)[len(confidences) // 2],
        "min": min(confidences),
        "max": max(confidences),
        "std": (sum((c - sum(confidences)/len(confidences))**2 for c in confidences) / len(confidences))**0.5,
        "bins": {k: len(v) for k, v in bins.items()},
    }


def evaluate_coverage(techniques: List[Dict], stix_path: Path) -> Dict:
    """Evaluate MITRE ATT&CK coverage"""
    if not stix_path.exists():
        log.warning(f"STIX file not found: {stix_path}")
        return {}
    
    stix_data = json.loads(stix_path.read_text())
    all_techniques = [
        obj for obj in stix_data["objects"]
        if obj.get("type") == "attack-pattern"
    ]
    
    all_tids = set()
    for tech in all_techniques:
        # Get external references for technique IDs
        for ref in tech.get("external_references", []):
            if ref.get("source_name") == "mitre-attack":
                tid = ref.get("external_id")
                if tid:
                    all_tids.add(tid)
    
    extracted_tids = set(t.get("technique_id") for t in techniques)
    
    # Tactics coverage
    tactic_count = Counter()
    for tech in all_techniques:
        for ref in tech.get("external_references", []):
            if ref.get("source_name") == "mitre-attack":
                tid = ref.get("external_id")
                if tid in extracted_tids:
                    for phase in tech.get("kill_chain_phases", []):
                        tactic_count[phase.get("phase_name")] += 1
    
    return {
        "total_att&ck_techniques": len(all_tids),
        "extracted_techniques": len(extracted_tids),
        "coverage_percentage": len(extracted_tids) / len(all_tids) * 100 if all_tids else 0,
        "tactics_covered": dict(tactic_count),
    }


def run_evaluation(
    seeds_path: Path,
    ground_truth_path: Optional[Path] = None,
    stix_path: Optional[Path] = None,
    confidence_threshold: float = 0.35,
) -> Dict:
    """Run complete evaluation
    
    Args:
        seeds_path: Path to generated seeds.json
        ground_truth_path: Optional ground truth annotations
        stix_path: Optional MITRE ATT&CK STIX file
        confidence_threshold: Minimum confidence for predictions
        
    Returns:
        Dictionary with all evaluation results
    """
    results = {}
    
    # Load predictions
    seeds = load_seeds(seeds_path)
    predicted_techniques = seeds.get("techniques", [])
    predicted_indicators = seeds.get("indicators", [])
    
    results["summary"] = {
        "total_techniques": len(predicted_techniques),
        "total_indicators": len(predicted_indicators),
    }
    
    # Confidence analysis (always available)
    results["confidence"] = analyze_confidence_calibration(predicted_techniques)
    
    # Coverage analysis (if STIX available)
    if stix_path:
        results["coverage"] = evaluate_coverage(predicted_techniques, stix_path)
    
    # Precision/Recall (if ground truth available)
    if ground_truth_path:
        gt = load_ground_truth(ground_truth_path)
        
        tech_metrics, tech_details = evaluate_techniques(
            predicted_techniques,
            gt.get("techniques", []),
            confidence_threshold
        )
        
        ind_metrics, ind_details = evaluate_indicators(
            predicted_indicators,
            gt.get("indicators", [])
        )
        
        results["techniques"] = {
            "precision": tech_metrics.precision,
            "recall": tech_metrics.recall,
            "f1": tech_metrics.f1,
            "details": tech_details,
        }
        
        results["indicators"] = {
            "precision": ind_metrics.precision,
            "recall": ind_metrics.recall,
            "f1": ind_metrics.f1,
            "details": ind_details,
        }
    
    return results


def print_evaluation_report(results: Dict):
    """Pretty print evaluation results"""
    print("=" * 60)
    print("CTI AGENT EVALUATION REPORT")
    print("=" * 60)
    
    # Summary
    print("\nSUMMARY:")
    print(f"  Techniques extracted: {results['summary']['total_techniques']}")
    print(f"  Indicators extracted: {results['summary']['total_indicators']}")
    
    # Confidence
    if "confidence" in results and results["confidence"]:
        conf = results["confidence"]
        print("\nCONFIDENCE ANALYSIS:")
        print(f"  Mean: {conf['mean']:.3f}")
        print(f"  Median: {conf['median']:.3f}")
        print(f"  Std Dev: {conf['std']:.3f}")
        print(f"  Range: [{conf['min']:.3f}, {conf['max']:.3f}]")
        if "bins" in conf:
            print("  Distribution:")
            for bin_name, count in conf["bins"].items():
                print(f"    {bin_name}: {count}")
    
    # Coverage
    if "coverage" in results:
        cov = results["coverage"]
        print("\nMITRE ATT&CK COVERAGE:")
        print(f"  Total techniques: {cov['total_att&ck_techniques']}")
        print(f"  Extracted: {cov['extracted_techniques']}")
        print(f"  Coverage: {cov['coverage_percentage']:.2f}%")
    
    # Techniques evaluation
    if "techniques" in results:
        tech = results["techniques"]
        print("\nTECHNIQUE EXTRACTION:")
        print(f"  Precision: {tech['precision']:.3f}")
        print(f"  Recall: {tech['recall']:.3f}")
        print(f"  F1 Score: {tech['f1']:.3f}")
        print(f"  Correct: {tech['details']['correct'][:5]}")
        print(f"  Incorrect: {tech['details']['incorrect'][:5]}")
        print(f"  Missed: {tech['details']['missed'][:5]}")
    
    # Indicators evaluation
    if "indicators" in results:
        ind = results["indicators"]
        print("\nINDICATOR EXTRACTION:")
        print(f"  Precision: {ind['precision']:.3f}")
        print(f"  Recall: {ind['recall']:.3f}")
        print(f"  F1 Score: {ind['f1']:.3f}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import argparse
    
    ap = argparse.ArgumentParser(description="Evaluate CTI Agent performance")
    ap.add_argument("--seeds", required=True, help="Path to seeds.json")
    ap.add_argument("--ground-truth", help="Path to ground truth annotations")
    ap.add_argument("--stix", help="Path to MITRE ATT&CK STIX JSON")
    ap.add_argument("--confidence-threshold", type=float, default=0.35)
    ap.add_argument("--output", help="Output JSON file for results")
    args = ap.parse_args()
    
    results = run_evaluation(
        Path(args.seeds),
        Path(args.ground_truth) if args.ground_truth else None,
        Path(args.stix) if args.stix else None,
        args.confidence_threshold,
    )
    
    print_evaluation_report(results)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2))
        log.info(f"Results saved to: {output_path}")
