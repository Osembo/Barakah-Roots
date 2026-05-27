import pandas as pd

df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")

def parse_species(s):
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(";")]

all_species = set()
for species_str in df["Species"].dropna():
    all_species.update(parse_species(species_str))

sorted_species = sorted(all_species)

print("[")
for s in sorted_species:
    print(f'    "{s}",')
print("]")