import csv
import json
import math
import pandas as pd

################################################################################
################################ Parse PCS 2003 ################################
################################################################################


def parse_pcs_2003(file_path, columns_aliases={"Libellé": "name"}):
    sheet = pd.read_excel(file_path, skiprows=1, header=0, index_col="Code")
    data = {}
    for i in sheet.index:
        data[str(i)] = {columns_aliases[c]: sheet.at[i, c] for c in sheet.columns}
    return data


pcs_2003_n1 = parse_pcs_2003("ressources/downloaded/PCS2003_N1.xls")
pcs_2003_n2 = parse_pcs_2003("ressources/downloaded/PCS2003_N2.xls")
pcs_2003_n3 = parse_pcs_2003("ressources/downloaded/PCS2003_N3.xls")
pcs_2003_n4 = parse_pcs_2003("ressources/downloaded/PCS2003_N4.xls")

for pcs_code, pcs in pcs_2003_n2.items():
    parent_pcs_code = pcs_code[:-1]
    pcs["parent"] = parent_pcs_code
    parent_pcs = pcs_2003_n1[parent_pcs_code]
    if "children" not in parent_pcs:
        parent_pcs["children"] = []
    parent_pcs["children"].append(pcs_code)

for pcs_code, pcs in pcs_2003_n3.items():
    parent_pcs_code = max([code for code in pcs_2003_n2.keys() if code <= pcs_code])
    pcs["parent"] = parent_pcs_code
    parent_pcs = pcs_2003_n2[parent_pcs_code]
    if "children" not in parent_pcs:
        parent_pcs["children"] = []
    parent_pcs["children"].append(pcs_code)

for pcs_code, pcs in pcs_2003_n4.items():
    parent_pcs_code = pcs_code[:-2]
    pcs["parent"] = parent_pcs_code
    parent_pcs = pcs_2003_n3[parent_pcs_code]
    if "children" not in parent_pcs:
        parent_pcs["children"] = []
    parent_pcs["children"].append(pcs_code)

pcs_2003 = {"n1": pcs_2003_n1, "n2": pcs_2003_n2, "n3": pcs_2003_n3, "n4": pcs_2003_n4}

with open("ressources/generated/pcs/pcs_2003.json", "w") as f:
    json.dump(pcs_2003, f, indent=4)

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


pcs_2020_n1 = parse_pcs_2020("ressources/downloaded/PCS2020_N1.xlsx", "PCS 2020_N1")
pcs_2020_n2 = parse_pcs_2020("ressources/downloaded/PCS2020_N2.xlsx", "PCS 2020_N2")
pcs_2020_n3 = parse_pcs_2020("ressources/downloaded/PCS2020_N3.xlsx", "PCS 2020_N3")
pcs_2020_n4 = parse_pcs_2020("ressources/downloaded/PCS2020_N4.xlsx", "PCS 2020_N4")

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

with open("ressources/generated/pcs/pcs_2020.json", "w") as f:
    json.dump(pcs_2020, f, indent=4)

################################################################################
###################### Parse correspondance PCS 2003-2020 ######################
################################################################################

pcs_2003_to_2020 = {}
with open("ressources/downloaded/PCS2003_to_2020.csv") as csvfile:
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

with open("ressources/generated/pcs/pcs_2003_to_2020.json", "w") as f:
    json.dump(pcs_2003_to_2020, f, indent=4)

################################################################################
###################### Parse correspondance PCS 2020-2003 ######################
################################################################################

pcs_2020_to_2003 = {}
with open("ressources/downloaded/PCS2020_to_2003.csv") as csvfile:
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

with open("ressources/generated/pcs/pcs_2020_to_2003.json", "w") as f:
    json.dump(pcs_2020_to_2003, f, indent=4)
