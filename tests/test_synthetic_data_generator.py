"""Tests for synthetic_data_generator module."""

import pytest
from pathlib import Path
import tempfile
import csv

from dara_system.synthetic_data_generator import (
    SyntheticDataGenerator,
    SyntheticDataConfig,
    generate_example_dataset
)


def test_synthetic_data_config_defaults():
    """Test SyntheticDataConfig with defaults."""
    config = SyntheticDataConfig()

    assert config.num_probands == 3
    assert config.num_rows == 1000
    assert config.primary_field == "value"
    assert config.fields is not None


def test_synthetic_data_generator_initialization():
    """Test SyntheticDataGenerator initialization."""
    config = SyntheticDataConfig(num_probands=2, num_rows=100)
    generator = SyntheticDataGenerator(config, seed=42)

    assert generator.config.num_probands == 2
    assert generator.config.num_rows == 100
    assert generator.seed == 42


def test_generate_multi_proband_csvs():
    """Test generating multiple CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SyntheticDataConfig(num_probands=2, num_rows=50)
        generator = SyntheticDataGenerator(config, seed=42)

        output_dir = Path(tmpdir)
        files = generator.generate_multi_proband_csvs(output_dir)

        # Check files were created
        assert len(files) == 2
        for file_path in files:
            assert file_path.exists()
            assert file_path.suffix == ".csv"

        # Check file content
        with open(files[0], 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 50
            assert "timestamp" in rows[0]
            assert "value" in rows[0]
            assert "label" in rows[0]


def test_generated_data_structure():
    """Test structure of generated data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SyntheticDataConfig(num_probands=1, num_rows=10)
        generator = SyntheticDataGenerator(config, seed=42)

        files = generator.generate_multi_proband_csvs(Path(tmpdir))

        # Read first file
        with open(files[0], 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)

            # Check fields
            assert "timestamp" in row
            assert "value" in row
            assert "status" in row
            assert "score" in row
            assert "label" in row

            # Check types (as strings in CSV)
            assert row["timestamp"].isdigit()
            float(row["value"])  # Should not raise
            assert row["status"] in ["low", "normal", "high"]


def test_generate_scenario_variants():
    """Test generating multiple scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SyntheticDataConfig(num_probands=2, num_rows=50)
        generator = SyntheticDataGenerator(config, seed=42)

        scenarios = generator.generate_scenario_variants(Path(tmpdir))

        # Check scenarios
        assert "baseline" in scenarios
        assert "high_activity" in scenarios
        assert "low_activity" in scenarios

        # Each scenario should have 2 files
        for scenario_name, files in scenarios.items():
            assert len(files) == 2
            for file_path in files:
                assert file_path.exists()


def test_generate_example_dataset():
    """Test convenience function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = generate_example_dataset(
            output_dir=tmpdir,
            num_probands=2,
            num_rows=50,
            seed=42
        )

        assert len(files) == 2
        for file_path in files:
            assert file_path.exists()


def test_reproducibility_with_seed():
    """Test that same seed produces same data."""
    with tempfile.TemporaryDirectory() as tmpdir1, \
         tempfile.TemporaryDirectory() as tmpdir2:

        config = SyntheticDataConfig(num_probands=1, num_rows=10)

        # Generate twice with same seed
        gen1 = SyntheticDataGenerator(config, seed=42)
        files1 = gen1.generate_multi_proband_csvs(Path(tmpdir1))

        gen2 = SyntheticDataGenerator(config, seed=42)
        files2 = gen2.generate_multi_proband_csvs(Path(tmpdir2))

        # Read and compare first rows
        with open(files1[0], 'r') as f1, open(files2[0], 'r') as f2:
            reader1 = csv.DictReader(f1)
            reader2 = csv.DictReader(f2)

            row1 = next(reader1)
            row2 = next(reader2)

            # Values should be identical
            assert row1["value"] == row2["value"]
            assert row1["status"] == row2["status"]


def test_value_ranges():
    """Test that generated values are in reasonable ranges."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SyntheticDataConfig(
            num_probands=1,
            num_rows=100,
            baseline_mean=50.0
        )
        generator = SyntheticDataGenerator(config, seed=42)

        files = generator.generate_multi_proband_csvs(Path(tmpdir))

        with open(files[0], 'r') as f:
            reader = csv.DictReader(f)
            values = [float(row["value"]) for row in reader]

            # Check value range (should be around baseline_mean)
            assert min(values) >= 0  # No negative values
            assert max(values) < 200  # Reasonable upper bound

            # Check scores are in 0-10 range
            f.seek(0)
            next(reader)  # skip header
            scores = [float(row["score"]) for row in csv.DictReader(f)]
            assert all(0 <= s <= 10 for s in scores)


def test_labels_are_valid():
    """Test that generated labels are valid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SyntheticDataConfig(num_probands=1, num_rows=50)
        generator = SyntheticDataGenerator(config, seed=42)

        files = generator.generate_multi_proband_csvs(Path(tmpdir))

        with open(files[0], 'r') as f:
            reader = csv.DictReader(f)
            labels = [row["label"] for row in reader]

            valid_labels = {"rest", "baseline", "active", "peak"}
            assert all(label in valid_labels for label in labels)
