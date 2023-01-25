# This script creates small/large networks of cloud and near/far edge servers.
# It uses the smalles/largest Erdos-Renyi (n,p) setup taken from
# 'pareto-front.csv', and attaches the LTE cells @


import pandas as pd
import networkx as nx
import json
import time


def get_degrees(G):
    # gets "degree: #nodes" for each node in the graph

    degrees = {}
    for v,deg in G.degree:
        if deg not in degrees:
            degrees[deg] = 1
        else:
            degrees[deg] += 1

    return degrees


def print_degrees(G):
    # Prints "degree: #nodes" for each node in the graph

    print(get_degrees(G))


def find_erdos_renyi_graph(n, p, server_specs, seed=0):
    # Find the Erdos-Renyi graph G(n,p) satisfying the degree and number of
    # nodes according to the server_specs

    satisfy_specs = False

    while not satisfy_specs:
        G = nx.erdos_renyi_graph(n=n, p=p, seed=seed, directed=False)
        degrees = get_degrees(G)
        seed += 1
        to_satisfy = len(server_specs['cpus'].keys())

        for s in server_specs['cpus'].keys():
            s_number = server_specs['number_of'][s]
            s_degree = server_specs['degree_of'][s]
            if s_degree not in degrees:
                break
            if degrees[s_degree] < s_number:
                break
            to_satisfy -= 1
        
        satisfy_specs = (to_satisfy == 0)

    return G


def attach_cells(G, cells_df):
    # Attaches the cells in cells_df to the nodes in G in decreasing degree
    # order

    i=0
    for v,deg in sorted(G.degree, key=lambda x: x[1],
                        reverse=True)[-len(cells_df):]:
        # create cell node linked to v
        cell_row = cells_df.iloc[i]
        cell_v_num = 10000000+i
        G.add_node(cell_v_num, lat=cell_row['Latitude'],
                   lng=cell_row['Longitude'], type='cell')
        G.add_edge(cell_v_num, v)
        i+=1


def create_servers(G, server_specs):
    # Iterates over G and adds servers according to server_specs: their degree,
    # number of CPUs, and how many

    servers_count = {
        s: server_specs['number_of'][s] for s in server_specs['cpus'].keys()
    }

    for v in list(G.nodes):
        for s in servers_count.keys():
            if servers_count[s] > 0:
                if len(G[v]) == server_specs['degree_of'][s]:
                    nx.set_node_attributes(G,
                        {v: server_specs['cpus'][s]}, 'cpus')
                    nx.set_node_attributes(G,
                        {v: s}, 'type')
                    servers_count[s] -= 1


def allocate_bw(G, bw=1000):
    # Allocates bw Mbps at each link in graph G

    bw_dict = {e: bw for e in G.edges}
    nx.set_edge_attributes(G, bw_dict, "bandwidth")




################
# SCRIPT START #
################


# Urtinsa LTE cells
urtinsa_df = pd.read_csv('urtinsa_cells.csv')
urtinsa_df = urtinsa_df[(urtinsa_df['Radio'] == 'LTE')]


pareto_front = pd.read_csv('pareto-front.csv')
pareto_front['p'] = pd.to_numeric(pareto_front['p'])
pareto_front['n'] = pd.to_numeric(pareto_front['n'])


# Small & dense (n,p) setup
small_n = pareto_front['n'].min()
small_p = pareto_front[pareto_front['n']==small_n]['p'].max()

# large & sparse (n,p) setup
large_n = pareto_front['n'].max()
large_p = pareto_front[pareto_front['n']==large_n]['p'].min()


# Server specifications - load them
with open('server-specs.json') as f:
    server_specs = json.load(f)


# Create the small network graph
small_G = find_erdos_renyi_graph(n=small_n, p=small_p,
                                 server_specs=server_specs, seed=100)
create_servers(small_G, server_specs)
attach_cells(small_G, urtinsa_df)
allocate_bw(small_G, bw=1000)
small_path = 'small_G.gml'
nx.write_gml(small_G, small_path)
print(f'small network GML@{small_path}')


# Create the large network graph
large_G = nx.erdos_renyi_graph(n=large_n, p=large_p, seed=100, directed=False)
large_G = find_erdos_renyi_graph(n=large_n, p=large_p,
                                 server_specs=server_specs, seed=0)
# Get largest connected component
largest_cc = max(nx.connected_components(large_G), key=len)
large_G = large_G.subgraph(largest_cc).copy()
create_servers(large_G, server_specs)
attach_cells(large_G, urtinsa_df)
allocate_bw(large_G, bw=1000)
large_path = 'large_G.gml'
nx.write_gml(large_G, large_path)
print(f'large network GML@{large_path}')


