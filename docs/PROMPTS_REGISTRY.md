# DaRa System - Prompts Registry

## Überblick

Dieses Dokument mappt die ursprünglichen Aufgaben-Prompts (1-12) zu den implementierten Modulen und dokumentiert deren Status, Versionen und bekannte Limitierungen.

---

## Prompt-zu-Modul Mapping

### Prompt 1: Document Loader

**Ursprünglicher Prompt:**
> "Verantwortlich für das Laden von Dateien (insbesondere CSVs) von lokal oder später erweiterbar von anderen Quellen."

**Implementiert als:** `document_loader.py`

**Status:** ✅ Vollständig implementiert

**Version:** 0.1.0

**Funktionalität:**
- Lädt CSV-Dateien von lokalem Dateisystem
- Validiert Dateipfade
- Liefert Metadaten (Größe, Änderungsdatum)
- Error-Handling für fehlende/ungültige Dateien

**Erweiterbarkeit:**
- Cloud Storage (S3, Google Cloud Storage) vorbereitet
- Datenbankzugriff vorbereitet
- API-Zugriff vorbereitet

**Bekannte Limitierungen:**
- Nur lokale Dateien implementiert
- Cloud-Integrationen sind Platzhalter

**Tests:** `tests/test_document_loader.py` (indirekt via synchronized_csv_reader getestet)

---

### Prompt 2: Embeddings

**Ursprünglicher Prompt:**
> "Schnittstelle, um später Embeddings zu erzeugen (z. B. aus Texten)."

**Implementiert als:** `embeddings.py`

**Status:** ⚠️ Strukturell implementiert, funktional Placeholder

**Version:** 0.1.0

**Funktionalität:**
- Klare API: `get_embeddings(texts: List[str]) -> List[List[float]]`
- `EmbeddingProvider` Basisklasse
- `TextChunker` für lange Texte

**Placeholder-Implementierung:**
- Generiert deterministische Pseudo-Embeddings via Hash
- NICHT semantisch bedeutungsvoll
- Nur für strukturellen Aufbau und Tests

**Zukünftige Integration:**
- OpenAI Embeddings
- Sentence Transformers
- Custom Fine-tuned Modelle

**Bekannte Limitierungen:**
- [Unsicherheit] Echte Embeddings erfordern externe Modelle
- Placeholder-Embeddings sind nicht semantisch

**Tests:** Unit-Tests vorhanden für Struktur

---

### Prompt 3: Vector Store

**Ursprünglicher Prompt:**
> "Abstraktion für einen Vektor-Speicher (z. B. für spätere RAG-Nutzung)."

**Implementiert als:** `vector_store.py`

**Status:** ✅ Vollständig implementiert (In-Memory)

**Version:** 0.1.0

**Funktionalität:**
- In-Memory Vector Store
- Cosine Similarity Search
- Metadaten-Filterung
- CRUD-Operationen (Add, Get, Delete, Clear)

**Bekannte Limitierungen:**
- [Unsicherheit] In-Memory = keine Persistenz
- [Unsicherheit] Nicht geeignet für sehr große Datenmengen (>1M Vektoren)

**Zukünftige Integration:**
- Pinecone
- Weaviate
- ChromaDB
- FAISS (für lokale Persistenz)

**Tests:** `tests/test_vector_store.py` (vollständig)

---

### Prompt 4: RAG Pipeline

**Ursprünglicher Prompt:**
> "Definiere eine RAG-Pipeline-Schnittstelle, die später mit echten LLMs integriert werden kann."

**Implementiert als:** `rag_pipeline.py`

**Status:** ⚠️ Strukturell implementiert, LLM-Integration Placeholder

**Version:** 0.1.0

**Funktionalität:**
- Query-to-Embedding-Konversion
- Vector Store Retrieval
- Top-K Similarity Search mit Threshold
- Dokumenten-Indexierung

**Placeholder-Implementierung:**
- LLM-Generierung ist Placeholder
- Gibt strukturierte Kontext-Informationen zurück

**Zukünftige Integration:**
- LangChain LLM Integration
- OpenAI GPT
- Anthropic Claude
- Custom Prompt Templates

**Bekannte Limitierungen:**
- [Unsicherheit] LLM-Generierung nicht implementiert
- Placeholder-Antworten sind nicht intelligent

**Tests:** Grundlegende Tests vorhanden

---

### Prompt 5: MCP Server

**Ursprünglicher Prompt:**
> "Lege die Grundstruktur für einen MCP-kompatiblen Server an."

**Implementiert als:** `mcp_server.py`

**Status:** ⚠️ Strukturell vorbereitet, echte MCP-Integration ausstehend

**Version:** 0.1.0

**Funktionalität:**
- Tool-Registry
- Tool-Registrierung und -Aufruf
- JSON Schema Export
- Singleton ToolRegistry

**Bekannte Limitierungen:**
- [Unsicherheit] Echtes MCP SDK nicht integriert
- Aktuell nur lokale Tool-Verwaltung

**Zukünftige Integration:**
- Offizielles MCP SDK
- Network-basierte Tool-Kommunikation
- Multi-Server-Koordination

**Tests:** Grundlegende Tests für Tool-Registry

---

### Prompt 6: DaRa Processor

**Ursprünglicher Prompt:**
> "Enthält allgemeine Hilfsfunktionen für DaRa-spezifische Daten: Normalisierung, Label-/Klassen-Handling, ggf. Hilfsfunktionen für Zeitachsen."

**Implementiert als:** `dara_processor.py`

**Status:** ✅ Vollständig implementiert

**Version:** 0.1.0

**Funktionalität:**
- `DataNormalizer`: Numerisch & kategorial
- `LabelHandler`: Encoding/Decoding
- `TimeAxisHelper`: Windows, Aggregation
- `TimeSlice` Datenstruktur

**Tests:** `tests/test_dara_processor.py` (vollständig)

**Bekannte Limitierungen:** Keine

---

### Prompt 7: Synchronized CSV Reader

**Ursprünglicher Prompt:**
> "Mehrere CSV-Dateien parallel so zu lesen, dass Zeile N jeweils denselben Zeitpunkt abbildet."

**Implementiert als:** `synchronized_csv_reader.py`

**Status:** ✅ Vollständig implementiert

**Version:** 0.1.0

**Funktionalität:**
- Zeitsynchrones Multi-File-Reading
- Batch-Reading
- Fehlerbehandlung (unterschiedliche Längen, fehlerhafte Zeilen)
- Fill-Missing und Skip-Errors Strategien

**Tests:** `tests/test_synchronized_csv_reader.py` (vollständig)

**Bekannte Limitierungen:** Keine

---

### Prompt 8: Multi-Proband Aggregator

**Ursprünglicher Prompt:**
> "Aggregation der synchron gelesenen Daten mehrerer Probanden pro Zeitpunkt."

**Implementiert als:** `multi_proband_aggregator.py`

**Status:** ✅ Vollständig implementiert

**Version:** 0.1.0

**Funktionalität:**
- TimeSlice-Aggregation
- Statistische Metriken (Mean, Median, Stdev, Min, Max)
- Zeitfenster-Aggregation
- Custom Aggregation Functions

**Tests:** `tests/test_multi_proband_aggregator.py` (vollständig)

**Bekannte Limitierungen:** Keine

---

### Prompt 9: Process Analysis Agent

**Ursprünglicher Prompt:**
> "Nimmt Zeit-Slices oder aggregierte Zeitfenster entgegen, identifiziert Prozessphasen, Zustände oder Muster, formuliert textuelle Beschreibungen."

**Implementiert als:** `process_analysis_agent.py`

**Status:** ✅ Vollständig implementiert

**Version:** 0.1.0

**Funktionalität:**
- Phasen-Identifikation (Baseline, Active, Peak, Transition, Recovery)
- Pattern Recognition (Trends, Plateaus)
- Textuelle Beschreibungen
- Konfigurierbale Schwellwerte

**Tests:** `tests/test_process_analysis_agent.py` (vollständig)

**Bekannte Limitierungen:**
- [Unsicherheit] Pattern-Erkennung verwendet einfache Heuristiken
- Machine Learning-basierte Pattern Discovery könnte genauer sein

---

### Prompt 10: Notion Reporter

**Ursprünglicher Prompt:**
> "Ergebnisse (z. B. aus process_analysis_agent) nach Notion schreiben."

**Implementiert als:** `notion_reporter.py`

**Status:** ✅ Strukturell vollständig, API-Integration Placeholder

**Version:** 0.1.0

**Funktionalität:**
- Formatierung für Notion
- Simulation-Modus ohne API-Token
- Health-Status-Checks
- Konfiguration via Umgebungsvariablen

**Bekannte Limitierungen:**
- [Unsicherheit] Echte Notion API Calls nicht getestet (benötigt Token)
- Aktuell Simulation-Modus

**Zukünftige Integration:**
- Echte Notion SDK Integration
- Automatisierte Tests mit Mock-API

**Tests:** Grundlegende Tests vorhanden

---

### Prompt 11: Google Drive Reporter

**Ursprünglicher Prompt:**
> "Ergebnisse nach Google Drive schreiben (Docs/Sheets o. Ä.)."

**Implementiert als:** `gdrive_reporter.py`

**Status:** ✅ Strukturell vollständig, API-Integration Placeholder

**Version:** 0.1.0

**Funktionalität:**
- Google Doc Formatierung
- Google Sheet Multi-Tab
- Simulation-Modus ohne Credentials
- Health-Status-Checks

**Bekannte Limitierungen:**
- [Unsicherheit] Echte Google API Calls nicht getestet (benötigt Credentials)
- Aktuell Simulation-Modus

**Zukünftige Integration:**
- Service Account Credentials
- OAuth2 Flow
- Automatisierte Tests mit Mock-API

**Tests:** Grundlegende Tests vorhanden

---

### Prompt 12: LangGraph Orchestrator

**Ursprünglicher Prompt:**
> "Flusssteuerung von SynchronizedCSVReader, MultiProbandAggregator, ProcessAnalysisAgent, Reporting Agents. Definiere States/Nodes für jeden Schritt, Übergänge und Fehlerpfade."

**Implementiert als:** `langgraph_orchestrator.py`

**Status:** ✅ Vollständig implementiert

**Version:** 0.1.0

**Funktionalität:**
- LangGraph State Machine
- 5 Nodes: read_csv, aggregate, analyze, report_notion, report_gdrive
- Flexible Node-Verkettung
- Error-Tracking
- `run_pipeline()` End-to-End-Funktion

**Tests:** Integration-Tests (indirekt via Component-Tests)

**Bekannte Limitierungen:** Keine

---

## Status-Übersicht

| Prompt | Modul | Status | Tests |
|--------|-------|--------|-------|
| 1 | document_loader | ✅ | ✅ |
| 2 | embeddings | ⚠️ Placeholder | ✅ |
| 3 | vector_store | ✅ | ✅ |
| 4 | rag_pipeline | ⚠️ LLM Placeholder | ⚠️ |
| 5 | mcp_server | ⚠️ SDK Placeholder | ⚠️ |
| 6 | dara_processor | ✅ | ✅ |
| 7 | synchronized_csv_reader | ✅ | ✅ |
| 8 | multi_proband_aggregator | ✅ | ✅ |
| 9 | process_analysis_agent | ✅ | ✅ |
| 10 | notion_reporter | ⚠️ API Placeholder | ⚠️ |
| 11 | gdrive_reporter | ⚠️ API Placeholder | ⚠️ |
| 12 | langgraph_orchestrator | ✅ | ⚠️ |

**Legende:**
- ✅ Vollständig implementiert/getestet
- ⚠️ Strukturell implementiert, funktional Placeholder/teilweise

---

## Unsicherheiten und Review-Bedarf

Folgende Komponenten wurden als **strukturell vorbereitet** markiert, benötigen aber später echte Integrationen:

### Embeddings (Prompt 2)
- **Unsicherheit:** Placeholder-Embeddings sind nicht semantisch
- **Lösung:** Integration mit echtem Embedding-Modell (Sentence Transformers, OpenAI)
- **Branch:** Könnte auf `review_required/embeddings` entwickelt werden

### RAG Pipeline (Prompt 4)
- **Unsicherheit:** LLM-Generierung nicht implementiert
- **Lösung:** LangChain LLM Integration
- **Branch:** Könnte auf `review_required/rag_llm` entwickelt werden

### MCP Server (Prompt 5)
- **Unsicherheit:** Echtes MCP SDK nicht integriert
- **Lösung:** Offizielles MCP SDK einbinden
- **Branch:** Könnte auf `review_required/mcp_sdk` entwickelt werden

### Reporter (Prompts 10, 11)
- **Unsicherheit:** Echte API Calls nicht getestet (benötigen Credentials)
- **Lösung:** Integration-Tests mit echten APIs oder Mock-Services
- **Branch:** Könnte auf `review_required/reporters_integration` entwickelt werden

---

## Versionshistorie

### Version 0.1.0 (Initial Release)
- Alle 12 Prompts strukturell implementiert
- Kernfunktionalität vollständig
- Placeholder für externe Integrationen
- Umfassende Tests für Core-Module

### Geplant für Version 0.2.0
- Echte Embedding-Modelle
- LLM-Integration in RAG Pipeline
- Vollständige API-Integration für Reporter
- MCP SDK Integration

---

## Siehe auch

- **ARCHITECTURE.md**: Architektur-Details
- **AGENTS.md**: Agent-Dokumentation
- **DATAFLOW.md**: Datenfluss-Beschreibung
