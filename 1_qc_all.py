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


# First list and save all SQUAD folders
quad_folders = []
category = []
for subject in subjects:
    quad_folders.append(str(subject['path'].joinpath(subject['id'] + "_" + subject['t'] + "_eddy.qc")) + "\n")
    if subject['t'] == 'bas':
        category.append(0)
    elif subject['t'] == 'fu':
        category.append(1)
    else:
        print("Aie !")

with open("squad_folders.txt", 'w') as f:
    f.writelines(quad_folders)

with open("category.txt", 'w') as f:
    f.write("bas\n")
    f.write("0\n")
    f.writelines([str(cat) + "\n" for cat in category])


#subprocess.run(["eddy_squad", "squad_folders_2", "-u", "-g", "category.txt"])
subprocess.run(["eddy_squad", "squad_folders.txt", "-u"])

