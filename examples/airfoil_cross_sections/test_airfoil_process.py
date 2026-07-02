from pre_process import *


airfoil_file = Path(__file__).parent / "coord_seligFmt" / "ah93k130.dat"

airfoil_data = process_airfoil_data(airfoil_file)

print(airfoil_data.title)
print("LE point:", airfoil_data.le_point)
print("TE point:", airfoil_data.te_point)

print("Upper coordinates:")
for x, y in zip(*airfoil_data.upper):
    print(f"({x}, {y})")
print("Lower coordinates:")
for x, y in zip(*airfoil_data.lower):
    print(f"({x}, {y})")
