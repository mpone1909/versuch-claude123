"""
Command-Line Interface (CLI) für das DaRa-System.

Bietet Befehle für:
- Experimente ausführen
- Experimente auflisten
- Ergebnisse anzeigen
- Beispiel-Konfigurationen erstellen
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from dara_system.config import get_config
from dara_system.experiment_config import (
    load_experiment_config,
    list_experiment_configs,
    create_example_config,
)
from dara_system.run_experiment import ExperimentRunner
from dara_system.observability import print_metrics_summary


def cmd_run_experiment(args):
    """Führt ein Experiment aus."""
    config_path = Path(args.config)

    if not config_path.exists():
        print(f"FEHLER: Konfigurationsdatei nicht gefunden: {config_path}")
        return 1

    try:
        runner = ExperimentRunner()
        report = runner.run_experiment_from_file(config_path, verbose=args.verbose)

        print(f"\nErgebnisse gespeichert in: {report['output_directory']}")

        if args.show_metrics:
            print_metrics_summary()

        return 0

    except Exception as e:
        print(f"\nFEHLER: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_list_experiments(args):
    """Listet verfügbare Experiment-Konfigurationen auf."""
    config = get_config()
    experiments_dir = config.paths.experiments_dir

    print(f"Experiment-Konfigurationen in: {experiments_dir}\n")

    config_files = list_experiment_configs(experiments_dir)

    if not config_files:
        print("Keine Experiment-Konfigurationen gefunden.")
        print(f"\nErstelle eine Beispiel-Konfiguration mit:")
        print(f"  dara-cli create-example {experiments_dir}/example.yaml")
        return 0

    print(f"Gefundene Konfigurationen ({len(config_files)}):\n")

    for config_file in config_files:
        print(f"  📄 {config_file.name}")

        if args.details:
            try:
                exp_config = load_experiment_config(config_file)
                print(f"     Name: {exp_config.name}")
                print(f"     Beschreibung: {exp_config.description}")
                print(f"     Probanden: {len(exp_config.proband_ids)}")
                print()
            except Exception as e:
                print(f"     FEHLER beim Laden: {e}\n")

    return 0


def cmd_show_results(args):
    """Zeigt Experiment-Ergebnisse an."""
    config = get_config()
    results_dir = config.paths.results_dir

    if args.experiment:
        # Zeige Ergebnisse eines spezifischen Experiments
        exp_dir = results_dir / args.experiment

        if not exp_dir.exists():
            print(f"FEHLER: Experiment-Verzeichnis nicht gefunden: {exp_dir}")
            return 1

        # Lade Report
        report_file = exp_dir / "experiment_report.json"
        if not report_file.exists():
            print(f"FEHLER: Kein Experiment-Report gefunden in {exp_dir}")
            return 1

        with open(report_file, "r", encoding="utf-8") as f:
            report = json.load(f)

        print("\n" + "=" * 70)
        print(f"EXPERIMENT: {report['experiment_name']}")
        print("=" * 70)
        print(f"Beschreibung: {report['description']}")
        print(f"Ausgeführt: {report['executed_at']}")
        print(f"Dauer: {report['duration_seconds']:.2f}s")
        print(f"\nErgebnisse:")
        print(f"  Total Slices: {report['results']['total_slices']}")
        print(f"  Total Patterns: {report['results']['total_patterns']}")

        if report.get("evaluation"):
            eval_data = report["evaluation"]
            print(f"\nEvaluation:")
            print(f"  Coverage: {eval_data['coverage'] * 100:.2f}%")
            print(f"  Valid Slices: {eval_data['valid_time_slices']}")
            print(f"  Anomaly Rate: {eval_data['anomaly_rate'] * 100:.2f}%")

        print(f"\nVerzeichnis: {exp_dir}")
        print("=" * 70 + "\n")

    else:
        # Liste alle Experiment-Ergebnisse
        print(f"Experiment-Ergebnisse in: {results_dir}\n")

        if not results_dir.exists():
            print("Noch keine Ergebnisse vorhanden.")
            return 0

        experiment_dirs = [d for d in results_dir.iterdir() if d.is_dir()]

        if not experiment_dirs:
            print("Noch keine Ergebnisse vorhanden.")
            return 0

        print(f"Verfügbare Experimente ({len(experiment_dirs)}):\n")

        for exp_dir in sorted(experiment_dirs):
            print(f"  📊 {exp_dir.name}")

            report_file = exp_dir / "experiment_report.json"
            if report_file.exists():
                try:
                    with open(report_file, "r", encoding="utf-8") as f:
                        report = json.load(f)
                    print(f"     Ausgeführt: {report['executed_at']}")
                    print(f"     Patterns: {report['results']['total_patterns']}")
                except Exception:
                    pass

            print()

        print(f"\nZeige Details mit: dara-cli show-results --experiment <name>")

    return 0


def cmd_create_example(args):
    """Erstellt eine Beispiel-Experiment-Konfiguration."""
    output_path = Path(args.output)

    if output_path.exists() and not args.force:
        print(f"FEHLER: Datei existiert bereits: {output_path}")
        print("Nutze --force zum Überschreiben")
        return 1

    try:
        create_example_config(output_path)
        print(f"✓ Beispiel-Konfiguration erstellt: {output_path}")
        print(f"\nBearbeite die Datei und führe das Experiment aus mit:")
        print(f"  dara-cli run {output_path}")
        return 0

    except Exception as e:
        print(f"FEHLER: {e}")
        return 1


def cmd_validate_config(args):
    """Validiert eine Experiment-Konfiguration."""
    config_path = Path(args.config)

    if not config_path.exists():
        print(f"FEHLER: Konfigurationsdatei nicht gefunden: {config_path}")
        return 1

    try:
        exp_config = load_experiment_config(config_path)
        errors = exp_config.validate()

        if errors:
            print(f"❌ Konfiguration ist ungültig:\n")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print(f"✓ Konfiguration ist valide")
            print(f"\nDetails:")
            print(f"  Name: {exp_config.name}")
            print(f"  Probanden: {len(exp_config.proband_ids)}")
            print(f"  CSV-Dateien: {len(exp_config.csv_file_paths)}")
            return 0

    except Exception as e:
        print(f"FEHLER beim Laden: {e}")
        return 1


def main():
    """Haupt-CLI-Einstiegspunkt."""
    parser = argparse.ArgumentParser(
        prog="dara-cli",
        description="DaRa Multi-Agent RAG/MCP System - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Befehle")

    # run-experiment
    run_parser = subparsers.add_parser("run", help="Führe ein Experiment aus")
    run_parser.add_argument("config", type=str, help="Pfad zur Experiment-Konfiguration")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose-Ausgabe")
    run_parser.add_argument(
        "--show-metrics", action="store_true", help="Zeige Metriken am Ende"
    )
    run_parser.set_defaults(func=cmd_run_experiment)

    # list-experiments
    list_parser = subparsers.add_parser("list", help="Liste Experiment-Konfigurationen")
    list_parser.add_argument("-d", "--details", action="store_true", help="Zeige Details")
    list_parser.set_defaults(func=cmd_list_experiments)

    # show-results
    results_parser = subparsers.add_parser("show-results", help="Zeige Experiment-Ergebnisse")
    results_parser.add_argument(
        "-e", "--experiment", type=str, help="Spezifisches Experiment"
    )
    results_parser.set_defaults(func=cmd_show_results)

    # create-example
    example_parser = subparsers.add_parser(
        "create-example", help="Erstelle Beispiel-Konfiguration"
    )
    example_parser.add_argument(
        "output", type=str, help="Ausgabe-Pfad (z.B. experiments/my_exp.yaml)"
    )
    example_parser.add_argument(
        "-f", "--force", action="store_true", help="Überschreibe existierende Datei"
    )
    example_parser.set_defaults(func=cmd_create_example)

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validiere eine Konfiguration")
    validate_parser.add_argument("config", type=str, help="Pfad zur Konfiguration")
    validate_parser.set_defaults(func=cmd_validate_config)

    # Parse Argumente
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Führe Kommando aus
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
