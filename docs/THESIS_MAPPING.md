# Thesis Mapping - DaRa Multi-Agent RAG/MCP System

Dieses Dokument bildet die Codekomponenten des DaRa-Systems auf typische Sektionen einer Masterarbeit ab und zeigt, wie das System zur wissenschaftlichen Arbeit beiträgt.

## Überblick

Das DaRa-System dient als technische Grundlage für Forschungsarbeiten im Bereich der Analyse von Intralogistik-Daten mit Multi-Agent-Systemen und RAG-Technologien.

---

## 1. Einleitung / Motivation

**Forschungskontext:**
- Multi-Proband-Studien in der Intralogistik
- Zeitsynchrone Datenanalyse über mehrere Beobachtungssubjekte
- Anwendung von RAG und Multi-Agent-Systemen auf strukturierte Zeitreihendaten

**Relevante Code-Komponenten:**
- `README.md` - Projektübersicht und Motivation
- `docs/ARCHITECTURE.md` - Systemarchitektur-Begründung

---

## 2. Grundlagen / Theoretischer Hintergrund

### 2.1 Retrieval-Augmented Generation (RAG)

**Theorie:**
- Kombination von Information Retrieval und Generierung
- Embedding-basierte Kontextsuche
- Vektor-Datenbanken für schnelle Ähnlichkeitssuche

**Code-Komponenten:**
- `src/dara_system/embeddings.py` - Embedding-Generierung
- `src/dara_system/vector_store.py` - Vektor-Speicherung und -Suche
- `src/dara_system/rag_pipeline.py` - RAG-Pipeline-Implementation

### 2.2 Multi-Agent-Systeme

**Theorie:**
- Verteilte Intelligenz und Aufgabenteilung
- Agent-Rollen: Analyse, Pattern Recognition, Reporting
- Orchestrierung und Koordination

**Code-Komponenten:**
- `src/dara_system/process_analysis_agent.py` - Prozessanalyse-Agent
- `src/dara_system/notion_reporter.py` - Reporting-Agent (Notion)
- `src/dara_system/gdrive_reporter.py` - Reporting-Agent (Google Drive)
- `docs/AGENTS.md` - Agent-Dokumentation

### 2.3 LangGraph & Orchestrierung

**Theorie:**
- Graph-basierte Workflow-Orchestrierung
- State Machines für komplexe Pipelines
- Kontrollfluss und Fehlerbehandlung

**Code-Komponenten:**
- `src/dara_system/langgraph_orchestrator.py` - Hauptorchestrator

### 2.4 Model Context Protocol (MCP)

**Theorie:**
- Standardisiertes Protokoll für Kontext-Bereitstellung
- Tool-Interfaces für LLMs
- [Unsicherheit] Konkrete MCP-Spezifikation und -Implementierung

**Code-Komponenten:**
- `src/dara_system/mcp_server.py` - MCP-Server-Stub

---

## 3. Methodik / Systemdesign

### 3.1 Datenmodell

**Forschungsfrage:**
Wie können zeitsynchrone Multi-Proband-Daten effizient verarbeitet werden?

**Code-Komponenten:**
- `src/dara_system/synchronized_csv_reader.py` - Zeitsynchrones CSV-Lesen
  - Zeile N in allen Dateien = gleicher Zeitpunkt
  - Batch-Verarbeitung
  - Fehlerbehandlung bei Inkonsistenzen

### 3.2 Datenverarbeitung

**Methode:**
1. **Laden**: CSV-Dateien einlesen (zeitsynchron)
2. **Aggregation**: Multi-Proband-Daten zusammenführen
3. **Analyse**: Mustererkennung und Prozessanalyse
4. **Reporting**: Ergebnisse persistieren

**Code-Komponenten:**
- `src/dara_system/document_loader.py` - Datei-Laden
- `src/dara_system/synchronized_csv_reader.py` - Synchrones Lesen
- `src/dara_system/multi_proband_aggregator.py` - Aggregation
- `src/dara_system/dara_processor.py` - DaRa-spezifische Verarbeitung

### 3.3 Analyse-Pipeline

**Methode:**
- Baseline-Erkennung (niedrige Aktivität)
- Peak-Erkennung (hohe Aktivität)
- Trend-Analyse
- Anomalie-Erkennung (statistische Ausreißer)

**Code-Komponenten:**
- `src/dara_system/process_analysis_agent.py` - Pattern Recognition
  - `detect_baseline()` - Baseline-Phasen
  - `detect_peaks()` - Peak-Erkennung
  - `detect_trends()` - Trend-Analyse
  - `detect_anomalies()` - Anomalie-Detektion

### 3.4 Datenfluss

**Dokumentation:**
- `docs/DATAFLOW.md` - Vollständiger Datenfluss durch das System

---

## 4. Implementierung

### 4.1 Systemarchitektur

**Layer-Modell:**
1. **Infrastructure Layer**: Config, Secrets, Logging
2. **Core Layer**: Loader, Embeddings, Vector Store, RAG, MCP
3. **Domain Layer**: DaRa-spezifische Verarbeitung (Sync Reader, Aggregator)
4. **Agent Layer**: Analyse-Agenten, Reporter
5. **Orchestration Layer**: LangGraph-Orchestrierung
6. **Application Layer**: Experiments, Evaluation, CLI

**Code-Komponenten:**
- `docs/ARCHITECTURE.md` - Detaillierte Architektur-Beschreibung
- Alle Module in `src/dara_system/`

### 4.2 Konfiguration & Umgebung

**Implementierung:**
- Zentrale Konfiguration mit Pydantic
- Umgebungsvariablen für Secrets
- Mehrschichtige Konfiguration (Paths, DaRa, APIs)

**Code-Komponenten:**
- `src/dara_system/config.py` - Konfigurationssystem
- `.env.example` - Beispiel-Umgebungsvariablen

### 4.3 Observability

**Implementierung:**
- Strukturiertes Logging
- Metriken (Counters, Gauges, Timers)
- Pipeline-Event-Tracking

**Code-Komponenten:**
- `src/dara_system/observability.py` - Logging & Metriken

---

## 5. Experimente / Evaluation

### 5.1 Experiment-Design

**Forschungsfragen:**
- Wie konsistent sind Pattern-Erkennungen über verschiedene Probanden?
- Welche Baseline/Peak-Schwellenwerte sind optimal?
- Wie hoch ist die Anomalie-Rate in realen Daten?

**Code-Komponenten:**
- `src/dara_system/experiment_config.py` - Experiment-Konfiguration
  - Definition von Experimenten
  - Parameter-Variation
  - Reproduzierbarkeit

- `src/dara_system/run_experiment.py` - Experiment-Ausführung
  - Automatisierte Pipeline-Runs
  - Ergebnis-Persistierung
  - Metadaten-Tracking

### 5.2 Metriken & Evaluation

**Evaluations-Metriken:**

1. **Coverage**: `valid_slices / total_slices`
   - Maß für Datenqualität

2. **Pattern-Statistiken**:
   - Anzahl erkannter Baselines
   - Anzahl erkannter Peaks
   - Anzahl erkannter Trends
   - Anzahl Anomalien

3. **Proband-Statistiken**:
   - Durchschnittliche Anzahl valider Probanden pro Zeitpunkt
   - Konsistenz über Probanden

4. **Feld-Statistiken**:
   - Min/Max/Mean über alle Zeit-Slices
   - Verteilungen numerischer Felder

**Code-Komponenten:**
- `src/dara_system/evaluation.py` - Evaluations-Framework
  - `evaluate_pipeline_results()` - Haupt-Evaluation
  - `compute_basic_stats()` - Basis-Statistiken
  - `compare_experiments()` - Experiment-Vergleich

### 5.3 Reproduzierbarkeit

**Maßnahmen:**
- Versionierte Experiment-Konfigurationen (YAML/JSON)
- Automatische Speicherung verwendeter Parameter
- Zeitstempel und Metadaten in Ergebnissen
- Git-basierte Versionierung

**Code-Komponenten:**
- `experiments/` - Experiment-Konfigurationen
- `results/` - Experiment-Ergebnisse
- Automatisches Backup der Config in jedem Ergebnis-Ordner

---

## 6. Ergebnisse

### 6.1 Datenaufbereitung

**Zu erwartende Ergebnisse:**
- Format-Beschreibung der aufbereiteten Daten
- Beispiel-Outputs aus `results/`

**Code-Komponenten:**
- Experiment-Reports in `results/<experiment_name>/`
  - `experiment_report.json` - Gesamt-Report
  - `evaluation_report.json` - Evaluations-Metriken
  - `analysis_result.json` - Analyse-Ergebnisse

### 6.2 Pattern-Erkennung

**Zu erwartende Ergebnisse:**
- Verteilung erkannter Pattern-Typen
- Konfidenz-Werte der Erkennungen
- Zeitliche Lokalisierung von Patterns

**Code-Komponenten:**
- `src/dara_system/process_analysis_agent.py`
- Pattern-Ausgaben in Analyse-Ergebnissen

### 6.3 Evaluations-Ergebnisse

**Zu erwartende Ergebnisse:**
- Coverage-Metriken
- Anomalie-Raten
- Performance-Metriken (Laufzeit, Speicher)

**Code-Komponenten:**
- `src/dara_system/evaluation.py`
- Metriken in `evaluation_report.json`

---

## 7. Diskussion

### 7.1 Limitationen

**Identifizierte Limitationen:**

1. **Embedding-Implementation**:
   - [Unsicherheit] Aktuelle Dummy-Implementation für Embeddings
   - Zukünftig: Integration echter Embedding-Modelle (z.B. Sentence-Transformers)

2. **MCP-Integration**:
   - [Unsicherheit] MCP-Server nur als Stub vorhanden
   - Zukünftig: Vollständige MCP-Protokoll-Implementation

3. **Skalierbarkeit**:
   - In-Memory Vector Store begrenzt durch RAM
   - Zukünftig: Integration persistenter Vektor-DB (z.B. Chroma, Pinecone)

4. **API**:
   - Nur Stub-Implementation
   - Zukünftig: FastAPI-basierte REST-API

**Code-Komponenten:**
- Stub-Module mit `[Implementierung fehlt]` Markierungen
- Dokumentierte TODOs in relevanten Modulen

### 7.2 Validität

**Threats to Validity:**

1. **Internal Validity**:
   - Feste Schwellenwerte (baseline_threshold, peak_threshold)
   - Mitigation: Konfigurierbare Parameter, Experimente mit Variation

2. **External Validity**:
   - Spezifisch für DaRa-Datenformat
   - Mitigation: Modularer Aufbau ermöglicht Anpassungen

3. **Construct Validity**:
   - Pattern-Erkennung basiert auf einfachen Heuristiken
   - Mitigation: Erweiterbare Agent-Architektur für komplexere Methoden

**Code-Komponenten:**
- `src/dara_system/config.py` - Konfigurierbare Parameter
- `src/dara_system/experiment_config.py` - Experiment-Variation

---

## 8. Zusammenfassung / Ausblick

### 8.1 Erreichte Ziele

**Implementierte Features:**
- ✅ Zeitsynchrone Multi-Proband-Datenverarbeitung
- ✅ Multi-Agent-Architektur mit Analyse- und Reporting-Agenten
- ✅ LangGraph-basierte Orchestrierung
- ✅ RAG-Grundstrukturen (Embeddings, Vector Store)
- ✅ Experiment-Framework mit Evaluation
- ✅ CLI-Tool für Experiment-Ausführung
- ✅ Umfassende Tests und CI/CD
- ✅ Vollständige Dokumentation

### 8.2 Zukünftige Arbeiten

**Geplante Erweiterungen:**

1. **ML-Integration**:
   - Echte Embedding-Modelle (Sentence-Transformers, OpenAI Embeddings)
   - Fortgeschrittene Anomalie-Erkennung (Isolation Forest, LSTM-basiert)
   - Supervised Learning für Pattern-Klassifikation

2. **MCP-Vollständige Implementation**:
   - Standardisierte Tool-Interfaces
   - Context-Bereitstellung für externe LLMs

3. **Skalierung**:
   - Persistente Vektor-Datenbank
   - Distributed Processing für große Datensätze
   - Streaming-Verarbeitung

4. **API & Deployment**:
   - FastAPI REST-API
   - Docker-Containerisierung
   - Cloud-Deployment (AWS, Azure, GCP)

5. **Erweiterte Evaluation**:
   - Ground-Truth-Labels für überwachtes Learning
   - Inter-Rater-Reliability bei manueller Annotation
   - A/B-Testing verschiedener Konfigurationen

**Code-Komponenten:**
- `src/dara_system/api_stub.py` - API-Planung
- Dokumentierte [Unsicherheit]-Marker in relevanten Modulen

---

## Zuordnungstabelle: Code → Thesis-Sektion

| Thesis-Sektion | Code-Komponenten |
|----------------|------------------|
| **1. Einleitung** | `README.md`, `docs/ARCHITECTURE.md` |
| **2. Grundlagen** | `embeddings.py`, `vector_store.py`, `rag_pipeline.py`, `mcp_server.py`, `langgraph_orchestrator.py`, `docs/AGENTS.md` |
| **3. Methodik** | `synchronized_csv_reader.py`, `multi_proband_aggregator.py`, `process_analysis_agent.py`, `docs/DATAFLOW.md` |
| **4. Implementierung** | Alle Module in `src/dara_system/`, `config.py`, `observability.py`, `docs/ARCHITECTURE.md` |
| **5. Experimente** | `experiment_config.py`, `run_experiment.py`, `evaluation.py`, `experiments/`, `cli.py` |
| **6. Ergebnisse** | `results/`, Experiment-Reports, Evaluations-Metriken |
| **7. Diskussion** | Stub-Module, [Unsicherheit]-Marker, Dokumentation |
| **8. Zusammenfassung** | `README.md`, `api_stub.py`, zukünftige TODOs |

---

## Verwendung für die Thesis

### Datensammlung für Ergebnisse

```bash
# Experiment ausführen
dara-cli run experiments/my_experiment.yaml

# Ergebnisse anzeigen
dara-cli show-results --experiment my_experiment

# Vergleich mehrerer Experimente (manuell)
# - Lade evaluation_report.json aus mehreren Experimenten
# - Nutze evaluation.compare_experiments()
```

### Code-Snippets für die Arbeit

Relevante Code-Abschnitte können direkt in die Thesis übernommen werden:
- Pattern-Erkennung-Algorithmen aus `process_analysis_agent.py`
- Aggregations-Logik aus `multi_proband_aggregator.py`
- Experiment-Konfiguration aus `experiment_config.py`

### Grafiken und Visualisierungen

[Unsicherheit] Das System enthält aktuell keine Visualisierungs-Komponenten.

**Empfehlung:**
- Separate Jupyter Notebooks für Visualisierungen
- Nutze `results/` Daten als Input für Plots
- Libraries: matplotlib, seaborn, plotly

---

## Offene Fragen / Unsicherheiten

1. **Embedding-Modell**: Welches Embedding-Modell ist optimal für DaRa-Daten?
2. **Ground Truth**: Wie werden Ground-Truth-Labels für Pattern-Evaluation erstellt?
3. **Schwellenwerte**: Optimale Werte für baseline/peak/anomaly Thresholds?
4. **MCP-Spezifikation**: Welche MCP-Version und -Features sind relevant?
5. **Skalierung**: Ab welcher Datengröße ist Distributed Processing nötig?

---

## Kontakt & Weiterführung

Für Fragen zur Thesis-Integration:
- Konsultiere `docs/ARCHITECTURE.md` für technische Details
- Nutze `dara-cli` für Experiment-Ausführung
- Erweitere `experiments/` für neue Versuchsaufbauten
- Siehe `tests/` für Usage-Beispiele aller Module
