python3 find_subjects.py /projects/adodep/FORMATED/ subjects.pickle output
numactl -N 0 python3 0_preprocess.py subjects.pickle 
numactl -N 0 python3 1_preprocess.py subjects.pickle 
numactl -N 0 python3 2_preprocess.py subjects.pickle 

