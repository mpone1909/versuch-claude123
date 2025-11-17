"""Tests für das Config-Modul."""

import pytest
from pathlib import Path
from dara_system.config import (
    PathConfig,
    DaRaConfig,
    NotionConfig,
    GoogleDriveConfig,
    SystemConfig,
    get_config,
    set_config,
)


def test_path_config_defaults():
    """Testet PathConfig mit Defaults."""
    config = PathConfig()

    assert config.project_root is not None
    assert config.data_dir is not None
    assert config.experiments_dir is not None
    assert config.results_dir is not None
    assert config.logs_dir is not None


def test_dara_config_defaults():
    """Testet DaRaConfig mit Defaults."""
    config = DaRaConfig()

    assert config.default_proband_ids == ["P1", "P2", "P3"]
    assert config.min_valid_probands == 2
    assert config.batch_size == 1000
    assert config.baseline_threshold == 0.3
    assert config.peak_threshold == 0.8
    assert config.primary_numeric_field == "value"


def test_notion_config_disabled_by_default():
    """Testet dass Notion standardmäßig deaktiviert ist."""
    config = NotionConfig()

    assert config.enabled is False
    assert config.api_token is None


def test_google_drive_config_disabled_by_default():
    """Testet dass Google Drive standardmäßig deaktiviert ist."""
    config = GoogleDriveConfig()

    assert config.enabled is False
    assert config.credentials_path is None


def test_system_config_initialization():
    """Testet SystemConfig-Initialisierung."""
    config = SystemConfig()

    assert config.paths is not None
    assert config.dara is not None
    assert config.notion is not None
    assert config.google_drive is not None
    assert config.orchestrator is not None


def test_get_config_singleton():
    """Testet get_config Singleton-Verhalten."""
    config1 = get_config()
    config2 = get_config()

    assert config1 is config2


def test_get_config_reload():
    """Testet get_config mit reload."""
    config1 = get_config()
    config2 = get_config(reload=True)

    # Nach reload sollte es eine neue Instanz sein
    assert config1 is not config2


def test_set_config():
    """Testet set_config."""
    new_config = SystemConfig()
    set_config(new_config)

    retrieved = get_config()
    assert retrieved is new_config
