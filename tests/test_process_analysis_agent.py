"""Tests für Process Analysis Agent Module"""

import pytest
from src.dara_system.process_analysis_agent import (
    ProcessAnalysisAgent,
    ProcessPhase,
    ProcessAnalysisError
)
from src.dara_system.multi_proband_aggregator import AggregatedTimeSlice


class TestProcessAnalysisAgent:
    """Tests für ProcessAnalysisAgent"""

    @pytest.fixture
    def sample_aggregated_slices(self):
        """Erstellt Test-AggregatedTimeSlices"""
        slices = []

        # Simuliere aufsteigenden Trend
        for i in range(10):
            value = i * 10.0
            slices.append(AggregatedTimeSlice(
                timestamp=i,
                proband_count=3,
                statistics={
                    "value": {
                        "mean": value,
                        "min": value - 5,
                        "max": value + 5,
                        "stdev": 2.0
                    }
                }
            ))

        return slices

    def test_initialization(self):
        """Test: Initialisierung"""
        agent = ProcessAnalysisAgent(
            baseline_threshold=0.2,
            peak_threshold=0.9
        )

        assert agent.baseline_threshold == 0.2
        assert agent.peak_threshold == 0.9

    def test_analyze_aggregated_slices(self, sample_aggregated_slices):
        """Test: Analyse von AggregatedTimeSlices"""
        agent = ProcessAnalysisAgent()

        result = agent.analyze_aggregated_slices(
            sample_aggregated_slices,
            primary_field="value"
        )

        assert result is not None
        assert len(result.states) == 10
        assert result.time_range == (0, 9)
        assert result.summary is not None

    def test_phase_identification(self, sample_aggregated_slices):
        """Test: Phasen-Identifikation"""
        agent = ProcessAnalysisAgent(
            baseline_threshold=0.2,
            peak_threshold=0.8
        )

        result = agent.analyze_aggregated_slices(
            sample_aggregated_slices,
            primary_field="value"
        )

        # Erste States sollten Baseline sein (niedrige Werte)
        assert result.states[0].phase == ProcessPhase.BASELINE

        # Letzte States sollten Peak sein (hohe Werte)
        assert result.states[-1].phase == ProcessPhase.PEAK

    def test_pattern_detection(self, sample_aggregated_slices):
        """Test: Muster-Erkennung"""
        agent = ProcessAnalysisAgent(min_pattern_length=3)

        result = agent.analyze_aggregated_slices(
            sample_aggregated_slices,
            primary_field="value"
        )

        # Sollte aufsteigenden Trend erkennen
        assert len(result.patterns) > 0

        # Mindestens ein ascending_trend
        ascending = [p for p in result.patterns if p.pattern_type == "ascending_trend"]
        assert len(ascending) > 0

    def test_empty_data_error(self):
        """Test: Fehler bei leeren Daten"""
        agent = ProcessAnalysisAgent()

        with pytest.raises(ProcessAnalysisError):
            agent.analyze_aggregated_slices([], primary_field="value")

    def test_missing_field_error(self):
        """Test: Fehler bei fehlendem Feld"""
        agent = ProcessAnalysisAgent()

        slices = [AggregatedTimeSlice(
            timestamp=0,
            proband_count=1,
            statistics={"other_field": {"mean": 10.0}}
        )]

        with pytest.raises(ProcessAnalysisError):
            agent.analyze_aggregated_slices(slices, primary_field="nonexistent")

    def test_plateau_detection(self):
        """Test: Plateau-Erkennung"""
        # Erstelle Daten mit Plateau
        slices = []
        for i in range(15):
            value = 50.0 if i >= 5 and i < 12 else float(i * 10)
            slices.append(AggregatedTimeSlice(
                timestamp=i,
                proband_count=2,
                statistics={"value": {"mean": value}}
            ))

        agent = ProcessAnalysisAgent(min_pattern_length=3)
        result = agent.analyze_aggregated_slices(slices, primary_field="value")

        # Sollte Plateau erkennen
        plateaus = [p for p in result.patterns if p.pattern_type == "plateau"]
        assert len(plateaus) > 0

    def test_statistics_calculation(self, sample_aggregated_slices):
        """Test: Statistik-Berechnung"""
        agent = ProcessAnalysisAgent()
        result = agent.analyze_aggregated_slices(
            sample_aggregated_slices,
            primary_field="value"
        )

        stats = result.statistics

        assert "total_time_points" in stats
        assert stats["total_time_points"] == 10
        assert "value_mean" in stats
        assert "value_min" in stats
        assert "value_max" in stats
