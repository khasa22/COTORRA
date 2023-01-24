import pandas as pd
from haversine import haversine, Unit

# The CSV file below is retreived from OpenCellId the 23rd of Jan 2023 for SPA
cols = [
'Radio','MCC','MNC','LAC/TAC/NID','CID','?','Longitude','Latitude','Samples','Changeable=1','Changeable=0','Created','Updated','AverageSignal'
]
df = pd.read_csv('/tmp/spain-opencellid-23-01-2023.csv',
                 usecols=cols)
df['Longitude'] = pd.to_numeric(df['Longitude'])
df['Latitude'] = pd.to_numeric(df['Latitude'])

# Circles covering URTINSA
circles = [
    # == EAST area
    (40.349606,-3.797842,403.13),
    #(40.344385,-3.801742,461.90),
    # == WEST area
    # (40.339712,-3.808968,460.00),
    # (40.335361,-3.815104,460.00)
]

# Urtinsa dictionary to store cells
urtinsa_dict = {c: [] for c in cols}

# Only keep cells in Urtinsa
for idx,row in df.iterrows():
    cell = [row['Latitude'], row['Longitude']]
    for circle in circles:
        if haversine(cell, circle[:2], unit=Unit.METERS) < circle[2]:
            print(cell)
            for c in df.columns:
                urtinsa_dict[c].append(row[c])

urtinsa_FILE = 'urtinsa_cells.csv'
urtinsa_df = pd.DataFrame(urtinsa_dict)
urtinsa_df.to_csv(urtinsa_FILE)
print('Data printed @', urtinsa_FILE)


