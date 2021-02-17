import subprocess
import pathlib
import os


def run_and_log(cmd, logger):
    try:
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except Exception as e:
        logger.info(e.stdout.decode('utf-8'))
        logger.error(e)
        logger.error(e.stderr.decode('utf-8'))

        return False
    else:
        logger.info(output.stdout.decode('utf-8'))

        return True


def get_fsl_version():
    fsl_dir = os.environ['FSL_DIR']
    if not fsl_dir:
        raise RuntimeError("FSL_DIR not set!")

    version_filename = "{}/etc/fslversion".format(fsl_dir)
    with open(version_filename, 'r') as f:
        version = f.readline()

    return version

