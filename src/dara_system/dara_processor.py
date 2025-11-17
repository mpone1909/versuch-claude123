"""
DaRa Processor Module

Allgemeine Hilfsfunktionen für DaRa-spezifische Datenverarbeitung.
Normalisierung, Label-Handling, Zeitachsen-Operationen.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimeSlice:
    """Repräsentiert einen Zeitpunkt mit Daten von mehreren Probanden."""
    timestamp: int  # Zeilen-Index oder echte Zeitstempel
    data: Dict[str, Any]  # Probanden-ID -> Daten
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DaRaProcessorError(Exception):
    """Fehler in DaRa-Verarbeitung"""
    pass


class DataNormalizer:
    """
    Normalisiert DaRa-Daten in ein einheitliches Format.
    """

    @staticmethod
    def normalize_numeric(value: Any, default: float = 0.0) -> float:
        """
        Normalisiert einen Wert zu Float.

        Args:
            value: Eingabewert
            default: Rückgabewert bei ungültigen Werten

        Returns:
            Float-Wert
        """
        try:
            if value is None or value == '':
                return default
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Konnte Wert nicht normalisieren: {value}, nutze default={default}")
            return default

    @staticmethod
    def normalize_categorical(
        value: Any,
        valid_categories: Optional[List[str]] = None,
        default: str = "unknown"
    ) -> str:
        """
        Normalisiert kategoriale Werte.

        Args:
            value: Eingabewert
            valid_categories: Erlaubte Kategorien (optional)
            default: Default bei ungültigen Werten

        Returns:
            Normalisierter String
        """
        if value is None or value == '':
            return default

        str_value = str(value).strip().lower()

        if valid_categories:
            if str_value not in valid_categories:
                logger.warning(
                    f"Kategorie '{str_value}' nicht in erlaubten Kategorien, "
                    f"nutze default='{default}'"
                )
                return default

        return str_value

    @staticmethod
    def normalize_row(
        row: Dict[str, Any],
        numeric_fields: Optional[List[str]] = None,
        categorical_fields: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Normalisiert eine komplette Datenzeile.

        Args:
            row: Eingabe-Dictionary
            numeric_fields: Liste von Feldern die als Float normalisiert werden
            categorical_fields: Dict {Feldname: [erlaubte Kategorien]}

        Returns:
            Normalisiertes Dictionary
        """
        normalized = {}

        for key, value in row.items():
            if numeric_fields and key in numeric_fields:
                normalized[key] = DataNormalizer.normalize_numeric(value)
            elif categorical_fields and key in categorical_fields:
                normalized[key] = DataNormalizer.normalize_categorical(
                    value,
                    valid_categories=categorical_fields[key]
                )
            else:
                # Behalte original
                normalized[key] = value

        return normalized


class LabelHandler:
    """
    Verwaltet Labels und Klassifikationen für DaRa-Daten.
    """

    def __init__(self, label_mapping: Optional[Dict[str, int]] = None):
        """
        Initialisiert den Label Handler.

        Args:
            label_mapping: Optional, Mapping von Label-Namen zu Integer-IDs
        """
        self.label_mapping = label_mapping or {}
        self.reverse_mapping = {v: k for k, v in self.label_mapping.items()}

    def encode_label(self, label: str) -> int:
        """
        Encodiert ein Label zu einer Integer-ID.

        Args:
            label: Label-String

        Returns:
            Integer-ID

        Raises:
            DaRaProcessorError: Wenn Label nicht im Mapping
        """
        if label not in self.label_mapping:
            # Auto-add neues Label
            new_id = len(self.label_mapping)
            self.label_mapping[label] = new_id
            self.reverse_mapping[new_id] = label
            logger.info(f"Neues Label hinzugefügt: '{label}' -> {new_id}")

        return self.label_mapping[label]

    def decode_label(self, label_id: int) -> str:
        """
        Decodiert eine Integer-ID zurück zu einem Label.

        Args:
            label_id: Label-ID

        Returns:
            Label-String

        Raises:
            DaRaProcessorError: Wenn ID nicht bekannt
        """
        if label_id not in self.reverse_mapping:
            raise DaRaProcessorError(f"Unbekannte Label-ID: {label_id}")

        return self.reverse_mapping[label_id]

    def get_all_labels(self) -> List[str]:
        """
        Gibt alle bekannten Labels zurück.

        Returns:
            Liste von Label-Strings
        """
        return list(self.label_mapping.keys())


class TimeAxisHelper:
    """
    Hilfsfunktionen für zeitliche Operationen.
    """

    @staticmethod
    def create_time_windows(
        total_rows: int,
        window_size: int,
        step_size: Optional[int] = None
    ) -> List[tuple[int, int]]:
        """
        Erstellt Zeitfenster für Window-basierte Analysen.

        Args:
            total_rows: Gesamtanzahl der Zeilen
            window_size: Größe jedes Fensters
            step_size: Schrittgröße zwischen Fenstern (default: window_size)

        Returns:
            Liste von (start_index, end_index) Tupeln
        """
        if step_size is None:
            step_size = window_size

        windows = []
        start = 0

        while start < total_rows:
            end = min(start + window_size, total_rows)
            windows.append((start, end))
            start += step_size

        return windows

    @staticmethod
    def aggregate_time_slice(
        time_slice: TimeSlice,
        aggregation_func: str = "mean"
    ) -> Dict[str, float]:
        """
        Aggregiert Daten innerhalb eines TimeSlice.

        Args:
            time_slice: TimeSlice mit Probanden-Daten
            aggregation_func: "mean", "median", "min", "max", "sum"

        Returns:
            Dictionary mit aggregierten Werten pro Merkmal
        """
        # Sammle alle numerischen Werte pro Feld
        field_values: Dict[str, List[float]] = {}

        for proband_data in time_slice.data.values():
            if not isinstance(proband_data, dict):
                continue

            for field, value in proband_data.items():
                if isinstance(value, (int, float)):
                    if field not in field_values:
                        field_values[field] = []
                    field_values[field].append(float(value))

        # Aggregiere
        import statistics

        aggregated = {}
        for field, values in field_values.items():
            if not values:
                continue

            if aggregation_func == "mean":
                aggregated[field] = statistics.mean(values)
            elif aggregation_func == "median":
                aggregated[field] = statistics.median(values)
            elif aggregation_func == "min":
                aggregated[field] = min(values)
            elif aggregation_func == "max":
                aggregated[field] = max(values)
            elif aggregation_func == "sum":
                aggregated[field] = sum(values)
            else:
                logger.warning(f"Unbekannte Aggregationsfunktion: {aggregation_func}")
                aggregated[field] = statistics.mean(values)

        return aggregated
