import csv
import json
import math

with open("ressources/generated/pcs/pcs_2003.json", "r") as f:
    pcs_2003 = json.load(f)

################################################################################
############################## Parse PCS age 2021 ##############################
################################################################################


def parse_csv_as_dict(
    file_path,
    columns,
    index_column,
    indices=None,
    columns_types=None,
    delimiter=";",
    first_data_row=1,
    last_data_row=None,
):
    with open(file_path, "r") as file:
        lines = [line.rstrip() for line in file]
        if last_data_row is None:
            last_data_row = len(lines)
        if columns_types is None:
            columns_types = [str for _ in columns]
        data_rows = [lines[i] for i in range(first_data_row - 1, last_data_row)]
        rows = list(csv.DictReader(data_rows, fieldnames=columns, delimiter=delimiter))
        if indices is None:
            return {
                row[index_column]: {
                    k: t(row[k])
                    for k, t in zip(columns, columns_types)
                    if k != index_column
                }
                for row in rows
            }
        else:
            return {
                i: {
                    k: t(row[k])
                    for k, t in zip(columns, columns_types)
                    if k != index_column
                }
                for row, i in zip(rows, indices)
            }


columns = ["age"] + list(pcs_2003["n1"].keys())
columns_types = [str] + [int for _ in pcs_2003["n1"].keys()]
indices = [
    "15-19",
    "20-24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60-64",
    "65+",
]

data = {}
data["total"] = parse_csv_as_dict(
    "ressources/downloaded/AGE_PCS_2021.csv",
    columns=columns,
    index_column="age",
    columns_types=columns_types,
    indices=indices,
    first_data_row=47,
)
data["men"] = parse_csv_as_dict(
    "ressources/downloaded/AGE_PCS_2021.csv",
    columns=columns,
    index_column="age",
    columns_types=columns_types,
    indices=indices,
    first_data_row=65,
)
data["women"] = parse_csv_as_dict(
    "ressources/downloaded/AGE_PCS_2021.csv",
    columns=columns,
    index_column="age",
    columns_types=columns_types,
    indices=indices,
    first_data_row=83,
)

with open("ressources/generated/sex_age_pcs_2021/data.json", "w") as f:
    json.dump(data, f, indent=4)


################################################################################
################################ Generate page #################################
################################################################################

accounted_pcs_codes = list(pcs_2003["n1"].keys())[:8]

max_log_dim = max(
    [
        max([pcs_values[code] for code in accounted_pcs_codes])
        for pcs_values in data["total"].values()
    ]
)
pcs_color_palette = {
    "1": "rgba(34, 139, 34, 1)",  # Forest green
    "2": "rgba(255, 165, 0, 1)",  # Orange
    "3": "rgba(0, 0, 128, 1)",  # Navy blue
    "4": "rgba(100, 149, 237, 1)",  # Cornflower blue
    "5": "rgba(255, 215, 0, 1)",  # Gold
    "6": "rgba(220, 20, 60, 1)",  # Crimson red
    "7": "rgba(128, 128, 128, 1)",  # Gray
    "8": "rgba(105, 105, 105, 1)",  # Dim gray
}

option = {
    "title": {
        "text": "Population par age, par PCS (2021)",
        "top": 20,
        "left": "center",
        "textStyle": {"fontSize": 22},
    },
    "toolbox": {
        "feature": {
            "saveAsImage": {},
        },
        "top": 0,
        "right": 5,
    },
    "legend": {
        "data": [pcs["name"] for pcs in pcs_2003["n1"].values()],
        "top": 68,
        "left": "center",
        "padding": [0, 15, 0, 15],
        "textStyle": {"fontSize": 16},
        "selected": {
            pcs_2003["n1"]["7"]["name"]: False,
            pcs_2003["n1"]["8"]["name"]: False,
        },
        "inactiveColor": '#444',
    },
    "grid": {
        "left": 20,
        "right": 40,
        "bottom": 30,
        "containLabel": True,
    },
    "tooltip": {"trigger": "axis"},
    "xAxis": {
        "type": "category",
        "name": "",
        "textStyle": {"fontSize": 18},
        "boundaryGap": False,
        "splitLine": {"show": True},
        "data": [age + " ans" for age in data["total"].keys()],
    },
    "yAxis": {
        "type": "value",
        "name": "Effectif",
        "textStyle": {"fontSize": 18},
        "minorSplitLine": {"show": True},
    },
    "series": [
        {
            "name": pcs_2003["n1"][pcs_code]["name"],
            "type": "line",
            "data": [data["total"][age][pcs_code] for age in indices],
            "itemStyle": {"color": pcs_color_palette[pcs_code]},
        }
        for pcs_code in accounted_pcs_codes
    ],
}

with open("pages/sex_age_pcs_2021/all_age_pcs/index.js", "w") as f:
    f.write(
        """var chartDom = document.getElementById('chart-container');
var myChart = echarts.init(chartDom, 'dark', {
    renderer: 'canvas',
    useDirtyRect: false
});
var option = JSON.parse("""
        + json.dumps(json.dumps(option))
        + """);
myChart.setOption(option);
const baseGridTop = 160;
const lengendLineHeight = 26;
function adjust() {
    let chartWidth = chartDom.clientWidth;
    if (chartWidth >= 1077) {
        option.legend.orient = 'horizontal';
        option.grid.top = baseGridTop;
    } else if (chartWidth >= 775) {
        option.legend.orient = 'horizontal';
        option.grid.top = baseGridTop + lengendLineHeight;
    } else if (chartWidth >= 647) {
        option.legend.orient = 'horizontal';
        option.grid.top = baseGridTop + 2 * lengendLineHeight;
    } else {
        option.legend.orient = 'vertical';
        option.grid.top = baseGridTop + 6 * lengendLineHeight;
    }
    myChart.setOption(option);
    myChart.resize();
}
window.addEventListener("load", adjust)
window.addEventListener('resize', adjust);"""
    )
