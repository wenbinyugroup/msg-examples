from __future__ import annotations

"""Batch runner for airfoil cross-section evaluations.

This script orchestrates repeated execution of :mod:`main` across many airfoil
coordinate files. It handles file selection, per-case working directories,
optional parallel execution, configuration-file loading, and CSV aggregation of
post-processed structural properties.
"""

import argparse
import asyncio
import csv
import json
import logging
import random
from pathlib import Path
from typing import Any

from scripts.helpers import configure_logging, resolve_path, write_case_error_file
from scripts.main import run_airfoil_case
from scripts.post_process import post_process_vabs_output


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_CSV = "results.csv"


def collect_airfoil_files(
    airfoil_dir: str | Path,
    airfoil_files: list[str] | None = None,
    sample_size: int | None = None,
    seed: int | None = None,
) -> list[Path]:
    """Collect the airfoil files selected for batch processing.

    Parameters
    ----------
    airfoil_dir : str or Path
        Directory containing candidate airfoil coordinate files.
    airfoil_files : list of str or None, optional
        Optional explicit subset of filenames or paths. Relative entries are
        resolved under ``airfoil_dir``.
    sample_size : int or None, optional
        Optional random sample size drawn from the selected file set.
    seed : int or None, optional
        Random seed used when ``sample_size`` is provided.

    Returns
    -------
    list of Path
        Sorted list of absolute airfoil file paths.

    Raises
    ------
    NotADirectoryError
        If ``airfoil_dir`` does not exist or is not a directory.
    FileNotFoundError
        If any explicitly requested airfoil file is missing.
    ValueError
        If ``sample_size`` is invalid.
    """
    airfoil_dir = resolve_path(airfoil_dir)
    if not airfoil_dir.is_dir():
        raise NotADirectoryError(f"Airfoil directory not found: {airfoil_dir}")

    if airfoil_files:
        files = []
        for airfoil_file in airfoil_files:
            candidate = resolve_path(airfoil_file, base_dir=airfoil_dir)
            if not candidate.is_file():
                raise FileNotFoundError(f"Airfoil file not found: {candidate}")
            files.append(candidate)
    else:
        files = sorted(path for path in airfoil_dir.iterdir() if path.is_file())

    if sample_size is not None:
        if sample_size < 1:
            raise ValueError("sample_size must be at least 1.")
        if sample_size > len(files):
            raise ValueError(
                f"sample_size={sample_size} is larger than the number of selected airfoils ({len(files)})."
            )
        rng = random.Random(seed)
        files = rng.sample(files, sample_size)

    return sorted(files, key=lambda path: path.name)


async def run_single_airfoil(
    airfoil_file: Path,
    working_dir: str | Path,
    property_names: list[str],
    template_file: str | Path = "airfoil_skin_only.template.xml",
    material_file: str | Path | None = None,
    template_params: dict[str, Any] | None = None,
    solver_timeout: float | None = None,
    failed_case: str = "stop",
) -> dict[str, Any]:
    """Run one airfoil case and return a tabular result row.

    Parameters
    ----------
    airfoil_file : Path
        Absolute path to the airfoil coordinate file for this case.
    working_dir : str or Path
        Root output directory containing one subdirectory per airfoil.
    property_names : list of str
        Structural properties to extract from the VABS output.
    template_file : str or Path, default="airfoil_skin_only.template.xml"
        XML template used by the single-case runner.
    material_file : str or Path or None, optional
        Optional material database copied into the case directory.
    template_params : dict of str to Any or None, optional
        User-defined XML template placeholders.
    solver_timeout : float or None, optional
        Maximum allowed runtime in seconds for each solver command.
    failed_case : {"continue", "stop"}, default="stop"
        Failure handling policy for this case. ``"continue"`` records the
        failure in the output row. ``"stop"`` re-raises the exception.

    Returns
    -------
    dict of str to Any
        One row of batch output including metadata, status, error message, and
        extracted property values.
    """
    case_dir = resolve_path(Path(working_dir) / airfoil_file.stem)
    case_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(__name__)

    row = {
        "airfoil_name": airfoil_file.stem,
        # "airfoil_file": str(airfoil_file),
        # "case_dir": str(case_dir),
        "status": "ok",
        "error": "",
    }

    logger.info("Starting batch case: %s", airfoil_file.name)
    try:
        vabs_output = await run_airfoil_case(
            airfoil_path=airfoil_file,
            working_dir=case_dir,
            template_file=template_file,
            material_file=material_file,
            template_params=template_params,
            solver_timeout=solver_timeout,
            failed_case=failed_case,
        )
        if vabs_output is None:
            raise RuntimeError("Case failed and returned no VABS output.")
        row.update(post_process_vabs_output(vabs_output, property_names))
        logger.info("Finished batch case: %s", airfoil_file.name)
    except Exception as exc:
        error_file = write_case_error_file(
            case_dir,
            exc,
            header=f"Batch case failed: {airfoil_file.name}",
        )
        if failed_case == "stop":
            logger.error("Wrote case error report to %s", error_file)
            logger.exception("Batch case failed and stops the run: %s", airfoil_file.name)
            raise
        row["status"] = "error"
        row["error"] = str(exc)
        for property_name in property_names:
            row[property_name] = None
        logger.error("Wrote case error report to %s", error_file)
        logger.exception("Batch case failed: %s", airfoil_file.name)

    return row


def build_result_fieldnames(property_names: list[str]) -> list[str]:
    """Build the CSV column order for batch results."""
    return ["airfoil_name", "status", "error", *property_names]


def initialize_results_csv(output_csv: str | Path, fieldnames: list[str]) -> Path:
    """Create or overwrite the output CSV and write its header."""
    output_csv = resolve_path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    return output_csv


def append_result_row(output_csv: str | Path, fieldnames: list[str], row: dict[str, Any]) -> None:
    """Append one completed batch result row to the CSV."""
    normalized_row = {field: row.get(field, "") for field in fieldnames}
    with Path(output_csv).open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(normalized_row)


async def run_batch(
    airfoil_dir: str | Path,
    working_dir: str | Path,
    property_names: list[str],
    output_csv: str | Path,
    airfoil_files: list[str] | None = None,
    sample_size: int | None = None,
    seed: int | None = None,
    jobs: int = 1,
    template_file: str | Path = "airfoil_skin_only.template.xml",
    material_file: str | Path | None = None,
    template_params: dict[str, Any] | None = None,
    solver_timeout: float | None = None,
    failed_case: str = "stop",
) -> list[dict[str, Any]]:
    """Run the selected airfoils and collect batch results.

    Parameters
    ----------
    airfoil_dir : str or Path
        Directory containing candidate airfoil files.
    working_dir : str or Path
        Root directory under which per-airfoil case directories are created.
    property_names : list of str
        Structural properties to extract after each solver run.
    output_csv : str or Path
        CSV file updated as each case completes.
    airfoil_files : list of str or None, optional
        Optional explicit subset of files to run.
    sample_size : int or None, optional
        Optional random sample size.
    seed : int or None, optional
        Random seed used for sampling.
    jobs : int, default=1
        Number of airfoil cases to execute concurrently.
    template_file : str or Path, default="airfoil_skin_only.template.xml"
        XML template used by the case runner.
    material_file : str or Path or None, optional
        Optional material database copied into each case directory.
    template_params : dict of str to Any or None, optional
        User-defined XML template placeholders.
    solver_timeout : float or None, optional
        Maximum allowed runtime in seconds for each solver command.
    failed_case : {"continue", "stop"}, default="stop"
        Batch failure handling policy.

    Returns
    -------
    list of dict of str to Any
        Result rows for all requested airfoils.

    Raises
    ------
    ValueError
        If ``jobs`` is less than 1 or no airfoil files are selected.
    """
    if jobs < 1:
        raise ValueError("jobs must be at least 1.")
    if failed_case not in {"continue", "stop"}:
        raise ValueError("failed_case must be either 'continue' or 'stop'.")

    selected_files = collect_airfoil_files(
        airfoil_dir=airfoil_dir,
        airfoil_files=airfoil_files,
        sample_size=sample_size,
        seed=seed,
    )
    if not selected_files:
        raise ValueError("No airfoil files were selected.")

    working_dir = resolve_path(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.info("Selected %d airfoil files", len(selected_files))
    logger.info("Working directory: %s", working_dir)
    fieldnames = build_result_fieldnames(property_names)
    output_csv = initialize_results_csv(output_csv, fieldnames)
    logger.info("Initialized incremental results CSV at %s", output_csv)

    semaphore = asyncio.Semaphore(jobs)
    results: list[dict[str, Any]] = []
    stop_exception: Exception | None = None

    async def run_with_limit(airfoil_file: Path) -> dict[str, Any]:
        async with semaphore:
            return await run_single_airfoil(
                airfoil_file=airfoil_file,
                working_dir=working_dir,
                property_names=property_names,
                template_file=template_file,
                material_file=material_file,
                template_params=template_params,
                solver_timeout=solver_timeout,
                failed_case=failed_case,
            )

    tasks = [
        asyncio.create_task(run_with_limit(airfoil_file))
        for airfoil_file in selected_files
    ]
    for task in asyncio.as_completed(tasks):
        try:
            row = await task
            results.append(row)
            append_result_row(output_csv, fieldnames, row)
            logger.info("Appended result for %s to %s", row["airfoil_name"], output_csv)
        except asyncio.CancelledError:
            continue
        except Exception as exc:
            if failed_case == "stop" and stop_exception is None:
                stop_exception = exc
                logger.exception("Batch case failed and stops the async run.")
                for pending_task in tasks:
                    if not pending_task.done():
                        pending_task.cancel()
            else:
                raise

    await asyncio.gather(*tasks, return_exceptions=True)
    if stop_exception is not None:
        raise stop_exception

    return results


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load and normalize a batch-run JSON configuration file.

    Parameters
    ----------
    config_path : str or Path
        Path to the JSON configuration file.

    Returns
    -------
    dict of str to Any
        Configuration dictionary with supported path-like entries resolved to
        absolute paths.

    Raises
    ------
    ValueError
        If the JSON file does not contain a top-level object.
    """
    config_path = resolve_path(config_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError(f"Config file must contain a JSON object: {config_path}")

    config["_config_dir"] = str(config_path.parent)

    for key in ("airfoil_dir", "working_dir"):
        if key in config and config[key] is not None:
            config[key] = str(resolve_path(config[key], base_dir=config_path.parent))
    if "template_file" in config and config["template_file"] is not None:
        config["template_file"] = str(
            resolve_path(config["template_file"], base_dir=config_path.parent)
        )
    if "material_file" in config and config["material_file"] is not None:
        config["material_file"] = str(
            resolve_path(config["material_file"], base_dir=config_path.parent)
        )

    return config


def build_settings(args: argparse.Namespace) -> dict[str, Any]:
    """Merge configuration-file settings with CLI overrides.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments from the batch-run entry point.

    Returns
    -------
    dict of str to Any
        Final settings dictionary used for batch execution.

    Raises
    ------
    ValueError
        If required settings are missing after merging defaults, config, and
        CLI overrides.
    """
    settings: dict[str, Any] = {}
    if args.config is not None:
        settings.update(load_config(args.config))

    cli_overrides = {
        "airfoil_dir": args.airfoil_dir,
        "working_dir": args.working_dir,
        "airfoil_files": args.airfoil_files,
        "sample_size": args.sample_size,
        "seed": args.seed,
        "jobs": args.jobs,
        "failed_case": args.failed_case,
        "properties": args.properties,
        "output_csv": args.output_csv,
        "template_file": args.template_file,
        "material_file": args.material_file,
        "solver_timeout": args.solver_timeout,
    }
    settings.update({key: value for key, value in cli_overrides.items() if value is not None})

    settings.setdefault("seed", 0)
    settings.setdefault("jobs", 1)
    settings.setdefault("failed_case", "stop")
    settings.setdefault("output_csv", DEFAULT_OUTPUT_CSV)
    settings.setdefault("template_file", "airfoil_skin_only.template.xml")
    settings.setdefault("material_file", None)
    settings.setdefault("solver_timeout", None)
    settings.setdefault("template_params", {})
    settings.setdefault("_config_dir", None)

    missing = [
        key for key in ("airfoil_dir", "working_dir", "properties")
        if key not in settings or settings[key] in (None, "")
    ]
    if missing:
        raise ValueError(f"Missing required run settings: {', '.join(missing)}")
    if settings["failed_case"] not in {"continue", "stop"}:
        raise ValueError("failed_case must be either 'continue' or 'stop'.")

    return settings


async def async_main() -> None:
    """Run the batch-analysis command-line interface.

    Returns
    -------
    None
        The batch results are written to the configured CSV file. Progress and
        failures are recorded in the batch log.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Run airfoil cross-section analyses in batch mode. "
            "Use either CLI options or `python run.py config.json`."
        )
    )
    parser.add_argument(
        "config",
        nargs="?",
        help="Optional JSON config file path.",
    )
    parser.add_argument(
        "--airfoil-dir",
        help="Directory containing airfoil coordinate files.",
    )
    parser.add_argument(
        "--working-dir",
        help="Root directory for per-airfoil case directories.",
    )
    parser.add_argument(
        "--airfoil-files",
        nargs="+",
        help="Optional subset of airfoil files to run. Relative names are resolved under --airfoil-dir.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        help="Optional random sample size from the selected airfoil files.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed used with --sample-size.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        help="Number of airfoils to run in parallel.",
    )
    parser.add_argument(
        "--failed-case",
        choices=("continue", "stop"),
        help="Failure handling policy for batch cases.",
    )
    parser.add_argument(
        "--properties",
        nargs="+",
        help="Property names to extract, such as ea gj ei22 ei33.",
    )
    parser.add_argument(
        "--output-csv",
        help="Output CSV path. Relative paths are resolved under --working-dir.",
    )
    parser.add_argument(
        "--template-file",
        help="Path to the PreVABS XML template file.",
    )
    parser.add_argument(
        "--material-file",
        help="Path to the material database file copied into each case directory.",
    )
    parser.add_argument(
        "--solver-timeout",
        type=float,
        help="Optional timeout in seconds applied to each solver command.",
    )
    args = parser.parse_args()
    settings = build_settings(args)

    working_dir = resolve_path(settings["working_dir"])
    working_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logging(working_dir / "run.log")
    logger.info("Starting batch run")
    logger.info("Airfoil directory: %s", settings["airfoil_dir"])
    logger.info("Requested properties: %s", ", ".join(settings["properties"]))
    logger.info("Parallel jobs: %s", settings["jobs"])
    logger.info("Solver timeout: %s", settings["solver_timeout"])
    logger.info("Failed-case policy: %s", settings["failed_case"])

    output_base_dir = settings["_config_dir"] or working_dir
    output_csv = resolve_path(settings["output_csv"], base_dir=output_base_dir)
    results = await run_batch(
        airfoil_dir=settings["airfoil_dir"],
        working_dir=working_dir,
        property_names=settings["properties"],
        output_csv=output_csv,
        airfoil_files=settings.get("airfoil_files"),
        sample_size=settings.get("sample_size"),
        seed=settings.get("seed"),
        jobs=settings["jobs"],
        template_file=settings["template_file"],
        material_file=settings.get("material_file"),
        template_params=settings.get("template_params"),
        solver_timeout=settings.get("solver_timeout"),
        failed_case=settings["failed_case"],
    )
    logger.info("Saved %d result rows to %s", len(results), output_csv)


def main() -> None:
    """Synchronous wrapper for the async batch CLI."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
