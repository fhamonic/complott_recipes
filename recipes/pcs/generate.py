import pandas as pd


with open("ressources/downloaded/index.json", "r") as f:
    data = f.read()

print(data)

# # Write to the output directory
with open("ressources/generated/pcs/result.txt", "w") as f:
    f.write(f"Processed Data: {data.upper()}")
