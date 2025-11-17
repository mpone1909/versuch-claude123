"""
Observability-Modul für das DaRa-System.

Bietet einheitliches Logging und einfache Metriken-Erfassung
für alle Komponenten des Systems.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager


# Globale Metriken-Sammlung
_metrics: Dict[str, Any] = {
    "counters": {},
    "timers": {},
    "gauges": {},
}


class DaRaLogger:
    """
    Zentrales Logging-Interface für das DaRa-System.
    """

    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        log_file: Optional[Path] = None,
        console_output: bool = True,
    ):
        """
        Initialisiert einen DaRa-Logger.

        Args:
            name: Name des Loggers (typischerweise Modul-Name)
            log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optionaler Pfad zur Log-Datei
            console_output: Ob auf Konsole geloggt werden soll
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.propagate = False

        # Entferne existierende Handler
        self.logger.handlers = []

        # Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console-Handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File-Handler
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Debug-Level Logging."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Info-Level Logging."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Warning-Level Logging."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Error-Level Logging."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Critical-Level Logging."""
        self.logger.critical(message, extra=kwargs)

    def log_event(self, event_name: str, details: Dict[str, Any] = None):
        """
        Loggt ein strukturiertes Event.

        Args:
            event_name: Name des Events
            details: Zusätzliche Event-Details
        """
        details = details or {}
        message = f"EVENT: {event_name}"
        if details:
            message += f" | {details}"
        self.info(message)


def get_logger(
    name: str,
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> DaRaLogger:
    """
    Factory-Funktion zum Erstellen eines DaRa-Loggers.

    Args:
        name: Name des Loggers
        log_level: Optionales Log-Level (default: INFO)
        log_file: Optionale Log-Datei

    Returns:
        DaRaLogger-Instanz
    """
    log_level = log_level or "INFO"
    return DaRaLogger(name=name, log_level=log_level, log_file=log_file)


# Metriken-Funktionen


def increment_counter(name: str, value: int = 1, tags: Dict[str, str] = None):
    """
    Inkrementiert einen Counter.

    Args:
        name: Counter-Name
        value: Wert zum Inkrementieren
        tags: Optionale Tags für Kategorisierung
    """
    key = _make_metric_key(name, tags)

    if key not in _metrics["counters"]:
        _metrics["counters"][key] = 0

    _metrics["counters"][key] += value


def set_gauge(name: str, value: float, tags: Dict[str, str] = None):
    """
    Setzt einen Gauge-Wert.

    Args:
        name: Gauge-Name
        value: Wert
        tags: Optionale Tags
    """
    key = _make_metric_key(name, tags)
    _metrics["gauges"][key] = value


def record_timer(name: str, duration: float, tags: Dict[str, str] = None):
    """
    Zeichnet eine Timer-Messung auf.

    Args:
        name: Timer-Name
        duration: Dauer in Sekunden
        tags: Optionale Tags
    """
    key = _make_metric_key(name, tags)

    if key not in _metrics["timers"]:
        _metrics["timers"][key] = []

    _metrics["timers"][key].append(duration)


@contextmanager
def timed_block(name: str, logger: Optional[DaRaLogger] = None, tags: Dict[str, str] = None):
    """
    Context-Manager für zeitgesteuerte Code-Blöcke.

    Args:
        name: Name des Blocks
        logger: Optionaler Logger für Ausgabe
        tags: Optionale Tags

    Beispiel:
        with timed_block("data_loading", logger):
            # ... Code ...
    """
    start_time = time.time()

    if logger:
        logger.info(f"Start: {name}")

    try:
        yield
    finally:
        duration = time.time() - start_time
        record_timer(name, duration, tags)

        if logger:
            logger.info(f"Ende: {name} (Dauer: {duration:.3f}s)")


def get_metrics() -> Dict[str, Any]:
    """
    Holt alle gesammelten Metriken.

    Returns:
        Dictionary mit allen Metriken
    """
    # Berechne Statistiken für Timer
    timer_stats = {}
    for key, durations in _metrics["timers"].items():
        if durations:
            timer_stats[key] = {
                "count": len(durations),
                "total": sum(durations),
                "mean": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
            }

    return {
        "counters": _metrics["counters"].copy(),
        "gauges": _metrics["gauges"].copy(),
        "timers": timer_stats,
        "snapshot_at": datetime.now().isoformat(),
    }


def reset_metrics():
    """Setzt alle Metriken zurück."""
    _metrics["counters"].clear()
    _metrics["timers"].clear()
    _metrics["gauges"].clear()


def print_metrics_summary():
    """Gibt eine Zusammenfassung der Metriken auf der Konsole aus."""
    metrics = get_metrics()

    print("\n" + "=" * 60)
    print("METRIKEN-ZUSAMMENFASSUNG")
    print("=" * 60)

    print("\nCounters:")
    for name, value in metrics["counters"].items():
        print(f"  {name}: {value}")

    print("\nGauges:")
    for name, value in metrics["gauges"].items():
        print(f"  {name}: {value}")

    print("\nTimers:")
    for name, stats in metrics["timers"].items():
        print(f"  {name}:")
        print(f"    Count: {stats['count']}")
        print(f"    Total: {stats['total']:.3f}s")
        print(f"    Mean:  {stats['mean']:.3f}s")
        print(f"    Min:   {stats['min']:.3f}s")
        print(f"    Max:   {stats['max']:.3f}s")

    print("=" * 60 + "\n")


def _make_metric_key(name: str, tags: Dict[str, str] = None) -> str:
    """
    Erstellt einen Metrik-Key aus Name und Tags.

    Args:
        name: Metrik-Name
        tags: Optionale Tags

    Returns:
        Metrik-Key-String
    """
    if not tags:
        return name

    tag_parts = [f"{k}={v}" for k, v in sorted(tags.items())]
    return f"{name}[{','.join(tag_parts)}]"


# Pipeline-Event-Logging


class PipelineLogger:
    """
    Spezialisierter Logger für Pipeline-Ausführungen.
    """

    def __init__(self, pipeline_name: str, log_level: str = "INFO"):
        """
        Initialisiert einen Pipeline-Logger.

        Args:
            pipeline_name: Name der Pipeline
            log_level: Log-Level
        """
        self.pipeline_name = pipeline_name
        self.logger = get_logger(f"pipeline.{pipeline_name}", log_level=log_level)
        self.start_time = None

    def log_start(self, details: Dict[str, Any] = None):
        """Loggt Pipeline-Start."""
        self.start_time = time.time()
        self.logger.info(f"Pipeline '{self.pipeline_name}' gestartet")

        if details:
            self.logger.info(f"Details: {details}")

        increment_counter("pipeline.starts", tags={"pipeline": self.pipeline_name})

    def log_step(self, step_name: str, details: Dict[str, Any] = None):
        """Loggt einen Pipeline-Schritt."""
        self.logger.info(f"Schritt: {step_name}")

        if details:
            self.logger.debug(f"Schritt-Details: {details}")

        increment_counter("pipeline.steps", tags={"pipeline": self.pipeline_name, "step": step_name})

    def log_error(self, error: Exception, context: str = ""):
        """Loggt einen Pipeline-Fehler."""
        self.logger.error(f"Fehler in Pipeline '{self.pipeline_name}': {error}")

        if context:
            self.logger.error(f"Kontext: {context}")

        increment_counter("pipeline.errors", tags={"pipeline": self.pipeline_name})

    def log_complete(self, details: Dict[str, Any] = None):
        """Loggt Pipeline-Abschluss."""
        duration = time.time() - self.start_time if self.start_time else 0

        self.logger.info(f"Pipeline '{self.pipeline_name}' abgeschlossen (Dauer: {duration:.2f}s)")

        if details:
            self.logger.info(f"Ergebnis-Details: {details}")

        record_timer("pipeline.duration", duration, tags={"pipeline": self.pipeline_name})
        increment_counter("pipeline.completions", tags={"pipeline": self.pipeline_name})
