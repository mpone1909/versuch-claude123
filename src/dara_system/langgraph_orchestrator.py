"""
LangGraph Orchestrator Module

Orchestriert den gesamten DaRa-Analyse-Workflow mit LangGraph.
Koordiniert Reader, Aggregator, Agents und Reporter in einer State Machine.
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from pathlib import Path
import logging
from dataclasses import dataclass, asdict

# LangGraph Imports
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

# Interne Imports
from .synchronized_csv_reader import SynchronizedCSVReader
from .multi_proband_aggregator import MultiProbandAggregator, AggregatedTimeSlice
from .process_analysis_agent import ProcessAnalysisAgent, AnalysisResult
from .notion_reporter import NotionReporter
from .gdrive_reporter import GDriveReporter
from .dara_processor import TimeSlice

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State für den LangGraph Workflow."""
    # Input
    csv_file_paths: List[str]
    proband_ids: Optional[List[str]]

    # Intermediate Results
    time_slices: Optional[List[TimeSlice]]
    aggregated_slices: Optional[List[AggregatedTimeSlice]]
    analysis_result: Optional[AnalysisResult]

    # Output
    notion_result: Optional[Dict[str, Any]]
    gdrive_result: Optional[Dict[str, Any]]

    # Metadata
    status: str
    errors: List[str]
    step_count: int


@dataclass
class OrchestratorConfig:
    """Konfiguration für den Orchestrator."""
    # Reader Config
    batch_size: Optional[int] = None
    skip_errors: bool = True
    fill_missing: bool = True

    # Aggregator Config
    numeric_fields: Optional[List[str]] = None
    min_valid_probands: int = 1

    # Analysis Config
    primary_field: str = "value"
    baseline_threshold: float = 0.3
    peak_threshold: float = 0.8

    # Reporting Config
    create_notion_report: bool = False
    create_gdrive_doc: bool = False
    create_gdrive_sheet: bool = False
    report_title: Optional[str] = None


class OrchestrationError(Exception):
    """Fehler in der Orchestrierung"""
    pass


class LangGraphOrchestrator:
    """
    Orchestriert den kompletten DaRa-Workflow mit LangGraph.

    Workflow-Schritte:
    1. read_csv: Liest CSV-Dateien zeitsynchron
    2. aggregate: Aggregiert Probanden-Daten
    3. analyze: Führt Prozessanalyse durch
    4. report_notion: (Optional) Schreibt nach Notion
    5. report_gdrive: (Optional) Schreibt nach Google Drive
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialisiert den Orchestrator.

        Args:
            config: OrchestratorConfig (default: Standard-Config)
        """
        self.config = config or OrchestratorConfig()

        # Initialisiere Komponenten
        self.aggregator = MultiProbandAggregator(
            numeric_fields=self.config.numeric_fields,
            skip_missing=True,
            min_valid_probands=self.config.min_valid_probands
        )

        self.analysis_agent = ProcessAnalysisAgent(
            baseline_threshold=self.config.baseline_threshold,
            peak_threshold=self.config.peak_threshold
        )

        self.notion_reporter = NotionReporter() if self.config.create_notion_report else None
        self.gdrive_reporter = GDriveReporter() if (
            self.config.create_gdrive_doc or self.config.create_gdrive_sheet
        ) else None

        # Baue Graph
        self.workflow = self._build_workflow()

        logger.info("LangGraphOrchestrator initialisiert")

    def _build_workflow(self) -> StateGraph:
        """
        Baut den LangGraph Workflow.

        Returns:
            StateGraph
        """
        # Erstelle Graph
        workflow = StateGraph(WorkflowState)

        # Definiere Nodes
        workflow.add_node("read_csv", self._read_csv_node)
        workflow.add_node("aggregate", self._aggregate_node)
        workflow.add_node("analyze", self._analyze_node)

        if self.config.create_notion_report:
            workflow.add_node("report_notion", self._report_notion_node)

        if self.config.create_gdrive_doc or self.config.create_gdrive_sheet:
            workflow.add_node("report_gdrive", self._report_gdrive_node)

        # Definiere Kanten
        workflow.set_entry_point("read_csv")
        workflow.add_edge("read_csv", "aggregate")
        workflow.add_edge("aggregate", "analyze")

        # Reporting-Kanten
        if self.config.create_notion_report and (
            self.config.create_gdrive_doc or self.config.create_gdrive_sheet
        ):
            # Beide Reports
            workflow.add_edge("analyze", "report_notion")
            workflow.add_edge("report_notion", "report_gdrive")
            workflow.add_edge("report_gdrive", END)
        elif self.config.create_notion_report:
            # Nur Notion
            workflow.add_edge("analyze", "report_notion")
            workflow.add_edge("report_notion", END)
        elif self.config.create_gdrive_doc or self.config.create_gdrive_sheet:
            # Nur GDrive
            workflow.add_edge("analyze", "report_gdrive")
            workflow.add_edge("report_gdrive", END)
        else:
            # Kein Reporting
            workflow.add_edge("analyze", END)

        return workflow.compile()

    def _read_csv_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node: Liest CSV-Dateien zeitsynchron.

        Args:
            state: Workflow State

        Returns:
            Aktualisierter State
        """
        logger.info(f"[read_csv] Starte mit {len(state['csv_file_paths'])} Dateien")

        try:
            reader = SynchronizedCSVReader(
                file_paths=state["csv_file_paths"],
                proband_ids=state.get("proband_ids"),
                skip_errors=self.config.skip_errors,
                fill_missing=self.config.fill_missing
            )

            # Lese alle TimeSlices
            time_slices = list(reader.read_synchronized(batch_size=self.config.batch_size))

            logger.info(f"[read_csv] Erfolgreich {len(time_slices)} TimeSlices gelesen")

            state["time_slices"] = time_slices
            state["status"] = "csv_read"
            state["step_count"] = state.get("step_count", 0) + 1

        except Exception as e:
            logger.error(f"[read_csv] Fehler: {e}")
            state["errors"].append(f"CSV Read Error: {str(e)}")
            state["status"] = "failed"

        return state

    def _aggregate_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node: Aggregiert TimeSlices.

        Args:
            state: Workflow State

        Returns:
            Aktualisierter State
        """
        logger.info(f"[aggregate] Starte mit {len(state['time_slices'])} TimeSlices")

        try:
            time_slices = state["time_slices"]
            aggregated = self.aggregator.aggregate_time_slices(time_slices)

            logger.info(f"[aggregate] Erfolgreich {len(aggregated)} Slices aggregiert")

            state["aggregated_slices"] = aggregated
            state["status"] = "aggregated"
            state["step_count"] = state.get("step_count", 0) + 1

        except Exception as e:
            logger.error(f"[aggregate] Fehler: {e}")
            state["errors"].append(f"Aggregation Error: {str(e)}")
            state["status"] = "failed"

        return state

    def _analyze_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node: Führt Prozessanalyse durch.

        Args:
            state: Workflow State

        Returns:
            Aktualisierter State
        """
        logger.info(f"[analyze] Starte Analyse")

        try:
            aggregated = state["aggregated_slices"]
            analysis_result = self.analysis_agent.analyze_aggregated_slices(
                aggregated,
                primary_field=self.config.primary_field
            )

            logger.info(f"[analyze] Analyse abgeschlossen: {len(analysis_result.states)} States")

            state["analysis_result"] = analysis_result
            state["status"] = "analyzed"
            state["step_count"] = state.get("step_count", 0) + 1

        except Exception as e:
            logger.error(f"[analyze] Fehler: {e}")
            state["errors"].append(f"Analysis Error: {str(e)}")
            state["status"] = "failed"

        return state

    def _report_notion_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node: Schreibt Report nach Notion.

        Args:
            state: Workflow State

        Returns:
            Aktualisierter State
        """
        logger.info("[report_notion] Erstelle Notion Report")

        try:
            result = self.notion_reporter.send_analysis_report(
                state["analysis_result"],
                title=self.config.report_title
            )

            logger.info("[report_notion] Erfolgreich Report erstellt")

            state["notion_result"] = result
            state["step_count"] = state.get("step_count", 0) + 1

        except Exception as e:
            logger.error(f"[report_notion] Fehler: {e}")
            state["errors"].append(f"Notion Report Error: {str(e)}")
            # Kein Status-Fail, da Reporting optional

        return state

    def _report_gdrive_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node: Schreibt Report nach Google Drive.

        Args:
            state: Workflow State

        Returns:
            Aktualisierter State
        """
        logger.info("[report_gdrive] Erstelle Google Drive Reports")

        try:
            results = {}

            if self.config.create_gdrive_doc:
                doc_result = self.gdrive_reporter.create_doc_report(
                    state["analysis_result"],
                    title=self.config.report_title
                )
                results["doc"] = doc_result

            if self.config.create_gdrive_sheet:
                sheet_result = self.gdrive_reporter.create_sheet_report(
                    state["analysis_result"],
                    title=self.config.report_title
                )
                results["sheet"] = sheet_result

            logger.info("[report_gdrive] Erfolgreich Reports erstellt")

            state["gdrive_result"] = results
            state["step_count"] = state.get("step_count", 0) + 1

        except Exception as e:
            logger.error(f"[report_gdrive] Fehler: {e}")
            state["errors"].append(f"GDrive Report Error: {str(e)}")
            # Kein Status-Fail, da Reporting optional

        return state

    def run_pipeline(
        self,
        csv_file_paths: List[str],
        proband_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Führt die komplette Pipeline aus.

        Args:
            csv_file_paths: Liste von Pfaden zu CSV-Dateien
            proband_ids: Optional, IDs für Probanden

        Returns:
            Dictionary mit Ergebnissen und Metadaten

        Raises:
            OrchestrationError: Bei kritischen Fehlern
        """
        logger.info(f"=== Starte DaRa Pipeline mit {len(csv_file_paths)} Dateien ===")

        # Initialer State
        initial_state: WorkflowState = {
            "csv_file_paths": csv_file_paths,
            "proband_ids": proband_ids,
            "time_slices": None,
            "aggregated_slices": None,
            "analysis_result": None,
            "notion_result": None,
            "gdrive_result": None,
            "status": "started",
            "errors": [],
            "step_count": 0,
        }

        # Führe Workflow aus
        try:
            final_state = self.workflow.invoke(initial_state)

            logger.info(f"=== Pipeline abgeschlossen: {final_state['status']} ===")

            # Prüfe auf Fehler
            if final_state["status"] == "failed":
                raise OrchestrationError(
                    f"Pipeline fehlgeschlagen: {final_state['errors']}"
                )

            # Formatiere Rückgabe
            return self._format_results(final_state)

        except Exception as e:
            logger.error(f"Pipeline-Fehler: {e}")
            raise OrchestrationError(f"Pipeline-Ausführung fehlgeschlagen: {e}") from e

    def _format_results(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Formatiert finale Ergebnisse.

        Args:
            state: Finaler Workflow State

        Returns:
            Formatiertes Ergebnis-Dictionary
        """
        results = {
            "status": state["status"],
            "steps_completed": state["step_count"],
            "errors": state["errors"],
            "data": {},
        }

        # Füge Analyse-Ergebnis hinzu (falls vorhanden)
        if state.get("analysis_result"):
            analysis = state["analysis_result"]
            results["data"]["analysis"] = {
                "time_range": analysis.time_range,
                "summary": analysis.summary,
                "states_count": len(analysis.states),
                "patterns_count": len(analysis.patterns),
                "statistics": analysis.statistics,
            }

        # Reporting-Ergebnisse
        if state.get("notion_result"):
            results["data"]["notion"] = state["notion_result"]

        if state.get("gdrive_result"):
            results["data"]["gdrive"] = state["gdrive_result"]

        return results

    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über den Workflow zurück.

        Returns:
            Workflow-Informationen
        """
        return {
            "config": asdict(self.config),
            "components": {
                "aggregator": "MultiProbandAggregator",
                "analysis_agent": "ProcessAnalysisAgent",
                "notion_reporter": self.notion_reporter is not None,
                "gdrive_reporter": self.gdrive_reporter is not None,
            }
        }


def create_default_orchestrator() -> LangGraphOrchestrator:
    """
    Erstellt einen Orchestrator mit Standard-Konfiguration.

    Returns:
        LangGraphOrchestrator
    """
    config = OrchestratorConfig(
        skip_errors=True,
        fill_missing=True,
        min_valid_probands=1,
        primary_field="value",
        create_notion_report=False,
        create_gdrive_doc=False,
        create_gdrive_sheet=False,
    )

    return LangGraphOrchestrator(config)
