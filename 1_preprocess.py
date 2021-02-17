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


def apply_eddy(subject):
    # Initialize logger
    logger = logging.getLogger(subject['id']+subject['t'])
    logger.addHandler(logging.FileHandler(subject['path'].joinpath("1_preprocess_{}_{}.log".format(subject['id'], subject['t'])), mode='w'))
    logger.setLevel(logging.INFO)
    logger.info("Preprocessing subject {} at {}, step 1...".format(subject['id'], subject['t']))
    logger.info("{}".format(datetime.datetime.today()))
    logger.info("FSL version {}".format(utils.get_fsl_version()))
    logger.info("")

    start = time.perf_counter()

    eddy_output_root = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_eddy")
    fieldmap_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_fieldmap")
    mask_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_mask.nii.gz")
    acqp_file = pathlib.Path("acqparams.txt")
    index_file = pathlib.Path("index.txt")

    success = utils.run_and_log(["eddy_cuda9.1",
                                 "--imain=" + str(subject['dti']),
                                 "--mask=" + str(mask_file),
                                 "--acqp=" + str(acqp_file),
                                 "--index=" + str(index_file),
                                 "--bvecs=" + str(subject['bvec']),
                                 "--bvals=" + str(subject['bval']),
                                 "--out=" + str(eddy_output_root),
                                 #"--field=" + str(fieldmap_file),
                                 "-v"], logger)

    logger.info("1_preprocess done. Elapsed time={}".format(time.perf_counter() - start))

    return success


for subject in subjects[:1]:
    print("Processing subject {} at {}.".format(subject['id'], subject['t']))
    success = apply_eddy(subject)
    if not success:
        print("Exception raised while processing, see log for further details...")

