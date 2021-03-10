import pathlib
import time
import sys
import numpy as np
import subprocess
import ast
import string
import copy
from joblib import Parallel, delayed
import sys

np.set_printoptions(linewidth=1000, precision=4, floatmode='fixed')

root = pathlib.Path(sys.argv[1])
output_filename = sys.argv[2]
prefix = sys.argv[3]

class Features:
    def __init__(self):
        self.features = []

f = Features()

features = Features()


# Build a list of subjects
print("Globing...")
files = list(root.glob("*{}*.nii.gz".format(prefix)))
print("Building subjects list...")
subjects = list(dict.fromkeys([f.name[:8] for f in files]))

# Excluding subject if some step is missing
new_subjects = []
for subject in subjects:
    image_files = list(root.glob("{}*{}*.nii.gz".format(subject, prefix)))

    if(len(image_files) is not 2):
        print("Subject {} does not have 2 timepoints!".format(subject))
    else:
        new_subjects.append(subject)


subjects = new_subjects
print("{} subjects".format(len(subjects)))

def extracthdfeatures(filename):
    output = subprocess.run(["AimsFileInfo", "-i", filename], stdout=subprocess.PIPE)
    dict_str = str(output.stdout).replace("\\n", "").replace(" ", "").replace("\t", "")[13:-1]
    attributes = ast.literal_eval(dict_str)
    f.features.extend(list(attributes.keys()))
    f.features = list(dict.fromkeys(f.features))
    return attributes


# Extract from each subject the features at each timepoint
print("Extracting features...")
start = time.perf_counter()
subjects_features = []
def extract_subject(subject):
    image_files = list(root.glob("{}*{}*.nii.gz".format(subject, prefix)))

    if len(image_files) is not 2:
        print("Warning! Subject {} does not have 2 timepoints!".format(subject))
        return

    fu = [image for image in image_files if "fu" in image.stem][0]
    bas = [image for image in image_files if "bas" in image.stem][0]

    subject_features = {}
    subject_features['id'] = subject
    subject_features['bas'] = extracthdfeatures(bas)
    subject_features['fu'] = extracthdfeatures(fu)

    sys.stdout.write(".")
    sys.stdout.flush()
    return subject_features


subjects_features = Parallel(n_jobs=1)(delayed(extract_subject)(subject) for subject in subjects)
print("")


def reorder_features(d):
    return {k: d[k] for k in f.features}


def fill_missing_features(d):
    d = copy.deepcopy(d)
    keys = d.keys()
    for feature in f.features:
        if feature not in keys:
            d[feature] = "No Value"

    return reorder_features(d)


# Fill missing attributes
print("Filling missing features...")
for subject_features in subjects_features:
    subject_features['bas'] = fill_missing_features(subject_features['bas'])
    subject_features['fu'] = fill_missing_features(subject_features['fu'])

print("Done. Elapsed time={}".format(time.perf_counter() - start))


def save_longitudinal(output_filename):
    with open(output_filename, 'w') as fo:
        fo.write("Subject ID\t" + "\t".join(["\t".join(["{}_{}".format(t, feature) for t in ["bas", "fu"]]) for feature in f.features]) + "\n")
        for subject_features in subjects_features:
            features_bas = subject_features['bas'].values()
            features_fu = subject_features['fu'].values()

            fo.write(subject_features['id'])
            for feature_bas, feature_fu in zip(features_bas, features_fu):
                fo.write("\t{}\t{}".format(str(feature_bas), str(feature_fu)))
            fo.write("\n")


def save_transversal(output_filename, timepoint):
    with open(output_filename, 'w') as fo:
        fo.write("Subject ID\t" + "\t".join(f.features) + "\n")
        for subject_features in subjects_features:
            fo.write(subject_features['id'] + "\t" + "\t".join([str(feature) for feature in subject_features[timepoint].values()]) + "\n")


print("Saving transversal...")
save_transversal(output_filename + "_transversal_bas.csv", 'bas')
save_transversal(output_filename + "_transversal_fu.csv", 'fu')
print("Saving longitudinal...")
save_longitudinal(output_filename + "_longitudinal.csv")

