import pandas as pd
import networkx as nx

# Urtinsa LTE cells
urtinsa_df = pd.read_csv('urtinsa_cells.csv')
urtinsa_df = urtinsa_df[(urtinsa_df['Radio'] == 'LTE')]


pareto_front = pd.read_csv('pareto-front.csv')
pareto_front['p'] = pd.to_numeric(pareto_front['p'])
pareto_front['n'] = pd.to_numeric(pareto_front['n'])


# Small & dense (n,p) setup
small_n = pareto_front['n'].min()
small_p = pareto_front[pareto_front['n']==small_n]['p'].max()
print(small_n, small_p)

# large & sparse (n,p) setup
large_n = pareto_front['n'].max()
large_p = pareto_front[pareto_front['n']==large_n]['p'].min()
print(large_n, large_p)


small_G = nx.erdos_renyi_graph(n=small_n, p=small_p, seed=0, directed=False)

i=0
for v,deg in sorted(small_G.degree, key=lambda x: x[1],
                    reverse=True)[-len(urtinsa_df):]:
    # create cell node linked to v
    cell_row = urtinsa_df.iloc[i]
    cell_v_num = 10000000+i
    small_G.add_node(cell_v_num, lat=cell_row['Latitude'], lng=cell_row['Longitude'])
    small_G.add_edge(cell_v_num, v)
    i+=1


nx.write_gml(small_G, '/tmp/small_G.gml')


large_G = nx.erdos_renyi_graph(n=large_n, p=large_p, seed=0, directed=False)
nx.write_gml(large_G, '/tmp/large_G.gml')

#G = nx.erdos_renyi_graph(n=30*len(df), p=0.3, seed=3, directed=False)

