# Observability & Logging

Logging, Metriken und Observability im DARA-System.

## Übersicht

Das DARA-System bietet umfassendes Logging und Monitoring:

- **Strukturiertes Logging**: JSON und Text-Format
- **Performance-Tracking**: Zeitmessungen für kritische Operationen
- **Metriken-Sammlung**: Experiment-Statistiken
- **Event-Logging**: Wichtige System-Ereignisse
- **Error-Tracking**: Fehlerprotokollierung mit Context

## Module

### `observability.py`

Zentrale Observability-Funktionalität.

## Logging

### Setup

```python
from dara_system.observability import setup_logging

# Basis-Setup (INFO-Level, Text-Format)
setup_logging()

# Custom-Setup
setup_logging(
    level="DEBUG",
    log_format="json",
    log_file="logs/experiment.log"
)
```

### Logger verwenden

```python
from dara_system.observability import get_logger

# Erstelle Logger für dein Modul
logger = get_logger(__name__)

# Standard-Logging
logger.debug("Debug-Information")
logger.info("Information")
logger.warning("Warnung")
logger.error("Fehler")
logger.critical("Kritischer Fehler")
```

### Strukturiertes Logging

```python
logger = get_logger(__name__)

# Event mit zusätzlichen Daten loggen
logger.log_event(
    "experiment_started",
    {
        "experiment_id": "exp_001",
        "probands": 3,
        "csv_files": ["p1.csv", "p2.csv", "p3.csv"]
    }
)

# Fehler mit Context
logger.log_error(
    "data_load_failed",
    error=exception_obj,
    context={
        "file": "proband_1.csv",
        "row": 150
    }
)
```

### Log-Formate

#### Text-Format (Standard)

```
2024-01-15 10:30:45 INFO [dara_system.orchestrator] Experiment started: exp_001
2024-01-15 10:30:46 DEBUG [dara_system.csv_reader] Loading file: proband_1.csv
2024-01-15 10:30:47 WARNING [dara_system.aggregator] Missing data in row 42
```

#### JSON-Format

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "dara_system.orchestrator",
  "message": "Experiment started",
  "event": "experiment_started",
  "data": {
    "experiment_id": "exp_001",
    "probands": 3
  }
}
```

Aktivierung:

```python
setup_logging(log_format="json")
```

## Performance-Tracking

### Zeitmessung mit Context Manager

```python
from dara_system.observability import get_logger, timed_block

logger = get_logger(__name__)

# Messe Ausführungszeit
with timed_block("data_processing", logger):
    # Dein Code hier
    process_data(...)

# Log-Output:
# INFO: Starting: data_processing
# INFO: Completed: data_processing (duration: 2.345s)
```

### Decorator für Funktionen

```python
from dara_system.observability import time_function

@time_function
def analyze_data(data):
    # Analyse-Code
    return results

# Automatisches Logging von Ausführungszeit
results = analyze_data(my_data)
# INFO: Function analyze_data executed in 1.234s
```

### Manuelle Zeitmessung

```python
from dara_system.observability import get_logger
import time

logger = get_logger(__name__)
start_time = time.time()

# Dein Code
process_data(...)

duration = time.time() - start_time
logger.log_metric("processing_duration", duration, {"unit": "seconds"})
```

## Metriken

### Metriken sammeln

```python
from dara_system.observability import get_metrics, record_metric

# Einzelne Metrik aufzeichnen
record_metric("experiment.csv_files_processed", 3)
record_metric("experiment.total_rows", 3000)
record_metric("experiment.processing_time", 5.432)

# Mit Tags/Labels
record_metric(
    "analysis.patterns_detected",
    12,
    tags={"experiment_id": "exp_001", "proband_count": 3}
)
```

### Metriken abrufen

```python
from dara_system.observability import get_metrics

# Alle Metriken
metrics = get_metrics()
print(metrics)
# {
#   "experiment.csv_files_processed": 3,
#   "experiment.total_rows": 3000,
#   "analysis.patterns_detected": 12
# }

# Metriken für Experiment-Report
experiment_metrics = get_metrics(prefix="experiment.")
```

### Metriken zurücksetzen

```python
from dara_system.observability import reset_metrics

# Vor jedem Experiment
reset_metrics()
```

## Event-Logging

### System-Events

Das System loggt automatisch wichtige Events:

```python
# In verschiedenen Modulen
logger.log_event("csv_files_loaded", {"count": 3, "total_rows": 3000})
logger.log_event("aggregation_completed", {"slices": 1000})
logger.log_event("pattern_detected", {"type": "peak", "timestamp": 450})
logger.log_event("report_created", {"type": "notion", "success": True})
```

### Custom Events

```python
logger = get_logger(__name__)

logger.log_event(
    "custom_analysis_step",
    {
        "step": "baseline_calculation",
        "result": 45.6,
        "metadata": {...}
    }
)
```

## Integration in DARA-Workflows

### Orchestrator mit Logging

```python
from dara_system.langgraph_orchestrator import LangGraphOrchestrator
from dara_system.observability import setup_logging, get_logger, timed_block

# Setup
setup_logging(level="INFO", log_file="logs/experiment.log")
logger = get_logger(__name__)

# Orchestrator
orchestrator = LangGraphOrchestrator(config)

# Pipeline mit Logging
logger.log_event("pipeline_started", {"config": config})

with timed_block("full_pipeline", logger):
    results = orchestrator.run_pipeline(
        csv_file_paths=files,
        proband_ids=ids
    )

logger.log_event("pipeline_completed", {"results": results["data"]["summary"]})
```

### Experiment mit Metriken

```python
from dara_system.run_experiment import run_experiment
from dara_system.observability import get_metrics, reset_metrics

# Reset für neues Experiment
reset_metrics()

# Führe Experiment aus
results = run_experiment("experiments/my_experiment.yaml")

# Sammle Metriken
metrics = get_metrics()

# In Results speichern
results["observability"] = {
    "metrics": metrics,
    "log_file": "logs/my_experiment.log"
}
```

### Agent mit Logging

```python
from dara_system.process_analysis_agent import ProcessAnalysisAgent
from dara_system.observability import get_logger, timed_block

logger = get_logger(__name__)

agent = ProcessAnalysisAgent(
    baseline_threshold=0.3,
    peak_threshold=0.8
)

with timed_block("pattern_analysis", logger):
    analysis = agent.analyze_aggregated_slices(
        aggregated_slices,
        primary_field="value"
    )

logger.log_event(
    "analysis_completed",
    {
        "patterns_found": len(analysis.patterns),
        "summary": analysis.summary
    }
)
```

## Konfiguration

### Via `.env`

```bash
# Logging
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=text         # text oder json
LOG_FILE=logs/dara.log

# Observability (optional)
OBSERVABILITY_ENABLED=false
OBSERVABILITY_URL=http://localhost:4318
```

### Via Code

```python
from dara_system.config import get_config

config = get_config()

setup_logging(
    level=config.observability.log_level,
    log_format=config.observability.log_format,
    log_file=config.observability.log_file
)
```

## Externe Observability-Tools (Optional)

### OpenTelemetry-Integration (Zukünftig)

Für Integration mit OpenTelemetry:

```python
# Zukünftige Implementierung
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup Tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Setup Exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# In DARA-Code
with tracer.start_as_current_span("data_processing"):
    process_data(...)
```

### Grafana/Prometheus (Zukünftig)

Für Metriken-Export:

```python
# Beispiel: Prometheus-Metriken
from prometheus_client import Counter, Histogram, start_http_server

# Metriken definieren
experiments_total = Counter('dara_experiments_total', 'Total experiments')
processing_duration = Histogram('dara_processing_seconds', 'Processing duration')

# In Code
experiments_total.inc()
with processing_duration.time():
    process_data(...)

# Metrics-Server starten
start_http_server(8000)
```

## Log-Dateien

### Standard-Log-Struktur

```
logs/
├── dara.log                    # Haupt-Log
├── experiments/
│   ├── exp_001.log
│   ├── exp_002.log
│   └── ...
└── errors/
    └── errors_2024-01-15.log
```

### Log-Rotation

Für automatische Log-Rotation:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "logs/dara.log",
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)

setup_logging(handlers=[handler])
```

### Log-Analyse

```bash
# Filtere ERROR-Logs
grep ERROR logs/dara.log

# JSON-Logs analysieren
cat logs/dara.log | jq 'select(.level == "ERROR")'

# Zeige nur Events
cat logs/dara.log | jq 'select(.event != null)'
```

## Best Practices

### 1. Aussagekräftige Log-Messages

```python
# ✅ Gut
logger.info(f"Processing proband P1: 1000 rows loaded")

# ❌ Schlecht
logger.info("Processing")
```

### 2. Kontext mitgeben

```python
# ✅ Gut
logger.log_event("error_occurred", {
    "module": "csv_reader",
    "file": "proband_1.csv",
    "row": 150,
    "error_type": "ValueError"
})

# ❌ Schlecht
logger.error("Error occurred")
```

### 3. Geeignete Log-Level

- **DEBUG**: Detaillierte Entwicklungs-Informationen
- **INFO**: Normale Ablauf-Informationen
- **WARNING**: Unerwartete Situationen (aber kein Fehler)
- **ERROR**: Fehler, die behandelt wurden
- **CRITICAL**: Schwerwiegende Fehler

```python
logger.debug(f"Row data: {row}")  # Nur für Debugging
logger.info("Experiment started")  # Normaler Ablauf
logger.warning("Missing value, using default")  # Ungewöhnlich
logger.error(f"Failed to load file: {e}")  # Fehler
logger.critical("Database connection lost")  # Kritisch
```

### 4. Performance-sensible Bereiche tracken

```python
# Wichtige Operationen messen
with timed_block("data_aggregation", logger):
    aggregator.aggregate(...)

with timed_block("pattern_recognition", logger):
    agent.analyze(...)
```

### 5. Sensible Daten nicht loggen

```python
# ❌ Niemals
logger.info(f"API Token: {api_token}")

# ✅ Richtig
logger.info("API authentication successful")
```

## Troubleshooting

### Problem: Keine Logs werden geschrieben

**Lösung**: Setup aufrufen und Pfad prüfen:

```python
from dara_system.observability import setup_logging
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

setup_logging(log_file="logs/dara.log")
```

### Problem: Log-Datei wird zu groß

**Lösung**: Nutze Log-Rotation:

```python
from logging.handlers import RotatingFileHandler

setup_logging(
    handlers=[
        RotatingFileHandler("logs/dara.log", maxBytes=10_000_000, backupCount=5)
    ]
)
```

### Problem: JSON-Logs sind unleserlich

**Lösung**: Nutze `jq` für Formatierung:

```bash
# Schön formatiert
cat logs/dara.log | jq '.'

# Nur bestimmte Felder
cat logs/dara.log | jq '{timestamp, level, message}'
```

## Siehe auch

- [CONFIG.md](CONFIG.md) für Konfigurationsdetails
- [ARCHITECTURE.md](ARCHITECTURE.md) für System-Überblick
- `src/dara_system/observability.py` für Implementierung
