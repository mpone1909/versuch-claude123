"""
Synchronized CSV Reader Module

Liest mehrere CSV-Dateien zeitsynchron, wobei Zeile N in allen Dateien
denselben Zeitpunkt repräsentiert (z.B. verschiedene Probanden zum gleichen Zeitpunkt).
"""

from typing import List, Dict, Any, Optional, Iterator, Union
from pathlib import Path
from dataclasses import dataclass
import csv
import logging

from .dara_processor import TimeSlice

logger = logging.getLogger(__name__)


@dataclass
class CSVFileInfo:
    """Informationen zu einer CSV-Datei im synchronen Set."""
    path: Path
    proband_id: str
    header: List[str]
    total_rows: int


class SynchronizedReadError(Exception):
    """Fehler beim synchronisierten Lesen"""
    pass


class SynchronizedCSVReader:
    """
    Liest mehrere CSV-Dateien zeitsynchron.

    Jede Datei repräsentiert einen Probanden.
    Zeile N über alle Dateien hinweg = derselbe Zeitpunkt.

    Features:
    - Batch-Reading für Effizienz
    - Fehlerbehandlung bei unterschiedlichen Dateilängen
    - Strategien für fehlende/fehlerhafte Zeilen
    """

    def __init__(
        self,
        file_paths: List[Union[str, Path]],
        proband_ids: Optional[List[str]] = None,
        encoding: str = "utf-8",
        delimiter: str = ",",
        skip_errors: bool = True,
        fill_missing: bool = True
    ):
        """
        Initialisiert den Synchronized CSV Reader.

        Args:
            file_paths: Liste von Pfaden zu CSV-Dateien
            proband_ids: Optional, IDs für jeden Probanden (default: Dateinamen)
            encoding: Encoding der CSV-Dateien
            delimiter: CSV-Trennzeichen
            skip_errors: Bei True werden fehlerhafte Zeilen übersprungen
            fill_missing: Bei True werden fehlende Werte mit None gefüllt
        """
        self.file_paths = [Path(p) for p in file_paths]
        self.proband_ids = proband_ids or [p.stem for p in self.file_paths]
        self.encoding = encoding
        self.delimiter = delimiter
        self.skip_errors = skip_errors
        self.fill_missing = fill_missing

        # Validierung
        if len(self.file_paths) != len(self.proband_ids):
            raise SynchronizedReadError(
                f"Anzahl Dateien ({len(self.file_paths)}) != "
                f"Anzahl Probanden-IDs ({len(self.proband_ids)})"
            )

        # Prüfe Dateien
        for path in self.file_paths:
            if not path.exists():
                raise SynchronizedReadError(f"Datei nicht gefunden: {path}")

        self.file_info: List[CSVFileInfo] = []
        self._initialize_file_info()

        logger.info(
            f"SynchronizedCSVReader initialisiert mit {len(self.file_paths)} Dateien"
        )

    def _initialize_file_info(self):
        """Liest Header und Zeilenzahlen aller Dateien."""
        for path, proband_id in zip(self.file_paths, self.proband_ids):
            with open(path, 'r', encoding=self.encoding, newline='') as f:
                reader = csv.reader(f, delimiter=self.delimiter)
                header = next(reader, [])

                # Zähle Zeilen (exkl. Header)
                row_count = sum(1 for _ in reader)

            info = CSVFileInfo(
                path=path,
                proband_id=proband_id,
                header=header,
                total_rows=row_count
            )
            self.file_info.append(info)

            logger.debug(f"{proband_id}: {row_count} Zeilen, Header: {header}")

    def get_max_rows(self) -> int:
        """
        Gibt die maximale Zeilenanzahl über alle Dateien zurück.

        Returns:
            Maximale Zeilenanzahl
        """
        return max(info.total_rows for info in self.file_info)

    def get_min_rows(self) -> int:
        """
        Gibt die minimale Zeilenanzahl über alle Dateien zurück.

        Returns:
            Minimale Zeilenanzahl
        """
        return min(info.total_rows for info in self.file_info)

    def read_synchronized(
        self,
        start_row: int = 0,
        end_row: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> Iterator[TimeSlice]:
        """
        Liest Zeilen synchron über alle Dateien.

        Args:
            start_row: Startzeile (0-basiert)
            end_row: Endzeile (exklusiv, None = bis Ende)
            batch_size: Wenn gesetzt, werden Batches als einzelne TimeSlices zurückgegeben

        Yields:
            TimeSlice-Objekte mit Daten aller Probanden für jeden Zeitpunkt
        """
        if end_row is None:
            end_row = self.get_max_rows()

        logger.info(f"Lese synchron von Zeile {start_row} bis {end_row}")

        # Öffne alle Dateien
        file_handles = []
        csv_readers = []

        try:
            for info in self.file_info:
                f = open(info.path, 'r', encoding=self.encoding, newline='')
                file_handles.append(f)

                reader = csv.DictReader(f, delimiter=self.delimiter)
                csv_readers.append(reader)

            # Überspringe Zeilen bis start_row
            for _ in range(start_row):
                for reader in csv_readers:
                    try:
                        next(reader)
                    except StopIteration:
                        pass

            # Lese zeitsynchron
            if batch_size:
                yield from self._read_batched(csv_readers, start_row, end_row, batch_size)
            else:
                yield from self._read_row_by_row(csv_readers, start_row, end_row)

        finally:
            # Schließe alle Dateien
            for f in file_handles:
                f.close()

    def _read_row_by_row(
        self,
        csv_readers: List,
        start_row: int,
        end_row: int
    ) -> Iterator[TimeSlice]:
        """
        Liest Zeile für Zeile synchron.

        Args:
            csv_readers: Liste von CSV-DictReader-Objekten
            start_row: Startzeile
            end_row: Endzeile

        Yields:
            TimeSlice pro Zeile
        """
        for row_idx in range(start_row, end_row):
            time_slice_data = {}

            for info, reader in zip(self.file_info, csv_readers):
                try:
                    row = next(reader)
                    time_slice_data[info.proband_id] = dict(row)
                except StopIteration:
                    # Datei zu Ende
                    if self.fill_missing:
                        time_slice_data[info.proband_id] = None
                    else:
                        logger.warning(
                            f"Datei {info.proband_id} hat weniger Zeilen "
                            f"als erwartet bei Zeile {row_idx}"
                        )
                except Exception as e:
                    if self.skip_errors:
                        logger.warning(
                            f"Fehler beim Lesen von {info.proband_id}, "
                            f"Zeile {row_idx}: {e}"
                        )
                        time_slice_data[info.proband_id] = None
                    else:
                        raise SynchronizedReadError(
                            f"Fehler in {info.proband_id}, Zeile {row_idx}: {e}"
                        ) from e

            yield TimeSlice(
                timestamp=row_idx,
                data=time_slice_data,
                metadata={"source": "synchronized_read"}
            )

    def _read_batched(
        self,
        csv_readers: List,
        start_row: int,
        end_row: int,
        batch_size: int
    ) -> Iterator[TimeSlice]:
        """
        Liest in Batches und fasst mehrere Zeilen zu einem TimeSlice zusammen.

        Args:
            csv_readers: Liste von CSV-DictReader-Objekten
            start_row: Startzeile
            end_row: Endzeile
            batch_size: Anzahl Zeilen pro Batch

        Yields:
            TimeSlice pro Batch
        """
        batch_start = start_row

        while batch_start < end_row:
            batch_end = min(batch_start + batch_size, end_row)
            batch_data = {info.proband_id: [] for info in self.file_info}

            for row_idx in range(batch_start, batch_end):
                for info, reader in zip(self.file_info, csv_readers):
                    try:
                        row = next(reader)
                        batch_data[info.proband_id].append(dict(row))
                    except StopIteration:
                        if self.fill_missing:
                            batch_data[info.proband_id].append(None)
                    except Exception as e:
                        if self.skip_errors:
                            logger.warning(f"Fehler in {info.proband_id}, Zeile {row_idx}: {e}")
                            batch_data[info.proband_id].append(None)
                        else:
                            raise

            yield TimeSlice(
                timestamp=batch_start,
                data=batch_data,
                metadata={
                    "source": "synchronized_read_batch",
                    "batch_size": batch_end - batch_start,
                }
            )

            batch_start = batch_end

    def get_file_info_summary(self) -> List[Dict[str, Any]]:
        """
        Gibt eine Zusammenfassung der geladenen Dateien zurück.

        Returns:
            Liste von Dictionaries mit Datei-Informationen
        """
        return [
            {
                "proband_id": info.proband_id,
                "path": str(info.path),
                "total_rows": info.total_rows,
                "header": info.header,
            }
            for info in self.file_info
        ]
