# Konfigurationssystem

Dieses Dokument beschreibt das Konfigurationssystem des DARA Multi-Agent RAG/MCP-Systems.

## Übersicht

Das System nutzt ein zentralisiertes Konfigurationssystem basierend auf:

1. **Pydantic Models** für typsichere Konfiguration
2. **Umgebungsvariablen** für sensitive Daten und Umgebungs-spezifische Einstellungen
3. **.env-Dateien** für lokale Entwicklung
4. **YAML/JSON-Dateien** für Experiment-Konfigurationen

## Konfigurationsdatei: `.env`

Die `.env`-Datei wird NICHT ins Repository committed und enthält lokale/sensitive Konfiguration.

### Setup

1. Kopiere die Beispieldatei:
   ```bash
   cp .env.example .env
   ```

2. Bearbeite `.env` mit deinen Werten:
   ```bash
   nano .env
   ```

### Verfügbare Umgebungsvariablen

#### Pfade

```bash
# Verzeichnisse
DATA_DIR=data
EXPERIMENTS_DIR=experiments
RESULTS_DIR=results
LOGS_DIR=logs
```

#### DARA-spezifische Konfiguration

```bash
# Prozessanalyse-Parameter
DARA_PRIMARY_FIELD=value
DARA_BASELINE_THRESHOLD=0.3
DARA_PEAK_THRESHOLD=0.8
DARA_MIN_VALID_PROBANDS=2
```

#### Notion Integration

```bash
# Notion API
NOTION_ENABLED=false
NOTION_API_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here
```

**Wichtig**: Ohne diese Werte arbeitet der NotionReporter im Simulations-Modus.

#### Google Drive Integration

```bash
# Google Drive
GDRIVE_ENABLED=false
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
GDRIVE_FOLDER_ID=your_folder_id_here
```

**Wichtig**: Ohne Credentials arbeitet der GDriveReporter im Simulations-Modus.

#### LLM-Backends (Optional)

```bash
# LLM Backend-Typ: "fake", "local_http", oder "cloud"
LLM_BACKEND_TYPE=fake
LLM_MODEL_NAME=default-model

# Für local_http Backend
LLM_BACKEND_URL=http://localhost:8080

# Für cloud Backend
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
ANTHROPIC_API_KEY=your_api_key_here
```

#### MCP-Integration (Optional)

```bash
# MCP Server
MCP_ENABLED=false
MCP_SERVER_URL=http://localhost:3000
```

#### Observability (Optional)

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # oder "text"

# Externe Observability (optional)
OBSERVABILITY_ENABLED=false
OBSERVABILITY_URL=http://localhost:4318
```

#### Weitere Optionen

```bash
# Entwicklungsmodus
DEBUG=false

# Cache
ENABLE_CACHE=true
CACHE_DIR=.cache
```

## Zentrale Konfigurationsklasse

Das System nutzt eine zentrale `SystemConfig`-Klasse in `src/dara_system/config.py`:

```python
from dara_system.config import get_config

# Hole Konfiguration
config = get_config()

# Zugriff auf Teilkonfigurationen
print(config.paths.data_dir)
print(config.dara.baseline_threshold)
print(config.notion.enabled)
print(config.llm.backend_type)
```

### Konfigurationsstruktur

Die Konfiguration ist hierarchisch organisiert:

- **PathsConfig**: Pfade zu Verzeichnissen
- **DaraConfig**: DARA-spezifische Parameter
- **NotionConfig**: Notion-Integration
- **GDriveConfig**: Google Drive-Integration
- **LLMConfig**: LLM-Backend-Konfiguration
- **MCPConfig**: MCP-Integration
- **ObservabilityConfig**: Logging und Monitoring
- **SystemConfig**: Wurzel-Konfiguration

## Experiment-Konfigurationen

Experimente werden in YAML- oder JSON-Dateien im `experiments/`-Verzeichnis definiert.

### Beispiel: `experiments/my_experiment.yaml`

```yaml
name: my_dara_experiment
description: Beschreibung des Experiments

# CSV-Dateien (eine pro Proband)
csv_file_paths:
  - data/proband_1.csv
  - data/proband_2.csv
  - data/proband_3.csv

# Proband-IDs (müssen zur Anzahl der CSV-Dateien passen)
proband_ids:
  - P1
  - P2
  - P3

# Prozessanalyse-Parameter
primary_field: value
baseline_threshold: 0.3
peak_threshold: 0.8

# Optional: Zeilenbereich
row_range: [0, 1000]  # Von Zeile 0 bis 1000

# Ausführungsoptionen
run_evaluation: true
create_notion_report: false
create_gdrive_doc: false
```

### Validierung von Experiment-Konfigurationen

Das System bietet ein Tool zur Validierung:

```bash
# Einzelne Datei validieren
python tools/validate_experiments.py experiments/my_experiment.yaml

# Alle Dateien in einem Verzeichnis validieren
python tools/validate_experiments.py experiments/

# Mit Pfad-Prüfung (prüft ob CSV-Dateien existieren)
python tools/validate_experiments.py experiments/ --check-paths
```

## Programmatische Konfiguration

### Konfiguration überschreiben

```python
from dara_system.config import get_config

config = get_config()

# Temporär überschreiben (nur im aktuellen Prozess)
config.dara.baseline_threshold = 0.4
config.notion.enabled = True
```

### Konfiguration für Tests

```python
from dara_system.config import SystemConfig, DaraConfig

# Erstelle Test-Konfiguration
test_config = SystemConfig(
    dara=DaraConfig(
        baseline_threshold=0.5,
        peak_threshold=0.9
    )
)
```

## Best Practices

### 1. Sensitive Daten

**NIE** sensitive Daten (API-Keys, Tokens) direkt in Code oder ins Repository committen!

✅ **Richtig**:
```bash
# In .env
NOTION_API_TOKEN=secret_token_xyz
```

❌ **Falsch**:
```python
# In Code
NOTION_TOKEN = "secret_token_xyz"  # NIEMALS!
```

### 2. Default-Werte

Stelle sinnvolle Default-Werte bereit, sodass das System auch ohne `.env` lauffähig ist:

```python
# In config.py
class DaraConfig(BaseModel):
    baseline_threshold: float = Field(default=0.3)
    peak_threshold: float = Field(default=0.8)
```

### 3. Validierung

Nutze Pydantic-Validatoren für komplexe Validierung:

```python
from pydantic import validator

class DaraConfig(BaseModel):
    baseline_threshold: float
    peak_threshold: float

    @validator('peak_threshold')
    def peak_must_be_greater_than_baseline(cls, v, values):
        if 'baseline_threshold' in values and v <= values['baseline_threshold']:
            raise ValueError('peak_threshold must be > baseline_threshold')
        return v
```

### 4. Umgebungs-spezifische Konfiguration

Nutze unterschiedliche `.env`-Dateien für verschiedene Umgebungen:

```bash
# Entwicklung
.env.development

# Produktion
.env.production

# Tests
.env.test
```

Lade die passende Datei:

```python
from dotenv import load_dotenv

# Lade umgebungs-spezifische Datei
env_file = os.getenv("ENV", "development")
load_dotenv(f".env.{env_file}")
```

## Feature Flags

Nutze Boolean-Flags zum Ein-/Ausschalten von Features:

```bash
# In .env
ENABLE_MCP=false
ENABLE_OBSERVABILITY=false
USE_LOCAL_LLM=false
```

```python
# In Code
from dara_system.config import get_config

config = get_config()

if config.mcp.enabled:
    # MCP-spezifischer Code
    pass

if config.observability.enabled:
    # Observability-spezifischer Code
    pass
```

## Troubleshooting

### Problem: Umgebungsvariablen werden nicht geladen

**Lösung**: Stelle sicher, dass `.env` im Working Directory liegt:

```python
from dotenv import load_dotenv
from pathlib import Path

# Explizit laden
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)
```

### Problem: Validierungsfehler bei Konfiguration

**Lösung**: Prüfe die Konfiguration programmatisch:

```python
from dara_system.config import get_config

try:
    config = get_config()
    print("Konfiguration ist valide")
except Exception as e:
    print(f"Konfigurationsfehler: {e}")
```

### Problem: Experiment-Konfiguration fehlerhaft

**Lösung**: Nutze das Validierungstool:

```bash
python tools/validate_experiments.py experiments/my_experiment.yaml --verbose
```

## Referenz

### Vollständige `.env`-Vorlage

Siehe `.env.example` im Repository-Root für eine vollständige, kommentierte Vorlage.

### Konfigurationsklassen

Siehe `src/dara_system/config.py` für die vollständige Definition aller Konfigurationsklassen.

### Experiment-Schema

Siehe `src/dara_system/experiment_config.py` für die Definition des Experiment-Schemas.
