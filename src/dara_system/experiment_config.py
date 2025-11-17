"""
Experiment-Konfiguration für das DaRa-System.

Definiert Strukturen für:
- Experiment-Konfigurationen (Probanden, Szenarien, Parameter)
- Laden und Validieren von Experiment-Configs
- Mapping zu Orchestrator-Parametern
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ExperimentConfig:
    """
    Konfiguration für ein einzelnes Experiment.

    Ein Experiment definiert:
    - Welche Probanden/Dateien verwendet werden
    - Welche Zeitbereiche/Zeilen analysiert werden
    - Welche Analyse-Parameter gelten
    - Welche Reports erstellt werden sollen
    """

    # Experiment-Metadaten
    name: str
    description: str = ""
    author: str = "DaRa Research Team"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Daten-Auswahl
    csv_file_paths: List[str] = field(default_factory=list)
    proband_ids: List[str] = field(default_factory=list)

    # Zeitbereich (Zeilen-Indizes)
    start_row: int = 0
    end_row: Optional[int] = None  # None = bis zum Ende

    # Analyse-Parameter
    primary_field: str = "value"
    additional_fields: List[str] = field(default_factory=lambda: ["score"])
    baseline_threshold: float = 0.3
    peak_threshold: float = 0.8
    anomaly_std_multiplier: float = 2.5
    min_valid_probands: int = 2

    # Reporting-Optionen
    create_notion_report: bool = False
    create_gdrive_doc: bool = False
    create_gdrive_sheet: bool = False

    # Evaluations-Optionen
    run_evaluation: bool = True
    evaluation_metrics: List[str] = field(
        default_factory=lambda: ["basic_stats", "pattern_counts", "anomaly_counts"]
    )

    # Output-Konfiguration
    output_dir: Optional[str] = None  # None = results/<experiment_name>
    save_intermediate_results: bool = False

    def get_output_dir(self, base_results_dir: Path) -> Path:
        """
        Bestimmt das Output-Verzeichnis für dieses Experiment.

        Args:
            base_results_dir: Basis-Verzeichnis für alle Ergebnisse

        Returns:
            Pfad zum Experiment-Output-Verzeichnis
        """
        if self.output_dir:
            return Path(self.output_dir)
        return base_results_dir / self.name

    def validate(self) -> List[str]:
        """
        Validiert die Experiment-Konfiguration.

        Returns:
            Liste von Fehlermeldungen (leer wenn valide)
        """
        errors = []

        if not self.name:
            errors.append("Experiment-Name ist erforderlich")

        if not self.csv_file_paths:
            errors.append("Mindestens eine CSV-Datei erforderlich")

        if not self.proband_ids:
            errors.append("Mindestens eine Proband-ID erforderlich")

        if len(self.csv_file_paths) != len(self.proband_ids):
            errors.append(
                f"Anzahl CSV-Dateien ({len(self.csv_file_paths)}) muss "
                f"Anzahl Proband-IDs ({len(self.proband_ids)}) entsprechen"
            )

        if self.start_row < 0:
            errors.append("start_row muss >= 0 sein")

        if self.end_row is not None and self.end_row <= self.start_row:
            errors.append("end_row muss > start_row sein")

        if self.baseline_threshold < 0 or self.baseline_threshold > 1:
            errors.append("baseline_threshold muss zwischen 0 und 1 liegen")

        if self.peak_threshold < 0 or self.peak_threshold > 1:
            errors.append("peak_threshold muss zwischen 0 und 1 liegen")

        if self.min_valid_probands < 1:
            errors.append("min_valid_probands muss >= 1 sein")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert die Config zu einem Dictionary."""
        return asdict(self)

    def to_json(self, filepath: Path):
        """Speichert die Config als JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def to_yaml(self, filepath: Path):
        """Speichert die Config als YAML."""
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentConfig":
        """Erstellt eine Config aus einem Dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, filepath: Path) -> "ExperimentConfig":
        """Lädt eine Config aus einer JSON-Datei."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_yaml(cls, filepath: Path) -> "ExperimentConfig":
        """Lädt eine Config aus einer YAML-Datei."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


def load_experiment_config(filepath: Path) -> ExperimentConfig:
    """
    Lädt eine Experiment-Konfiguration aus einer Datei.

    Unterstützt YAML (.yaml, .yml) und JSON (.json) Formate.

    Args:
        filepath: Pfad zur Konfigurationsdatei

    Returns:
        ExperimentConfig-Instanz

    Raises:
        ValueError: Wenn das Dateiformat nicht unterstützt wird
        FileNotFoundError: Wenn die Datei nicht existiert
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {filepath}")

    suffix = filepath.suffix.lower()

    if suffix in [".yaml", ".yml"]:
        return ExperimentConfig.from_yaml(filepath)
    elif suffix == ".json":
        return ExperimentConfig.from_json(filepath)
    else:
        raise ValueError(f"Nicht unterstütztes Dateiformat: {suffix}")


def list_experiment_configs(experiments_dir: Path) -> List[Path]:
    """
    Listet alle Experiment-Konfigurationsdateien in einem Verzeichnis auf.

    Args:
        experiments_dir: Verzeichnis mit Experiment-Configs

    Returns:
        Liste von Pfaden zu Config-Dateien
    """
    experiments_dir = Path(experiments_dir)

    if not experiments_dir.exists():
        return []

    config_files = []
    for pattern in ["*.yaml", "*.yml", "*.json"]:
        config_files.extend(experiments_dir.glob(pattern))

    return sorted(config_files)


def create_example_config(output_path: Path):
    """
    Erstellt eine Beispiel-Experiment-Konfiguration.

    Args:
        output_path: Pfad für die Ausgabedatei
    """
    example = ExperimentConfig(
        name="example_experiment",
        description="Beispiel-Experiment mit 3 Probanden",
        csv_file_paths=[
            "data/proband_1.csv",
            "data/proband_2.csv",
            "data/proband_3.csv",
        ],
        proband_ids=["P1", "P2", "P3"],
        start_row=0,
        end_row=2000,
        primary_field="value",
        additional_fields=["score"],
        baseline_threshold=0.3,
        peak_threshold=0.8,
        anomaly_std_multiplier=2.5,
        min_valid_probands=2,
        create_notion_report=False,
        create_gdrive_doc=False,
        create_gdrive_sheet=False,
        run_evaluation=True,
        evaluation_metrics=["basic_stats", "pattern_counts", "anomaly_counts"],
    )

    output_path = Path(output_path)
    if output_path.suffix in [".yaml", ".yml"]:
        example.to_yaml(output_path)
    else:
        example.to_json(output_path)

    print(f"Beispiel-Konfiguration erstellt: {output_path}")
