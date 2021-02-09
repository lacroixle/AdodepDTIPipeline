import os
import sys
import glob
import subprocess
import pathlib
from joblib import Parallel, delayed
import time

dti_folder = os.environ['DTI_FOLDER']
output_folder_b0 = sys.argv[1]
output_folder_b0_mean = sys.argv[2]
output_folder_b0_mask = sys.argv[3]

dti_files = glob.glob(dti_folder + "*.nii.gz")
dti_files = [pathlib.PurePosixPath(dti_file) for dti_file in dti_files]

def process_file(dti_file):
	subject_id = dti_file.name.split(".")[0]
	output_b0_filename = output_folder_b0 + subject_id + "_b0.nii.gz"
	output_b0_mean_filename = output_folder_b0_mean + subject_id + "_b0_mean.nii.gz"
	output_b0_mask_filename = output_folder_b0_mask + subject_id + "_b0_extracted.nii.gz"
	print("Extracting B0 volumes from {}".format(subject_id))
	subprocess.run(["fslroi", str(dti_file), output_b0_filename, "0", "4"])
	subprocess.run(["fslmaths", output_b0_filename, "-Tmean", output_b0_mean_filename])
	subprocess.run(["bet", output_b0_mean_filename, output_b0_mask_filename, "-f", "0.2", "-m"])

start = time.perf_counter()
Parallel(n_jobs=36)(delayed(process_file)(dti_file) for dti_file in dti_files)
print("Elapsed time={}".format(time.perf_counter() - start))

