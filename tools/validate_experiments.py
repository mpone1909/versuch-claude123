#!/usr/bin/env python3
"""
Validate Experiments Tool

Validiert Experiment-Konfigurationsdateien auf Korrektheit.
Prüft Schema, Pfade und Konsistenz.
"""

import sys
import argparse
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ExperimentValidator:
    """Validiert Experiment-Konfigurationen."""

    REQUIRED_FIELDS = [
        "name",
        "csv_file_paths",
        "proband_ids"
    ]

    OPTIONAL_FIELDS = [
        "description",
        "primary_field",
        "baseline_threshold",
        "peak_threshold",
        "row_range",
        "run_evaluation",
        "create_notion_report",
        "create_gdrive_doc"
    ]

    def __init__(self, check_paths: bool = False):
        """
        Initialisiert den Validator.

        Args:
            check_paths: Wenn True, werden auch Dateipfade validiert
        """
        self.check_paths = check_paths
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_file(self, file_path: Path) -> bool:
        """
        Validiert eine Experiment-Datei.

        Args:
            file_path: Pfad zur Experiment-Konfiguration

        Returns:
            True wenn valide, False sonst
        """
        self.errors = []
        self.warnings = []

        # Prüfe ob Datei existiert
        if not file_path.exists():
            self.errors.append(f"Datei nicht gefunden: {file_path}")
            return False

        # Lade Konfiguration
        try:
            config = self._load_config(file_path)
        except Exception as e:
            self.errors.append(f"Fehler beim Laden der Datei: {e}")
            return False

        # Validiere Schema
        self._validate_schema(config)

        # Validiere Werte
        self._validate_values(config)

        # Validiere Pfade (optional)
        if self.check_paths:
            self._validate_paths(config)

        # Zusammenfassung
        is_valid = len(self.errors) == 0

        if is_valid:
            logger.info(f"✓ {file_path.name} ist valide")
            if self.warnings:
                for warning in self.warnings:
                    logger.warning(f"  ⚠ {warning}")
        else:
            logger.error(f"✗ {file_path.name} ist NICHT valide")
            for error in self.errors:
                logger.error(f"  ✗ {error}")

        return is_valid

    def _load_config(self, file_path: Path) -> Dict[str, Any]:
        """Lädt Konfigurationsdatei."""
        suffix = file_path.suffix.lower()

        if suffix in ['.yaml', '.yml']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"Nicht unterstütztes Format: {suffix}")

    def _validate_schema(self, config: Dict[str, Any]):
        """Validiert Schema der Konfiguration."""
        # Prüfe Pflichtfelder
        for field in self.REQUIRED_FIELDS:
            if field not in config:
                self.errors.append(f"Fehlendes Pflichtfeld: '{field}'")

        # Prüfe unbekannte Felder
        all_fields = self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS
        for field in config.keys():
            if field not in all_fields:
                self.warnings.append(f"Unbekanntes Feld: '{field}'")

    def _validate_values(self, config: Dict[str, Any]):
        """Validiert Werte in der Konfiguration."""
        # Name
        if "name" in config:
            if not isinstance(config["name"], str) or not config["name"].strip():
                self.errors.append("'name' muss ein nicht-leerer String sein")

        # CSV Paths
        if "csv_file_paths" in config:
            paths = config["csv_file_paths"]
            if not isinstance(paths, list) or len(paths) == 0:
                self.errors.append("'csv_file_paths' muss eine nicht-leere Liste sein")

        # Proband IDs
        if "proband_ids" in config:
            ids = config["proband_ids"]
            if not isinstance(ids, list) or len(ids) == 0:
                self.errors.append("'proband_ids' muss eine nicht-leere Liste sein")

            # Prüfe Anzahl
            if "csv_file_paths" in config:
                if len(ids) != len(config["csv_file_paths"]):
                    self.errors.append(
                        f"Anzahl proband_ids ({len(ids)}) != "
                        f"Anzahl csv_file_paths ({len(config['csv_file_paths'])})"
                    )

        # Thresholds
        for threshold_field in ["baseline_threshold", "peak_threshold"]:
            if threshold_field in config:
                value = config[threshold_field]
                if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                    self.errors.append(
                        f"'{threshold_field}' muss eine Zahl zwischen 0 und 1 sein"
                    )

        # Row Range
        if "row_range" in config:
            row_range = config["row_range"]
            if not isinstance(row_range, list) or len(row_range) != 2:
                self.errors.append("'row_range' muss eine Liste mit 2 Elementen sein [start, end]")
            else:
                start, end = row_range
                if not isinstance(start, int) or not isinstance(end, int):
                    self.errors.append("'row_range' Werte müssen Integers sein")
                elif start >= end:
                    self.errors.append(f"'row_range' start ({start}) muss < end ({end}) sein")

        # Boolean Felder
        for bool_field in ["run_evaluation", "create_notion_report", "create_gdrive_doc"]:
            if bool_field in config:
                if not isinstance(config[bool_field], bool):
                    self.warnings.append(f"'{bool_field}' sollte ein Boolean sein")

    def _validate_paths(self, config: Dict[str, Any]):
        """Validiert ob Dateipfade existieren."""
        if "csv_file_paths" in config:
            for path_str in config["csv_file_paths"]:
                path = Path(path_str)
                if not path.exists():
                    self.warnings.append(f"CSV-Datei nicht gefunden: {path_str}")


def validate_directory(directory: Path, check_paths: bool = False) -> Dict[str, bool]:
    """
    Validiert alle Experiment-Dateien in einem Verzeichnis.

    Args:
        directory: Verzeichnis mit Experiment-Konfigurationen
        check_paths: Pfade validieren

    Returns:
        Dictionary: filename -> is_valid
    """
    validator = ExperimentValidator(check_paths=check_paths)
    results = {}

    # Finde alle YAML/JSON-Dateien
    patterns = ["*.yaml", "*.yml", "*.json"]
    files = []
    for pattern in patterns:
        files.extend(directory.glob(pattern))

    if not files:
        logger.warning(f"Keine Experiment-Dateien in {directory} gefunden")
        return results

    logger.info(f"Validiere {len(files)} Datei(en) in {directory}\n")

    for file_path in sorted(files):
        is_valid = validator.validate_file(file_path)
        results[file_path.name] = is_valid

    # Zusammenfassung
    valid_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print("\n" + "=" * 60)
    print(f"Zusammenfassung: {valid_count}/{total_count} Dateien valide")
    print("=" * 60)

    return results


def main():
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(
        description="Validiert Experiment-Konfigurationsdateien"
    )

    parser.add_argument(
        "path",
        type=str,
        help="Pfad zu Experiment-Datei oder -Verzeichnis"
    )

    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Prüft ob referenzierte Dateipfade existieren"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    path = Path(args.path)

    if not path.exists():
        logger.error(f"Pfad nicht gefunden: {path}")
        sys.exit(1)

    # Validiere
    if path.is_file():
        validator = ExperimentValidator(check_paths=args.check_paths)
        is_valid = validator.validate_file(path)
        sys.exit(0 if is_valid else 1)
    elif path.is_dir():
        results = validate_directory(path, check_paths=args.check_paths)
        all_valid = all(results.values())
        sys.exit(0 if all_valid else 1)
    else:
        logger.error(f"Ungültiger Pfad: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
