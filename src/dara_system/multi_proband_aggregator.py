"""
Multi-Proband Aggregator Module

Aggregiert Daten von mehreren Probanden zu jedem Zeitpunkt.
Berechnet Statistiken, erkennt Muster und bereitet Daten für Analyse vor.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging
import statistics

from .dara_processor import TimeSlice

logger = logging.getLogger(__name__)


@dataclass
class AggregatedTimeSlice:
    """Aggregierte Daten für einen Zeitpunkt über alle Probanden."""
    timestamp: int
    proband_count: int
    statistics: Dict[str, Dict[str, float]]  # {field: {mean, std, min, max, ...}}
    raw_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AggregationError(Exception):
    """Fehler bei der Aggregation"""
    pass


class MultiProbandAggregator:
    """
    Aggregiert Daten von mehreren Probanden.

    Funktionen:
    - Statistische Aggregation (Mean, Median, Std, etc.)
    - Zeitfenster-basierte Aggregation
    - Flexible Aggregationsfunktionen
    - Behandlung fehlender Daten
    """

    def __init__(
        self,
        numeric_fields: Optional[List[str]] = None,
        skip_missing: bool = True,
        min_valid_probands: int = 1
    ):
        """
        Initialisiert den Aggregator.

        Args:
            numeric_fields: Liste von Feldern die numerisch aggregiert werden sollen
                           (None = automatische Erkennung)
            skip_missing: Überspringe fehlende/None-Werte bei Aggregation
            min_valid_probands: Mindestanzahl gültiger Probanden für Aggregation
        """
        self.numeric_fields = numeric_fields
        self.skip_missing = skip_missing
        self.min_valid_probands = min_valid_probands

        logger.info(
            f"MultiProbandAggregator initialisiert "
            f"(min_valid={min_valid_probands}, skip_missing={skip_missing})"
        )

    def aggregate_time_slice(
        self,
        time_slice: TimeSlice,
        include_raw: bool = False
    ) -> AggregatedTimeSlice:
        """
        Aggregiert einen einzelnen TimeSlice.

        Args:
            time_slice: TimeSlice mit Probanden-Daten
            include_raw: Wenn True, werden Rohdaten im Ergebnis mitgeliefert

        Returns:
            AggregatedTimeSlice mit Statistiken

        Raises:
            AggregationError: Bei zu wenigen gültigen Probanden
        """
        # Sammle Daten pro Feld
        field_data: Dict[str, List[float]] = {}
        valid_proband_count = 0

        for proband_id, proband_data in time_slice.data.items():
            if proband_data is None:
                continue

            valid_proband_count += 1

            if not isinstance(proband_data, dict):
                logger.warning(f"Proband {proband_id} hat keine Dict-Daten, überspringe")
                continue

            for field, value in proband_data.items():
                # Prüfe ob Feld aggregiert werden soll
                if self.numeric_fields and field not in self.numeric_fields:
                    continue

                # Versuche numerische Konversion
                numeric_value = self._to_numeric(value)
                if numeric_value is not None:
                    if field not in field_data:
                        field_data[field] = []
                    field_data[field].append(numeric_value)

        # Prüfe Mindestanzahl
        if valid_proband_count < self.min_valid_probands:
            raise AggregationError(
                f"Zu wenige gültige Probanden ({valid_proband_count}) "
                f"für Zeitpunkt {time_slice.timestamp}"
            )

        # Berechne Statistiken
        statistics_dict = {}
        for field, values in field_data.items():
            if not values:
                continue

            statistics_dict[field] = self._calculate_statistics(values)

        return AggregatedTimeSlice(
            timestamp=time_slice.timestamp,
            proband_count=valid_proband_count,
            statistics=statistics_dict,
            raw_data=time_slice.data if include_raw else None,
            metadata={
                "aggregation_method": "standard",
                "total_probands": len(time_slice.data),
                "valid_probands": valid_proband_count,
            }
        )

    def aggregate_time_slices(
        self,
        time_slices: List[TimeSlice],
        include_raw: bool = False
    ) -> List[AggregatedTimeSlice]:
        """
        Aggregiert mehrere TimeSlices.

        Args:
            time_slices: Liste von TimeSlices
            include_raw: Rohdaten einbeziehen

        Returns:
            Liste von AggregatedTimeSlices
        """
        logger.info(f"Aggregiere {len(time_slices)} TimeSlices")

        aggregated = []
        for time_slice in time_slices:
            try:
                agg = self.aggregate_time_slice(time_slice, include_raw)
                aggregated.append(agg)
            except AggregationError as e:
                if not self.skip_missing:
                    raise
                logger.warning(f"Überspringe Zeitpunkt {time_slice.timestamp}: {e}")

        logger.info(f"Erfolgreich {len(aggregated)} TimeSlices aggregiert")
        return aggregated

    def aggregate_time_window(
        self,
        time_slices: List[TimeSlice],
        window_aggregation: str = "mean"
    ) -> Dict[str, float]:
        """
        Aggregiert über ein Zeitfenster (mehrere TimeSlices).

        Args:
            time_slices: Liste von TimeSlices im Fenster
            window_aggregation: "mean", "median", "sum", "min", "max"

        Returns:
            Dictionary mit aggregierten Werten pro Feld
        """
        # Sammle alle Werte über alle TimeSlices
        all_field_values: Dict[str, List[float]] = {}

        for time_slice in time_slices:
            for proband_data in time_slice.data.values():
                if proband_data is None or not isinstance(proband_data, dict):
                    continue

                for field, value in proband_data.items():
                    numeric_value = self._to_numeric(value)
                    if numeric_value is not None:
                        if field not in all_field_values:
                            all_field_values[field] = []
                        all_field_values[field].append(numeric_value)

        # Aggregiere
        result = {}
        for field, values in all_field_values.items():
            if not values:
                continue

            if window_aggregation == "mean":
                result[field] = statistics.mean(values)
            elif window_aggregation == "median":
                result[field] = statistics.median(values)
            elif window_aggregation == "sum":
                result[field] = sum(values)
            elif window_aggregation == "min":
                result[field] = min(values)
            elif window_aggregation == "max":
                result[field] = max(values)
            else:
                logger.warning(f"Unbekannte Aggregation: {window_aggregation}, nutze mean")
                result[field] = statistics.mean(values)

        return result

    def _to_numeric(self, value: Any) -> Optional[float]:
        """
        Konvertiert einen Wert zu float.

        Args:
            value: Eingabewert

        Returns:
            Float oder None
        """
        if value is None or value == '':
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """
        Berechnet Standardstatistiken für eine Liste von Werten.

        Args:
            values: Liste numerischer Werte

        Returns:
            Dictionary mit Statistiken
        """
        if not values:
            return {}

        stats = {
            "count": len(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
        }

        # Median und Stdev nur wenn genug Werte
        if len(values) >= 2:
            stats["median"] = statistics.median(values)
            stats["stdev"] = statistics.stdev(values)
            stats["variance"] = statistics.variance(values)

        return stats

    def get_field_summary(
        self,
        aggregated_slices: List[AggregatedTimeSlice]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Erstellt eine Zusammenfassung aller Felder über alle Zeitpunkte.

        Args:
            aggregated_slices: Liste von AggregatedTimeSlices

        Returns:
            Dictionary {field: {overall_stats}}
        """
        field_means: Dict[str, List[float]] = {}

        for agg_slice in aggregated_slices:
            for field, stats in agg_slice.statistics.items():
                if "mean" in stats:
                    if field not in field_means:
                        field_means[field] = []
                    field_means[field].append(stats["mean"])

        summary = {}
        for field, means in field_means.items():
            summary[field] = {
                "time_points": len(means),
                "overall_mean": statistics.mean(means),
                "overall_min": min(means),
                "overall_max": max(means),
            }

            if len(means) >= 2:
                summary[field]["overall_stdev"] = statistics.stdev(means)

        return summary


class CustomAggregator:
    """
    Erweiterbarer Aggregator mit benutzerdefinierten Funktionen.
    """

    def __init__(self):
        """Initialisiert Custom Aggregator."""
        self.aggregation_functions: Dict[str, Callable] = {}

    def register_function(
        self,
        name: str,
        func: Callable[[List[float]], float]
    ):
        """
        Registriert eine benutzerdefinierte Aggregationsfunktion.

        Args:
            name: Name der Funktion
            func: Callable, nimmt Liste von Floats, gibt Float zurück
        """
        self.aggregation_functions[name] = func
        logger.info(f"Registriert: Aggregationsfunktion '{name}'")

    def apply_custom_aggregation(
        self,
        time_slice: TimeSlice,
        field: str,
        function_name: str
    ) -> Optional[float]:
        """
        Wendet eine benutzerdefinierte Aggregation an.

        Args:
            time_slice: TimeSlice
            field: Zu aggregierendes Feld
            function_name: Name der registrierten Funktion

        Returns:
            Aggregiertes Ergebnis oder None
        """
        if function_name not in self.aggregation_functions:
            raise AggregationError(f"Funktion '{function_name}' nicht registriert")

        # Sammle Werte
        values = []
        for proband_data in time_slice.data.values():
            if proband_data and isinstance(proband_data, dict):
                if field in proband_data:
                    try:
                        values.append(float(proband_data[field]))
                    except (ValueError, TypeError):
                        pass

        if not values:
            return None

        func = self.aggregation_functions[function_name]
        return func(values)
