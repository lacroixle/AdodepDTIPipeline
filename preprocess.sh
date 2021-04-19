python3 find_subjects_adodep.py /projects/adodep/FORMATED/ subjects_ext.pickle output_ext dataframes/subjects.h5
numactl -N 0 python3 0_preprocess.py subjects_ext.pickle
numactl -N 0 python3 1_preprocess.py subjects_ext.pickle
numactl -N 0 python3 1_qc.py subjects_ext.pickle
numactl -N 0 python3 1_qc_all.py subjects_ext.pickle
numactl -N 0 python3 2_preprocess.py subjects_ext.pickle
