import os

import sgio

def convert_sg(
    fn_sg_in='sg.msh',
    fn_materials='materials.json',
    fn_sg_out='sg.sg'
    ):

    # fn = 'sg.msh'

    sg = sgio.read(fn_sg_in, file_format='gmsh')
    # print(sg)

    # Load materials from JSON file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    materials_file = os.path.join(script_dir, fn_materials)

    sg.materials = sgio.read_materials_from_json(materials_file)

    sgio.write(sg, fn_sg_out, file_format='sc')


if __name__ == "__main__":
    convert_sg()
