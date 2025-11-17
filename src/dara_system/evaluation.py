"""
Evaluations-Modul für DaRa-Experimente.

Bietet Funktionen zur:
- Berechnung von Metriken aus Experiment-Ergebnissen
- Evaluation von Analyse-Qualität
- Vergleich mehrerer Experimente
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class EvaluationMetrics:
    """Container für Evaluations-Metriken."""

    # Grundlegende Statistiken
    total_time_slices: int = 0
    valid_time_slices: int = 0
    invalid_time_slices: int = 0
    coverage: float = 0.0  # valid / total

    # Proband-Statistiken
    total_probands: int = 0
    avg_valid_probands_per_slice: float = 0.0
    min_valid_probands: int = 0
    max_valid_probands: int = 0

    # Numerische Feld-Statistiken
    field_statistics: Dict[str, Dict[str, float]] = None

    # Pattern-Statistiken
    pattern_counts: Dict[str, int] = None
    total_patterns: int = 0

    # Anomalie-Statistiken
    anomaly_count: int = 0
    anomaly_rate: float = 0.0  # anomalies / valid_slices

    # Metadaten
    experiment_name: str = ""
    evaluated_at: str = ""

    def __post_init__(self):
        if self.field_statistics is None:
            self.field_statistics = {}
        if self.pattern_counts is None:
            self.pattern_counts = {}
        if not self.evaluated_at:
            self.evaluated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Metriken zu Dictionary."""
        return asdict(self)

    def to_json(self, filepath: Path):
        """Speichert Metriken als JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationMetrics":
        """Erstellt Metriken aus Dictionary."""
        return cls(**data)


def evaluate_pipeline_results(
    aggregated_slices: List[Any],
    analysis_result: Any,
    experiment_name: str = "",
    primary_field: str = "value",
) -> EvaluationMetrics:
    """
    Evaluiert die Ergebnisse einer Pipeline-Ausführung.

    Args:
        aggregated_slices: Liste der aggregierten Zeit-Slices
        analysis_result: Ergebnis des Process Analysis Agent
        experiment_name: Name des Experiments
        primary_field: Primäres numerisches Feld

    Returns:
        EvaluationMetrics-Instanz
    """
    metrics = EvaluationMetrics(experiment_name=experiment_name)

    # Grundlegende Slice-Statistiken
    metrics.total_time_slices = len(aggregated_slices)
    metrics.valid_time_slices = sum(1 for s in aggregated_slices if s.is_valid)
    metrics.invalid_time_slices = metrics.total_time_slices - metrics.valid_time_slices

    if metrics.total_time_slices > 0:
        metrics.coverage = metrics.valid_time_slices / metrics.total_time_slices

    # Proband-Statistiken
    if aggregated_slices:
        valid_proband_counts = [s.valid_proband_count for s in aggregated_slices if s.is_valid]
        if valid_proband_counts:
            metrics.avg_valid_probands_per_slice = sum(valid_proband_counts) / len(
                valid_proband_counts
            )
            metrics.min_valid_probands = min(valid_proband_counts)
            metrics.max_valid_probands = max(valid_proband_counts)

        # Schätze totale Probanden aus erstem Slice
        first_slice = aggregated_slices[0]
        if hasattr(first_slice, "proband_count"):
            metrics.total_probands = first_slice.proband_count

    # Numerische Feld-Statistiken
    metrics.field_statistics = {}

    for slice_obj in aggregated_slices:
        if not slice_obj.is_valid:
            continue

        for field_name, stats in slice_obj.statistics.items():
            if field_name not in metrics.field_statistics:
                metrics.field_statistics[field_name] = {
                    "min": float("inf"),
                    "max": float("-inf"),
                    "sum": 0.0,
                    "count": 0,
                }

            field_metrics = metrics.field_statistics[field_name]
            if "mean" in stats:
                mean_val = stats["mean"]
                field_metrics["min"] = min(field_metrics["min"], mean_val)
                field_metrics["max"] = max(field_metrics["max"], mean_val)
                field_metrics["sum"] += mean_val
                field_metrics["count"] += 1

    # Berechne Durchschnitte
    for field_name, stats in metrics.field_statistics.items():
        if stats["count"] > 0:
            stats["mean"] = stats["sum"] / stats["count"]

    # Pattern-Statistiken aus Analysis Result
    if hasattr(analysis_result, "patterns"):
        metrics.pattern_counts = {}
        for pattern in analysis_result.patterns:
            pattern_type = pattern.pattern_type
            metrics.pattern_counts[pattern_type] = metrics.pattern_counts.get(pattern_type, 0) + 1

        metrics.total_patterns = len(analysis_result.patterns)

    # Anomalie-Statistiken
    if hasattr(analysis_result, "patterns"):
        metrics.anomaly_count = sum(
            1 for p in analysis_result.patterns if p.pattern_type == "anomaly"
        )

        if metrics.valid_time_slices > 0:
            metrics.anomaly_rate = metrics.anomaly_count / metrics.valid_time_slices

    return metrics


def compute_basic_stats(aggregated_slices: List[Any], field_name: str) -> Dict[str, float]:
    """
    Berechnet grundlegende Statistiken für ein Feld über alle Slices.

    Args:
        aggregated_slices: Liste aggregierter Zeit-Slices
        field_name: Name des Feldes

    Returns:
        Dictionary mit Statistiken
    """
    values = []

    for slice_obj in aggregated_slices:
        if not slice_obj.is_valid:
            continue

        if field_name in slice_obj.statistics:
            stats = slice_obj.statistics[field_name]
            if "mean" in stats:
                values.append(stats["mean"])

    if not values:
        return {}

    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "count": len(values),
    }


def compare_experiments(
    metrics_list: List[EvaluationMetrics],
) -> Dict[str, Any]:
    """
    Vergleicht mehrere Experiment-Evaluationen.

    Args:
        metrics_list: Liste von EvaluationMetrics

    Returns:
        Dictionary mit Vergleichsdaten
    """
    if not metrics_list:
        return {}

    comparison = {
        "experiment_count": len(metrics_list),
        "experiments": [m.experiment_name for m in metrics_list],
        "coverage": {
            "min": min(m.coverage for m in metrics_list),
            "max": max(m.coverage for m in metrics_list),
            "mean": sum(m.coverage for m in metrics_list) / len(metrics_list),
        },
        "total_patterns": {
            "min": min(m.total_patterns for m in metrics_list),
            "max": max(m.total_patterns for m in metrics_list),
            "mean": sum(m.total_patterns for m in metrics_list) / len(metrics_list),
        },
        "anomaly_rate": {
            "min": min(m.anomaly_rate for m in metrics_list),
            "max": max(m.anomaly_rate for m in metrics_list),
            "mean": sum(m.anomaly_rate for m in metrics_list) / len(metrics_list),
        },
    }

    return comparison


def save_evaluation_report(
    metrics: EvaluationMetrics,
    output_dir: Path,
    filename: str = "evaluation_report.json",
):
    """
    Speichert einen Evaluations-Report.

    Args:
        metrics: Evaluations-Metriken
        output_dir: Zielverzeichnis
        filename: Dateiname
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename
    metrics.to_json(output_path)

    print(f"Evaluations-Report gespeichert: {output_path}")


def print_evaluation_summary(metrics: EvaluationMetrics):
    """
    Gibt eine Zusammenfassung der Evaluation auf der Konsole aus.

    Args:
        metrics: Evaluations-Metriken
    """
    print("\n" + "=" * 60)
    print(f"EVALUATIONS-ZUSAMMENFASSUNG: {metrics.experiment_name}")
    print("=" * 60)

    print(f"\nZeit-Slices:")
    print(f"  Total:   {metrics.total_time_slices}")
    print(f"  Valid:   {metrics.valid_time_slices}")
    print(f"  Invalid: {metrics.invalid_time_slices}")
    print(f"  Coverage: {metrics.coverage * 100:.2f}%")

    print(f"\nProbanden:")
    print(f"  Total: {metrics.total_probands}")
    print(f"  Durchschnitt pro Slice: {metrics.avg_valid_probands_per_slice:.2f}")
    print(f"  Min/Max: {metrics.min_valid_probands}/{metrics.max_valid_probands}")

    if metrics.field_statistics:
        print(f"\nFeld-Statistiken:")
        for field, stats in metrics.field_statistics.items():
            print(f"  {field}:")
            print(f"    Mean: {stats.get('mean', 'N/A'):.3f}")
            print(f"    Min:  {stats.get('min', 'N/A'):.3f}")
            print(f"    Max:  {stats.get('max', 'N/A'):.3f}")

    if metrics.pattern_counts:
        print(f"\nErkannte Patterns:")
        for pattern_type, count in metrics.pattern_counts.items():
            print(f"  {pattern_type}: {count}")
        print(f"  TOTAL: {metrics.total_patterns}")

    print(f"\nAnomalien:")
    print(f"  Anzahl: {metrics.anomaly_count}")
    print(f"  Rate:   {metrics.anomaly_rate * 100:.2f}%")

    print("=" * 60 + "\n")
