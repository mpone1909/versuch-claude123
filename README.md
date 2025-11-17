# DaRa Multi-Agent RAG/MCP System

Ein vollständiges Multi-Agent-System für die Verarbeitung, Analyse und Berichterstattung von zeitsynchronen DaRa-Forschungsdaten mit RAG (Retrieval-Augmented Generation) und MCP (Model Context Protocol) Integration.

## Überblick

Das DaRa-System ist eine modulare Python-Anwendung, die:
- **Zeitsynchrone CSV-Dateien** liest (Zeile N über alle Dateien = gleicher Zeitpunkt)
- **Multi-Proband-Daten aggregiert** mit statistischen Analysen
- **Prozessmuster erkennt** (Baseline, Peaks, Trends, Anomalien)
- **Berichte erstellt** und nach Notion sowie Google Drive exportiert
- **LangGraph-basierte Orchestrierung** für robuste End-to-End-Workflows nutzt

## Projektstruktur

```
versuch-claude123/
├── src/
│   └── dara_system/          # Haupt-Package
│       ├── __init__.py
│       ├── document_loader.py           # CSV/Dateien laden
│       ├── embeddings.py                # Embedding-Generierung
│       ├── vector_store.py              # Vektor-Speicherung & Suche
│       ├── rag_pipeline.py              # RAG-Pipeline
│       ├── mcp_server.py                # MCP-Server-Schnittstelle
│       ├── dara_processor.py            # DaRa-Hilfsfunktionen
│       ├── synchronized_csv_reader.py   # Zeitsynchrones CSV-Lesen
│       ├── multi_proband_aggregator.py  # Aggregation
│       ├── process_analysis_agent.py    # Prozessanalyse-Agent
│       ├── notion_reporter.py           # Notion-Reporter
│       ├── gdrive_reporter.py           # Google Drive-Reporter
│       └── langgraph_orchestrator.py    # LangGraph-Orchestrierung
├── tests/                    # Unit-Tests
│   ├── test_vector_store.py
│   ├── test_dara_processor.py
│   ├── test_synchronized_csv_reader.py
│   ├── test_multi_proband_aggregator.py
│   └── test_process_analysis_agent.py
├── docs/                     # Dokumentation
│   ├── ARCHITECTURE.md
│   ├── AGENTS.md
│   ├── DATAFLOW.md
│   └── PROMPTS_REGISTRY.md
├── pyproject.toml           # Build & Dependency-Konfiguration
├── .gitignore
└── README.md

```

## Installation

### Voraussetzungen

- Python 3.9 oder höher
- pip oder poetry

### Setup

1. Repository klonen:
```bash
git clone <repository-url>
cd versuch-claude123
```

2. Virtuelle Umgebung erstellen:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

3. Dependencies installieren:
```bash
pip install -e .
```

4. Für Entwicklung mit Test-Tools:
```bash
pip install -e ".[dev]"
```

## Schnellstart

### Beispiel: End-to-End-Pipeline

```python
from pathlib import Path
from dara_system.langgraph_orchestrator import (
    LangGraphOrchestrator,
    OrchestratorConfig
)

# Konfiguration
config = OrchestratorConfig(
    primary_field="value",
    baseline_threshold=0.3,
    peak_threshold=0.8,
    create_notion_report=False,  # Optional
    create_gdrive_doc=False,     # Optional
)

# Orchestrator erstellen
orchestrator = LangGraphOrchestrator(config)

# CSV-Dateien (eine pro Proband)
csv_files = [
    "data/proband_1.csv",
    "data/proband_2.csv",
    "data/proband_3.csv",
]

# Pipeline ausführen
results = orchestrator.run_pipeline(
    csv_file_paths=csv_files,
    proband_ids=["P1", "P2", "P3"]
)

# Ergebnisse anzeigen
print(results["data"]["analysis"]["summary"])
```

### CSV-Dateiformat

Jede CSV-Datei sollte folgende Struktur haben:

```csv
timestamp,value,status,score
0,10.5,active,5.0
1,12.3,active,6.5
2,11.8,passive,5.8
...
```

**Wichtig:** Zeile N in allen CSV-Dateien repräsentiert denselben Zeitpunkt.

## Kernfunktionalitäten

### 1. Zeitsynchrones CSV-Lesen

```python
from dara_system.synchronized_csv_reader import SynchronizedCSVReader

reader = SynchronizedCSVReader(
    file_paths=["p1.csv", "p2.csv", "p3.csv"],
    proband_ids=["P1", "P2", "P3"]
)

for time_slice in reader.read_synchronized():
    print(f"Zeitpunkt {time_slice.timestamp}:")
    print(f"  Probanden: {list(time_slice.data.keys())}")
```

### 2. Multi-Proband-Aggregation

```python
from dara_system.multi_proband_aggregator import MultiProbandAggregator

aggregator = MultiProbandAggregator(
    numeric_fields=["value", "score"],
    min_valid_probands=2
)

agg_result = aggregator.aggregate_time_slice(time_slice)
print(f"Mean value: {agg_result.statistics['value']['mean']}")
```

### 3. Prozessanalyse

```python
from dara_system.process_analysis_agent import ProcessAnalysisAgent

agent = ProcessAnalysisAgent(
    baseline_threshold=0.3,
    peak_threshold=0.8
)

analysis = agent.analyze_aggregated_slices(
    aggregated_slices,
    primary_field="value"
)

print(analysis.summary)
for pattern in analysis.patterns:
    print(f"Pattern: {pattern.pattern_type} - {pattern.description}")
```

### 4. Reporting

```python
from dara_system.notion_reporter import NotionReporter
from dara_system.gdrive_reporter import GDriveReporter

# Notion (benötigt API Token in Umgebungsvariable NOTION_API_TOKEN)
notion = NotionReporter()
notion.send_analysis_report(analysis, title="DaRa Analyse 2024")

# Google Drive (benötigt Credentials in GOOGLE_CREDENTIALS_PATH)
gdrive = GDriveReporter()
gdrive.create_doc_report(analysis, title="DaRa Report")
gdrive.create_sheet_report(analysis, title="DaRa Daten")
```

### 5. Command-Line Interface (CLI)

Das System bietet ein umfassendes CLI-Tool:

```bash
# Liste verfügbare Experimente
dara-cli list

# Führe ein Experiment aus
dara-cli run experiments/example_experiment.yaml

# Zeige Ergebnisse
dara-cli show-results

# Erstelle Beispiel-Konfiguration
dara-cli create-example experiments/my_experiment.yaml

# Validiere Konfiguration
dara-cli validate experiments/my_experiment.yaml
```

### 6. Experiment-Framework

Definiere Experimente in YAML/JSON:

```yaml
name: my_experiment
description: Beschreibung des Experiments
csv_file_paths:
  - data/proband_1.csv
  - data/proband_2.csv
proband_ids:
  - P1
  - P2
primary_field: value
baseline_threshold: 0.3
peak_threshold: 0.8
run_evaluation: true
```

Führe aus und erhalte automatisch:
- Analyse-Ergebnisse
- Evaluations-Metriken (Coverage, Pattern-Counts, Anomalie-Rate)
- Strukturierte Reports in `results/<experiment_name>/`

## Konfiguration

### System-Konfiguration

Das System nutzt ein zentrales Konfigurationssystem:

```python
from dara_system.config import get_config

config = get_config()

# Zugriff auf Teilkonfigurationen
print(config.paths.data_dir)
print(config.dara.baseline_threshold)
print(config.notion.enabled)
```

Konfiguration via `.env`-Datei (siehe `.env.example`):

```bash
# Kopiere Beispiel-Datei
cp .env.example .env

# Bearbeite .env mit deinen Werten
nano .env
```

### Umgebungsvariablen

Für externe Integrationen können folgende Umgebungsvariablen gesetzt werden:

```bash
# Notion
export NOTION_API_TOKEN="your_notion_token"
export NOTION_DATABASE_ID="your_database_id"

# Google Drive
export GOOGLE_CREDENTIALS_PATH="/path/to/credentials.json"
export GDRIVE_FOLDER_ID="your_folder_id"
```

**Hinweis:** Ohne diese Variablen arbeiten die Reporter im Simulations-Modus.

## Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=dara_system --cov-report=html

# Spezifischer Test
pytest tests/test_vector_store.py -v
```

## Observability

Das System bietet umfassendes Logging und Metriken:

```python
from dara_system.observability import get_logger, timed_block, get_metrics

# Strukturiertes Logging
logger = get_logger("my_module")
logger.info("Processing started")
logger.log_event("data_loaded", {"rows": 1000})

# Performance-Tracking
with timed_block("data_processing", logger):
    # ... your code ...
    pass

# Metriken abrufen
metrics = get_metrics()
print(metrics)
```

## Dokumentation

Weitere detaillierte Dokumentation finden Sie unter `docs/`:

- **ARCHITECTURE.md**: Architektur-Übersicht und Layer-Beschreibungen
- **AGENTS.md**: Detaillierte Agent-Dokumentation
- **DATAFLOW.md**: Datenfluss durch das System
- **PROMPTS_REGISTRY.md**: Mapping von Prompts zu Modulen
- **THESIS_MAPPING.md**: Zuordnung zu Masterarbeit-Sektionen

## Entwicklung

### Code-Stil

Das Projekt verwendet:
- **black** für Code-Formatierung
- **isort** für Import-Sortierung
- **flake8** für Linting
- **mypy** für Type-Checking (optional)

```bash
# Formatierung
black src/ tests/
isort src/ tests/

# Linting
flake8 src/ tests/
```

### Neue Module hinzufügen

1. Erstellen Sie das Modul in `src/dara_system/`
2. Fügen Sie Tests in `tests/test_<module>.py` hinzu
3. Dokumentieren Sie das Modul mit Docstrings
4. Aktualisieren Sie die Dokumentation in `docs/`

## Lizenz

MIT

## Kontakt

DaRa Research Team

## Changelog

### Version 0.1.0 (Initial Release)

- ✅ Projektstruktur und Build-Konfiguration
- ✅ Kernmodule (document_loader, embeddings, vector_store, rag_pipeline, mcp_server, dara_processor)
- ✅ Zeitsynchrone CSV-Verarbeitung
- ✅ Multi-Proband-Aggregation
- ✅ Process Analysis Agent mit Pattern Recognition
- ✅ Notion & Google Drive Reporter
- ✅ LangGraph-Orchestrierung
- ✅ Konfigurationssystem mit Pydantic
- ✅ Experiment-Framework & Evaluation
- ✅ Observability (Logging & Metriken)
- ✅ Command-Line Interface (CLI)
- ✅ API-Stubs für zukünftige REST-API
- ✅ GitHub Actions CI/CD
- ✅ Umfassende Unit-Tests
- ✅ Vollständige Dokumentation inkl. Thesis-Mapping
