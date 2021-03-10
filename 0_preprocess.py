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
    logger = logging.getLogger(subject['id']+subject['t'])
    logger.addHandler(logging.FileHandler(subject['path'].joinpath("0_preprocess_{}_{}.log".format(subject['id'], subject['t'])), mode='w'))
    logger.setLevel(logging.INFO)
    logger.info("Preprocessing subject {} at {}, step 0...".format(subject['id'], subject['t']))
    logger.info("{}".format(datetime.datetime.today()))
    logger.info("FSL version {}".format(utils.get_fsl_version()))
    logger.info("")
    start = time.perf_counter()

    # Generate mask on the 4 b0 images
    b0_file = subject['path'].joinpath(subject['t'] + "_b0.nii.gz")
    b0_mean_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_b0_mean.nii.gz")
    mask_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_mask.nii.gz")

    utils.run_and_log(["fslroi", subject['dti'], b0_file, "0", "4"], logger)
    utils.run_and_log(["fslmaths", b0_file, "-Tmean", b0_mean_file], logger)
    #utils.run_and_log(["bet", b0_mean_file, subject['path'].joinpath(subject['id'] + "_" + subject['t']), "-f", "0.5", "-g", "-0.05", "-m", "-n", "-v"], logger)
    utils.run_and_log(["bet2", b0_mean_file, subject['path'].joinpath(subject['id'] + "_" + subject['t']), "-m", "-f", "0.2", "-n", "-w", "1.2"], logger)
    utils.run_and_log(["fslmaths", mask_file, "-fillh", mask_file], logger)
    #utils.run_and_log(["fslmaths", mask_file, "-kernel", "sphere", "4", "-dilM", mask_file], logger)
    #utils.run_and_log(["fslmaths", mask_file, "-kernel", "sphere", "3", "-eroF", mask_file], logger)


    b0_file.unlink()
    b0_mean_file.unlink()

    # Compute masked magnitude
    # First split the magnitude file
    mag_name = subject['mag'].name.split(".")[0]
    utils.run_and_log(["fslsplit", subject['mag'], subject['path'].joinpath(mag_name)], logger)
    mag_0_file = subject['path'].joinpath(mag_name + "0000.nii.gz")
    mag_1_file = subject['path'].joinpath(mag_name + "0001.nii.gz")

    # Ressample mag and phase files into the dti data resolution
    mag_file = subject['path'].joinpath(subject['t'] + "_mag.nii.gz")
    phase_file = subject['path'].joinpath(subject['t'] + "_phase.nii.gz")

    utils.run_and_log(["flirt", "-in", mag_0_file, "-ref", mask_file, "-out", mag_file, "-interp", "nearestneighbour", "-applyxfm", "-usesqform", "-datatype", "short"], logger)
    utils.run_and_log(["flirt", "-in", subject['phase'], "-ref", mask_file, "-out", phase_file, "-interp", "nearestneighbour", "-applyxfm", "-usesqform", "-datatype", "short"], logger)

    # Mask from magnitude
    mag_mask_file = subject['path'].joinpath(subject['t'] + "_mag_mask.nii.gz")
    utils.run_and_log(["bet2", mag_file, subject['path'].joinpath(subject['t'] + "_mag"), "-m", "-f", "0.6", "-g", "-0.1", "-n", "-v"], logger)

    # Some erode/dilation pass to smoothen and "regularize" the mask
    utils.run_and_log(["fslmaths", mag_mask_file, "-fillh", mag_mask_file], logger)
    #utils.run_and_log(["fslmaths", mag_mask_file, "-kernel", "sphere", "4", "-ero", mag_mask_file], logger)
    #utils.run_and_log(["fslmaths", mag_mask_file, "-kernel", "sphere", "5", "-dilF", mag_mask_file], logger)

    # Mask magnitude
    utils.run_and_log(["fslmaths", mag_file, "-mas", mag_mask_file, mag_file], logger)

    # Compute fieldmap
    logger.info("Computing fieldmap...")
    fieldmap_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_fieldmap.nii.gz")
    # utils.run_and_log(["fsl_prepare_fieldmap", "SIEMENS", phase_file, mag_file, fieldmap_file, "2.46"], logger)
    utils.run_and_log(["fsl_prepare_fieldmap", "SIEMENS", phase_file, mag_file, fieldmap_file, "2.65"], logger)

    # Smooth fieldmap
    utils.run_and_log(["fugue", "--loadfmap={}".format(fieldmap_file),
                       "-s", "5",
                       "--savefmap={}".format(fieldmap_file)], logger)

    # Convert rad.s-1 into Hz
    utils.run_and_log(["fslmaths", fieldmap_file, "-div", "6.2830", fieldmap_file], logger)

    mag_0_file.unlink()
    mag_1_file.unlink()

    logger.info("")
    logger.info("0_preprocess done. Elapsed time={}".format(time.perf_counter() - start))


print("Running preprocessing...")
start = time.perf_counter()

Parallel(n_jobs=int(72/4))(delayed(preprocess)(subject) for subject in subjects)

print("Done. Elapsed time={}".format(time.perf_counter() - start))

