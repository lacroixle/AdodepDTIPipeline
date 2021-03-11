import os
import contextlib
import sys
import glob
import subprocess
import pathlib
from joblib import Parallel, delayed
import time
import logging
import pickle


data_folder = pathlib.Path(sys.argv[1])
output_filename = pathlib.Path(sys.argv[2])
output_folder = pathlib.Path(sys.argv[3])

b0_folder = data_folder.joinpath("B0_maps")
dti_folder = data_folder.joinpath("DTI")


# We first retrieve a list of subject ids
subject_ids = b0_folder.glob("*.nii.gz")
subject_ids = list(dict.fromkeys([pathlib.PurePosixPath(subject_id).name.split("_")[0] for subject_id in subject_ids]))


# Build a list of b0_mag and b0_phase pair for each subject and timepoint
subjects = []
for subject_id in subject_ids:
    b0_mag_bas = b0_folder.joinpath(subject_id + "_magbas.nii.gz")
    b0_phase_bas = b0_folder.joinpath(subject_id + "_phasebas.nii.gz")
    b0_mag_fu = b0_folder.joinpath(subject_id + "_magfu.nii.gz")
    b0_phase_fu = b0_folder.joinpath(subject_id + "_phasefu.nii.gz")
    dti_bas = dti_folder.joinpath(subject_id + "_dtibas.nii.gz")
    dti_fu = dti_folder.joinpath(subject_id + "_dtifu.nii.gz")
    bvec_bas = dti_folder.joinpath(subject_id + "_dtibas.bvec")
    bval_bas = dti_folder.joinpath(subject_id + "_dtibas.bval")
    bvec_fu = dti_folder.joinpath(subject_id + "_dtifu.bvec")
    bval_fu = dti_folder.joinpath(subject_id + "_dtifu.bval")

    if not all([b0_mag_bas.exists(), b0_phase_bas.exists(), b0_mag_fu.exists(), b0_phase_fu.exists(), dti_bas.exists(), dti_fu.exists()]):
        print("Missing informations for {}".format(subject_id))
        continue

    subject_path = output_folder.joinpath(subject_id)
    subject_path.mkdir(exist_ok=True)

    subjects.append({'id': subject_id, 'path': subject_path, 't': "bas", 'mag': b0_mag_bas, 'phase': b0_phase_bas, 'dti': dti_bas, 'bvec': bvec_bas, 'bval': bval_bas})
    subjects.append({'id': subject_id, 'path': subject_path, 't': "fu", 'mag': b0_mag_fu, 'phase': b0_phase_fu, 'dti': dti_fu, 'bvec': bvec_fu, 'bval': bval_fu})

print("Found {} subjects.".format(len(subjects)))

with open(output_filename, 'wb') as f:
    pickle.dump(subjects, f)


