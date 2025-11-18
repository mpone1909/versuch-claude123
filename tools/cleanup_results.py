#!/usr/bin/env python3
"""
Cleanup Results Tool

Bereinigt alte Experiment-Ergebnisse.
Archiviert oder löscht alte Resultate basierend auf Alter.
"""

import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ResultsCleaner:
    """Bereinigt Experiment-Ergebnisse."""

    def __init__(
        self,
        results_dir: Path,
        archive_dir: Optional[Path] = None,
        dry_run: bool = False
    ):
        """
        Initialisiert den Cleaner.

        Args:
            results_dir: Verzeichnis mit Ergebnissen
            archive_dir: Optional, Archivverzeichnis
            dry_run: Wenn True, werden keine Änderungen durchgeführt
        """
        self.results_dir = results_dir
        self.archive_dir = archive_dir
        self.dry_run = dry_run

        if not self.results_dir.exists():
            raise ValueError(f"Results-Verzeichnis nicht gefunden: {results_dir}")

        if self.archive_dir:
            self.archive_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_old_results(
        self,
        days_threshold: int = 30,
        delete: bool = False
    ) -> Dict[str, Any]:
        """
        Bereinigt alte Ergebnisse.

        Args:
            days_threshold: Alter in Tagen (älter als dieser Wert wird bereinigt)
            delete: Wenn True, werden Dateien gelöscht statt archiviert

        Returns:
            Dictionary mit Cleanup-Statistiken
        """
        threshold_date = datetime.now() - timedelta(days=days_threshold)

        stats = {
            "total_found": 0,
            "archived": 0,
            "deleted": 0,
            "errors": 0,
            "bytes_freed": 0
        }

        logger.info(f"Suche nach Ergebnissen älter als {days_threshold} Tage...")
        logger.info(f"Schwellwert-Datum: {threshold_date.strftime('%Y-%m-%d')}")

        if self.dry_run:
            logger.info("🔍 DRY RUN - Keine Änderungen werden durchgeführt\n")

        # Finde alle Unterverzeichnisse
        for item in self.results_dir.iterdir():
            if not item.is_dir():
                continue

            stats["total_found"] += 1

            # Prüfe Alter
            mtime = datetime.fromtimestamp(item.stat().st_mtime)

            if mtime < threshold_date:
                # Berechne Größe
                size = self._get_dir_size(item)
                stats["bytes_freed"] += size

                logger.info(
                    f"  {item.name} (Größe: {self._format_size(size)}, "
                    f"Alter: {(datetime.now() - mtime).days} Tage)"
                )

                if self.dry_run:
                    if delete:
                        logger.info(f"    → Würde gelöscht werden")
                    else:
                        logger.info(f"    → Würde archiviert werden")
                else:
                    try:
                        if delete:
                            self._delete_directory(item)
                            stats["deleted"] += 1
                            logger.info(f"    ✓ Gelöscht")
                        else:
                            self._archive_directory(item)
                            stats["archived"] += 1
                            logger.info(f"    ✓ Archiviert")
                    except Exception as e:
                        stats["errors"] += 1
                        logger.error(f"    ✗ Fehler: {e}")

        # Zusammenfassung
        print("\n" + "=" * 60)
        print("Cleanup-Zusammenfassung:")
        print("=" * 60)
        print(f"Gefundene Verzeichnisse:  {stats['total_found']}")
        print(f"Archiviert:               {stats['archived']}")
        print(f"Gelöscht:                 {stats['deleted']}")
        print(f"Fehler:                   {stats['errors']}")
        print(f"Freigegebener Speicher:   {self._format_size(stats['bytes_freed'])}")
        print("=" * 60)

        return stats

    def cleanup_empty_directories(self) -> int:
        """
        Entfernt leere Verzeichnisse.

        Returns:
            Anzahl entfernter Verzeichnisse
        """
        removed_count = 0

        logger.info("Suche nach leeren Verzeichnissen...")

        for item in self.results_dir.iterdir():
            if not item.is_dir():
                continue

            if not any(item.iterdir()):  # Verzeichnis ist leer
                logger.info(f"  Leeres Verzeichnis: {item.name}")

                if not self.dry_run:
                    try:
                        item.rmdir()
                        logger.info(f"    ✓ Entfernt")
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"    ✗ Fehler: {e}")
                else:
                    logger.info(f"    → Würde entfernt werden")

        logger.info(f"\nEntfernte leere Verzeichnisse: {removed_count}")
        return removed_count

    def _archive_directory(self, directory: Path):
        """Archiviert ein Verzeichnis."""
        if not self.archive_dir:
            raise ValueError("Kein Archiv-Verzeichnis konfiguriert")

        # Erstelle Archiv-Pfad mit Datum
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = self.archive_dir / f"{directory.name}_{timestamp}"

        shutil.move(str(directory), str(archive_path))

    def _delete_directory(self, directory: Path):
        """Löscht ein Verzeichnis."""
        shutil.rmtree(directory)

    def _get_dir_size(self, directory: Path) -> int:
        """
        Berechnet Größe eines Verzeichnisses.

        Args:
            directory: Verzeichnis

        Returns:
            Größe in Bytes
        """
        total_size = 0
        for item in directory.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size

    def _format_size(self, bytes_size: int) -> str:
        """
        Formatiert Byte-Größe lesbar.

        Args:
            bytes_size: Größe in Bytes

        Returns:
            Formatierter String (z.B. "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"


def main():
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(
        description="Bereinigt alte Experiment-Ergebnisse"
    )

    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Verzeichnis mit Ergebnissen (default: results/)"
    )

    parser.add_argument(
        "--archive-dir",
        type=str,
        help="Archivverzeichnis (default: results/archive/)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Alter in Tagen für Cleanup (default: 30)"
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Löschen statt archivieren"
    )

    parser.add_argument(
        "--clean-empty",
        action="store_true",
        help="Entferne leere Verzeichnisse"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry Run - zeigt nur was passieren würde"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        logger.error(f"Results-Verzeichnis nicht gefunden: {results_dir}")
        sys.exit(1)

    archive_dir = None
    if args.archive_dir:
        archive_dir = Path(args.archive_dir)
    elif not args.delete:
        archive_dir = results_dir / "archive"

    # Erstelle Cleaner
    cleaner = ResultsCleaner(
        results_dir=results_dir,
        archive_dir=archive_dir,
        dry_run=args.dry_run
    )

    # Cleanup
    if args.clean_empty:
        cleaner.cleanup_empty_directories()
    else:
        stats = cleaner.cleanup_old_results(
            days_threshold=args.days,
            delete=args.delete
        )

        if stats["errors"] > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
