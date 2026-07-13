from __future__ import annotations

"""Post-process VABS output files for the airfoil cross-section example.

This module isolates read-only operations on previously generated VABS output
files so that properties can be re-extracted without re-running the expensive
geometry generation and solver pipeline.
"""

import argparse
from pathlib import Path
from typing import Any

import sgio

from .helpers import ensure_root_logging, resolve_path


def read_vabs_output(vabs_output_path: str | Path) -> Any:
    """Read one VABS output file into an SGIO model object.

    Parameters
    ----------
    vabs_output_path : str or Path
        Path to a VABS output file such as ``airfoil_cs.sg.k`` or
        ``airfoil_cs.sg.K``.

    Returns
    -------
    Any
        Parsed SGIO model object returned by ``sgio.read_output_model``.

    Raises
    ------
    RuntimeError
        If the output file cannot be parsed into a model.
    """
    vabs_output_path = resolve_path(vabs_output_path)
    model = sgio.read_output_model(
        str(vabs_output_path),
        file_format="vabs",
        model_type="BM2",
    )
    if model is None:
        raise RuntimeError(f"Failed to read VABS output: {vabs_output_path}")
    return model


def extract_properties(model: Any, property_names: list[str]) -> dict[str, Any]:
    """Extract named properties from an SGIO model.

    Parameters
    ----------
    model : Any
        SGIO model object that implements ``get(name)`` and optionally
        ``getAll()``.
    property_names : list of str
        Property identifiers such as ``ea``, ``gj``, ``ei22``, or ``ei33``.

    Returns
    -------
    dict of str to Any
        Mapping from requested property names to extracted values.

    Raises
    ------
    TypeError
        If ``model`` does not provide the required ``get`` interface.
    KeyError
        If a requested property name is not recognized by the model.
    """
    if not hasattr(model, "get"):
        raise TypeError(f"Model does not support property lookup via get(): {type(model)!r}")

    available_names = set()
    if hasattr(model, "getAll"):
        available_names = {name.lower() for name in model.getAll().keys()}

    extracted: dict[str, Any] = {}
    for property_name in property_names:
        value = model.get(property_name)
        if value is None and available_names and property_name.lower() not in available_names:
            raise KeyError(
                f"Property '{property_name}' not found. Available keys: "
                f"{', '.join(sorted(available_names))}"
            )
        extracted[property_name] = value
    return extracted


def post_process_vabs_output(
    vabs_output_path: str | Path,
    property_names: list[str],
) -> dict[str, Any]:
    """Read a VABS output file and extract selected properties.

    Parameters
    ----------
    vabs_output_path : str or Path
        Path to the VABS output file.
    property_names : list of str
        Property identifiers to extract from the parsed model.

    Returns
    -------
    dict of str to Any
        Extracted property values keyed by property name.
    """
    model = read_vabs_output(vabs_output_path)
    return extract_properties(model, property_names)


def main() -> None:
    """Run the post-processing CLI for one VABS output file.

    Returns
    -------
    None
        Requested properties are printed to standard output in ``name,value``
        format, one property per line.
    """
    ensure_root_logging()
    parser = argparse.ArgumentParser(
        description="Read one VABS output file and extract selected properties."
    )
    parser.add_argument(
        "--vabs-output",
        required=True,
        help="Path to the VABS output file, such as airfoil_cs.sg.k.",
    )
    parser.add_argument(
        "--properties",
        nargs="+",
        required=True,
        help="Property names to extract, such as ea gj ei22 ei33.",
    )
    args = parser.parse_args()

    props = post_process_vabs_output(args.vabs_output, args.properties)
    for name, value in props.items():
        print(f"{name},{value}")


if __name__ == "__main__":
    main()
