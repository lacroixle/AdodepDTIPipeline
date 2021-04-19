import subprocess
import sys
import logging
import pathlib
from joblib import Parallel, delayed
import time
import logging
import pickle
import utils
import datetime

subjects_filename = pathlib.Path(sys.argv[1])

with open(subjects_filename, 'rb') as f:
    subjects = pickle.load(f)


def eddy_qc(subject):
    # Initialize logger
    logger = logging.getLogger(subject['id']+subject['t'])
    logger.addHandler(logging.FileHandler(subject['path'].joinpath("1_qc_{}_{}.log".format(subject['id'], subject['t'])), mode='w'))
    logger.setLevel(logging.INFO)
    logger.info("Eddy output quality control for subject {} at {}...".format(subject['id'], subject['t']))
    logger.info("{}".format(datetime.datetime.today()))
    logger.info("FSL version {}".format(utils.get_fsl_version()))
    logger.info("")

    start = time.perf_counter()


    eddy_qc_folder = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_eddy.qc")
    if eddy_qc_folder.exists():
        files = eddy_qc_folder.glob("*")
        [f.unlink() for f in files]
        eddy_qc_folder.rmdir()

    success = utils.run_and_log(["eddy_quad", subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_eddy"), "-idx", subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_index.txt"), "-par", "acqparams.txt", "-m", subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_mask.nii.gz"), "-b", subject['bval'], "--field={}".format(subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_fieldmap.nii.gz")), "-g", subject['bvec']], logger)


    logger.info("1_qc done. Elapsed time={}".format(time.perf_counter() - start))

    return success


for subject in subjects:
    print("Eddy QC for subject {} at {}.".format(subject['id'], subject['t']))

# start = time.perf_counter()
# Parallel(n_jobs=1, batch_size=5)(delayed(eddy_qc)(subject) for subject in subjects)
# print("Done. Elapsed time={}".format(time.perf_counter() - start))

