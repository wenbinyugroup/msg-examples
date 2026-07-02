from __future__ import annotations

"""Run one airfoil cross-section analysis case.

This script performs the per-airfoil workflow:

1. prepare required input files in a case working directory
2. derive leading- and trailing-edge data from the airfoil coordinates
3. render a PreVABS XML file from a template
4. invoke ``prevabs`` and ``vabs``
5. return the generated VABS output file path for later post-processing
"""

import argparse
import asyncio
import shutil
from pathlib import Path
from typing import Any

from helpers import (
    close_case_logger,
    create_case_logger,
    ensure_root_logging,
    resolve_path,
    run_solver_command,
    write_case_error_file,
)
from pre_process import (
    ProcessedAirfoilData,
    export_selig_airfoil_file,
    find_thickness_location,
    format_point,
    process_airfoil_data,
    round_with_precision,
)


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_FILE = "airfoil_skin_only.template.xml"
CS_NAME = "airfoil_cs"
DEFAULT_TEMPLATE_PARAMS = {
    "translate_x": -0.25,
    "translate_y": 0.0,
    "scale": 1.0,
    "mesh_size": 0.01,
    "element_shape": "quad",
    "element_type": "linear",
    "material_density": 2.906e3,
    "material_e": 90.321e9,
    "material_nu": 3.30e-1,
    "lamina_thickness": 0.01,
}


def build_template_context(
    airfoil_filename: str,
    processed_airfoil: ProcessedAirfoilData,
    material_filename: str | None = None,
    template_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build placeholder values for XML template rendering.

    Parameters
    ----------
    airfoil_filename : str
        Filename of the processed airfoil coordinate file inside the case
        directory.
    processed_airfoil : ProcessedAirfoilData
        Processed airfoil data, including the LE/TE points and source decimal
        precision used to format them.
    material_filename : str or None, optional
        Filename of the material database inside the case directory.
        When provided, both ``material_file`` and ``material_file_stem`` are
        added to the template context.
    template_params : dict of str to Any or None, optional
        User-provided template parameters. These values override
        ``DEFAULT_TEMPLATE_PARAMS`` when keys overlap.

    Returns
    -------
    dict of str to Any
        Template context passed to ``str.format``.
    """
    le_x, le_y = format_point(
        processed_airfoil.le_point,
        processed_airfoil.x_precision,
        processed_airfoil.y_precision,
    )
    te_x, te_y = format_point(
        processed_airfoil.te_point,
        processed_airfoil.x_precision,
        processed_airfoil.y_precision,
    )
    te_fill_x, te_fill_y = format_point(
        processed_airfoil.te_fill_point,
        processed_airfoil.x_precision,
        processed_airfoil.y_precision,
    )
    context = {
        "airfoil_file": airfoil_filename,
        "le_x": le_x,
        "le_y": le_y,
        "te_x": te_x,
        "te_y": te_y,
        "te_fill_x": te_fill_x,
        "te_fill_y": te_fill_y,
    }
    if material_filename is not None:
        context["material_file"] = material_filename
        context["material_file_stem"] = Path(material_filename).stem
    context.update(DEFAULT_TEMPLATE_PARAMS)
    if template_params:
        context.update(template_params)

    # Locate the chordwise position where the airfoil thickness reaches twice
    # the lamina thickness, scanning inward from the trailing edge. This marks
    # where the trailing-edge fill begins on both the top and bottom surfaces.
    te_start_x = find_thickness_location(
        processed_airfoil.airfoil,
        float(context["lamina_thickness"])*1.1,
    )
    te_start_x_str = f"{te_start_x:.{processed_airfoil.x_precision}f}"
    context["te_start_top_x"] = te_start_x_str
    context["te_start_bottom_x"] = te_start_x_str

    # Place the trailing-edge fill point at the chordwise midpoint between
    # te_start and the trailing edge, with its vertical coordinate on the
    # camber line at that location.
    te_x_value = processed_airfoil.te_point[0]
    te_fill_x_value = te_start_x + (te_x_value - te_start_x) * 0.1
    te_fill_point = (
        round_with_precision(te_fill_x_value, processed_airfoil.x_precision),
        round_with_precision(
            float(processed_airfoil.airfoil.camber_line(te_fill_x_value)),
            processed_airfoil.y_precision,
        ),
    )
    context["te_fill_x"], context["te_fill_y"] = format_point(
        te_fill_point,
        processed_airfoil.x_precision,
        processed_airfoil.y_precision,
    )

    return context


def render_prevabs_input(template_text: str, template_context: dict[str, Any]) -> str:
    """Render a PreVABS XML input file from a template context.

    Parameters
    ----------
    template_text : str
        Raw XML template text containing ``str.format`` placeholders.
    template_context : dict of str to Any
        Placeholder values used for formatting.

    Returns
    -------
    str
        Rendered XML text.

    Raises
    ------
    KeyError
        If the template references a placeholder not present in
        ``template_context``.
    """
    try:
        return template_text.format(**template_context)
    except KeyError as exc:
        missing_key = exc.args[0]
        raise KeyError(
            f"Template placeholder '{missing_key}' is missing from the template context."
        ) from exc


async def run_airfoil_case(
    airfoil_path: str | Path,
    working_dir: str = ".",
    template_file: str | Path = TEMPLATE_FILE,
    material_file: str | Path | None = None,
    template_params: dict[str, Any] | None = None,
    solver_timeout: float | None = None,
    failed_case: str = "stop",
) -> Path | None:
    """Run one airfoil cross-section analysis case.

    Parameters
    ----------
    airfoil_path : str or Path
        Path to the source airfoil coordinate file.
    working_dir : str, default="."
        Case working directory. Prepared inputs and solver outputs are
        generated here.
    template_file : str or Path, default=TEMPLATE_FILE
        XML template used to build the PreVABS input file.
    material_file : str or Path or None, optional
        Optional material database file copied into the case directory.
    template_params : dict of str to Any or None, optional
        User-defined placeholder values merged into the XML template context.
    solver_timeout : float or None, optional
        Maximum allowed runtime in seconds for each solver command.
        ``None`` disables the timeout.
    failed_case : {"continue", "stop"}, default="stop"
        Failure handling policy. ``"stop"`` re-raises the first exception.
        ``"continue"`` logs the failure and returns ``None``.

    Returns
    -------
    Path or None
        Path to the generated VABS output file. Returns ``None`` only when
        ``failed_case="continue"`` and the case fails.

    Raises
    ------
    FileNotFoundError
        If any required input file does not exist.
    RuntimeError
        If an external solver invocation fails.
    """
    if failed_case not in {"continue", "stop"}:
        raise ValueError("failed_case must be either 'continue' or 'stop'.")

    ensure_root_logging()
    airfoil_path = resolve_path(airfoil_path)
    if not airfoil_path.exists():
        raise FileNotFoundError(f"Airfoil file not found: {airfoil_path}")

    working_path = resolve_path(working_dir, base_dir=SCRIPT_DIR)
    working_path.mkdir(parents=True, exist_ok=True)
    template_path = resolve_path(template_file, base_dir=SCRIPT_DIR)
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    material_path = None
    if material_file is not None:
        material_path = resolve_path(material_file, base_dir=SCRIPT_DIR)
        if not material_path.exists():
            raise FileNotFoundError(f"Material file not found: {material_path}")
    logger = create_case_logger(working_path, airfoil_path.stem)

    try:
        logger.info("Starting airfoil case: %s", airfoil_path.name)

        copied_material = None
        if material_path is not None:
            copied_material = working_path / material_path.name
            shutil.copy2(material_path, copied_material)
            logger.info("Copied material file to %s", copied_material)

        # Process airfoil data, then export the normalized coordinates to the case directory.
        processed_airfoil = process_airfoil_data(airfoil_path)
        copied_airfoil = working_path / airfoil_path.name
        export_selig_airfoil_file(copied_airfoil, processed_airfoil)
        logger.info("Exported processed airfoil file to %s", copied_airfoil)
        logger.info(
            "Computed LE point %s and TE point %s",
            processed_airfoil.le_point,
            processed_airfoil.te_point,
        )

        # Substitute values into the prevabs input template
        # and write the rendered input file to the working directory
        template_text = template_path.read_text(encoding="utf-8")
        template_context = build_template_context(
            airfoil_filename=copied_airfoil.name,
            processed_airfoil=processed_airfoil,
            material_filename=copied_material.name if copied_material is not None else None,
            template_params=template_params,
        )
        prevabs_input_text = render_prevabs_input(template_text, template_context)
        prevabs_input = working_path / f"{CS_NAME}.xml"
        prevabs_input.write_text(prevabs_input_text, encoding="utf-8")
        logger.info("Wrote PreVABS input to %s", prevabs_input)

        # Run PreVABS
        await run_solver_command(
            ["prevabs", "-i", prevabs_input.name, "--hm"],
            # ["prevabs", "-i", prevabs_input.name, "--hm", "-v", "--nopopup"],
            cwd=prevabs_input.parent,
            logger=logger,
            timeout=solver_timeout,
        )

        # Run VABS
        vabs_input = prevabs_input.with_suffix(".sg")
        await run_solver_command(
            ["vabs", vabs_input.name],
            cwd=vabs_input.parent,
            logger=logger,
            timeout=solver_timeout,
        )

        vabs_output = f"{vabs_input}.k"
        logger.info("Generated VABS output at %s", vabs_output)
        logger.info("Completed airfoil case: %s", airfoil_path.name)
        return Path(vabs_output)
    except Exception as exc:
        error_file = write_case_error_file(
            working_path,
            exc,
            header=f"Airfoil case failed: {airfoil_path.name}",
        )
        logger.error("Wrote case error report to %s", error_file)
        logger.exception("Airfoil case failed: %s", airfoil_path.name)
        if failed_case == "continue":
            return None
        raise
    finally:
        close_case_logger(logger)


def main(
    airfoil_path: str | Path,
    working_dir: str = ".",
    template_file: str | Path = TEMPLATE_FILE,
    material_file: str | Path | None = None,
    template_params: dict[str, Any] | None = None,
    solver_timeout: float | None = None,
    failed_case: str = "stop",
) -> Path | None:
    """Synchronous wrapper for :func:`run_airfoil_case`."""
    return asyncio.run(
        run_airfoil_case(
            airfoil_path=airfoil_path,
            working_dir=working_dir,
            template_file=template_file,
            material_file=material_file,
            template_params=template_params,
            solver_timeout=solver_timeout,
            failed_case=failed_case,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run one airfoil cross-section analysis.")
    parser.add_argument(
        "--airfoil-file",
        required=True,
        help="Path to the airfoil coordinate file in Selig format.",
    )
    parser.add_argument(
        "--working-dir",
        default=".",
        help="Directory used for prepared inputs and solver outputs.",
    )
    parser.add_argument(
        "--template-file",
        default=TEMPLATE_FILE,
        help="Path to the PreVABS XML template file.",
    )
    parser.add_argument(
        "--material-file",
        help="Optional material database file to copy into the working directory.",
    )
    parser.add_argument(
        "--solver-timeout",
        type=float,
        help="Optional timeout in seconds applied to each solver command.",
    )
    parser.add_argument(
        "--failed-case",
        choices=("continue", "stop"),
        default="stop",
        help="Failure handling policy for this case.",
    )
    args = parser.parse_args()
    main(
        airfoil_path=args.airfoil_file,
        working_dir=args.working_dir,
        template_file=args.template_file,
        material_file=args.material_file,
        solver_timeout=args.solver_timeout,
        failed_case=args.failed_case,
    )
