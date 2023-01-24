import pandas as pd
import networkx as nx

# Load & remove GSM (2G) cells
df = pd.read_csv('urtinsa_cells.csv')
df = df[(df['Radio'] != 'GSM')]

print(len(df))
G = nx.erdos_renyi_graph(n=30*len(df), p=0.3, seed=3, directed=False)

