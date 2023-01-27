# This script executes stress tests for DLMD as resources decrease within
# infrastructure graphs.

import functools as reduce
import networkx as nx
import pandas as pd
import numpy as np
import copy

##################
# DLMD FUNCTIONS #
##################

def shortest_and_weight(G, src, dst, weight_fn):
    # Finds the shortest path between src and dst using as cost the weight_fn
    # using Dijkstra
    # The weight_fn receives the edge enedpoints and the edge data

    path = shortest_path(G, source=src, target=dst,
                         weight=weight_fn, method='dijkstra')
    path_weight = [weight_fn(n1,n2,G.edges[n1,n2])\
            for n1,n2 in zip(path[:-1], path[1:])]
    
    return path, path_weight



def dlmd(G, SFC, PoA):
    # Executes de DLMD algorithm and yields the VF-placement for a robotic
    # service with a robot that can be attached to the PoAs. 
    # The code asumes the best PoA is obtained.
    # TODO: update it to do the SNR filtering outside
    # The SFC is a graph


    # Server level function l(s)
    l = lambda s: 1 if G.nodes[s]['type'] == 'cloud' else (
            2 if G.nodes[s]['type'] == 'far_edge' else 3)

    # Obtain the edges with less than 'bw' bandwidth
    low_bw = lambda G,bw: [e for e,d in G.edges(data=True)\
                            if d['bandwidth'] <= bw]

    # Check the used CPUs @server=s in the deployment
    used_cpus = lambda s,dep,G,SFC: sum([SFC.nodes[vf]['cpus']\
            for vf in dep if (len(vf)==1) and dep[vf]==s])

    # Dijkstra weight function using the delay and used bw
    dlmd_weight_G = lambda n1,n2,G: G.edges(data=True)[n1,n2]['delay'] +\
                                    G.edges(data=True)[n1,n2]['used_bw']
    dlmd_weight = lambda n1,n2,data: data['delay'] + data['used_bw']

    # Distance
    # TODO
    dlmd_w_to_poa = lambda s,PoA,G: dlmd_weight_G(s,PoA,G)


    # Deployment
    deployment = {}

    # Filter the servers
    servers = [n for n in dict(G.nodes) if 'type' in G.nodes(data=True)[n] and\
            G.nodes(data=True)[n]['type'] in ['near_edge', 'far_edge', 'cloud']]


    # Create sorted VFs & VLs
    vfs =  sorted(SFC.nodes, reverse=True)
    vls =  list(zip(sorted(SFC.nodes, reverse=True)[:-1],
                    sorted(SFC.nodes, reverse=True)[1:]))

    hop = -1
    for vf in vfs:
        min_eta = 1000

        # Find the server deployment or steer to PoA
        for s in servers if vf != vfs[-1] else PoA:
            # Check if server s has enough CPUs
            free_cpus = G.nodes[s]['cpus']] - used_cpus(s,deployment,G,SFC)
            if SFC.nodes[vf]['cpus'] <= free_cpus:
                continue

            # Server cost
            _, server_poa_eta = shortest_and_weight(G=G, src=s, dst=PoA,
                                                    weight_fn=dlmd_weight)
            eta = l(s) + server_poa_eta
            
            # link cost
            if hop > 0 and hop < len(vls):
                # Prior VF
                vf_1 = vfs[hop]

                # Prune links without enough BW
                vl_bw = SFV.edges(data=True)[vls[hop]]
                pruned_links = low_bw(G, vl_bw)
                G_pruned = copy.deepcopy(G)
                G_pruned.remove_edges_from(pruned_links)

                # Find path between (vf,vf-1)
                s_1 = deployment[v_1]
                try networkx.exception.NetworkXNoPath as no_path:
                    path, path_eta = shortest_and_weight(
                            G=G_pruned, src=s_1, dst=s, weight_fn=dlmd_weight)
                    eta += path_eta
                except no_path:
                    path = []
                    eta += 100000

            # Select the deployment if better
            if eta < min_eta:
                deployment[vf] = s
                deployment[vf_1,vf] = path

        # Go to next hop in the SFC
        hop += 1

    # Check if the deployment has been completed
    completed = reduce(lambda a,b: a and b,
                       [vf in deployment for vf in SFC.nodes])

    return deployment, completed



def deployment_delay(G, deployment):
    # Computes the delay of a deployment over the graph G

    delay = 0

    for vf1,vf2 in [k in deployment.keys() if len(k)==2]:
        path = deployment[vf1,vf2]
        delay += sum([G.edges(data=True)[n1,n2]['delay']\
                        for n1,n2 in zip(path[:-1], path[1:])]])

    return delay


def deployment_free_edge(G, SFC, deployment):
    # Calculates the free edge resources at the edge 
    # note: the deployment must have been successfull

    n_edges = [n for n,d in G.nodes(data=True) if d['type']=='near_edge']
    n_edge_cpus = sum([d['cpus'] for n,d in G.nodes(data=True)\
                        if d['type']=='near_edge'])
    f_edges = [n for n,d in G.nodes(data=True) if d['type']=='far_edge']
    f_edge_cpus = sum([d['cpus'] for n,d in G.nodes(data=True)\
                        if d['type']=='far_edge'])

    # Total edge resource
    total_edge = n_edge_cpus + f_edge_cpus
    consumed_edge = n_edge_cpus + f_edge_cpus

    for vf in SFC.nodes:
        if G.nodes(data=True)[deployment[vf]]['type'] != 'cloud':
            consumed_edge -= SFC.nodes(data=True)['cpus']
            

    return 1 - consumed_edge/total_edge
    
    




#########################
# STRESS-TEST FUNCTIONS #
#########################

def stress_network(G, p_step=0.1):
    # Stress G resources at steps of p_step percent

    stressed_networks = {0: copy.deepcopy(G_)}

    # Get the server nodes
    n_edges = [n for n,d in G.nodes(data=True) if d['type']=='near_edge']
    f_edges = [n for n,d in G.nodes(data=True) if d['type']=='far_edge']
    clouds = [n for n,d in G.nodes(data=True) if d['type']=='cloud']

    # CPU sums
    n_edge_cpus = G.nodes(data=True)[n_edges[0]]['cpus']
    f_edge_cpus = G.nodes(data=True)[f_edges[0]]['cpus']
    cloud_cpus = G.nodes(data=True)[clouds[0]]['cpus']

    # CPU decreases and edge removal steps
    edges_step = int(len(G.edges) * p_step)
    n_edge_step = int(n_edge_cpus * p_step)
    f_edge_step = int(f_edge_cpus * p_step)
    cloud_step = int(cloud_cpus * p_step)

    G_ = stressed_networks[0]
    for p in np.arange(p_step, 1, p_step):

        # Remove an edge from the highest degree node
        for i in range(edges_step):
            nodes_deg = sorted([(n, len(G_[n])) for n in G_.nodes],
                           key=lambda x: x[1], reverse=True)
            highest_neighs = 
            G_.remove_edge(nodes_deg[0][0], list(G_[nodes_deg[0][0]])[0])

        # Remove CPUs
        for s in n_edges:
            G_.nodes[s]['cpus'] = max(0, G_.nodes[s]['cpus'] - n_edge_step)
        for s in f_edges:
            G_.nodes[s]['cpus'] = max(0, G_.nodes[s]['cpus'] - f_edge_step)
        for s in clouds:
            G_.nodes[s]['cpus'] = max(0, G_.nodes[s]['cpus'] - cloud_step)

        # Store the p-stressed graph
        stressed_networks[p] = copy.deepcopy(G_)

    return stressed_networks


if __name__ == '__main__':
    # Read the infrastructure CSV
    G = pd.read_csv('small_G.csv')

    # Create the SFC
    SFC_len = 3
    SFC = nx.path_graph(SFC_len)
    VF_cpus = 1
    nx.set_node_attributes(SFC, {n: VF_cpus for n in range(SFC_len)}, 'cpus')
    SFC[SCF_len]['cpus'] = 0
    print('SFC created ')

    # Store the stress-test results
    p_step = 0.1
    stress_test = {}

    # Create the stressed networks
    for p, G_ in stressed_networks().items:
        cells = [n for n in G_.nodes(data=True) if G_.nodes[n]['type']=='cell']
        stress_test[p] = {}

        # Deploy as the robot moves
        for cell in cells:
            deployment, completed = dlmd(G_, SFC, PoAs)

            # Store deployment results
            stress_test[p][f'completed_{cell}'] = completed
            stress_test[p][f'delay_{cell}'] = deployment_delay(G, deployment)
            stress_test[p][f'free_edge_{cell}'] = deployment_free_edge(G, SFC,
                                                                   deployment)

    # Store the stress-test in a CSV
    df_dict = {p: [] for p in stress_test.keys()}
    for p in df_dict:
        columns = []
        for cell in cells:
            df_dict[p] += [
                stress_test[p][f'completed_{cell}'],
                stress_test[p][f'delay_{cell}'],
                stress_test[p][f'free_edge_{cell}'],
            ]
            columns += [
                f'completed_{cell}',
                f'delay_{cell}',
                f'free_edge_{cell}',
            ]
    pd.DataFrame(df_dict, columns=columns).to_csv('/tmp/stress-test.csv')
