"""
Document Loader Module

Verantwortlich für das Laden von Dateien (CSV, JSON, etc.) von verschiedenen Quellen.
Aktuell: Lokales Dateisystem, erweiterbar für Cloud-Storage.
"""

from pathlib import Path
from typing import List, Union, Dict, Any, Optional
import csv
import logging

logger = logging.getLogger(__name__)


class DocumentLoadError(Exception):
    """Fehler beim Laden von Dokumenten"""
    pass


class DocumentLoader:
    """
    Lädt Dokumente von verschiedenen Quellen.

    Aktuell unterstützt:
    - Lokale CSV-Dateien

    Zukünftig erweiterbar für:
    - Cloud Storage (S3, Google Cloud Storage)
    - Datenbanken
    - APIs
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialisiert den Document Loader.

        Args:
            base_path: Optional, Basis-Pfad für relative Pfadangaben
        """
        self.base_path = base_path or Path.cwd()
        logger.info(f"DocumentLoader initialisiert mit base_path: {self.base_path}")

    def load_csv_files(
        self,
        file_paths: List[Union[str, Path]],
        encoding: str = "utf-8",
        delimiter: str = ","
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Lädt mehrere CSV-Dateien.

        Args:
            file_paths: Liste von Dateipfaden (absolut oder relativ zu base_path)
            encoding: Encoding der CSV-Dateien
            delimiter: CSV-Trennzeichen

        Returns:
            Dictionary: {Dateipfad: Liste von Zeilen als Dictionaries}

        Raises:
            DocumentLoadError: Bei Problemen beim Laden
        """
        results = {}

        for file_path in file_paths:
            try:
                results[str(file_path)] = self._load_single_csv(
                    file_path, encoding, delimiter
                )
            except Exception as e:
                logger.error(f"Fehler beim Laden von {file_path}: {e}")
                raise DocumentLoadError(f"Konnte {file_path} nicht laden: {e}") from e

        return results

    def _load_single_csv(
        self,
        file_path: Union[str, Path],
        encoding: str,
        delimiter: str
    ) -> List[Dict[str, Any]]:
        """
        Lädt eine einzelne CSV-Datei.

        Args:
            file_path: Pfad zur CSV-Datei
            encoding: Encoding
            delimiter: Trennzeichen

        Returns:
            Liste von Dictionaries (eine pro Zeile)
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {path}")

        if not path.is_file():
            raise ValueError(f"Pfad ist keine Datei: {path}")

        logger.info(f"Lade CSV-Datei: {path}")

        rows = []
        with open(path, 'r', encoding=encoding, newline='') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row_num, row in enumerate(reader, start=1):
                rows.append(dict(row))

        logger.info(f"Erfolgreich {len(rows)} Zeilen aus {path} geladen")
        return rows

    def validate_file_exists(self, file_path: Union[str, Path]) -> bool:
        """
        Prüft, ob eine Datei existiert.

        Args:
            file_path: Zu prüfender Pfad

        Returns:
            True wenn Datei existiert, sonst False
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path

        return path.exists() and path.is_file()

    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Liefert Metadaten zu einer Datei.

        Args:
            file_path: Dateipfad

        Returns:
            Dictionary mit Metadaten (size, modified, etc.)
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {path}")

        stat = path.stat()
        return {
            "path": str(path),
            "size_bytes": stat.st_size,
            "modified_timestamp": stat.st_mtime,
            "is_file": path.is_file(),
            "extension": path.suffix,
        }
