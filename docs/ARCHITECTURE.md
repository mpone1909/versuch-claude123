# DaRa System - Architektur

## Überblick

Das DaRa Multi-Agent RAG/MCP-System ist in **modularen Layern** aufgebaut, die klare Verantwortlichkeiten und Schnittstellen haben. Die Architektur folgt dem Prinzip der **Separation of Concerns** und ermöglicht einfache Erweiterbarkeit.

## Architektur-Layer

### Layer 1: Core Infrastructure

**Zweck:** Grundlegende Infrastruktur für RAG und MCP

**Module:**
- `document_loader.py`: Lädt Dokumente (aktuell CSV, erweiterbar)
- `embeddings.py`: Generiert Embeddings (aktuell Placeholder, später echte Modelle)
- `vector_store.py`: Speichert und durchsucht Vektoren (In-Memory, erweiterbar zu Vektordatenbanken)
- `rag_pipeline.py`: RAG-Pipeline für Retrieval + (zukünftige) LLM-Integration
- `mcp_server.py`: MCP-Server-Grundstruktur für Tool-Registry

**Charakteristiken:**
- Generisch und wiederverwendbar
- Nicht DaRa-spezifisch
- Klar definierte APIs
- Erweiterbar für verschiedene Backend-Implementierungen

**Abhängigkeiten:**
- Nur Standard-Libraries und etablierte Packages (numpy, pandas)
- Keine Abhängigkeiten zu höheren Layern

---

### Layer 2: DaRa Data Processing

**Zweck:** DaRa-spezifische Datenverarbeitung

**Module:**
- `dara_processor.py`: Hilfsfunktionen (Normalisierung, Labels, Zeitachsen)
- `synchronized_csv_reader.py`: Zeitsynchrones Lesen mehrerer CSV-Dateien
- `multi_proband_aggregator.py`: Aggregation von Multi-Proband-Daten

**Charakteristiken:**
- Fokus auf DaRa-Datenformat (zeitsynchrone CSVs)
- Robuste Fehlerbehandlung (fehlende Zeilen, unterschiedliche Längen)
- Batch-Processing für Effizienz
- Statistische Aggregationsmethoden

**Abhängigkeiten:**
- Layer 1 (Core Infrastructure) für grundlegende Datenstrukturen
- `TimeSlice`-Datenstruktur als zentrale Abstraktion

**Datenstrukturen:**
```
TimeSlice:
  - timestamp: int
  - data: Dict[proband_id -> proband_data]
  - metadata: Dict

AggregatedTimeSlice:
  - timestamp: int
  - proband_count: int
  - statistics: Dict[field -> {mean, std, min, max, ...}]
  - metadata: Dict
```

---

### Layer 3: Analysis Agents

**Zweck:** Intelligente Analyse und Pattern Recognition

**Module:**
- `process_analysis_agent.py`: Analysiert Prozessphasen und Muster

**Charakteristiken:**
- Identifiziert Prozessphasen (Baseline, Active, Peak, Transition, Recovery)
- Erkennt Muster (aufsteigende/absteigende Trends, Plateaus)
- Generiert textuelle Beschreibungen
- Konfigurierbare Schwellwerte und Parameter

**Eingaben:**
- `List[AggregatedTimeSlice]` von Layer 2

**Ausgaben:**
- `AnalysisResult`:
  - `states`: Liste von `ProcessState`
  - `patterns`: Liste von `ProcessPattern`
  - `summary`: Textuelle Zusammenfassung
  - `statistics`: Aggregierte Statistiken

**Erweiterbarkeit:**
- Neue Phasen können durch Erweiterung von `ProcessPhase` Enum hinzugefügt werden
- Custom Pattern-Detector können als separate Methoden implementiert werden
- Agent-Basisklasse ermöglicht mehrere spezialisierte Agents

**Zukünftige Agents (vorbereitet):**
- `PatternRecognitionAgent`: Spezialisiert auf komplexe Muster
- `AnomalyDetectionAgent`: Erkennt Ausreißer und Anomalien
- `PredictiveAgent`: Vorhersagen basierend auf historischen Daten

---

### Layer 4: Reporting Agents

**Zweck:** Export von Analyseergebnissen zu externen Systemen

**Module:**
- `notion_reporter.py`: Schreibt nach Notion
- `gdrive_reporter.py`: Erstellt Google Docs/Sheets

**Charakteristiken:**
- Formatierung von `AnalysisResult` für verschiedene Zielformate
- Simulation-Modus ohne API-Credentials
- Robustes Error-Handling (Rate Limits, Network-Fehler)
- Konfiguration über Umgebungsvariablen

**Sicherheit:**
- API-Keys werden NIEMALS im Code gespeichert
- Nur über Umgebungsvariablen geladen
- Health-Status-Checks vor API-Operationen

**Notion-Integration:**
- Strukturierte Pages mit Headings, Listen, Tabellen
- Optional: Database Entries
- Format: Markdown-ähnlich

**Google Drive-Integration:**
- Google Docs: Formatierte Reports
- Google Sheets: Tabellarische Daten (Multi-Sheet)
- Authentifizierung via Service Account oder OAuth2

---

### Layer 5: Orchestration

**Zweck:** End-to-End-Workflow-Koordination

**Module:**
- `langgraph_orchestrator.py`: LangGraph-basierte State Machine

**Charakteristiken:**
- Koordiniert alle Layer in kohärentem Workflow
- State-basierte Ausführung mit LangGraph
- Flexible Node-Verkettung basierend auf Konfiguration
- Fehler-Tracking und Recovery

**Workflow-Nodes:**
1. **read_csv**: Liest CSV-Dateien zeitsynchron (Layer 2)
2. **aggregate**: Aggregiert Multi-Proband-Daten (Layer 2)
3. **analyze**: Führt Prozessanalyse durch (Layer 3)
4. **report_notion**: Optional, schreibt nach Notion (Layer 4)
5. **report_gdrive**: Optional, schreibt nach Google Drive (Layer 4)

**Konfiguration:**
```python
OrchestratorConfig:
  - batch_size: Optional[int]
  - numeric_fields: Optional[List[str]]
  - primary_field: str
  - baseline_threshold: float
  - peak_threshold: float
  - create_notion_report: bool
  - create_gdrive_doc: bool
  - create_gdrive_sheet: bool
```

**State:**
```python
WorkflowState:
  - csv_file_paths: List[str]          # Input
  - time_slices: List[TimeSlice]       # After read_csv
  - aggregated_slices: List[...]       # After aggregate
  - analysis_result: AnalysisResult    # After analyze
  - notion_result: Dict                # After report_notion
  - gdrive_result: Dict                # After report_gdrive
  - status: str
  - errors: List[str]
```

---

## Datenfluss

```
CSV-Dateien (Proband 1, 2, 3, ...)
    ↓
[Layer 2: SynchronizedCSVReader]
    ↓
TimeSlices (zeitsynchron)
    ↓
[Layer 2: MultiProbandAggregator]
    ↓
AggregatedTimeSlices (mit Statistiken)
    ↓
[Layer 3: ProcessAnalysisAgent]
    ↓
AnalysisResult (States, Patterns, Summary)
    ↓
[Layer 4: Reporter] → Notion & Google Drive
```

## Design-Prinzipien

### 1. Modularität
- Jedes Modul hat eine klar definierte Verantwortung
- Keine zirkulären Abhängigkeiten
- Layer dürfen nur von niedrigeren Layern abhängen

### 2. Erweiterbarkeit
- Neue Agents können einfach hinzugefügt werden
- Neue Reporter durch Implementierung der Reporter-Schnittstelle
- Custom Aggregationsfunktionen via `CustomAggregator`

### 3. Testbarkeit
- Jedes Modul hat dedizierte Unit-Tests
- Fixtures für Test-Daten
- Mocking für externe APIs

### 4. Konfigurierbarkeit
- Schwellwerte, Parameter über Config-Objekte
- Umgebungsvariablen für Secrets
- Keine Hardcoded-Werte

### 5. Fehlertoleranz
- Graceful Degradation (z.B. Simulation-Modus ohne API-Keys)
- Fehler-Logging auf allen Ebenen
- Skip-/Fallback-Strategien

## Erweiterungspunkte

### Neue Datenquellen
1. Implementiere neue Methode in `DocumentLoader`
2. Behalte `List[Dict]` Return-Format bei
3. Füge Tests hinzu

### Neue Analyse-Methoden
1. Erweitere `ProcessAnalysisAgent` oder erstelle neuen Agent
2. Definiere neue `ProcessPhase` oder `PatternType`
3. Implementiere Detection-Logik
4. Integriere in Orchestrator

### Neue Reporting-Ziele
1. Erstelle neuen Reporter (z.B. `SlackReporter`)
2. Implementiere `create_report(AnalysisResult) -> Dict`
3. Füge Health-Status-Check hinzu
4. Registriere in Orchestrator-Config

### RAG/MCP-Integration
1. Ersetze Placeholder-Embeddings durch echtes Modell
2. Integriere Vector Store mit echter Vektordatenbank
3. Verbinde RAG Pipeline mit LLM
4. Erweitere MCP Server mit echtem MCP SDK

## Technologie-Stack

- **Core**: Python 3.9+
- **Orchestrierung**: LangGraph
- **Datenverarbeitung**: pandas, numpy
- **Testing**: pytest, pytest-cov
- **Typing**: pydantic (für Type-Safe-Configs)
- **APIs**: requests, google-api-python-client
- **Zukünftig**:
  - Embedding-Modelle (Sentence Transformers, OpenAI)
  - Vektordatenbanken (Pinecone, ChromaDB, Weaviate)
  - LLMs (via LangChain)

## Performance-Überlegungen

### Aktuell
- In-Memory-Verarbeitung (geeignet für kleine bis mittlere Datensätze)
- Batch-Reading für CSV-Dateien
- Einfache Python-Datenstrukturen

### Skalierung (zukünftig)
- Streaming-Processing für sehr große Dateien
- Persistente Vector Stores
- Distributed Processing (Dask, Ray)
- Caching-Layer für Embeddings

## Sicherheitsaspekte

1. **API-Keys**: Nur via Umgebungsvariablen
2. **Datenvalidierung**: Input-Validierung auf allen Ebenen
3. **Error-Messages**: Keine sensiblen Informationen in Logs
4. **Testing**: Keine echten Credentials in Tests (Mocking)

## Limitierungen

### Bekannte Einschränkungen (Version 0.1.0)
1. Embeddings sind Placeholder (deterministisch, nicht semantisch)
2. Vector Store ist In-Memory (keine Persistenz)
3. RAG Pipeline ohne echten LLM
4. MCP Server ohne vollständige SDK-Integration
5. Reporter-Simulation ohne echte API-Calls (wenn keine Credentials)

Diese Limitierungen sind bewusst als strukturelle Vorbereitung gewählt, um spätere Integration zu erleichtern.
