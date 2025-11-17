"""Tests für Multi-Proband Aggregator Module"""

import pytest
from src.dara_system.multi_proband_aggregator import (
    MultiProbandAggregator,
    CustomAggregator,
    AggregationError
)
from src.dara_system.dara_processor import TimeSlice


class TestMultiProbandAggregator:
    """Tests für MultiProbandAggregator"""

    @pytest.fixture
    def sample_time_slice(self):
        """Erstellt einen Test-TimeSlice"""
        return TimeSlice(
            timestamp=0,
            data={
                "proband1": {"value": 10.0, "score": 5.0},
                "proband2": {"value": 20.0, "score": 15.0},
                "proband3": {"value": 30.0, "score": 25.0},
            }
        )

    def test_initialization(self):
        """Test: Initialisierung"""
        aggregator = MultiProbandAggregator(
            numeric_fields=["value", "score"],
            min_valid_probands=2
        )

        assert aggregator.numeric_fields == ["value", "score"]
        assert aggregator.min_valid_probands == 2

    def test_aggregate_time_slice(self, sample_time_slice):
        """Test: TimeSlice-Aggregation"""
        aggregator = MultiProbandAggregator()

        result = aggregator.aggregate_time_slice(sample_time_slice)

        assert result.timestamp == 0
        assert result.proband_count == 3

        # Prüfe Statistiken
        assert "value" in result.statistics
        assert result.statistics["value"]["mean"] == 20.0
        assert result.statistics["value"]["min"] == 10.0
        assert result.statistics["value"]["max"] == 30.0

    def test_aggregate_with_missing_data(self):
        """Test: Aggregation mit fehlenden Daten"""
        time_slice = TimeSlice(
            timestamp=0,
            data={
                "p1": {"value": 10.0},
                "p2": None,  # Fehlende Daten
                "p3": {"value": 30.0},
            }
        )

        aggregator = MultiProbandAggregator(skip_missing=True)
        result = aggregator.aggregate_time_slice(time_slice)

        # Nur 2 gültige Probanden
        assert result.proband_count == 2

    def test_min_valid_probands_error(self):
        """Test: Fehler bei zu wenigen Probanden"""
        time_slice = TimeSlice(
            timestamp=0,
            data={"p1": {"value": 10.0}}
        )

        aggregator = MultiProbandAggregator(min_valid_probands=3)

        with pytest.raises(AggregationError):
            aggregator.aggregate_time_slice(time_slice)

    def test_aggregate_time_slices(self):
        """Test: Mehrere TimeSlices aggregieren"""
        time_slices = [
            TimeSlice(timestamp=i, data={f"p{j}": {"val": i + j} for j in range(3)})
            for i in range(5)
        ]

        aggregator = MultiProbandAggregator()
        results = aggregator.aggregate_time_slices(time_slices)

        assert len(results) == 5

    def test_aggregate_time_window(self):
        """Test: Zeitfenster-Aggregation"""
        time_slices = [
            TimeSlice(timestamp=0, data={"p1": {"val": 10.0}, "p2": {"val": 20.0}}),
            TimeSlice(timestamp=1, data={"p1": {"val": 30.0}, "p2": {"val": 40.0}}),
        ]

        aggregator = MultiProbandAggregator()
        window_agg = aggregator.aggregate_time_window(time_slices, "mean")

        # Mean über alle Werte: (10+20+30+40)/4 = 25
        assert window_agg["val"] == 25.0

    def test_field_summary(self):
        """Test: Feld-Zusammenfassung"""
        time_slices = [
            TimeSlice(timestamp=i, data={"p1": {"val": float(i * 10)}})
            for i in range(5)
        ]

        aggregator = MultiProbandAggregator()
        agg_slices = aggregator.aggregate_time_slices(time_slices)

        summary = aggregator.get_field_summary(agg_slices)

        assert "val" in summary
        assert summary["val"]["time_points"] == 5


class TestCustomAggregator:
    """Tests für CustomAggregator"""

    def test_register_function(self):
        """Test: Custom-Funktion registrieren"""
        aggregator = CustomAggregator()

        def custom_func(values):
            return sum(values) / len(values) if values else 0.0

        aggregator.register_function("my_avg", custom_func)

        assert "my_avg" in aggregator.aggregation_functions

    def test_apply_custom_aggregation(self):
        """Test: Custom-Aggregation anwenden"""
        aggregator = CustomAggregator()

        # Registriere Median-Funktion
        def median(values):
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            return sorted_vals[n // 2]

        aggregator.register_function("median", median)

        time_slice = TimeSlice(
            timestamp=0,
            data={
                "p1": {"score": 10.0},
                "p2": {"score": 20.0},
                "p3": {"score": 30.0},
            }
        )

        result = aggregator.apply_custom_aggregation(time_slice, "score", "median")
        assert result == 20.0
