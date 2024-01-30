import pandas as pd
import os
import csv
import sys
import re


def get_filename():
    if len(sys.argv) > 1 and sys.argv[1].endswith('.txt'):
        filename = sys.argv[1]
    else:
        print('\033[91m' + 'Provide series_matrix.txt!')
        sys.exit()
    return (filename)


def define_dividers(filename):
    study_end = 0
    samples_end = 0
    with open(filename) as file:
        for line in file:
            study_end += 1
            samples_end += 1
            if line.startswith("!Sample_title"):
                break

        for line in file:
            samples_end += 1
            if line.startswith("!series_matrix_table_begin"):
                break
    return (study_end, samples_end)


def column_merge(x): return '|'.join(x[x.notnull()].astype(str))


def create_study(filename, geo_accession, study_end):
    study = pd.read_csv(filename, sep='\t', nrows=study_end - 3)
    study["!Series_title"] = study["!Series_title"].str.replace("!", "")
    study = study.set_index("!Series_title").T
    study['Study Title'] = study.index
    study = study.groupby(level=0, axis=1).apply(lambda x: x.apply(column_merge, axis=1))
    drop_cols = []
    for i in study.columns:
        str_len = len(study[i][0])
        if str_len > 2000:
            drop_cols.append(i)
    if len(drop_cols) > 0:
        print("In study metadata following columns deleted for having too long values:", drop_cols)
    study = study.drop(drop_cols, axis=1)
    study.to_csv(geo_accession + "/" + geo_accession + "_study.tsv", sep='\t', index=False)


def create_samples(filename, geo_accession, study_end, samples_end):
    samples = pd.read_csv(filename, sep='\t', skiprows=study_end, nrows=samples_end - study_end - 2)
    samples.columns = samples.columns.str.replace('!', '')
    samples["Sample_geo_accession"] = samples["Sample_geo_accession"].str.replace("!", "")
    samples = samples.rename(columns={"Sample_geo_accession": "Sample Source ID"})
    samples = samples.set_index("Sample Source ID").T
    new_columns = []
    for item in samples.columns:
        counter = 0
        newitem = item
        while newitem in new_columns:
            counter += 1
            newitem = "{}_{}".format(item, counter)
        new_columns.append(newitem)
    samples.columns = new_columns
    samples['Sample Source ID'] = samples.index
    samples.to_csv(geo_accession + "/" + geo_accession + "_samples.tsv", sep='\t', index=False)


def create_expression(filename, geo_accession, samples_end):
    try:
        expression = pd.read_csv(filename, sep='\t', skiprows=samples_end, low_memory=False)
    except:
        return (-1)
    expression = expression.dropna()
    expression.to_csv(geo_accession + "/" + geo_accession + "_expression.tsv", sep='\t',
                      index=False)

    gct_filename = geo_accession + "_expression.gct"
    df = pd.read_csv(geo_accession + "/" + geo_accession + "_expression.tsv", sep='\t')
    df.insert(1, 'Description', None)
    df = df.rename(columns={
        df.columns[0]: "NAME"})
    rows = len(df.index)
    samples = len(df.iloc[0])

    with open(geo_accession + "/" + gct_filename, 'w') as out_file:
        writer = csv.writer(out_file, delimiter='\t')
        row = [None] * samples
        row[0] = '#1.2'
        writer.writerow(row)
        row[0], row[1] = rows, samples - 2
        writer.writerow(row)

    df.to_csv(geo_accession + "/" + gct_filename, mode='a', sep='\t', index=False)


def main():
    filename = get_filename()
    geo_accession = re.findall(r"GSE[0-9]+", filename)[0]
    print(geo_accession)
    os.makedirs(geo_accession, exist_ok=True)
    study_end, samples_end = define_dividers(filename)
    try:
        create_study(filename, geo_accession, study_end)
    except:
        print('\033[91m' + "Error creating study file!")
        sys.exit(1)
    try:
        create_samples(filename, geo_accession, study_end, samples_end)
    except:
        print('\033[91m' + "Error creating samples file!")
        sys.exit(2)
    try:
        create_expression(filename, geo_accession, samples_end)
    except:
        print("Expression not found in file. Only study and samples will be created")
    print('\033[92m' + "Files successfully prepared. Look at folder", geo_accession)

    if os.path.exists(geo_accession + "/" + geo_accession + "_expression.tsv"):
        os.remove(geo_accession + "/" + geo_accession + "_expression.tsv")


if __name__ == '__main__':
    main()
