import math
import pandas as pd


df_0 = pd.read_csv("covariables_adodep_dti.csv", sep=";")
df_1 = pd.read_csv("covariables_adodep_dti_2.csv", sep=";")

df_0 = pd.DataFrame(df_0.values.tolist(), columns=df_0.columns, index=df_0["code sujet BL"])
df_1 = pd.DataFrame(df_1.values.tolist(), columns=df_1.columns, index=df_1["code sujet BL"])

# Unknown ghost subject
#df_1.drop(index="04_BV_020_T", inplace=True)


def is_subject_in_0(subject_id):
    if subject_id == "04_BV_020_T":
        return True

    return subject_id in df_0.index


def get_attribute_0(subject_id, t, attribute):
    if subject_id == "04_BV_020_T":
        if attribute == "audit":
            if t == "bas":
                return 6
            elif t == "fu":
                return 11

    if t == 'fu':
        subject_id = get_attribute_1(subject_id, 'Code FU')

    return df_0.loc[subject_id, attribute]


def get_attribute_1(subject_id, attribute):
    return df_1.loc[subject_id, attribute]


subjects_id = list(df_1["code sujet BL"])
print("Found {} subjects.".format(len(subjects_id)))
subjects = []
output_df = pd.DataFrame()

for subject in subjects_id:
    #d = {'id': subject.replace("_", "")}
    d = {}
    d['gender'] = get_attribute_1(subject, 'gender')
    d['bipolar'] = get_attribute_1(subject, 'bipolar')
    d['qit'] = get_attribute_1(subject, 'QIT')
    d['age_bas'] = get_attribute_1(subject, 'age J0')
    d['ttt_bas'] = get_attribute_1(subject, 'TTT_J0/AD')
    d['prisma_bas'] = get_attribute_1(subject, 'Prisma BL')

    if is_subject_in_0(subject):
        d['audit_bas'] = get_attribute_0(subject, 'bas', 'audit')

    # Check if follow up is available
    fu_available = str(get_attribute_1(subject, 'Code FU')) != "nan"
    d['fu'] = fu_available

    if fu_available:
        d['age_fu'] = get_attribute_1(subject, 'age FU')
        d['ttt_fu'] = get_attribute_1(subject, 'TTT_FU/AD')
        d['thymo_fu'] = get_attribute_1(subject, 'Thymorégulateur_FU')
        d['prisma_fu'] = get_attribute_1(subject, 'Prisma FU')
        d['audit_fu'] = get_attribute_0(subject, 'fu', 'audit')

    subjects.append(pd.Series(d, name=subject.replace("_", "")))

output_df = pd.DataFrame(subjects)

output_df.to_excel("subjects.xlsx", "table")
output_df.to_hdf("subjects.h5", "table")

