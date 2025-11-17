"""
Synthetic Data Generator Module

Erzeugt synthetische DARA-ähnliche CSV-Dateien für Tests und Experimente.
Simuliert zeitsynchrone Multi-Proband-Daten mit realistischen Werten und Mustern.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import csv
import random
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class SyntheticDataConfig:
    """Konfiguration für synthetische Datengenerierung."""
    num_probands: int = 3
    num_rows: int = 1000
    primary_field: str = "value"
    fields: List[str] = None
    baseline_mean: float = 50.0
    baseline_std: float = 5.0
    peak_probability: float = 0.1
    peak_multiplier: float = 2.0
    anomaly_probability: float = 0.05

    def __post_init__(self):
        if self.fields is None:
            self.fields = ["timestamp", "value", "status", "score", "label"]


class SyntheticDataGenerator:
    """
    Generiert synthetische DARA-ähnliche Daten.

    Features:
    - Multiple Probanden mit leicht unterschiedlichen Charakteristiken
    - Realistische Muster (Baseline, Peaks, Trends, Anomalien)
    - Zeitsynchrone Struktur
    - Konfigurierbare Parameter
    """

    def __init__(self, config: Optional[SyntheticDataConfig] = None, seed: Optional[int] = None):
        """
        Initialisiert den Generator.

        Args:
            config: Konfiguration für die Datengenerierung
            seed: Random Seed für Reproduzierbarkeit
        """
        self.config = config or SyntheticDataConfig()
        self.seed = seed
        if seed is not None:
            random.seed(seed)

        logger.info(f"SyntheticDataGenerator initialisiert: {self.config.num_probands} Probanden, "
                   f"{self.config.num_rows} Zeilen")

    def generate_multi_proband_csvs(
        self,
        output_dir: Path,
        proband_prefix: str = "proband",
        file_extension: str = ".csv"
    ) -> List[Path]:
        """
        Generiert CSV-Dateien für mehrere Probanden.

        Args:
            output_dir: Ausgabeverzeichnis
            proband_prefix: Präfix für Dateinamen
            file_extension: Dateiendung

        Returns:
            Liste der erzeugten Dateipfade
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        for i in range(self.config.num_probands):
            proband_id = f"{proband_prefix}_{i+1}"
            file_path = output_dir / f"{proband_id}{file_extension}"

            # Generiere Daten für diesen Probanden
            data = self._generate_proband_data(proband_id)

            # Schreibe CSV
            self._write_csv(file_path, data)

            generated_files.append(file_path)
            logger.info(f"Erzeugt: {file_path} ({len(data)} Zeilen)")

        return generated_files

    def _generate_proband_data(self, proband_id: str) -> List[Dict[str, Any]]:
        """
        Generiert Daten für einen einzelnen Probanden.

        Args:
            proband_id: ID des Probanden

        Returns:
            Liste von Zeilen-Dictionaries
        """
        data = []

        # Proband-spezifische Variation (jeder Proband ist leicht unterschiedlich)
        proband_offset = random.uniform(-10, 10)
        proband_variance = random.uniform(0.8, 1.2)

        for row_idx in range(self.config.num_rows):
            row = self._generate_row(
                timestamp=row_idx,
                proband_offset=proband_offset,
                proband_variance=proband_variance
            )
            data.append(row)

        return data

    def _generate_row(
        self,
        timestamp: int,
        proband_offset: float,
        proband_variance: float
    ) -> Dict[str, Any]:
        """
        Generiert eine einzelne Datenzeile.

        Args:
            timestamp: Zeitstempel
            proband_offset: Proband-spezifischer Offset
            proband_variance: Proband-spezifische Varianz

        Returns:
            Dictionary mit Feldwerten
        """
        # Baseline-Wert mit proband-spezifischer Variation
        base_value = self.config.baseline_mean + proband_offset
        noise = random.gauss(0, self.config.baseline_std) * proband_variance
        value = base_value + noise

        # Trend über Zeit (langsame Drift)
        trend = math.sin(timestamp / 100.0) * 5.0
        value += trend

        # Gelegentliche Peaks
        if random.random() < self.config.peak_probability:
            value *= self.config.peak_multiplier

        # Anomalien
        is_anomaly = random.random() < self.config.anomaly_probability
        if is_anomaly:
            value += random.choice([-30, 30])  # Abrupte Sprünge

        # Status basiert auf Wert
        if value < self.config.baseline_mean * 0.5:
            status = "low"
        elif value > self.config.baseline_mean * 1.5:
            status = "high"
        else:
            status = "normal"

        # Score (normalisiert)
        score = max(0.0, min(10.0, value / 10.0))

        # Label (kategorisiert)
        if value < 40:
            label = "rest"
        elif value < 60:
            label = "baseline"
        elif value < 80:
            label = "active"
        else:
            label = "peak"

        return {
            "timestamp": timestamp,
            "value": round(value, 2),
            "status": status,
            "score": round(score, 2),
            "label": label
        }

    def _write_csv(self, file_path: Path, data: List[Dict[str, Any]]):
        """
        Schreibt Daten in eine CSV-Datei.

        Args:
            file_path: Pfad zur Ausgabedatei
            data: Liste von Zeilen-Dictionaries
        """
        if not data:
            logger.warning(f"Keine Daten zum Schreiben für {file_path}")
            return

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = self.config.fields
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)

    def generate_scenario_variants(
        self,
        output_dir: Path,
        num_scenarios: int = 3
    ) -> Dict[str, List[Path]]:
        """
        Generiert mehrere Szenarien mit unterschiedlichen Charakteristiken.

        Args:
            output_dir: Ausgabeverzeichnis
            num_scenarios: Anzahl der Szenarien

        Returns:
            Dictionary: scenario_name -> Liste von CSV-Pfaden
        """
        scenarios = {}

        # Szenario 1: Normale Baseline
        config1 = SyntheticDataConfig(
            num_probands=self.config.num_probands,
            num_rows=self.config.num_rows,
            baseline_mean=50.0,
            peak_probability=0.05,
            anomaly_probability=0.02
        )
        gen1 = SyntheticDataGenerator(config1, seed=self.seed)
        scenario_dir1 = Path(output_dir) / "scenario_baseline"
        files1 = gen1.generate_multi_proband_csvs(scenario_dir1, proband_prefix="baseline")
        scenarios["baseline"] = files1

        # Szenario 2: Hohe Aktivität
        config2 = SyntheticDataConfig(
            num_probands=self.config.num_probands,
            num_rows=self.config.num_rows,
            baseline_mean=70.0,
            peak_probability=0.15,
            anomaly_probability=0.05
        )
        gen2 = SyntheticDataGenerator(config2, seed=self.seed + 1 if self.seed else None)
        scenario_dir2 = Path(output_dir) / "scenario_high_activity"
        files2 = gen2.generate_multi_proband_csvs(scenario_dir2, proband_prefix="active")
        scenarios["high_activity"] = files2

        # Szenario 3: Niedriger Aktivität
        config3 = SyntheticDataConfig(
            num_probands=self.config.num_probands,
            num_rows=self.config.num_rows,
            baseline_mean=30.0,
            peak_probability=0.02,
            anomaly_probability=0.01
        )
        gen3 = SyntheticDataGenerator(config3, seed=self.seed + 2 if self.seed else None)
        scenario_dir3 = Path(output_dir) / "scenario_low_activity"
        files3 = gen3.generate_multi_proband_csvs(scenario_dir3, proband_prefix="lowact")
        scenarios["low_activity"] = files3

        logger.info(f"Generiert: {len(scenarios)} Szenarien in {output_dir}")
        return scenarios


def generate_example_dataset(
    output_dir: str = "data/synthetic",
    num_probands: int = 3,
    num_rows: int = 1000,
    seed: Optional[int] = 42
) -> List[Path]:
    """
    Convenience-Funktion zum schnellen Erzeugen eines Beispiel-Datasets.

    Args:
        output_dir: Ausgabeverzeichnis
        num_probands: Anzahl Probanden
        num_rows: Anzahl Zeilen pro Proband
        seed: Random Seed

    Returns:
        Liste der erzeugten CSV-Dateien
    """
    config = SyntheticDataConfig(
        num_probands=num_probands,
        num_rows=num_rows
    )
    generator = SyntheticDataGenerator(config, seed=seed)
    return generator.generate_multi_proband_csvs(Path(output_dir))


if __name__ == "__main__":
    # Beispielaufruf
    logging.basicConfig(level=logging.INFO)

    print("Generiere synthetische DARA-Daten...")

    # Einfaches Beispiel
    files = generate_example_dataset(
        output_dir="data/synthetic_example",
        num_probands=3,
        num_rows=500,
        seed=42
    )

    print(f"\nErzeugte Dateien:")
    for f in files:
        print(f"  - {f}")

    # Mehrere Szenarien
    print("\nGeneriere Szenarien...")
    generator = SyntheticDataGenerator(seed=42)
    scenarios = generator.generate_scenario_variants(
        output_dir=Path("data/synthetic_scenarios"),
        num_scenarios=3
    )

    print(f"\nErzeugte Szenarien:")
    for scenario_name, scenario_files in scenarios.items():
        print(f"  {scenario_name}:")
        for f in scenario_files:
            print(f"    - {f}")
