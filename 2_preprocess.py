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


def compute_dti(subject):
    # Initialize logger
    logger = logging.getLogger(subject['id']+subject['t'])
    logger.addHandler(logging.FileHandler(subject['path'].joinpath("2_preprocess_{}_{}.log".format(subject['id'], subject['t'])), mode='w'))
    logger.setLevel(logging.INFO)
    logger.info("Preprocessing subject {} at {}, step 2...".format(subject['id'], subject['t']))
    logger.info("{}".format(datetime.datetime.today()))
    logger.info("FSL version {}".format(utils.get_fsl_version()))
    logger.info("")

    start = time.perf_counter()

    dtifit_output_root = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_dtifit")
    mask_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_mask.nii.gz")
    data_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_eddy.nii.gz")

    success = utils.run_and_log(["dtifit",
                                 "--data={}".format(subject['dti']),
                                 "--out={}".format(dtifit_output_root),
                                 "--mask={}".format(mask_file),
                                 "--bvecs={}".format(subject['bvec']),
                                 "--bvals={}".format(subject['bval']),
                                 "-V"], logger)

    logger.info("2_preprocess done. Elapsed time={}".format(time.perf_counter() - start))

    return success


# for subject in subjects:
#     print("Processing subject {} at {}.".format(subject['id'], subject['t']))
#     success = compute_dti(subject)
#     if not success:
#         print("Exception raised while processing, see log for further details...")

Parallel(n_jobs=4)(delayed(compute_dti)(subject) for subject in subjects)

