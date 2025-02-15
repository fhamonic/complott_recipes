import json
import os
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


pcs_2003_n1 = parse_pcs_2003("fetched/pcs2003_liste_n1.xls")
pcs_2003_n2 = parse_pcs_2003("fetched/pcs2003_liste_n2.xls")
pcs_2003_n3 = parse_pcs_2003("fetched/pcs2003_liste_n3.xls")
pcs_2003_n4 = parse_pcs_2003("fetched/pcs2003_liste_n4.xls")

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

with open("data/pcs_2003.json", "w") as f:
    json.dump(pcs_2003, f, indent=4)
