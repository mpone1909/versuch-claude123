"""
Experiment-Runner für das DaRa-System.

Lädt Experiment-Konfigurationen, führt die Pipeline aus,
und speichert Ergebnisse und Evaluationen.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from dara_system.experiment_config import ExperimentConfig, load_experiment_config
from dara_system.config import get_config
from dara_system.langgraph_orchestrator import LangGraphOrchestrator, OrchestratorConfig
from dara_system.evaluation import (
    evaluate_pipeline_results,
    save_evaluation_report,
    print_evaluation_summary,
)


class ExperimentRunner:
    """
    Führt DaRa-Experimente basierend auf Konfigurationsdateien aus.
    """

    def __init__(self, system_config=None):
        """
        Initialisiert den Experiment-Runner.

        Args:
            system_config: Optionale SystemConfig-Instanz
        """
        self.system_config = system_config or get_config()

    def run_experiment(
        self, experiment_config: ExperimentConfig, verbose: bool = False
    ) -> dict:
        """
        Führt ein einzelnes Experiment aus.

        Args:
            experiment_config: Experiment-Konfiguration
            verbose: Verbose-Ausgabe aktivieren

        Returns:
            Dictionary mit Experiment-Ergebnissen
        """
        print(f"\n{'=' * 70}")
        print(f"EXPERIMENT: {experiment_config.name}")
        print(f"{'=' * 70}")
        print(f"Beschreibung: {experiment_config.description}")
        print(f"Autor: {experiment_config.author}")
        print(f"CSV-Dateien: {len(experiment_config.csv_file_paths)}")
        print(f"Probanden: {', '.join(experiment_config.proband_ids)}")
        print(f"Zeilen: {experiment_config.start_row} - {experiment_config.end_row or 'Ende'}")
        print(f"{'=' * 70}\n")

        # Validiere Konfiguration
        errors = experiment_config.validate()
        if errors:
            print("FEHLER: Ungültige Experiment-Konfiguration:")
            for error in errors:
                print(f"  - {error}")
            raise ValueError("Experiment-Konfiguration ist ungültig")

        # Erstelle Output-Verzeichnis
        output_dir = experiment_config.get_output_dir(self.system_config.paths.results_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if verbose:
            print(f"Output-Verzeichnis: {output_dir}")

        # Speichere verwendete Konfiguration
        config_backup_path = output_dir / "experiment_config.json"
        experiment_config.to_json(config_backup_path)

        if verbose:
            print(f"Konfiguration gespeichert: {config_backup_path}")

        # Erstelle Orchestrator-Konfiguration
        orchestrator_config = OrchestratorConfig(
            primary_field=experiment_config.primary_field,
            baseline_threshold=experiment_config.baseline_threshold,
            peak_threshold=experiment_config.peak_threshold,
            anomaly_std_multiplier=experiment_config.anomaly_std_multiplier,
            create_notion_report=experiment_config.create_notion_report,
            create_gdrive_doc=experiment_config.create_gdrive_doc,
            create_gdrive_sheet=experiment_config.create_gdrive_sheet,
        )

        # Erstelle Orchestrator
        orchestrator = LangGraphOrchestrator(orchestrator_config)

        # Führe Pipeline aus
        print("Starte Pipeline-Ausführung...")
        start_time = datetime.now()

        try:
            results = orchestrator.run_pipeline(
                csv_file_paths=experiment_config.csv_file_paths,
                proband_ids=experiment_config.proband_ids,
                start_row=experiment_config.start_row,
                end_row=experiment_config.end_row,
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print(f"Pipeline abgeschlossen in {duration:.2f}s")

        except Exception as e:
            print(f"FEHLER bei Pipeline-Ausführung: {e}")
            raise

        # Extrahiere Ergebnisse
        aggregated_slices = results.get("data", {}).get("aggregated_slices", [])
        analysis_result = results.get("data", {}).get("analysis")

        # Speichere Analyse-Ergebnis
        if analysis_result:
            analysis_path = output_dir / "analysis_result.json"
            with open(analysis_path, "w", encoding="utf-8") as f:
                # Konvertiere zu dict wenn möglich
                if hasattr(analysis_result, "to_dict"):
                    analysis_data = analysis_result.to_dict()
                else:
                    analysis_data = {
                        "summary": getattr(analysis_result, "summary", ""),
                        "patterns": [
                            {
                                "pattern_type": p.pattern_type,
                                "description": p.description,
                                "start_index": p.start_index,
                                "end_index": p.end_index,
                                "confidence": p.confidence,
                            }
                            for p in getattr(analysis_result, "patterns", [])
                        ],
                    }
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)

            if verbose:
                print(f"Analyse-Ergebnis gespeichert: {analysis_path}")

        # Evaluation
        evaluation_metrics = None
        if experiment_config.run_evaluation and aggregated_slices and analysis_result:
            print("\nEvaluiere Ergebnisse...")

            evaluation_metrics = evaluate_pipeline_results(
                aggregated_slices=aggregated_slices,
                analysis_result=analysis_result,
                experiment_name=experiment_config.name,
                primary_field=experiment_config.primary_field,
            )

            # Speichere Evaluation
            save_evaluation_report(evaluation_metrics, output_dir)

            # Zeige Zusammenfassung
            print_evaluation_summary(evaluation_metrics)

        # Erstelle Experiment-Report
        experiment_report = {
            "experiment_name": experiment_config.name,
            "description": experiment_config.description,
            "author": experiment_config.author,
            "executed_at": start_time.isoformat(),
            "duration_seconds": duration,
            "config": experiment_config.to_dict(),
            "results": {
                "total_slices": len(aggregated_slices),
                "total_patterns": len(analysis_result.patterns) if analysis_result else 0,
            },
            "evaluation": evaluation_metrics.to_dict() if evaluation_metrics else None,
            "output_directory": str(output_dir),
        }

        report_path = output_dir / "experiment_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(experiment_report, f, indent=2, ensure_ascii=False)

        print(f"\nExperiment-Report gespeichert: {report_path}")
        print(f"Alle Ergebnisse in: {output_dir}")

        return experiment_report

    def run_experiment_from_file(self, config_path: Path, verbose: bool = False) -> dict:
        """
        Lädt und führt ein Experiment aus einer Konfigurationsdatei aus.

        Args:
            config_path: Pfad zur Experiment-Konfigurationsdatei
            verbose: Verbose-Ausgabe aktivieren

        Returns:
            Dictionary mit Experiment-Ergebnissen
        """
        print(f"Lade Experiment-Konfiguration: {config_path}")
        experiment_config = load_experiment_config(config_path)

        return self.run_experiment(experiment_config, verbose=verbose)


def main():
    """
    Kommandozeilen-Einstiegspunkt für den Experiment-Runner.
    """
    if len(sys.argv) < 2:
        print("Verwendung: python -m dara_system.run_experiment <config_file> [--verbose]")
        print("\nBeispiel:")
        print("  python -m dara_system.run_experiment experiments/example.yaml")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    if not config_path.exists():
        print(f"FEHLER: Konfigurationsdatei nicht gefunden: {config_path}")
        sys.exit(1)

    try:
        runner = ExperimentRunner()
        report = runner.run_experiment_from_file(config_path, verbose=verbose)

        print("\n" + "=" * 70)
        print("EXPERIMENT ERFOLGREICH ABGESCHLOSSEN")
        print("=" * 70)
        print(f"Ergebnisse: {report['output_directory']}")

    except Exception as e:
        print(f"\nFEHLER: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
