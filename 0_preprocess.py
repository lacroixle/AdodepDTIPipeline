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


def preprocess(subject):
    # Initialize logger
    logger = logging.getLogger(subject['id'])
    logger.addHandler(logging.FileHandler(subject['path'].joinpath("0_preprocess.log"), mode='w'))
    logger.setLevel(logging.INFO)
    logger.info("Preprocessing subject {}, step 0...".format(subject['id']))
    logger.info("{}".format(datetime.datetime.today()))
    logger.info("FSL version {}".format(utils.get_fsl_version()))
    logger.info("")
    start = time.perf_counter()

    # Generate mask on the 4 b0 images
    b0_file = subject['path'].joinpath(subject['t'] + "_b0.nii.gz")
    b0_mean_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_b0_mean.nii.gz")

    utils.run_and_log(["fslroi", subject['dti'], b0_file, "0", "4"], logger)
    utils.run_and_log(["fslmaths", b0_file, "-Tmean", b0_mean_file], logger)
    b0_file.unlink()

    # Compute masked magnitude
    # First split the magnitude file
    b0_mag_name = subject['mag'].name.split(".")[0]
    utils.run_and_log(["fslsplit", subject['mag'], subject['path'].joinpath(b0_mag_name)], logger)
    b0_mag_0_file = subject['path'].joinpath(b0_mag_name + "0000.nii.gz")
    b0_mag_1_file = subject['path'].joinpath(b0_mag_name + "0001.nii.gz")

    # Ressample mag and phase files into the dti data resolution
    mag_file = subject['path'].joinpath(subject['t'] + "_mag.nii.gz")
    phase_file = subject['path'].joinpath(subject['t'] + "_phase.nii.gz")

    utils.run_and_log(["flirt", "-in", b0_mag_1_file, "-ref", b0_mean_file, "-out", mag_file, "-interp", "trilinear", "-applyxfm", "-usesqform", "-datatype", "short"], logger)
    utils.run_and_log(["flirt", "-in", subject['phase'], "-ref", b0_mean_file, "-out", phase_file, "-interp", "trilinear", "-applyxfm", "-usesqform", "-datatype", "short"], logger)

    # Mask magnitude
    mask_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_mask.nii.gz")
    utils.run_and_log(["bet2", mag_file, subject['path'].joinpath(subject['id'] + "_" + subject['t']), "-m", "-f", "0.65", "-g", "-0.1", "-n", "-w", "2"], logger)

    # Some erode/dilation pass to smoothen and "regularize" the mask
    mask_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_mask.nii.gz")
    utils.run_and_log(["fslmaths", mask_file, "-kernel", "sphere", "5", "-ero", mask_file], logger)
    utils.run_and_log(["fslmaths", mask_file, "-kernel", "sphere", "7", "-dilF", mask_file], logger)

    # Mask mag
    utils.run_and_log(["fslmaths", mag_file, "-mas", mask_file, mag_file], logger)

    # Compute fieldmap
    logger.info("Computing fieldmap...")
    fieldmap_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_fieldmap.nii.gz")
    utils.run_and_log(["fsl_prepare_fieldmap", "SIEMENS", phase_file, mag_file, fieldmap_file, "2.46"], logger)

    # Convert rad.s-1 into Hz
    utils.run_and_log(["fslmaths", fieldmap_file, "-mul", "0.159155", fieldmap_file], logger)

    b0_mag_0_file.unlink()
    b0_mag_1_file.unlink()
    # b0_ressampled_mask_file.unlink()

    logger.info("")
    logger.info("0_preprocess done. Elapsed time={}".format(time.perf_counter() - start))


print("Running preprocessing...")
start = time.perf_counter()

Parallel(n_jobs=36)(delayed(preprocess)(subject) for subject in subjects)

print("Done. Elapsed time={}".format(time.perf_counter() - start))

