import csv
import json
import math
import pandas as pd

with open("recipes/pcs/2003/data/pcs_2003.json", "r") as f:
    pcs_2003 = json.load(f)

################################################################################
################################ Parse PCS 2020 ################################
################################################################################


def parse_pcs_2020(
    file_path,
    index_col,
    columns_aliases={
        "Intitulé PCS 2020": "name",
        "libellé court – nomenclature d’usage": "short_name",
    },
):
    sheet = pd.read_excel(file_path, header=0, index_col=index_col)
    data = {}
    for i in sheet.index:
        data[str(i)] = {columns_aliases[c]: sheet.at[i, c] for c in sheet.columns}
    return data


pcs_2020_n1 = parse_pcs_2020("fetched/Nomenclature_N1_PCS2020.xlsx", "PCS 2020_N1")
pcs_2020_n2 = parse_pcs_2020("fetched/Nomenclature_N2_PCS2020.xlsx", "PCS 2020_N2")
pcs_2020_n3 = parse_pcs_2020("fetched/Nomenclature_N3_PCS2020.xlsx", "PCS 2020_N3")
pcs_2020_n4 = parse_pcs_2020("fetched/Nomenclature_N4_PCS2020.xlsx", "PCS 2020_N4")

merged_pcs_2020 = pcs_2020_n1 | pcs_2020_n2 | pcs_2020_n3 | pcs_2020_n4

for pcs_code, pcs in merged_pcs_2020.items():
    if len(pcs_code) == 1:
        continue
    parent_pcs_code = pcs_code[:-1]
    pcs["parent"] = parent_pcs_code
    parent_pcs = merged_pcs_2020[parent_pcs_code]
    if "children" not in parent_pcs:
        parent_pcs["children"] = []
    parent_pcs["children"].append(pcs_code)

pcs_2020 = {"N1": pcs_2020_n1, "N2": pcs_2020_n2, "N3": pcs_2020_n3, "N4": pcs_2020_n4}

with open("data/pcs_2020.json", "w") as f:
    json.dump(pcs_2020, f, indent=4)

################################################################################
###################### Parse correspondance PCS 2003-2020 ######################
################################################################################

pcs_2003_to_2020 = {}
with open("fetched/matrice_P2003_P2020.csv") as csvfile:
    spamreader = csv.DictReader(csvfile, delimiter=";")
    for row in spamreader:
        pct = row["pct"]
        if pct == "a":
            pct = 0
        elif pct == "ns":
            pct = float("nan")
        else:
            pct = float(pct.replace(",", "."))
        pcs_2003_code = row["PCS2003"]
        if pcs_2003_code not in pcs_2003_to_2020:
            pcs_2003_to_2020[pcs_2003_code] = {}
        pcs_2003_to_2020[pcs_2003_code][row["PCS2020"]] = pct

for pcs_2003_code in pcs_2003_to_2020.keys():
    pcs_2003 = pcs_2003_to_2020[pcs_2003_code]
    remainder = 100.0 - sum([pct for pct in pcs_2003.values() if not math.isnan(pct)])
    num_ns = sum([math.isnan(pct) for pct in pcs_2003.values()])
    pcs_2003_to_2020[pcs_2003_code] = {
        pcs_2020_code: pct if not math.isnan(pct) else round(remainder / num_ns, 3)
        for pcs_2020_code, pct in pcs_2003.items()
    }

with open("data/pcs_2003_to_2020.json", "w") as f:
    json.dump(pcs_2003_to_2020, f, indent=4)

################################################################################
###################### Parse correspondance PCS 2020-2003 ######################
################################################################################

pcs_2020_to_2003 = {}
with open("fetched/matrice_P2020_P2003.csv") as csvfile:
    spamreader = csv.DictReader(csvfile, delimiter=";")
    for row in spamreader:
        pct = row["pct"]
        if pct == "a":
            pct = 0
        elif pct == "ns":
            pct = float("nan")
        else:
            pct = float(pct.replace(",", "."))
        pcs_2020_code = row["PCS2020"]
        if pcs_2020_code not in pcs_2020_to_2003:
            pcs_2020_to_2003[pcs_2020_code] = {}
        pcs_2020_to_2003[pcs_2020_code][row["PCS2003"]] = pct

for pcs_2020_code in pcs_2020_to_2003.keys():
    pcs_2020 = pcs_2020_to_2003[pcs_2020_code]
    remainder = 100.0 - sum([pct for pct in pcs_2020.values() if not math.isnan(pct)])
    num_ns = sum([math.isnan(pct) for pct in pcs_2020.values()])
    pcs_2020_to_2003[pcs_2020_code] = {
        pcs_2020_code: pct if not math.isnan(pct) else round(remainder / num_ns, 3)
        for pcs_2020_code, pct in pcs_2020.items()
    }

with open("data/pcs_2020_to_2003.json", "w") as f:
    json.dump(pcs_2020_to_2003, f, indent=4)
