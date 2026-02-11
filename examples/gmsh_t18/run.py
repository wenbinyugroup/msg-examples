import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh = logging.FileHandler('run.log')
fh.setLevel(logging.INFO)
logger.addHandler(fh)

import os

import numpy as np
import pandas as pd
import sgio

from build_sg import build_sg
from convert import convert_sg

working_dir = 'evals'

# Run SG analysis for a range of radii
radii = np.linspace(0.1, 0.4, 7)
logger.info(f'{radii=}')

out = []

eng_const_names = [
    'e1', 'e2', 'e3', 'nu12', 'nu13', 'nu23', 'g12', 'g13', 'g23'
    ]

for i, radius in enumerate(radii):
    logger.info(f'Running for radius: {radius}')

    _out = {'radius': radius}

    # Create working directory if it doesn't exist
    wd = os.path.join(working_dir, f'eval.{i}')
    if not os.path.exists(wd):
        os.makedirs(wd)

    # Build SG using gmsh
    fn_sg_base = os.path.join(wd, 'sg')
    build_sg(radius=radius, fn_sg_base=fn_sg_base, fn_materials='data/materials.json', mesh_size=0.05, nopopup=True)

    # Convert to SwiftComp format
    fn_sg_sc = f'{fn_sg_base}.sg'
    convert_sg(fn_sg_in=f'{fn_sg_base}.msh', fn_sg_out=fn_sg_sc)
    _out['fn_sg_sc'] = fn_sg_sc

    # Run SwiftComp and read output
    sgio.run('swiftcomp', fn_sg_sc, 'h', smdim=3)
    sc_out = sgio.read_output_model(f'{fn_sg_sc}.k', file_format='sc', model_type='sd1')
    _props = sc_out.model_dump(exclude_none=True)
    for i, name in enumerate(eng_const_names):
        _out[name] = _props[name]

    out.append(_out)

# Write results to CSV
df = pd.DataFrame(out)
df.to_csv('results/t18_results.csv', index=False)
