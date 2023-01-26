# This script executes stress tests for DLMD as resources decrease within
# infrastructure graphs.

import functools as reduce
import networkx as nx
import pandas as pd


def dlmd(G, SFC, max_delay, PoAs):
    # Executes de DLMD algorithm and yields the VF-placement for a robotic
    # service with a robot that can be attached to the PoAs. 
    # The code asumes the feasible PoAs are done.
    # The SFC is a graph

    # Server level function l(s)
    l = lambda s: 1 if G.nodes[s]['type'] == 'cloud' else (
            2 if G.nodes[s]['type'] == 'far_edge' else 3)

    # Obtain the edges with less than 'bw' bandwidth
    low_bw = lambda G,bw: [e for e,d in G.edges(data=True)\
                            if d['bandwidth'] <= bw]

    # Dijkstra weight function using the delay and used bw
    dlmd_weight_G = lambda n1,n2,G: G.edges(data=True)[n1,n2]['delay'] +\
                                    G.edges(data=True)[n1,n2]['used_bw']
    dlmd_weight = lambda n1,n2,data: data['delay'] + data['used_bw']


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

        for s in [s for s in servers\
                if SFC.nodes[vf]['cpus'] <= G.nodes[s]['cpus']]:
            # Server cost
            eta = l(s)
            
            # link cost
            if hop > 0 and hop < len(vls):
                # Prior VF
                vf_1 = vfs[hop]

                # Prune links without enough BW
                vl_bw = SFV.edges(data=True)[vls[hop]]
                pruned_links = low_bw(G, vl_bw)
                G_pruned = G.copy()
                G_pruned.remove_edges_from(pruned_links)

                # Find path between (vf,vf-1)
                s_1 = deployment[v_1]
                try networkx.exception.NetworkXNoPath as no_path:
                    path = shortest_path(G_pruned, source=s_1, target=s,
                                         weight=dlmd_weight, method='dijkstra')
                    eta += [dlmd_weight_G(n1,n2,G_pruned)\
                            for n1,n2 in zip(path[:-1], path[1:])]
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






if __name__ == '__main__':
    pass

