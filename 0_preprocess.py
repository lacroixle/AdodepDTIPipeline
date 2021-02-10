import os
import contextlib
import sys
import glob
import subprocess
import pathlib
from joblib import Parallel, delayed
import time
import logging


data_folder = pathlib.Path(os.environ['DATAFOLDER'])
b0_folder = data_folder.joinpath("B0_maps")
dti_folder = data_folder.joinpath("DTI")
output_folder = pathlib.Path(sys.argv[1])


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

    if not all([b0_mag_bas.exists(), b0_phase_bas.exists(), b0_mag_fu.exists(), b0_phase_fu.exists(), dti_bas.exists(), dti_fu.exists()]):
        continue

    subject_path = output_folder.joinpath(subject_id)
    subject_path.mkdir(exist_ok=True)

    subjects.append({'id': subject_id, 'path': subject_path, 't': "bas", 'mag': b0_mag_bas, 'phase': b0_phase_bas, 'dti': dti_bas})
    subjects.append({'id': subject_id, 'path': subject_path, 't': "fu", 'mag': b0_mag_fu, 'phase': b0_phase_fu, 'dti': dti_fu})


def preprocess(subject):
    # Generate mask on the 4 b0 images
    b0_file = subject['path'].joinpath(subject['t'] + "_b0.nii.gz")
    b0_mean_file = subject['path'].joinpath(subject['t'] + "_b0_mean.nii.gz")
    b0_mask_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_b0_mask.nii.gz")

    subprocess.run(["fslroi", subject['dti'], b0_file, "0", "4"])
    subprocess.run(["fslmaths", b0_file, "-Tmean", b0_mean_file])
    subprocess.run(["bet", b0_mean_file, subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_b0"), "-f", "0.5", "-m", "-n"])
    b0_file.unlink()
    b0_mean_file.unlink()

    # Compute masked magnitude
    # First split the magnitude file
    b0_mag_name = subject['mag'].name.split(".")[0]
    subprocess.run(["fslsplit", subject['mag'], subject['path'].joinpath(b0_mag_name)])
    b0_mag_0_file = subject['path'].joinpath(b0_mag_name + "0000.nii.gz")
    b0_mag_1_file = subject['path'].joinpath(b0_mag_name + "0001.nii.gz")

    # Ressample b0 mask into mag file resolution
    b0_ressampled_mask_file = subject['path'].joinpath(b0_mag_name + "_b0_ressampled_mask.nii.gz")
    subprocess.run(["flirt", "-in", b0_mask_file, "-ref", b0_mag_0_file, "-out", b0_ressampled_mask_file, "-applyxfm", "-usesqform"])

    # Mask mag
    subprocess.run(["fslmaths", b0_mag_0_file, "-mas", b0_ressampled_mask_file, b0_mag_0_file])

    fieldmap_file = subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_fieldmap.nii.gz")
    subprocess.run(["fsl_prepare_fieldmap", "SIEMENS", subject['phase'], b0_mag_0_file, fieldmap_file, "2.46"])

    # Upsample fieldmap
    subprocess.run(["flirt", "-in", fieldmap_file, "-ref", b0_mask_file, "-out", fieldmap_file, "-applyxfm", "-usesqform"])

    # Convert rad.s-1 into Hz
    subprocess.run(["fslmaths", fieldmap_file, "-mul", "0.159155", fieldmap_file])

    b0_mag_0_file.unlink()
    b0_mag_1_file.unlink()
    b0_ressampled_mask_file.unlink()


print("Running preprocessing...")
start = time.perf_counter()

with open(os.devnull, 'w') as devnull:
    with contextlib.redirect_stdout(devnull):
        Parallel(n_jobs=36)(delayed(preprocess)(subject) for subject in subjects[:1])

print("Done. Elapsed time=".format(time.perf_counter() - start))

