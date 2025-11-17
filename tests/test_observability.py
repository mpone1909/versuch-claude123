"""Tests für das Observability-Modul."""

import pytest
import time
from dara_system.observability import (
    DaRaLogger,
    get_logger,
    increment_counter,
    set_gauge,
    record_timer,
    get_metrics,
    reset_metrics,
    timed_block,
    PipelineLogger,
)


def test_dara_logger_creation():
    """Testet Logger-Erstellung."""
    logger = DaRaLogger("test_logger", log_level="INFO")

    assert logger.logger is not None
    assert logger.logger.name == "test_logger"


def test_dara_logger_methods():
    """Testet Logger-Methoden (Smoke-Test)."""
    logger = DaRaLogger("test", console_output=False)

    # Diese sollten nicht crashen
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    logger.log_event("test_event", {"key": "value"})


def test_get_logger():
    """Testet get_logger Factory."""
    logger = get_logger("test_module")

    assert isinstance(logger, DaRaLogger)


def test_increment_counter():
    """Testet Counter-Inkrementierung."""
    reset_metrics()

    increment_counter("test_counter", 1)
    increment_counter("test_counter", 2)

    metrics = get_metrics()
    assert metrics["counters"]["test_counter"] == 3


def test_increment_counter_with_tags():
    """Testet Counter mit Tags."""
    reset_metrics()

    increment_counter("requests", 1, tags={"endpoint": "api"})
    increment_counter("requests", 1, tags={"endpoint": "api"})
    increment_counter("requests", 1, tags={"endpoint": "web"})

    metrics = get_metrics()

    # Tags werden in den Key eingebunden
    assert "requests" in str(metrics["counters"])


def test_set_gauge():
    """Testet Gauge-Werte."""
    reset_metrics()

    set_gauge("memory_usage", 100.5)
    set_gauge("memory_usage", 200.7)

    metrics = get_metrics()
    assert metrics["gauges"]["memory_usage"] == 200.7


def test_record_timer():
    """Testet Timer-Recording."""
    reset_metrics()

    record_timer("operation", 1.5)
    record_timer("operation", 2.0)
    record_timer("operation", 1.0)

    metrics = get_metrics()
    timer_stats = metrics["timers"]["operation"]

    assert timer_stats["count"] == 3
    assert timer_stats["total"] == 4.5
    assert timer_stats["mean"] == 1.5
    assert timer_stats["min"] == 1.0
    assert timer_stats["max"] == 2.0


def test_timed_block():
    """Testet timed_block Context-Manager."""
    reset_metrics()

    with timed_block("test_operation"):
        time.sleep(0.01)  # Kurze Wartezeit

    metrics = get_metrics()
    assert "test_operation" in metrics["timers"]
    assert metrics["timers"]["test_operation"]["count"] == 1
    assert metrics["timers"]["test_operation"]["total"] > 0


def test_reset_metrics():
    """Testet Metriken-Reset."""
    increment_counter("test", 5)
    set_gauge("test_gauge", 10)
    record_timer("test_timer", 1.0)

    reset_metrics()
    metrics = get_metrics()

    assert len(metrics["counters"]) == 0
    assert len(metrics["gauges"]) == 0
    assert len(metrics["timers"]) == 0


def test_pipeline_logger():
    """Testet PipelineLogger."""
    reset_metrics()

    logger = PipelineLogger("test_pipeline")

    logger.log_start({"input": "test"})
    logger.log_step("step1", {"detail": "value"})
    logger.log_step("step2")
    logger.log_complete({"output": "result"})

    metrics = get_metrics()

    # Überprüfe dass Metriken gesammelt wurden
    assert any("pipeline.starts" in k for k in metrics["counters"].keys())
    assert any("pipeline.steps" in k for k in metrics["counters"].keys())


def test_pipeline_logger_error():
    """Testet PipelineLogger Fehlerbehandlung."""
    reset_metrics()

    logger = PipelineLogger("test_pipeline")
    logger.log_start()

    try:
        raise ValueError("Test error")
    except ValueError as e:
        logger.log_error(e, "test context")

    metrics = get_metrics()
    assert any("pipeline.errors" in k for k in metrics["counters"].keys())
