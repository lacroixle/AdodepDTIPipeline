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
import math
import pandas as pd

subjects_filename = pathlib.Path(sys.argv[1])
params_file = pathlib.Path(sys.argv[2])

with open(subjects_filename, 'rb') as f:
    subjects = pickle.load(f)

subjects_params = pd.read_csv(params_file, sep=";")
subjects_params = subjects_params.set_index(['subject_id', 't'])

parallel = True

# If a subject ID is explicitely given, only process this one
if len(sys.argv) == 5:
    subject_id = sys.argv[3]
    subject_t = sys.argv[4]
    subjects = list([subject for subject in subjects if subject['id'] == subject_id and subject['t'] == subject_t])

    if not subjects:
        print("Could not find subject {} at time {}!".format(subject_id, subject_t))
        exit()

    parallel = False


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

    # Load subject params for time t
    params = {}
    try:
        params = subjects_params.loc[(subject['id'], subject['t'])].to_dict()
        params = dict([(key, params[key]) for key in params.keys() if not math.isnan(float(params[key]))])
    except:
        pass

    # Compute fieldmap for b0 image unwrapping and eddy
    # First split the magnitude file
    mag_name = subject['mag'].name.split(".")[0]
    utils.run_and_log(["fslsplit", subject['mag'], subject['path'].joinpath(mag_name)], logger)
    mag_0_file = subject['path'].joinpath(mag_name + "0000.nii.gz")
    mag_1_file = subject['path'].joinpath(mag_name + "0001.nii.gz")

    # Ressample mag and phase files into the dti data resolution
    mag_file = subject['path'].joinpath(subject['t'] + "_mag.nii.gz")
    phase_file = subject['path'].joinpath(subject['t'] + "_phase.nii.gz")

    # mag_file = subject['path'].joinpath(mag_name + "0000.nii.gz")
    # phase_file = subject['phase']

    # utils.run_and_log(["flirt", "-in", mag_0_file, "-ref", subject['dti'], "-out", mag_file, "-interp", "nearestneighbour", "-applyxfm", "-usesqform", "-datatype", "short"], logger)
    # utils.run_and_log(["flirt", "-in", subject['phase'], "-ref", subject['dti'], "-out", phase_file, "-interp", "nearestneighbour", "-applyxfm", "-usesqform", "-datatype", "short"], logger)

    f_mag_mask = params.get('f_mag_mask', 0.6)
    g_mag_mask = params.get('g_mag_mask', -0.01)

    # # Mask from magnitude
    # logger.info("Masking mag image with f={} and g={}".format(f_mag_mask, g_mag_mask))
    # mag_mask_file = subject['path'].joinpath(subject['t'] + "_mag_mask.nii.gz")
    # utils.run_and_log(["bet", mag_file, subject['path'].joinpath(subject['t'] + "_mag"), "-m", "-f", str(f_mag_mask), "-g", str(g_mag_mask), "-n", "-v", "-R"], logger)

    # # Some erode/dilation pass to smoothen and "regularize" the mask
    # utils.run_and_log(["fslmaths", mag_mask_file, "-fillh", mag_mask_file], logger)
    # utils.run_and_log(["fslmaths", mag_mask_file, "-kernel", "gauss", "3", "-fmean", "-thr", "0.55", "-bin", mag_mask_file], logger)
    # #utils.run_and_log(["fslmaths", mag_mask_file, "-kernel", "sphere", "5", "-ero", mag_mask_file], logger)
    # # Mask magnitude
    # utils.run_and_log(["fslmaths", mag_file, "-mas", mag_mask_file, mag_file], logger)
    # # utils.run_and_log(["fslmaths", mag_file, "-mas", mask_file, mag_file], logger)

    # # Compute fieldmap
    # logger.info("Computing fieldmap...")
    fieldmap_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_fieldmap.nii.gz")
    # utils.run_and_log(["fsl_prepare_fieldmap", "SIEMENS", phase_file, mag_file, fieldmap_file, "2.46"], logger)

    # Smooth fieldmap
    # utils.run_and_log(["fugue", "--loadfmap={}".format(fieldmap_file),
    #                    "--smooth3=4",
    #                    "--savefmap={}".format(fieldmap_file)], logger)

    utils.run_and_log(["flirt", "-in", fieldmap_file, "-ref", subject['dti'], "-out", fieldmap_file, "-interp", "trilinear", "-applyxfm", "-usesqform"], logger)

    # Convert Hz into rad.s^-1 (for fugue)
    utils.run_and_log(["fslmaths", fieldmap_file, "-mul", "6.2830", fieldmap_file], logger)

    # Generate mask on the 4 unwrapped b0 images
    b0_file = subject['path'].joinpath(subject['t'] + "_b0.nii.gz")
    b0_mean_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_b0_mean.nii.gz")
    b0_mean_unwarped_file = subject['path'].joinpath(subject['id'] + "_" + subject ['t'] + "_b0_unwarped.nii.gz")
    mask_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_mask.nii.gz")

    f_mask = params.get('f_mask', 0.4)
    g_mask = params.get('g_mask', -0.1)

    logger.info("Masking mean unwarped b0 image with f={} and g={}".format(f_mask, g_mask))
    utils.run_and_log(["fslroi", subject['dti'], b0_file, "0", "4"], logger)
    utils.run_and_log(["fslmaths", b0_file, "-Tmean", b0_mean_file], logger)
    utils.run_and_log(["fugue", "-i", b0_mean_file, "--dwell=0.000289996", "--loadfmap={}".format(fieldmap_file), "--unwarpdir=y", "-u", b0_mean_unwarped_file], logger)
    utils.run_and_log(["bet", b0_mean_unwarped_file, subject['path'].joinpath(subject['id'] + "_" + subject['t']), "-m", "-f", str(f_mask), "-g", str(g_mask), "-S"], logger)
    utils.run_and_log(["fslmaths", mask_file, "-kernel", "gauss", "3", "-fmean", "-thr", "0.55", "-bin", mask_file], logger)
    utils.run_and_log(["fslmaths", mask_file, "-fillh", mask_file], logger)


    #b0_file.unlink()
    #b0_mean_file.unlink()


    # Convert fieldmap back into Hz
    utils.run_and_log(["fslmaths", fieldmap_file, "-div", "6.2830", fieldmap_file], logger)

    # mag_0_file.unlink()
    # mag_1_file.unlink()

    logger.info("")
    logger.info("0_preprocess done. Elapsed time={}".format(time.perf_counter() - start))


print("Running preprocessing...")
start = time.perf_counter()

n_jobs = 18
if not parallel:
    n_jobs = 1

Parallel(n_jobs=n_jobs)(delayed(preprocess)(subject) for subject in subjects)

print("Done. Elapsed time={}".format(time.perf_counter() - start))

