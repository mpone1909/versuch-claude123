"""
Konfigurationssystem für das DaRa Multi-Agent System.

Bietet zentrale Konfigurationsklassen für:
- Dateipfade (Input/Output)
- DaRa-spezifische Parameter
- API-Konfigurationen (Notion, Google Drive)
- Orchestrierungs-Einstellungen
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class PathConfig(BaseSettings):
    """Konfiguration für Dateipfade."""

    # Basis-Verzeichnisse
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent,
        description="Projekt-Root-Verzeichnis",
    )
    data_dir: Optional[Path] = Field(default=None, description="Verzeichnis für Eingabedaten")
    experiments_dir: Optional[Path] = Field(default=None, description="Verzeichnis für Experiment-Configs")
    results_dir: Optional[Path] = Field(default=None, description="Verzeichnis für Ergebnisse")
    logs_dir: Optional[Path] = Field(default=None, description="Verzeichnis für Logs")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Setze Defaults basierend auf project_root
        if self.data_dir is None:
            self.data_dir = self.project_root / "data"
        if self.experiments_dir is None:
            self.experiments_dir = self.project_root / "experiments"
        if self.results_dir is None:
            self.results_dir = self.project_root / "results"
        if self.logs_dir is None:
            self.logs_dir = self.project_root / "logs"

    def ensure_directories(self):
        """Erstellt alle konfigurierten Verzeichnisse, falls sie nicht existieren."""
        for dir_path in [self.data_dir, self.experiments_dir, self.results_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    class Config:
        env_prefix = "DARA_PATH_"


class DaRaConfig(BaseSettings):
    """DaRa-spezifische Konfiguration."""

    # Standard-Probandenauswahl
    default_proband_ids: List[str] = Field(
        default_factory=lambda: ["P1", "P2", "P3"],
        description="Standard-Probanden-IDs",
    )

    # Verarbeitungs-Parameter
    min_valid_probands: int = Field(
        default=2, description="Mindestanzahl valider Probanden für Aggregation"
    )
    batch_size: int = Field(default=1000, description="Batch-Größe für zeitsynchrones Lesen")

    # Analyse-Parameter
    baseline_threshold: float = Field(
        default=0.3, description="Schwellenwert für Baseline-Erkennung"
    )
    peak_threshold: float = Field(default=0.8, description="Schwellenwert für Peak-Erkennung")
    anomaly_std_multiplier: float = Field(
        default=2.5, description="Standardabweichungs-Multiplikator für Anomalie-Erkennung"
    )

    # Datenfeld-Konfiguration
    primary_numeric_field: str = Field(
        default="value", description="Primäres numerisches Feld für Analyse"
    )
    additional_numeric_fields: List[str] = Field(
        default_factory=lambda: ["score"], description="Zusätzliche numerische Felder"
    )

    class Config:
        env_prefix = "DARA_"


class NotionConfig(BaseSettings):
    """Notion API Konfiguration."""

    api_token: Optional[str] = Field(default=None, description="Notion API Token")
    database_id: Optional[str] = Field(default=None, description="Notion Database ID")
    enabled: bool = Field(default=False, description="Notion-Integration aktiviert")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-enable wenn Token vorhanden
        if self.api_token and self.database_id:
            self.enabled = True

    class Config:
        env_prefix = "NOTION_"


class GoogleDriveConfig(BaseSettings):
    """Google Drive API Konfiguration."""

    credentials_path: Optional[Path] = Field(
        default=None, description="Pfad zur Google Credentials JSON-Datei"
    )
    folder_id: Optional[str] = Field(default=None, description="Google Drive Folder ID")
    enabled: bool = Field(default=False, description="Google Drive-Integration aktiviert")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-enable wenn Credentials vorhanden
        if self.credentials_path and self.credentials_path.exists() and self.folder_id:
            self.enabled = True

    class Config:
        env_prefix = "GOOGLE_"


class OrchestratorConfig(BaseSettings):
    """Orchestrierungs-Konfiguration."""

    # Report-Optionen
    create_notion_report: bool = Field(
        default=False, description="Notion-Report erstellen"
    )
    create_gdrive_doc: bool = Field(
        default=False, description="Google Drive Doc erstellen"
    )
    create_gdrive_sheet: bool = Field(
        default=False, description="Google Drive Sheet erstellen"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log-Level")
    verbose: bool = Field(default=False, description="Verbose-Modus")

    class Config:
        env_prefix = "ORCHESTRATOR_"


class SystemConfig:
    """
    Zentrale System-Konfiguration.

    Kombiniert alle Teil-Konfigurationen und bietet eine einheitliche Schnittstelle.
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialisiert die System-Konfiguration.

        Args:
            env_file: Optionaler Pfad zur .env-Datei
        """
        # Lade .env-Datei falls vorhanden
        if env_file and os.path.exists(env_file):
            from dotenv import load_dotenv

            load_dotenv(env_file)

        # Initialisiere Teilkonfigurationen
        self.paths = PathConfig()
        self.dara = DaRaConfig()
        self.notion = NotionConfig()
        self.google_drive = GoogleDriveConfig()
        self.orchestrator = OrchestratorConfig()

        # Erstelle Verzeichnisse
        self.paths.ensure_directories()

    def __repr__(self) -> str:
        return (
            f"SystemConfig(\n"
            f"  paths={self.paths}\n"
            f"  dara={self.dara}\n"
            f"  notion={self.notion}\n"
            f"  google_drive={self.google_drive}\n"
            f"  orchestrator={self.orchestrator}\n"
            f")"
        )


# Singleton-Instanz (kann überschrieben werden)
_default_config: Optional[SystemConfig] = None


def get_config(reload: bool = False, env_file: Optional[str] = None) -> SystemConfig:
    """
    Holt die globale System-Konfiguration.

    Args:
        reload: Wenn True, wird die Konfiguration neu geladen
        env_file: Optionaler Pfad zur .env-Datei

    Returns:
        SystemConfig-Instanz
    """
    global _default_config

    if _default_config is None or reload:
        _default_config = SystemConfig(env_file=env_file)

    return _default_config


def set_config(config: SystemConfig):
    """
    Setzt die globale System-Konfiguration.

    Args:
        config: Neue SystemConfig-Instanz
    """
    global _default_config
    _default_config = config
