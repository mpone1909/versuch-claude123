# DaRa System - Datenfluss

## Überblick

Dieses Dokument beschreibt den Fluss von Daten durch das DaRa-System, von rohen CSV-Dateien bis zu finalen Reports in Notion und Google Drive.

---

## End-to-End Datenfluss

### Schritt 1: CSV-Dateien (Input)

**Quelle:** Lokales Dateisystem (oder zukünftig: Cloud Storage)

**Format:** Mehrere CSV-Dateien, eine pro Proband

**Beispiel-Dateien:**
- `proband_001.csv`
- `proband_002.csv`
- `proband_003.csv`

**Struktur jeder Datei:**
```csv
timestamp,value,status,score,other_metric
0,10.5,active,5.0,100
1,12.3,active,6.5,105
2,11.8,passive,5.8,102
3,15.2,active,8.0,110
...
```

**Wichtige Eigenschaft:**
- Zeile N in **allen** Dateien repräsentiert denselben Zeitpunkt
- Beispiel: Zeile 5 in allen Dateien = Zeitpunkt 5

---

### Schritt 2: Zeitsynchrones Lesen

**Modul:** `SynchronizedCSVReader`

**Prozess:**
1. Öffnet alle CSV-Dateien parallel
2. Liest Zeile N aus jeder Datei
3. Kombiniert zu einem `TimeSlice`
4. Wiederholt für alle Zeilen

**Output:** Iterator von `TimeSlice`-Objekten

**TimeSlice-Struktur:**
```python
TimeSlice {
    timestamp: 0,
    data: {
        "proband_001": {
            "timestamp": "0",
            "value": "10.5",
            "status": "active",
            "score": "5.0",
            "other_metric": "100"
        },
        "proband_002": {
            "timestamp": "0",
            "value": "9.8",
            "status": "active",
            "score": "4.5",
            "other_metric": "98"
        },
        "proband_003": {
            "timestamp": "0",
            "value": "11.2",
            "status": "passive",
            "score": "5.5",
            "other_metric": "103"
        }
    },
    metadata: {
        "source": "synchronized_read"
    }
}
```

**Fehlerbehandlung:**
- Unterschiedliche Dateilängen: Kürzere Dateien werden mit `None` gefüllt (wenn `fill_missing=True`)
- Fehlerhafte Zeilen: Werden übersprungen (wenn `skip_errors=True`)
- Fehlende Dateien: Exception wird geworfen

---

### Schritt 3: Multi-Proband-Aggregation

**Modul:** `MultiProbandAggregator`

**Prozess:**
1. Nimmt einen `TimeSlice` entgegen
2. Sammelt numerische Werte pro Feld über alle Probanden
3. Berechnet Statistiken (Mean, Median, Std, Min, Max)
4. Gibt `AggregatedTimeSlice` zurück

**Transformation:**

**Input (TimeSlice):**
```python
{
    "proband_001": {"value": "10.5", "score": "5.0"},
    "proband_002": {"value": "9.8", "score": "4.5"},
    "proband_003": {"value": "11.2", "score": "5.5"}
}
```

**Output (AggregatedTimeSlice):**
```python
AggregatedTimeSlice {
    timestamp: 0,
    proband_count: 3,
    statistics: {
        "value": {
            "count": 3,
            "mean": 10.5,      # (10.5 + 9.8 + 11.2) / 3
            "median": 10.5,
            "stdev": 0.7,
            "min": 9.8,
            "max": 11.2
        },
        "score": {
            "count": 3,
            "mean": 5.0,       # (5.0 + 4.5 + 5.5) / 3
            "median": 5.0,
            "stdev": 0.5,
            "min": 4.5,
            "max": 5.5
        }
    },
    metadata: {
        "aggregation_method": "standard",
        "total_probands": 3,
        "valid_probands": 3
    }
}
```

**Konfigurierbare Aggregationen:**
- Standard: Mean, Median, Stdev, Min, Max
- Custom: Beliebige Funktionen via `CustomAggregator`

---

### Schritt 4: Prozessanalyse

**Modul:** `ProcessAnalysisAgent`

**Prozess:**
1. Nimmt Liste von `AggregatedTimeSlice`-Objekten
2. Extrahiert primäres Feld (z.B. "value")
3. Normalisiert Werte auf [0, 1]
4. Klassifiziert jeden Zeitpunkt in Phase
5. Erkennt Muster über Zeitreihe
6. Generiert Summary

**Transformation:**

**Input:** Liste von `AggregatedTimeSlice`

**Zwischenschritt - Normalisierung:**
```python
# Original Werte:     [10.5, 12.3, 11.8, 15.2, ...]
# Min: 9.8, Max: 15.2
# Normalisierte:      [0.13, 0.46, 0.37, 1.0, ...]
```

**Phasen-Klassifikation:**
```python
# Normalisierter Wert → Phase
0.13 → BASELINE     (< 0.3)
0.46 → ACTIVE       (0.3 - 0.8)
0.37 → ACTIVE       (0.3 - 0.8)
1.0  → PEAK         (> 0.8)
```

**Output (AnalysisResult):**
```python
AnalysisResult {
    time_range: (0, 100),
    states: [
        ProcessState {
            timestamp: 0,
            phase: BASELINE,
            confidence: 0.8,
            features: {"mean": 10.5, "stdev": 0.7, ...},
            description: "Baseline-Phase (Wert: 10.50, gering aktiv)"
        },
        ProcessState {
            timestamp: 1,
            phase: ACTIVE,
            confidence: 0.7,
            features: {"mean": 12.3, "stdev": 0.8, ...},
            description: "Aktive Phase (Wert: 12.30, moderate Aktivität)"
        },
        ...
    ],
    patterns: [
        ProcessPattern {
            start_timestamp: 5,
            end_timestamp: 15,
            pattern_type: "ascending_trend",
            description: "Aufsteigender Trend über 10 Zeitpunkte",
            confidence: 0.8,
            features: {
                "start_value": 12.0,
                "end_value": 18.5,
                "change": 6.5
            }
        },
        ...
    ],
    summary: "Prozessanalyse über 100 Zeitpunkte:\n- Dominante Phase: active (60 Zeitpunkte)\n- Erkannte Muster: 3\n...",
    statistics: {
        "total_time_points": 100,
        "total_patterns": 3,
        "value_mean": 14.2,
        "value_stdev": 2.5,
        "phases_distribution": {
            "baseline": 20,
            "active": 60,
            "peak": 15,
            "transition": 5
        }
    }
}
```

**Pattern-Erkennung:**

Beispiel - Aufsteigender Trend:
```
Zeitpunkte: [0,  1,  2,  3,  4,  5,  6,  7]
Werte:      [10, 11, 12, 13, 14, 15, 16, 17]
                  ↑   ↑   ↑   ↑   ↑   ↑   ↑
            Jeder Wert > vorheriger → Trend erkannt
```

Beispiel - Plateau:
```
Zeitpunkte: [10, 11, 12, 13, 14, 15, 16, 17]
Werte:      [20, 20, 20, 21, 20, 20, 20, 20]
                  ↑   ↑   ↑   ↑   ↑   ↑   ↑
            Werte ~konstant → Plateau erkannt
```

---

### Schritt 5: Reporting

#### 5a: Notion Reporter

**Modul:** `NotionReporter`

**Prozess:**
1. Nimmt `AnalysisResult`
2. Formatiert in Notion-Blöcke
3. Erstellt Page via Notion API

**Formatierung:**
```python
AnalysisResult → Notion Blocks

Summary → Heading + Paragraph
Statistics → Heading + Bulleted List
States (Sample) → Heading + Numbered List
Patterns → Heading + Bulleted List
```

**Output:**
```python
{
    "success": True,
    "title": "DaRa Analyse - 2024-11-17",
    "url": "https://notion.so/page-id",
    "blocks_count": 12
}
```

**Beispiel Notion-Page:**
```
# DaRa Prozessanalyse Report

Erstellt: 2024-11-17 14:30:00

## Zusammenfassung
Prozessanalyse über 100 Zeitpunkte:
- Dominante Phase: active (60 Zeitpunkte)
- Erkannte Muster: 3
- Wertebereich: 9.80 - 18.50

## Statistiken
• total_time_points: 100
• total_patterns: 3
• value_mean: 14.2
...

## Erkannte Muster (3)
• ascending_trend (t=5-15): Aufsteigender Trend über 10 Zeitpunkte (Confidence: 0.80)
...
```

#### 5b: Google Drive Reporter

**Modul:** `GDriveReporter`

**Prozess (Google Doc):**
1. Nimmt `AnalysisResult`
2. Formatiert in Doc-Elemente
3. Erstellt Doc via Google Docs API

**Prozess (Google Sheet):**
1. Nimmt `AnalysisResult`
2. Konvertiert zu tabellarischem Format
3. Erstellt Multi-Sheet Spreadsheet

**Sheet-Struktur:**
```
Sheet 1: "Process States"
| Timestamp | Phase    | Confidence | Description                          |
|-----------|----------|------------|--------------------------------------|
| 0         | baseline | 0.8        | Baseline-Phase (Wert: 10.50, ...)   |
| 1         | active   | 0.7        | Aktive Phase (Wert: 12.30, ...)     |
...

Sheet 2: "Patterns"
| Type             | Start | End | Description                      | Confidence |
|------------------|-------|-----|----------------------------------|------------|
| ascending_trend  | 5     | 15  | Aufsteigender Trend über 10 ...  | 0.8        |
...

Sheet 3: "Statistics"
| Metric                  | Value |
|-------------------------|-------|
| total_time_points       | 100   |
| value_mean              | 14.2  |
...
```

**Output:**
```python
{
    "success": True,
    "title": "DaRa Daten - 2024-11-17",
    "url": "https://docs.google.com/spreadsheets/d/...",
    "sheets_count": 3
}
```

---

## Orchestrierung mit LangGraph

### Workflow State Machine

**States:**
```python
WorkflowState {
    # Input
    csv_file_paths: ["p1.csv", "p2.csv", "p3.csv"],
    proband_ids: ["P1", "P2", "P3"],

    # Intermediate
    time_slices: [TimeSlice, ...],           # Nach read_csv
    aggregated_slices: [AggregatedTimeSlice, ...],  # Nach aggregate
    analysis_result: AnalysisResult,         # Nach analyze

    # Output
    notion_result: {...},                    # Nach report_notion
    gdrive_result: {...},                    # Nach report_gdrive

    # Meta
    status: "completed",
    errors: [],
    step_count: 5
}
```

**Node-Ablauf:**
```
[read_csv]
    ↓
State: time_slices gefüllt
    ↓
[aggregate]
    ↓
State: aggregated_slices gefüllt
    ↓
[analyze]
    ↓
State: analysis_result gefüllt
    ↓
[report_notion] (optional)
    ↓
State: notion_result gefüllt
    ↓
[report_gdrive] (optional)
    ↓
State: gdrive_result gefüllt
    ↓
[END]
```

---

## Daten-Transformationen im Überblick

```
CSV Zeilen (Strings)
    ↓ [DocumentLoader / SynchronizedCSVReader]
TimeSlice (Dict[proband_id, Dict[field, str]])
    ↓ [MultiProbandAggregator + DataNormalizer]
AggregatedTimeSlice (Dict[field, Statistics])
    ↓ [ProcessAnalysisAgent]
AnalysisResult (States, Patterns, Summary)
    ↓ [NotionReporter / GDriveReporter]
Externe Dokumente (Notion Page / Google Doc/Sheet)
```

---

## Datenvolumen und Performance

### Beispiel-Szenario

**Input:**
- 10 Probanden
- 1000 Zeitpunkte
- 5 numerische Felder pro Zeile

**Zwischenschritte:**
- TimeSlices: 1000 Objekte
- AggregatedTimeSlices: 1000 Objekte
- ProcessStates: 1000 Objekte
- ProcessPatterns: ~10-20 Objekte (abhängig von Daten)

**Memory-Nutzung (grob):**
- TimeSlices: ~5 MB
- AggregatedTimeSlices: ~2 MB
- AnalysisResult: ~1 MB

**Performance:**
- CSV-Reading: O(n) mit n = Anzahl Zeilen
- Aggregation: O(n * p) mit p = Anzahl Probanden
- Analysis: O(n) für Phasen, O(n²) für Patterns (kann optimiert werden)

---

## Fehlerbehandlung im Datenfluss

### Fehlertypen und Handling

1. **CSV-Read-Fehler:**
   - Fehlende Datei → Exception, Pipeline stoppt
   - Fehlerhafte Zeile → Skip (wenn `skip_errors=True`)
   - Unterschiedliche Längen → Auffüllen mit `None` (wenn `fill_missing=True`)

2. **Aggregations-Fehler:**
   - Zu wenige Probanden → Exception oder Skip (konfigurierbar)
   - Nicht-numerische Werte → Werden ignoriert

3. **Analyse-Fehler:**
   - Keine Daten → Exception
   - Fehlendes Feld → Exception mit klarer Fehlermeldung

4. **Reporting-Fehler:**
   - API-Fehler → Logged, aber Pipeline continues (Reporting ist optional)
   - Keine Credentials → Simulation-Modus

---

## Siehe auch

- **ARCHITECTURE.md**: Layer-Struktur
- **AGENTS.md**: Agent-Details
- **README.md**: Code-Beispiele
