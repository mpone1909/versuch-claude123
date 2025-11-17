"""Tests für das Experiment-Config-Modul."""

import pytest
from pathlib import Path
from dara_system.experiment_config import (
    ExperimentConfig,
    load_experiment_config,
    create_example_config,
)


def test_experiment_config_defaults():
    """Testet ExperimentConfig mit Minimal-Parametern."""
    config = ExperimentConfig(
        name="test_exp",
        csv_file_paths=["data/p1.csv"],
        proband_ids=["P1"],
    )

    assert config.name == "test_exp"
    assert config.start_row == 0
    assert config.end_row is None
    assert config.primary_field == "value"
    assert config.run_evaluation is True


def test_experiment_config_validation_success():
    """Testet erfolgreiche Validierung."""
    config = ExperimentConfig(
        name="test_exp",
        csv_file_paths=["data/p1.csv", "data/p2.csv"],
        proband_ids=["P1", "P2"],
    )

    errors = config.validate()
    assert len(errors) == 0


def test_experiment_config_validation_missing_name():
    """Testet Validierung mit fehlendem Namen."""
    config = ExperimentConfig(
        name="",
        csv_file_paths=["data/p1.csv"],
        proband_ids=["P1"],
    )

    errors = config.validate()
    assert any("Name ist erforderlich" in e for e in errors)


def test_experiment_config_validation_mismatch_files_probands():
    """Testet Validierung bei unterschiedlicher Anzahl Dateien/Probanden."""
    config = ExperimentConfig(
        name="test",
        csv_file_paths=["data/p1.csv", "data/p2.csv"],
        proband_ids=["P1"],
    )

    errors = config.validate()
    assert any("muss" in e and "entsprechen" in e for e in errors)


def test_experiment_config_validation_invalid_thresholds():
    """Testet Validierung mit ungültigen Schwellenwerten."""
    config = ExperimentConfig(
        name="test",
        csv_file_paths=["data/p1.csv"],
        proband_ids=["P1"],
        baseline_threshold=1.5,  # Ungültig
    )

    errors = config.validate()
    assert any("baseline_threshold" in e for e in errors)


def test_experiment_config_to_dict():
    """Testet Konvertierung zu Dictionary."""
    config = ExperimentConfig(
        name="test",
        csv_file_paths=["data/p1.csv"],
        proband_ids=["P1"],
    )

    data = config.to_dict()

    assert isinstance(data, dict)
    assert data["name"] == "test"
    assert data["csv_file_paths"] == ["data/p1.csv"]


def test_experiment_config_from_dict():
    """Testet Erstellung aus Dictionary."""
    data = {
        "name": "test",
        "csv_file_paths": ["data/p1.csv"],
        "proband_ids": ["P1"],
    }

    config = ExperimentConfig.from_dict(data)

    assert config.name == "test"
    assert config.csv_file_paths == ["data/p1.csv"]


def test_create_example_config(tmp_path):
    """Testet Erstellung einer Beispiel-Config."""
    output_path = tmp_path / "example.yaml"

    create_example_config(output_path)

    assert output_path.exists()

    # Lade und validiere
    config = load_experiment_config(output_path)
    assert config.name == "example_experiment"
    assert len(config.validate()) == 0


def test_load_experiment_config_yaml(tmp_path):
    """Testet Laden einer YAML-Config."""
    config_path = tmp_path / "test.yaml"
    create_example_config(config_path)

    loaded = load_experiment_config(config_path)

    assert loaded.name == "example_experiment"


def test_load_experiment_config_nonexistent():
    """Testet Laden einer nicht-existierenden Datei."""
    with pytest.raises(FileNotFoundError):
        load_experiment_config(Path("nonexistent.yaml"))
