import os
import sys
import glob
import subprocess
import pathlib
from joblib import Parallel, delayed
import time

b0_folder = os.environ['B0_FOLDER']
output_folder_mag = sys.argv[1]
b0_mask_folder = sys.argv[2]

# We first retrieve a list of subject ids
subject_ids = glob.glob(b0_folder + "*.nii.gz")
subject_ids = list(dict.fromkeys([pathlib.PurePosixPath(subject_id).name.split("_")[0] for subject_id in subject_ids]))

# Build a list of b0_mag and b0_phase pair for each subject and timepoint
b0_maps = []
for subject_id in subject_ids:
	b0_mag_bas = pathlib.Path(b0_folder + subject_id + "_magbas.nii.gz")
	b0_phase_bas = pathlib.Path(b0_folder + subject_id + "_phasebas.nii.gz")
	b0_mag_fu = pathlib.Path(b0_folder + subject_id + "_magfu.nii.gz")
	b0_phase_fu = pathlib.Path(b0_folder + subject_id + "_phasefu.nii.gz")

	if not all([b0_mag_bas.exists(), b0_phase_bas.exists(), b0_mag_fu.exists(), b0_phase_fu.exists()]):
		continue

	b0_maps.append({'subject_id': subject_id, 't': "bas", 'mag': b0_mag_bas, 'phase': b0_phase_bas})
	b0_maps.append({'subject_id': subject_id, 't': "fu", 'mag': b0_mag_fu, 'phase': b0_phase_fu})


def compute_field(b0_map):
	# Compute masked magnitude
	# ========================

	# First split the magnitude file
	b0_mag_name = b0_map['mag'].name.split(".")[0]
	subprocess.run(["fslsplit", b0_map['mag'], output_folder_mag + b0_mag_name])
	b0_mag_0_filename = output_folder_mag + b0_mag_name + "0000.nii.gz"
	b0_mag_1_filename = output_folder_mag + b0_mag_name + "0001.nii.gz"

	# Ressample b0 mask into mag file resolution
	b0_mask_filename = b0_mask_folder + b0_map['subject_id'] + "_dti" + b0_map['t'] + "_b0_extracted_mask.nii.gz"
	b0_ressampled_mask_filename = output_folder_mag + b0_map['subject_id'] + "_dti" + b0_map['t'] + "_b0_ressampled_mask.nii.gz"
	subprocess.run(["flirt", "-in", b0_mask_filename, "-ref", b0_mag_0_filename, "-out", b0_ressampled_mask_filename, "-applyxfm", "-usesqform"])

	# Mask mag
	subprocess.run(["fslmaths", b0_mag_0_filename, "-mas", b0_ressampled_mask_filename, b0_mag_0_filename])

	# Compute fieldmap
	# ================

	fieldmap_filename = output_folder_mag + b0_map['subject_id'] + "_" + b0_map['t'] + "_fieldmap.nii.gz"
	subprocess.run(["fsl_prepare_fieldmap", "SIEMENS", b0_map['phase'], b0_mag_0_filename, fieldmap_filename, "2.46"])

	# Upsample fieldmap
	subprocess.run(["flirt", "-in", fieldmap_filename, "-ref", b0_mask_filename, "-out", fieldmap_filename, "-applyxfm", "-usesqform"])

	# Convert rad.s-1 into Hz
	subprocess.run(["fslmaths", fieldmap_filename, "-mul", "0.159155", fieldmap_filename])

	# Cleanup
	# =======
	pathlib.Path(b0_mag_0_filename).unlink()
	pathlib.Path(b0_mag_1_filename).unlink()
	pathlib.Path(b0_ressampled_mask_filename).unlink()


start = time.perf_counter()
Parallel(n_jobs=36)(delayed(compute_field)(b0_map) for b0_map in b0_maps)
print("Elapsed time={}".format(time.perf_counter() - start))

