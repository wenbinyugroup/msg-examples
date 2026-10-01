"""Run every builder for its geometry sweep x two material sets (set1, set2).

    .venv/Scripts/python build_all.py [builder ...]

Each builder runs in its own environment (its own uv venv, or Abaqus's Python), with the
builder directory as working directory. Cases are named <prefix>_<set1|set2>_<value>, where
value is the swept geometry parameter with "." written as "p" (Abaqus job names allow no dots).
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent

# builder: (case prefix, swept parameter, CLI flag, values, baseline value,
#           {"set1": extra args, "set2": extra args}, command prefix)
SWEEPS = {
    "abaqus_honeycomb": (
        "honeycomb", "t/l", "--t-over-l", ["0.05", "0.10", "0.15", "0.20"], "0.10",
        {"set1": ["--material", "aluminum_5052_h32"],
         "set2": ["--material", "as4_8773_lamina", "--ply-angle", "90"]},
        [shutil.which("abaqus") or "abaqus", "cae", "noGUI=build.py", "--"],
    ),
    "gmshmodel_udfrp": (
        "udfrp", "fibre count", "--count", ["4", "8", "12", "16"], "16",
        {"set1": ["--fibre", "e_glass_fibre_nittobo"], "set2": ["--fibre", "t300_carbon_fibre"]},
        ["uv", "run", "python", "build.py"],
    ),
    "microgen_tpms": (
        "tpms", "offset", "--offset", ["0.5", "0.8", "1.1", "1.4"], "0.5",
        {"set1": ["--material", "peek_victrex_450g"], "set2": ["--material", "ti6al4v_am"]},
        ["uv", "run", "--no-sync", "python", "build.py"],  # no-sync keeps the re-pinned VTK
    ),
    "texgen_weave": (
        "weave", "yarn spacing", "--spacing", ["0.85", "1.0", "1.2", "1.4"], "1.0",
        {"set1": ["--yarn", "e_glass_fibre_nittobo"], "set2": ["--yarn", "as4_8773_lamina"]},
        ["uv", "run", "python", "build.py"],
    ),
}


def case_name(builder, material, value):
    return f"{SWEEPS[builder][0]}_{material}_{value.replace('.', 'p')}"


def main(builders):
    for builder in builders:
        _, _, flag, values, _, materials, command = SWEEPS[builder]
        for material, extra in materials.items():
            for value in values:
                args = command + [flag, value, *extra, "--name", case_name(builder, material, value)]
                print(">", " ".join(args), flush=True)
                subprocess.run(args, cwd=HERE / "builders" / builder, check=True)
                # abaqus.bat exits 0 even when CAE fails, so check the output instead
                if not list((HERE / "models" / builder).glob(case_name(builder, material, value) + ".*")):
                    raise RuntimeError(f"{builder} wrote no model for {args}")


if __name__ == "__main__":
    main(sys.argv[1:] or list(SWEEPS))
