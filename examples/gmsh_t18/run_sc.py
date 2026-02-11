import os
import pprint
import subprocess

def run_sc(
    fn_sg_sc='sg.sg',
    sgdim=3,
    analysis='H',
    swiftcomp_command='SwiftComp'
    ):

    env = os.environ.copy()
    pprint.pprint(env)

    # Get swiftcomp path from environment
    # swiftcomp_path = os.environ.get('SwiftComp_ROOT')

    cmd = [swiftcomp_command, fn_sg_sc, str(sgdim), analysis]
    print(f'Running command: {cmd}')
    cp = subprocess.run(cmd, capture_output=True, env=env)
    # cp = subprocess.run(' '.join(cmd), shell=True, capture_output=True)
    return cp
