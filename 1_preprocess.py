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


# If a subject ID is explicitely given, only process this one
if len(sys.argv) == 4:
    subject_id = sys.argv[2]
    subject_t = sys.argv[3]
    subjects = list([subject for subject in subjects if subject['id'] == subject_id and subject['t'] == subject_t])

    if not subjects:
        print("Could not find subject {} at time {}!".format(subject_id, subject_t))
        exit()


def apply_eddy(subject):
    print("Processing subject {} at {}.".format(subject['id'], subject['t']))

    # Initialize logger
    logger = logging.getLogger(subject['id']+subject['t'])
    logger.addHandler(logging.FileHandler(subject['path'].joinpath("1_preprocess_{}_{}.log".format(subject['id'], subject['t'])), mode='w'))
    logger.setLevel(logging.INFO)
    logger.info("Preprocessing subject {} at {}, step 1...".format(subject['id'], subject['t']))
    logger.info("{}".format(datetime.datetime.today()))
    logger.info("FSL version {}".format(utils.get_fsl_version()))
    logger.info("")

    start = time.perf_counter()

    index_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_index.txt")

    # First generate index file to match the number of b0 values.
    with open(subject['bval'], 'r') as f:
        count = len(f.read()[:-2].split(" "))

    with open(index_file, 'w') as f:
        f.write("1 "*count)

    logger.info("Found {} diffusion directions.".format(count))

    eddy_output_root = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_eddy")
    fieldmap_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_fieldmap")
    mask_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_mask.nii.gz")
    acqp_file = pathlib.Path("acqparams.txt")

    success = utils.run_and_log(["eddy_cuda9.1",
                                 "--imain=" + str(subject['dti']),
                                 "--mask=" + str(mask_file),
                                 "--acqp=" + str(acqp_file),
                                 "--index=" + str(index_file),
                                 "--bvecs=" + str(subject['bvec']),
                                 "--bvals=" + str(subject['bval']),
                                 "--out=" + str(eddy_output_root),
                                 "--field=" + str(fieldmap_file),
                                 "--repol",
                                 "--slspec=slspec.txt",
                                 # "--json=DTI_spec.json",
                                 "--niter=6",
                                 "--fwhm=10,5,1,0,0,0",
                                 "--mporder=8",
                                 "--s2v_niter=8",
                                 "--ol_type=both",
                                 "--estimate_move_by_susceptibility",
                                 "--very_verbose"], logger)

    logger.info("1_preprocess done. Elapsed time={}".format(time.perf_counter() - start))

    return success


for subject in subjects:
    success = apply_eddy(subject)
    if not success:
        print("Exception raised while processing, see log for further details...")


