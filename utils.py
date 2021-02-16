import subprocess


def run_and_log(cmd, logger):
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    if output.stdout:
        logger.info(output.stdout.decode('utf-8'))

