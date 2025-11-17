"""Tests für DaRa Processor Module"""

import pytest
from src.dara_system.dara_processor import (
    DataNormalizer,
    LabelHandler,
    TimeAxisHelper,
    TimeSlice,
    DaRaProcessorError
)


class TestDataNormalizer:
    """Tests für DataNormalizer"""

    def test_normalize_numeric(self):
        """Test: Numerische Normalisierung"""
        assert DataNormalizer.normalize_numeric("42") == 42.0
        assert DataNormalizer.normalize_numeric(3.14) == 3.14
        assert DataNormalizer.normalize_numeric(None) == 0.0
        assert DataNormalizer.normalize_numeric("") == 0.0
        assert DataNormalizer.normalize_numeric("invalid", default=99.0) == 99.0

    def test_normalize_categorical(self):
        """Test: Kategoriale Normalisierung"""
        assert DataNormalizer.normalize_categorical("Test") == "test"
        assert DataNormalizer.normalize_categorical("  ABC  ") == "abc"
        assert DataNormalizer.normalize_categorical(None) == "unknown"

        # Mit erlaubten Kategorien
        result = DataNormalizer.normalize_categorical(
            "valid",
            valid_categories=["valid", "invalid"]
        )
        assert result == "valid"

        # Mit ungültiger Kategorie
        result = DataNormalizer.normalize_categorical(
            "xyz",
            valid_categories=["valid", "invalid"],
            default="unknown"
        )
        assert result == "unknown"

    def test_normalize_row(self):
        """Test: Zeilen-Normalisierung"""
        row = {
            "value": "42.5",
            "category": "Active",
            "name": "Test"
        }

        normalized = DataNormalizer.normalize_row(
            row,
            numeric_fields=["value"],
            categorical_fields={"category": ["active", "passive"]}
        )

        assert normalized["value"] == 42.5
        assert normalized["category"] == "active"
        assert normalized["name"] == "Test"  # Unverändert


class TestLabelHandler:
    """Tests für LabelHandler"""

    def test_encode_label(self):
        """Test: Label-Encoding"""
        handler = LabelHandler()

        id1 = handler.encode_label("baseline")
        id2 = handler.encode_label("active")
        id3 = handler.encode_label("baseline")  # Duplikat

        assert id1 == id3  # Gleiches Label = gleiche ID
        assert id1 != id2

    def test_decode_label(self):
        """Test: Label-Decoding"""
        handler = LabelHandler(label_mapping={"baseline": 0, "active": 1})

        assert handler.decode_label(0) == "baseline"
        assert handler.decode_label(1) == "active"

    def test_decode_unknown_label(self):
        """Test: Fehler bei unbekannter ID"""
        handler = LabelHandler()

        with pytest.raises(DaRaProcessorError):
            handler.decode_label(999)

    def test_get_all_labels(self):
        """Test: Alle Labels abrufen"""
        handler = LabelHandler()

        handler.encode_label("label1")
        handler.encode_label("label2")
        handler.encode_label("label3")

        labels = handler.get_all_labels()
        assert len(labels) == 3
        assert "label1" in labels


class TestTimeAxisHelper:
    """Tests für TimeAxisHelper"""

    def test_create_time_windows(self):
        """Test: Zeitfenster erstellen"""
        windows = TimeAxisHelper.create_time_windows(
            total_rows=100,
            window_size=20,
            step_size=20
        )

        assert len(windows) == 5
        assert windows[0] == (0, 20)
        assert windows[-1] == (80, 100)

    def test_create_overlapping_windows(self):
        """Test: Überlappende Fenster"""
        windows = TimeAxisHelper.create_time_windows(
            total_rows=100,
            window_size=30,
            step_size=10
        )

        # Überlappung
        assert windows[0] == (0, 30)
        assert windows[1] == (10, 40)

    def test_aggregate_time_slice(self):
        """Test: TimeSlice-Aggregation"""
        time_slice = TimeSlice(
            timestamp=0,
            data={
                "proband1": {"value": 10.0, "score": 5.0},
                "proband2": {"value": 20.0, "score": 15.0},
            }
        )

        aggregated = TimeAxisHelper.aggregate_time_slice(time_slice, "mean")

        assert aggregated["value"] == 15.0  # Mean von 10 und 20
        assert aggregated["score"] == 10.0  # Mean von 5 und 15

    def test_aggregate_different_functions(self):
        """Test: Verschiedene Aggregationsfunktionen"""
        time_slice = TimeSlice(
            timestamp=0,
            data={
                "p1": {"val": 10.0},
                "p2": {"val": 20.0},
                "p3": {"val": 30.0},
            }
        )

        assert TimeAxisHelper.aggregate_time_slice(time_slice, "min")["val"] == 10.0
        assert TimeAxisHelper.aggregate_time_slice(time_slice, "max")["val"] == 30.0
        assert TimeAxisHelper.aggregate_time_slice(time_slice, "sum")["val"] == 60.0
