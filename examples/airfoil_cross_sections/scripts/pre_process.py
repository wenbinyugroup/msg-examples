from __future__ import annotations

"""Airfoil data pre-processing utilities.

This module reads airfoil coordinate files, computes LE/TE camber-line
points, and exports normalized coordinates in Selig format for use by
the cross-section analysis workflow.
"""

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import airfoils
import numpy as np
from airfoils import fileio


@dataclass(frozen=True)
class ProcessedAirfoilData:
    """Processed airfoil data used by the case runner."""

    title: str
    upper: tuple[tuple[float, ...], tuple[float, ...]]
    lower: tuple[tuple[float, ...], tuple[float, ...]]
    x_precision: int
    y_precision: int
    le_point: tuple[float, float]
    te_point: tuple[float, float]
    te_fill_point: tuple[float, float]
    airfoil: airfoils.Airfoil


def infer_coordinate_precision(airfoil_file: str | Path) -> tuple[int, int]:
    """Infer decimal precision for x/y coordinates from an airfoil file."""
    coordinate_pattern = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
    x_precision = 6
    y_precision = 6

    with Path(airfoil_file).open("r", encoding="utf-8") as infile:
        for line_number, raw_line in enumerate(infile):
            if line_number == 0:
                continue

            values = coordinate_pattern.findall(raw_line)
            if len(values) < 2:
                continue

            x_precision = max(x_precision, _count_decimal_places(values[0]))
            y_precision = max(y_precision, _count_decimal_places(values[1]))

    return x_precision, y_precision


def _count_decimal_places(value: str) -> int:
    """Count decimal places in a numeric string, handling scientific notation."""
    mantissa = value.lower().split("e", maxsplit=1)[0]
    if "." not in mantissa:
        return 0
    return len(mantissa.split(".", maxsplit=1)[1])


def format_point(point: tuple[float, float], x_precision: int, y_precision: int) -> tuple[str, str]:
    """Format one point using the requested x/y decimal precision."""
    return (
        f"{point[0]:.{x_precision}f}",
        f"{point[1]:.{y_precision}f}",
    )


def round_with_precision(value: float, precision: int) -> float:
    """Round one value to the requested precision and normalize tiny values to zero."""
    rounded = round(value, precision)
    tolerance = max(10 ** (-precision), 1e-12)
    if abs(rounded) < tolerance:
        return 0.0
    return rounded


def _import_airfoil_data(
    airfoil_file: str | Path,
) -> tuple[np.ndarray, np.ndarray]:
    """Import upper/lower coordinates, tolerating headers that start with a digit.

    ``airfoils.fileio._import_format_1`` only skips a header line when it starts
    with a letter (``^[a-z]``). Airfoil names such as ``74-130 WP2`` or
    ``12% JOUKOWSKI AIRFOIL`` begin with a digit, so the library treats them as
    coordinate rows and crashes in ``np.fromstring``. We copy the coordinate
    lines to a temporary file with a header the library reliably ignores, then
    delegate to the library so its normalization/splitting logic is preserved.
    """
    source = Path(airfoil_file)
    lines = source.read_text(encoding="utf-8").splitlines()
    # A leading '#' is not a letter nor a number-start, so the library skips it.
    sanitized = ["# airfoil", *lines[1:]]

    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".dat", delete=False, encoding="utf-8"
    )
    try:
        tmp.write("\n".join(sanitized) + "\n")
        tmp.close()
        return fileio.import_airfoil_data(tmp.name)
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def process_airfoil_data(airfoil_file: str | Path) -> ProcessedAirfoilData:
    """Read an airfoil coordinate file and compute LE/TE camber-line points.

    Parameters
    ----------
    airfoil_file : str or Path
        Path to an airfoil coordinate file readable by ``airfoils.fileio``.

    Returns
    -------
    ProcessedAirfoilData
        Title, normalized upper/lower coordinate arrays, and two camber-line
        points ``(le_point, te_point)`` at the normalized leading and
        trailing edge locations.
    """
    airfoil_path = Path(airfoil_file)
    with airfoil_path.open("r", encoding="utf-8") as infile:
        title = infile.readline().rstrip("\r\n")

    x_precision, y_precision = infer_coordinate_precision(airfoil_path)
    upper_raw, lower_raw = _import_airfoil_data(airfoil_path)
    airfoil = airfoils.Airfoil(upper_raw, lower_raw)
    le_point = (
        round_with_precision(0.0, x_precision),
        round_with_precision(float(airfoil.camber_line(0.0)), y_precision),
    )
    te_point = (
        round_with_precision(1.0, x_precision),
        round_with_precision(float(airfoil.camber_line(1.0)), y_precision),
    )
    te_fill_point = (
        round_with_precision(0.95, x_precision),
        round_with_precision(float(airfoil.camber_line(0.95)), y_precision),
    )
    upper = (
        tuple(float(value) for value in upper_raw[0]),
        tuple(float(value) for value in upper_raw[1]),
    )
    lower = (
        tuple(float(value) for value in lower_raw[0]),
        tuple(float(value) for value in lower_raw[1]),
    )
    return ProcessedAirfoilData(
        title=title,
        upper=upper,
        lower=lower,
        x_precision=x_precision,
        y_precision=y_precision,
        le_point=le_point,
        te_point=te_point,
        te_fill_point=te_fill_point,
        airfoil=airfoil,
    )


def find_thickness_location(
    airfoil: airfoils.Airfoil,
    half_thickness: float,
    *,
    n_samples: int = 1000,
) -> float:
    """Find the chordwise location where the airfoil thickness equals ``2 * t``.

    Scanning from the trailing edge (x = 1) toward the leading edge (x = 0),
    this returns the x-coordinate of the first location where the local
    airfoil thickness ``y_upper(x) - y_lower(x)`` reaches ``2 * half_thickness``.

    Parameters
    ----------
    airfoil : airfoils.Airfoil
        Airfoil whose thickness distribution is evaluated.
    half_thickness : float
        Half the target thickness ``t`` (e.g. ``0.01``); the target thickness
        is ``2 * t``.
    n_samples : int, optional
        Number of chordwise samples used to bracket the crossing.

    Returns
    -------
    float
        Chordwise (x) coordinate of the first crossing, in ``[0, 1]``. If the
        trailing edge is already thicker than ``2 * half_thickness`` (a blunt
        trailing edge whose gap exceeds the combined skin thickness), the two
        skins never meet before the trailing edge, so ``1.0`` is returned and
        the fill region begins at the trailing edge itself.

    Raises
    ------
    ValueError
        If the target thickness is never reached along the chord (the airfoil
        is everywhere thinner than ``2 * half_thickness``).
    """
    target = 2.0 * half_thickness
    # Sample from the trailing edge toward the leading edge.
    xs = np.linspace(1.0, 0.0, n_samples)
    thickness = airfoil.y_upper(xs) - airfoil.y_lower(xs)

    # Blunt trailing edge: if the trailing-edge gap already exceeds the combined
    # skin thickness, the top and bottom skins meet at (or beyond) the trailing
    # edge, so the fill region starts at the trailing edge.
    if thickness[0] >= target:
        return 1.0

    diff = thickness - target

    for i in range(1, len(xs)):
        if diff[i - 1] == 0.0:
            return float(xs[i - 1])
        if diff[i - 1] * diff[i] < 0.0:
            # Linear interpolation between the bracketing samples.
            x0, x1 = xs[i - 1], xs[i]
            d0, d1 = diff[i - 1], diff[i]
            return float(x0 - d0 * (x1 - x0) / (d1 - d0))

    if diff[-1] == 0.0:
        return float(xs[-1])

    raise ValueError(
        f"Thickness {target} (2 * {half_thickness}) is never reached along the chord."
    )


def export_selig_airfoil_file(
    output_file: str | Path,
    processed_airfoil: ProcessedAirfoilData,
) -> None:
    """Write processed airfoil coordinates in Selig format."""
    upper_x, upper_y = processed_airfoil.upper
    lower_x, lower_y = processed_airfoil.lower

    if upper_x[0] < upper_x[-1]:
        upper_points = list(zip(reversed(upper_x), reversed(upper_y)))
    else:
        upper_points = list(zip(upper_x, upper_y))

    if lower_x[0] > lower_x[-1]:
        lower_points = list(zip(reversed(lower_x), reversed(lower_y)))
    else:
        lower_points = list(zip(lower_x, lower_y))

    lines = [processed_airfoil.title]
    lines.extend(
        f"{x:.{processed_airfoil.x_precision}f} {y:.{processed_airfoil.y_precision}f}"
        for x, y in upper_points
    )
    lines.extend(
        f"{x:.{processed_airfoil.x_precision}f} {y:.{processed_airfoil.y_precision}f}"
        for x, y in lower_points[1:]
    )
    Path(output_file).write_text("\n".join(lines) + "\n", encoding="utf-8")
