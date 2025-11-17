"""Tests für Synchronized CSV Reader Module"""

import pytest
import tempfile
import csv
from pathlib import Path
from src.dara_system.synchronized_csv_reader import (
    SynchronizedCSVReader,
    SynchronizedReadError
)


class TestSynchronizedCSVReader:
    """Tests für SynchronizedCSVReader"""

    @pytest.fixture
    def temp_csv_files(self):
        """Erstellt temporäre Test-CSV-Dateien"""
        temp_dir = tempfile.mkdtemp()
        files = []

        # Erstelle 3 CSV-Dateien mit gleicher Struktur
        for i in range(3):
            file_path = Path(temp_dir) / f"proband_{i}.csv"

            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "value", "status"])
                writer.writeheader()

                # 5 Zeilen pro Datei
                for row in range(5):
                    writer.writerow({
                        "timestamp": row,
                        "value": (i + 1) * 10 + row,
                        "status": "active" if row % 2 == 0 else "passive"
                    })

            files.append(file_path)

        yield files

        # Cleanup
        for file in files:
            file.unlink()

    def test_initialization(self, temp_csv_files):
        """Test: Initialisierung"""
        reader = SynchronizedCSVReader(temp_csv_files)

        assert len(reader.file_info) == 3
        assert reader.get_max_rows() == 5
        assert reader.get_min_rows() == 5

    def test_read_synchronized(self, temp_csv_files):
        """Test: Synchrones Lesen"""
        reader = SynchronizedCSVReader(temp_csv_files)

        time_slices = list(reader.read_synchronized())

        assert len(time_slices) == 5  # 5 Zeilen pro Datei

        # Prüfe ersten TimeSlice
        first_slice = time_slices[0]
        assert first_slice.timestamp == 0
        assert len(first_slice.data) == 3  # 3 Probanden

    def test_read_with_start_end(self, temp_csv_files):
        """Test: Lesen mit Start/End-Zeile"""
        reader = SynchronizedCSVReader(temp_csv_files)

        time_slices = list(reader.read_synchronized(start_row=1, end_row=3))

        assert len(time_slices) == 2  # Zeilen 1-2 (end_row exklusiv)
        assert time_slices[0].timestamp == 1

    def test_proband_ids(self, temp_csv_files):
        """Test: Custom Proband IDs"""
        proband_ids = ["P1", "P2", "P3"]
        reader = SynchronizedCSVReader(temp_csv_files, proband_ids=proband_ids)

        time_slices = list(reader.read_synchronized(end_row=1))

        assert "P1" in time_slices[0].data
        assert "P2" in time_slices[0].data
        assert "P3" in time_slices[0].data

    def test_missing_file(self):
        """Test: Fehler bei fehlender Datei"""
        with pytest.raises(SynchronizedReadError):
            SynchronizedCSVReader(["/nonexistent/file.csv"])

    def test_file_info_summary(self, temp_csv_files):
        """Test: Datei-Info-Zusammenfassung"""
        reader = SynchronizedCSVReader(temp_csv_files)

        summary = reader.get_file_info_summary()

        assert len(summary) == 3
        assert all("total_rows" in info for info in summary)
        assert all(info["total_rows"] == 5 for info in summary)
