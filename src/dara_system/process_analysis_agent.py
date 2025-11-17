"""
Process Analysis Agent Module

Analysiert Prozessphasen, Zustände und Muster in zeitsynchronen DaRa-Daten.
Identifiziert Trends, Anomalien und generiert textuelle Beschreibungen.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .multi_proband_aggregator import AggregatedTimeSlice
from .dara_processor import TimeSlice

logger = logging.getLogger(__name__)


class ProcessPhase(Enum):
    """Definierte Prozessphasen."""
    BASELINE = "baseline"
    ACTIVE = "active"
    TRANSITION = "transition"
    PEAK = "peak"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


@dataclass
class ProcessState:
    """Repräsentiert einen Prozesszustand zu einem Zeitpunkt."""
    timestamp: int
    phase: ProcessPhase
    confidence: float  # 0.0 - 1.0
    features: Dict[str, float]
    description: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessPattern:
    """Erkanntes Muster über einen Zeitraum."""
    start_timestamp: int
    end_timestamp: int
    pattern_type: str
    description: str
    confidence: float
    features: Dict[str, Any]


@dataclass
class AnalysisResult:
    """Ergebnis einer Prozessanalyse."""
    time_range: Tuple[int, int]
    states: List[ProcessState]
    patterns: List[ProcessPattern]
    summary: str
    statistics: Dict[str, Any]


class ProcessAnalysisError(Exception):
    """Fehler bei der Prozessanalyse"""
    pass


class ProcessAnalysisAgent:
    """
    Agent zur Analyse von Prozessphasen und -mustern.

    Aufgaben:
    - Identifikation von Prozessphasen (Baseline, Active, Peak, etc.)
    - Erkennung von Trends und Mustern
    - Anomalie-Detektion
    - Generierung textueller Beschreibungen

    Methoden sind konfigurierbar und erweiterbar.
    """

    def __init__(
        self,
        baseline_threshold: float = 0.3,
        peak_threshold: float = 0.8,
        transition_window: int = 5,
        min_pattern_length: int = 3
    ):
        """
        Initialisiert den Process Analysis Agent.

        Args:
            baseline_threshold: Schwellwert für Baseline-Erkennung (relativ zu Max)
            peak_threshold: Schwellwert für Peak-Erkennung
            transition_window: Fenstergröße für Transitions-Erkennung
            min_pattern_length: Minimale Länge für Muster-Erkennung
        """
        self.baseline_threshold = baseline_threshold
        self.peak_threshold = peak_threshold
        self.transition_window = transition_window
        self.min_pattern_length = min_pattern_length

        logger.info(
            f"ProcessAnalysisAgent initialisiert "
            f"(baseline_threshold={baseline_threshold}, peak_threshold={peak_threshold})"
        )

    def analyze_aggregated_slices(
        self,
        aggregated_slices: List[AggregatedTimeSlice],
        primary_field: str = "value"
    ) -> AnalysisResult:
        """
        Analysiert eine Sequenz von aggregierten TimeSlices.

        Args:
            aggregated_slices: Liste von AggregatedTimeSlices
            primary_field: Primäres Feld für Phasen-Analyse

        Returns:
            AnalysisResult mit States, Patterns und Summary

        Raises:
            ProcessAnalysisError: Bei Analyse-Fehlern
        """
        if not aggregated_slices:
            raise ProcessAnalysisError("Keine Daten zur Analyse vorhanden")

        logger.info(f"Analysiere {len(aggregated_slices)} aggregierte TimeSlices")

        # 1. Extrahiere primäre Werte
        values, timestamps = self._extract_values(aggregated_slices, primary_field)

        if not values:
            raise ProcessAnalysisError(f"Keine Werte für Feld '{primary_field}' gefunden")

        # 2. Normalisiere Werte für Phasen-Erkennung
        normalized_values = self._normalize_values(values)

        # 3. Identifiziere Phasen
        states = self._identify_phases(
            timestamps,
            normalized_values,
            aggregated_slices,
            primary_field
        )

        # 4. Erkenne Muster
        patterns = self._detect_patterns(states, values)

        # 5. Generiere Summary
        summary = self._generate_summary(states, patterns, values)

        # 6. Berechne Statistiken
        statistics = self._calculate_analysis_statistics(states, patterns, values)

        time_range = (timestamps[0], timestamps[-1])

        logger.info(
            f"Analyse abgeschlossen: {len(states)} States, "
            f"{len(patterns)} Patterns erkannt"
        )

        return AnalysisResult(
            time_range=time_range,
            states=states,
            patterns=patterns,
            summary=summary,
            statistics=statistics
        )

    def _extract_values(
        self,
        aggregated_slices: List[AggregatedTimeSlice],
        field: str
    ) -> Tuple[List[float], List[int]]:
        """
        Extrahiert Werte eines Feldes aus aggregierten Slices.

        Args:
            aggregated_slices: AggregatedTimeSlices
            field: Feldname

        Returns:
            (values, timestamps) Tupel
        """
        values = []
        timestamps = []

        for agg_slice in aggregated_slices:
            if field in agg_slice.statistics:
                # Nutze Mean als Default
                if "mean" in agg_slice.statistics[field]:
                    values.append(agg_slice.statistics[field]["mean"])
                    timestamps.append(agg_slice.timestamp)

        return values, timestamps

    def _normalize_values(self, values: List[float]) -> List[float]:
        """
        Normalisiert Werte auf Bereich [0, 1].

        Args:
            values: Rohe Werte

        Returns:
            Normalisierte Werte
        """
        if not values:
            return []

        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            # Alle Werte gleich
            return [0.5] * len(values)

        return [(v - min_val) / (max_val - min_val) for v in values]

    def _identify_phases(
        self,
        timestamps: List[int],
        normalized_values: List[float],
        aggregated_slices: List[AggregatedTimeSlice],
        primary_field: str
    ) -> List[ProcessState]:
        """
        Identifiziert Prozessphasen basierend auf Werten.

        Args:
            timestamps: Zeitpunkte
            normalized_values: Normalisierte Werte
            aggregated_slices: Original-Slices für Features
            primary_field: Primäres Feld

        Returns:
            Liste von ProcessStates
        """
        states = []

        for i, (timestamp, norm_value) in enumerate(zip(timestamps, normalized_values)):
            # Bestimme Phase basierend auf Schwellwerten
            phase, confidence = self._classify_phase(
                norm_value,
                normalized_values,
                i
            )

            # Extrahiere Features aus aggregiertem Slice
            features = {}
            if i < len(aggregated_slices):
                agg_slice = aggregated_slices[i]
                if primary_field in agg_slice.statistics:
                    features = agg_slice.statistics[primary_field].copy()

            # Generiere Beschreibung
            description = self._describe_phase(phase, norm_value, features)

            state = ProcessState(
                timestamp=timestamp,
                phase=phase,
                confidence=confidence,
                features=features,
                description=description,
                metadata={"normalized_value": norm_value}
            )

            states.append(state)

        return states

    def _classify_phase(
        self,
        norm_value: float,
        all_values: List[float],
        index: int
    ) -> Tuple[ProcessPhase, float]:
        """
        Klassifiziert einen Wert zu einer Phase.

        Args:
            norm_value: Normalisierter Wert (0-1)
            all_values: Alle normalisierten Werte (für Kontext)
            index: Index des aktuellen Werts

        Returns:
            (Phase, Confidence) Tupel
        """
        confidence = 0.8  # Default

        # Peak: Wert über Peak-Threshold
        if norm_value >= self.peak_threshold:
            return ProcessPhase.PEAK, confidence

        # Baseline: Wert unter Baseline-Threshold
        if norm_value <= self.baseline_threshold:
            return ProcessPhase.BASELINE, confidence

        # Transition: Starke Änderung zum vorherigen Wert
        if index > 0:
            prev_value = all_values[index - 1]
            change = abs(norm_value - prev_value)

            if change > 0.2:  # Signifikante Änderung
                return ProcessPhase.TRANSITION, confidence * 0.9

        # Active: Mittlerer Bereich
        return ProcessPhase.ACTIVE, confidence * 0.7

    def _describe_phase(
        self,
        phase: ProcessPhase,
        norm_value: float,
        features: Dict[str, float]
    ) -> str:
        """
        Generiert textuelle Beschreibung einer Phase.

        Args:
            phase: Prozessphase
            norm_value: Normalisierter Wert
            features: Feature-Dictionary

        Returns:
            Beschreibungstext
        """
        mean = features.get("mean", 0.0)
        stdev = features.get("stdev", 0.0)

        descriptions = {
            ProcessPhase.BASELINE: f"Baseline-Phase (Wert: {mean:.2f}, gering aktiv)",
            ProcessPhase.ACTIVE: f"Aktive Phase (Wert: {mean:.2f}, moderate Aktivität)",
            ProcessPhase.TRANSITION: f"Übergangsphase (Wert: {mean:.2f}, Änderung erkannt)",
            ProcessPhase.PEAK: f"Peak-Phase (Wert: {mean:.2f}, maximale Aktivität)",
            ProcessPhase.RECOVERY: f"Erholungsphase (Wert: {mean:.2f}, abnehmend)",
            ProcessPhase.UNKNOWN: f"Unbekannte Phase (Wert: {mean:.2f})",
        }

        base_desc = descriptions.get(phase, f"Phase: {phase.value}")

        if stdev > 0:
            base_desc += f", Variabilität: {stdev:.2f}"

        return base_desc

    def _detect_patterns(
        self,
        states: List[ProcessState],
        values: List[float]
    ) -> List[ProcessPattern]:
        """
        Erkennt Muster in der Sequenz von States.

        Args:
            states: Liste von ProcessStates
            values: Rohe Werte

        Returns:
            Liste von ProcessPatterns
        """
        patterns = []

        # 1. Erkenne aufsteigende Trends
        ascending = self._detect_trend(states, values, ascending=True)
        patterns.extend(ascending)

        # 2. Erkenne absteigende Trends
        descending = self._detect_trend(states, values, ascending=False)
        patterns.extend(descending)

        # 3. Erkenne Plateaus
        plateaus = self._detect_plateaus(states, values)
        patterns.extend(plateaus)

        return patterns

    def _detect_trend(
        self,
        states: List[ProcessState],
        values: List[float],
        ascending: bool
    ) -> List[ProcessPattern]:
        """
        Erkennt aufsteigende oder absteigende Trends.

        Args:
            states: ProcessStates
            values: Werte
            ascending: True für aufsteigend, False für absteigend

        Returns:
            Liste von Trend-Patterns
        """
        patterns = []
        trend_start = None
        trend_indices = []

        for i in range(1, len(values)):
            is_trending = (values[i] > values[i - 1]) if ascending else (values[i] < values[i - 1])

            if is_trending:
                if trend_start is None:
                    trend_start = i - 1
                trend_indices.append(i)
            else:
                if trend_start is not None and len(trend_indices) >= self.min_pattern_length:
                    # Trend beendet, speichere Pattern
                    pattern = ProcessPattern(
                        start_timestamp=states[trend_start].timestamp,
                        end_timestamp=states[trend_indices[-1]].timestamp,
                        pattern_type="ascending_trend" if ascending else "descending_trend",
                        description=f"{'Aufsteigender' if ascending else 'Absteigender'} Trend "
                                    f"über {len(trend_indices)} Zeitpunkte",
                        confidence=0.8,
                        features={
                            "start_value": values[trend_start],
                            "end_value": values[trend_indices[-1]],
                            "change": values[trend_indices[-1]] - values[trend_start],
                        }
                    )
                    patterns.append(pattern)

                trend_start = None
                trend_indices = []

        return patterns

    def _detect_plateaus(
        self,
        states: List[ProcessState],
        values: List[float]
    ) -> List[ProcessPattern]:
        """
        Erkennt Plateaus (konstante Werte über Zeit).

        Args:
            states: ProcessStates
            values: Werte

        Returns:
            Liste von Plateau-Patterns
        """
        patterns = []
        plateau_start = None
        plateau_indices = []
        threshold = 0.05  # 5% Variation erlaubt

        for i in range(1, len(values)):
            if abs(values[i] - values[i - 1]) / (values[i - 1] + 1e-10) < threshold:
                if plateau_start is None:
                    plateau_start = i - 1
                plateau_indices.append(i)
            else:
                if plateau_start is not None and len(plateau_indices) >= self.min_pattern_length:
                    pattern = ProcessPattern(
                        start_timestamp=states[plateau_start].timestamp,
                        end_timestamp=states[plateau_indices[-1]].timestamp,
                        pattern_type="plateau",
                        description=f"Plateau über {len(plateau_indices)} Zeitpunkte",
                        confidence=0.85,
                        features={
                            "plateau_value": sum(values[plateau_start:plateau_indices[-1] + 1])
                                             / (len(plateau_indices) + 1),
                        }
                    )
                    patterns.append(pattern)

                plateau_start = None
                plateau_indices = []

        return patterns

    def _generate_summary(
        self,
        states: List[ProcessState],
        patterns: List[ProcessPattern],
        values: List[float]
    ) -> str:
        """
        Generiert textuelle Zusammenfassung der Analyse.

        Args:
            states: ProcessStates
            patterns: ProcessPatterns
            values: Werte

        Returns:
            Summary-Text
        """
        # Zähle Phasen
        phase_counts = {}
        for state in states:
            phase_counts[state.phase] = phase_counts.get(state.phase, 0) + 1

        # Finde dominante Phase
        dominant_phase = max(phase_counts, key=phase_counts.get) if phase_counts else ProcessPhase.UNKNOWN

        summary_lines = [
            f"Prozessanalyse über {len(states)} Zeitpunkte:",
            f"- Dominante Phase: {dominant_phase.value} ({phase_counts[dominant_phase]} Zeitpunkte)",
            f"- Erkannte Muster: {len(patterns)}",
            f"- Wertebereich: {min(values):.2f} - {max(values):.2f}",
        ]

        # Füge Muster-Info hinzu
        if patterns:
            summary_lines.append(f"- Erkannte Trend-/Mustertypen:")
            pattern_types = {}
            for pattern in patterns:
                pattern_types[pattern.pattern_type] = pattern_types.get(pattern.pattern_type, 0) + 1

            for ptype, count in pattern_types.items():
                summary_lines.append(f"  * {ptype}: {count}x")

        return "\n".join(summary_lines)

    def _calculate_analysis_statistics(
        self,
        states: List[ProcessState],
        patterns: List[ProcessPattern],
        values: List[float]
    ) -> Dict[str, Any]:
        """
        Berechnet Statistiken zur Analyse.

        Args:
            states: ProcessStates
            patterns: ProcessPatterns
            values: Werte

        Returns:
            Statistik-Dictionary
        """
        import statistics as stats

        return {
            "total_time_points": len(states),
            "total_patterns": len(patterns),
            "value_mean": stats.mean(values),
            "value_stdev": stats.stdev(values) if len(values) > 1 else 0.0,
            "value_min": min(values),
            "value_max": max(values),
            "phases_distribution": {
                phase.value: sum(1 for s in states if s.phase == phase)
                for phase in ProcessPhase
            }
        }
