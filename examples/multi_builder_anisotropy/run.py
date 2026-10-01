"""Recompute the energy-ratio anisotropy measure from the published stiffness matrices.

    uv run python run.py

Reads the effective stiffness C of every case from results/summary.csv (SwiftComp output,
also in results/<builder>/<case>.sg.k), recomputes A_energy_ratio with energy_ratio.py and
checks it against the stored value. Building the models and running SwiftComp needs the
modeling tools and is not part of this example's environment.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from energy_ratio import energy_ratio_based_measure

HERE = Path(__file__).parent


def stiffness(row):
    """Symmetric 6x6 Voigt stiffness from the C11..C66 columns of a summary row."""
    C = np.zeros((6, 6))
    for i in range(6):
        for j in range(i, 6):
            C[i, j] = C[j, i] = row[f"C{i + 1}{j + 1}"]
    return C


def main():
    summary = pd.read_csv(HERE / "results" / "summary.csv")
    for _, row in summary.iterrows():
        A = energy_ratio_based_measure(stiffness(row))
        print(f"{row['case']:<22} A_energy_ratio = {A:8.4f}  (stored {row['A_energy_ratio']:8.4f})")
        assert abs(A - row["A_energy_ratio"]) < 1e-6 * max(1.0, A), row["case"]


if __name__ == "__main__":
    main()
