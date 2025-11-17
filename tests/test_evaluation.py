"""Tests für das Evaluation-Modul."""

import pytest
from dataclasses import dataclass
from dara_system.evaluation import (
    EvaluationMetrics,
    evaluate_pipeline_results,
    compute_basic_stats,
    compare_experiments,
)


@dataclass
class MockAggregatedSlice:
    """Mock für aggregierte Zeit-Slices."""

    is_valid: bool
    valid_proband_count: int
    proband_count: int
    statistics: dict


@dataclass
class MockPattern:
    """Mock für erkannte Patterns."""

    pattern_type: str
    description: str
    start_index: int
    end_index: int
    confidence: float


@dataclass
class MockAnalysisResult:
    """Mock für Analyse-Ergebnisse."""

    summary: str
    patterns: list


def test_evaluation_metrics_initialization():
    """Testet EvaluationMetrics-Initialisierung."""
    metrics = EvaluationMetrics(experiment_name="test")

    assert metrics.experiment_name == "test"
    assert metrics.total_time_slices == 0
    assert metrics.field_statistics == {}
    assert metrics.pattern_counts == {}


def test_evaluation_metrics_to_dict():
    """Testet Konvertierung zu Dictionary."""
    metrics = EvaluationMetrics(experiment_name="test", total_time_slices=100)

    data = metrics.to_dict()

    assert isinstance(data, dict)
    assert data["experiment_name"] == "test"
    assert data["total_time_slices"] == 100


def test_evaluate_pipeline_results_basic():
    """Testet grundlegende Pipeline-Evaluation."""
    # Mock-Daten
    slices = [
        MockAggregatedSlice(
            is_valid=True,
            valid_proband_count=3,
            proband_count=3,
            statistics={"value": {"mean": 10.0}},
        ),
        MockAggregatedSlice(
            is_valid=True,
            valid_proband_count=3,
            proband_count=3,
            statistics={"value": {"mean": 15.0}},
        ),
        MockAggregatedSlice(
            is_valid=False,
            valid_proband_count=0,
            proband_count=3,
            statistics={},
        ),
    ]

    patterns = [
        MockPattern("baseline", "Baseline phase", 0, 10, 0.9),
        MockPattern("peak", "Peak detected", 15, 20, 0.85),
        MockPattern("anomaly", "Anomaly found", 25, 26, 0.7),
    ]

    analysis = MockAnalysisResult(summary="Test analysis", patterns=patterns)

    # Evaluiere
    metrics = evaluate_pipeline_results(slices, analysis, "test_exp", "value")

    assert metrics.total_time_slices == 3
    assert metrics.valid_time_slices == 2
    assert metrics.invalid_time_slices == 1
    assert metrics.coverage == 2 / 3
    assert metrics.total_patterns == 3
    assert metrics.anomaly_count == 1
    assert "baseline" in metrics.pattern_counts
    assert "peak" in metrics.pattern_counts
    assert "anomaly" in metrics.pattern_counts


def test_compute_basic_stats():
    """Testet Berechnung von Basis-Statistiken."""
    slices = [
        MockAggregatedSlice(
            is_valid=True,
            valid_proband_count=3,
            proband_count=3,
            statistics={"value": {"mean": 10.0}},
        ),
        MockAggregatedSlice(
            is_valid=True,
            valid_proband_count=3,
            proband_count=3,
            statistics={"value": {"mean": 20.0}},
        ),
        MockAggregatedSlice(
            is_valid=True,
            valid_proband_count=3,
            proband_count=3,
            statistics={"value": {"mean": 30.0}},
        ),
    ]

    stats = compute_basic_stats(slices, "value")

    assert stats["min"] == 10.0
    assert stats["max"] == 30.0
    assert stats["mean"] == 20.0
    assert stats["count"] == 3


def test_compute_basic_stats_empty():
    """Testet Basis-Statistiken mit leerer Liste."""
    stats = compute_basic_stats([], "value")

    assert stats == {}


def test_compare_experiments():
    """Testet Vergleich mehrerer Experimente."""
    metrics1 = EvaluationMetrics(
        experiment_name="exp1",
        coverage=0.8,
        total_patterns=10,
        anomaly_rate=0.05,
    )

    metrics2 = EvaluationMetrics(
        experiment_name="exp2",
        coverage=0.9,
        total_patterns=15,
        anomaly_rate=0.03,
    )

    comparison = compare_experiments([metrics1, metrics2])

    assert comparison["experiment_count"] == 2
    assert comparison["coverage"]["min"] == 0.8
    assert comparison["coverage"]["max"] == 0.9
    assert comparison["total_patterns"]["min"] == 10
    assert comparison["total_patterns"]["max"] == 15


def test_compare_experiments_empty():
    """Testet Vergleich mit leerer Liste."""
    comparison = compare_experiments([])

    assert comparison == {}
