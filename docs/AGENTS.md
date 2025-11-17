# DaRa System - Agents Dokumentation

## Überblick

Agents sind spezialisierte Module, die spezifische Analyseaufgaben autonom durchführen. Das DaRa-System nutzt ein Agent-basiertes Design für maximale Flexibilität und Erweiterbarkeit.

---

## ProcessAnalysisAgent

**Modul:** `process_analysis_agent.py`

**Aufgabe:** Analysiert Prozessphasen, Zustände und Muster in zeitsynchronen DaRa-Daten

### Verantwortlichkeiten

#### Was der Agent TUT:
1. **Phasen-Identifikation**
   - Klassifiziert jeden Zeitpunkt in eine Prozessphase
   - Unterstützte Phasen:
     - `BASELINE`: Grundzustand, niedrige Aktivität
     - `ACTIVE`: Moderate Aktivität
     - `TRANSITION`: Übergangsphase mit signifikanter Änderung
     - `PEAK`: Maximale Aktivität
     - `RECOVERY`: Erholungsphase (zukünftig)
     - `UNKNOWN`: Unklassifiziert

2. **Pattern Recognition**
   - **Ascending Trends**: Kontinuierlich steigende Werte
   - **Descending Trends**: Kontinuierlich fallende Werte
   - **Plateaus**: Konstante Werte über längere Zeit

3. **Textuelle Beschreibungen**
   - Generiert verständliche Beschreibungen für jede Phase
   - Erstellt Zusammenfassungen über gesamte Zeitreihen
   - Formatiert Ergebnisse für Reports

4. **Statistische Auswertung**
   - Berechnet Verteilung von Phasen
   - Aggregiert Metriken über Zeitreihen
   - Confidence-Scores für Klassifikationen

#### Was der Agent NICHT tut:
- ❌ Rohdaten lesen (Aufgabe von `SynchronizedCSVReader`)
- ❌ Probanden-Aggregation (Aufgabe von `MultiProbandAggregator`)
- ❌ Reporting (Aufgabe der Reporter-Agents)
- ❌ Daten-Normalisierung (Aufgabe von `DataNormalizer`)

### Inputs

```python
List[AggregatedTimeSlice]
```

**Struktur von AggregatedTimeSlice:**
```python
{
    "timestamp": int,
    "proband_count": int,
    "statistics": {
        "field_name": {
            "mean": float,
            "median": float,
            "stdev": float,
            "min": float,
            "max": float
        }
    }
}
```

**Parameter:**
- `primary_field`: Hauptfeld für Analyse (default: "value")
- `baseline_threshold`: Schwellwert für Baseline-Phase (0-1, default: 0.3)
- `peak_threshold`: Schwellwert für Peak-Phase (0-1, default: 0.8)
- `transition_window`: Fenstergröße für Transition-Erkennung (default: 5)
- `min_pattern_length`: Minimale Länge für Muster (default: 3)

### Outputs

```python
AnalysisResult
```

**Struktur:**
```python
{
    "time_range": (start_timestamp, end_timestamp),
    "states": [ProcessState, ...],
    "patterns": [ProcessPattern, ...],
    "summary": str,
    "statistics": {
        "total_time_points": int,
        "total_patterns": int,
        "value_mean": float,
        "value_stdev": float,
        "phases_distribution": {
            "baseline": int,
            "active": int,
            "peak": int,
            ...
        }
    }
}
```

**ProcessState:**
```python
{
    "timestamp": int,
    "phase": ProcessPhase,
    "confidence": float (0-1),
    "features": Dict[str, float],
    "description": str
}
```

**ProcessPattern:**
```python
{
    "start_timestamp": int,
    "end_timestamp": int,
    "pattern_type": str,  # "ascending_trend", "descending_trend", "plateau"
    "description": str,
    "confidence": float,
    "features": Dict[str, Any]
}
```

### Konfigurationsbeispiele

#### Konservative Analyse (weniger Phasen-Wechsel):
```python
agent = ProcessAnalysisAgent(
    baseline_threshold=0.2,  # Niedrig
    peak_threshold=0.9,      # Hoch
    min_pattern_length=5     # Längere Muster
)
```

#### Sensitive Analyse (mehr Details):
```python
agent = ProcessAnalysisAgent(
    baseline_threshold=0.4,  # Höher
    peak_threshold=0.7,      # Niedriger
    min_pattern_length=2     # Kürzere Muster
)
```

### Verwendung

```python
from dara_system.process_analysis_agent import ProcessAnalysisAgent

# Initialisierung
agent = ProcessAnalysisAgent(
    baseline_threshold=0.3,
    peak_threshold=0.8
)

# Analyse durchführen
result = agent.analyze_aggregated_slices(
    aggregated_slices=agg_slices,
    primary_field="value"
)

# Ergebnisse verwenden
print(result.summary)

for state in result.states[:5]:  # Erste 5 States
    print(f"{state.timestamp}: {state.phase.value} - {state.description}")

for pattern in result.patterns:
    print(f"Muster: {pattern.pattern_type} ({pattern.description})")
```

### Erweiterung

#### Neue Phase hinzufügen:

1. Erweitere `ProcessPhase` Enum:
```python
class ProcessPhase(Enum):
    # Bestehende...
    CUSTOM_PHASE = "custom_phase"
```

2. Implementiere Klassifikationslogik in `_classify_phase`:
```python
def _classify_phase(self, norm_value, all_values, index):
    # ... bestehende Logik ...

    # Neue Phase
    if <custom_condition>:
        return ProcessPhase.CUSTOM_PHASE, confidence
```

#### Neuer Pattern-Typ:

1. Implementiere Detector-Methode:
```python
def _detect_custom_pattern(self, states, values):
    patterns = []
    # Detection-Logik
    return patterns
```

2. Rufe in `_detect_patterns` auf:
```python
def _detect_patterns(self, states, values):
    patterns = []
    patterns.extend(self._detect_trend(...))
    patterns.extend(self._detect_custom_pattern(states, values))
    return patterns
```

---

## Zukünftige Agents (Strukturell vorbereitet)

### PatternRecognitionAgent

**Status:** Nicht implementiert, Struktur vorbereitet

**Geplante Aufgaben:**
- Komplexe Muster-Erkennung (Zyklen, Periodizitäten)
- Machine Learning-basierte Pattern Discovery
- Cross-Proband-Muster

**Schnittstelle (geplant):**
```python
class PatternRecognitionAgent:
    def recognize_patterns(
        self,
        time_slices: List[TimeSlice],
        pattern_library: Optional[List[Pattern]] = None
    ) -> List[RecognizedPattern]:
        ...
```

### AnomalyDetectionAgent

**Status:** Nicht implementiert, Struktur vorbereitet

**Geplante Aufgaben:**
- Erkennung von Ausreißern
- Statistische Anomalie-Detektion
- Kontextuelle Anomalien (basierend auf historischen Daten)

**Schnittstelle (geplant):**
```python
class AnomalyDetectionAgent:
    def detect_anomalies(
        self,
        aggregated_slices: List[AggregatedTimeSlice],
        threshold: float = 3.0  # Z-Score
    ) -> List[Anomaly]:
        ...
```

### PredictiveAgent

**Status:** Nicht implementiert, Struktur vorbereitet

**Geplante Aufgaben:**
- Vorhersage zukünftiger Prozesszustände
- Trend-Extrapolation
- Probabilistische Prognosen

**Schnittstelle (geplant):**
```python
class PredictiveAgent:
    def predict_future_states(
        self,
        historical_slices: List[AggregatedTimeSlice],
        forecast_horizon: int
    ) -> List[PredictedState]:
        ...
```

---

## Reporter-Agents

Reporter-Agents sind spezialisiert auf Output-Generierung, nicht auf Analyse.

### NotionReporter

**Modul:** `notion_reporter.py`

**Aufgabe:** Schreibt Analyse-Ergebnisse als strukturierte Pages nach Notion

#### Verantwortlichkeiten

**Was der Reporter TUT:**
- Formatiert `AnalysisResult` für Notion
- Erstellt strukturierte Pages (Headings, Listen, Tabellen)
- Optional: Database Entries
- Health-Checks für API-Verbindung

**Was der Reporter NICHT tut:**
- ❌ Datenanalyse
- ❌ Aggregation
- ❌ Pattern Recognition

#### Inputs

- `AnalysisResult` vom ProcessAnalysisAgent
- Optional: `title`, `tags`

#### Outputs

```python
{
    "success": bool,
    "title": str,
    "url": str,  # Notion Page URL
    "blocks_count": int
}
```

#### Konfiguration

Via Umgebungsvariablen:
```bash
export NOTION_API_TOKEN="secret_..."
export NOTION_DATABASE_ID="..."
```

### GDriveReporter

**Modul:** `gdrive_reporter.py`

**Aufgabe:** Erstellt Google Docs und Sheets mit Analyse-Daten

#### Verantwortlichkeiten

**Was der Reporter TUT:**
- Formatiert `AnalysisResult` für Google Docs/Sheets
- Erstellt formatierte Dokumente
- Erstellt Multi-Sheet Spreadsheets
- Service Account / OAuth2 Authentifizierung

**Was der Reporter NICHT tut:**
- ❌ Datenanalyse
- ❌ Aggregation
- ❌ Pattern Recognition

#### Inputs

- `AnalysisResult` vom ProcessAnalysisAgent
- Optional: `title`

#### Outputs (create_doc_report)

```python
{
    "success": bool,
    "title": str,
    "url": str,  # Google Doc URL
    "elements_count": int
}
```

#### Outputs (create_sheet_report)

```python
{
    "success": bool,
    "title": str,
    "url": str,  # Google Sheet URL
    "sheets_count": int
}
```

#### Konfiguration

Via Umgebungsvariablen:
```bash
export GOOGLE_CREDENTIALS_PATH="/path/to/credentials.json"
export GDRIVE_FOLDER_ID="..."
```

---

## Agent-Koordination

Agents werden durch den `LangGraphOrchestrator` koordiniert:

```
CSV Files
   ↓
[SynchronizedCSVReader]
   ↓
TimeSlices
   ↓
[MultiProbandAggregator]
   ↓
AggregatedTimeSlices
   ↓
[ProcessAnalysisAgent] ← Analysiert
   ↓
AnalysisResult
   ↓
[NotionReporter] ← Berichtet
[GDriveReporter] ← Berichtet
```

---

## Best Practices für neue Agents

### 1. Single Responsibility
Jeder Agent hat EINE klar definierte Aufgabe.

### 2. Klare Inputs/Outputs
Definiere Datenstrukturen mit `dataclass` oder `TypedDict`.

### 3. Konfigurierbarkeit
Wichtige Parameter als Constructor-Argumente.

### 4. Logging
Nutze Python `logging` für Transparenz.

### 5. Error Handling
Robuste Fehlerbehandlung mit spezifischen Exceptions.

### 6. Testbarkeit
Schreibe Unit-Tests mit Fixtures.

### 7. Dokumentation
- Docstrings für alle Public Methods
- Beispiele in Docstrings
- Update dieser AGENTS.md-Datei

---

## Siehe auch

- **ARCHITECTURE.md**: Layer-Übersicht
- **DATAFLOW.md**: Datenfluss-Diagramme
- **README.md**: Schnellstart-Beispiele
