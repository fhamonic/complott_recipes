import json
import pandas as pd
import re
import sentence_transformers as st

with open("ressources/generated/pcs/pcs_2003.json", "r") as f:
    pcs_2003 = json.load(f)

################################################################################
################################ PCS data 2019 #################################
################################################################################

pcs_data_2019 = {}

ages_columns = ["15-24 ans", "25-49 ans", "50 ans ou plus"]
diplomes_columns = [
    "Aucun diplôme, brevet des collèges",
    "CAP-BEP",
    "Bac",
    "Bac+2 ou plus",
]
status_columns = [
    "Indépendants",
    "CDI",
    "CDD et intérim > 3 mois",
    "CCD et intérim <= 3 mois",
    "Apprentis, stagiaires, contrats aidés",
]
sheet = pd.read_excel(
    "ressources/downloaded/PCS_DATA_2019.xlsx",
    skiprows=3,
    nrows=152,
    header=None,
    names=[
        "Effectif",
        "Part emploi total",
        "Part PCS N1",
        "femmes",
    ]
    + ages_columns
    + diplomes_columns
    + status_columns
    + [
        "Sous-emploi",
        "Temps partiel",
        "Travail le samedi",
        "Travail le dimanche",
        "Travail la nuit",
        "Travail à domicile",
    ],
    index_col=0,
)

index_labels = list([s for s in sheet.index if str(s) != "nan"])

n2_data = {}
for id in index_labels:
    if re.match("^[A-Z]", id) and id in [pcs["name"] for pcs in pcs_2003["n1"].values()]:
    # if re.match("^[0-9]{2} ", id):
        print(id)

print(sheet.at[sheet.index[1], "Effectif"])

# model = st.SentenceTransformer("distiluse-base-multilingual-cased-v1")
# index_embeddings = model.encode(index_labels)

# print(embeddings)

# data = {}
# for i in sheet.index:
#     data[str(i)] = {columns_aliases[c]: sheet.at[i, c] for c in sheet.columns}


# with open("ressources/generated/pcs/pcs_2020_to_2003.json", "w") as f:
#     json.dump(pcs_2020_to_2003, f, indent=4)
