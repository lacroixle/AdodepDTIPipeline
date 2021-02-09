import numpy as np
#import matplotlib
import matplotlib.pyplot as plt

#matplotlib.use('Qt5Agg')

formatted_dir = "/projects/adodep/FORMATED/DTI/"
subject = "02PP021P_dtibas"

bval_file = formatted_dir + subject + ".bval"
bvec_file = formatted_dir + subject + ".bvec"
nifti_file = formatted_dir + subject + ".nii.gz"

bval = np.loadtxt(bval_file)
bvec = np.loadtxt(bvec_file)

print(bval)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(bvec[0], bvec[1], bvec[2])
plt.show()
