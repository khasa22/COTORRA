# This script executes stress tests for DLMD as resources decrease within
# infrastructure graphs.

from functools import reduce
import networkx as nx
import pandas as pd
import numpy as np
import copy
import argparse
import time



##################
# DLMD FUNCTIONS #
##################

def shortest_and_weight(G, src, dst, weight_fn):
    # Finds the shortest path between src and dst using as cost the weight_fn
    # using Dijkstra
    # The weight_fn receives the edge enedpoints and the edge data

    path = nx.shortest_path(G, source=src, target=dst,
                            weight=weight_fn, method='dijkstra')
    path_weight = sum([weight_fn(n1,n2,G.edges[n1,n2])\
                       for n1,n2 in zip(path[:-1], path[1:])])
    
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
    low_bw = lambda G,bw: [(n1,n2) for n1,n2,d in G.edges(data=True)\
                            if d['bandwidth'] <= bw]

    # Check the used CPUs @server=s in the deployment
    used_cpus = lambda s,dep,G,SFC: sum([SFC.nodes[vf]['cpus']\
            for vf in dep if (type(vf)!=tuple) and dep[vf]==s])

    # Dijkstra weight function using the delay and used bw
    dlmd_weight_G = lambda n1,n2,G: G.edges(data=True)[n1,n2]['delay'] +\
                                    G.edges(data=True)[n1,n2]['used_bw']
    dlmd_weight = lambda n1,n2,data: data['delay'] + data['used_bw']


    # Deployment
    deployment = {}

    # Filter the servers
    servers = [n for n,d in G.nodes(data=True) if 'type' in d and
                d['type'] in ['near_edge', 'far_edge', 'cloud']]


    # Create sorted VFs & VLs
    vfs =  sorted(SFC.nodes, reverse=True)
    vls =  list(zip(sorted(SFC.nodes, reverse=True)[:-1],
                    sorted(SFC.nodes, reverse=True)[1:]))

    hop = -1
    max_eta = 1000
    for vf in vfs:
        print('  vf:', vf)
        min_eta = max_eta
        path = []

        # Find the server deployment or steer to PoA
        for s in (servers if vf != vfs[-1] else [PoA]):
            # Check if server s has enough CPUs
            free_cpus = G.nodes[s]['cpus'] - used_cpus(s,deployment,G,SFC)
            if SFC.nodes[vf]['cpus'] > free_cpus:
                continue

            # Server weight=eta based on distance to the PoA
            try:
                _, server_poa_eta = shortest_and_weight(G=G, src=s, dst=PoA,
                                                        weight_fn=dlmd_weight)
                eta = l(s) + server_poa_eta
            # Exit if the server has no connectivity to the PoA
            except nx.exception.NetworkXNoPath as no_path:
                continue
            
            # link cost
            if hop >= 0:
                # Prior VF
                vf_1 = vfs[hop]

                # Prune links without enough BW
                vl_bw = SFC[vf_1][vf]['bandwidth']
                pruned_links = low_bw(G, vl_bw)
                G_pruned = copy.deepcopy(G)
                G_pruned.remove_edges_from(pruned_links)

                # Find path between (vf,vf-1)
                s_1 = deployment[vf_1]
                try:
                    path, path_eta = shortest_and_weight(
                            G=G_pruned, src=s_1, dst=s, weight_fn=dlmd_weight)
                    eta += path_eta
                except nx.exception.NetworkXNoPath as no_path:
                    path = []
                    eta += 100000


            # Select the deployment if it's better
            if eta < min_eta:
                min_eta = eta
                deployment[vf] = s
                if hop >= 0:
                    deployment[vf_1,vf] = path


        # Return if the VF could not be deployed
        if min_eta == max_eta:
            return deployment, False

        # Consume the VL bandwidth along the best deployment path
        if hop >= 0:
            for n1,n2 in zip(path[:-1], path[1:]):
                G[n1][n2]['bandwidth'] -= vl_bw
                G[n1][n2]['used_bw'] += vl_bw


        # Go to next hop in the SFC
        hop += 1

    # Check if the deployment has been completed
    completed = reduce(lambda a,b: a and b,
                       [vf in deployment for vf in SFC.nodes])

    return deployment, completed



def deployment_delay(G, deployment):
    # Computes the delay of a deployment over the graph G

    delay = 0

    for vf1,vf2 in filter(lambda k: type(k)==tuple, deployment.keys()):
        path = deployment[vf1,vf2]
        delay += sum([G[n1][n2]['delay']\
                        for n1,n2 in zip(path[:-1], path[1:])])

    return delay


def deployment_free_edge(G, G_, SFC, deployment):
    # Calculates the free edge resources at the edge 
    # using the original graph G, and the stressed graph G_
    # note: the deployment must have been successfull
    # returns: free_ALL_edge, free_far_edge, free_near_edge

    n_edges = [n for n,d in G.nodes(data=True)\
                if ('type' in d) and (d['type']=='near_edge')]
    n_edge_cpus = sum([d['cpus'] for n,d in G.nodes(data=True)\
                        if ('type' in d) and (d['type']=='near_edge')])
    n_edge_cpus_ = sum([d['cpus'] for n,d in G_.nodes(data=True)\
                        if ('type' in d) and (d['type']=='near_edge')])
    f_edges = [n for n,d in G.nodes(data=True)\
                if ('type' in d) and (d['type']=='far_edge')]
    f_edge_cpus = sum([d['cpus'] for n,d in G.nodes(data=True)\
                        if ('type' in d) and (d['type']=='far_edge')])
    f_edge_cpus_ = sum([d['cpus'] for n,d in G_.nodes(data=True)\
                        if ('type' in d) and (d['type']=='far_edge')])

    # Total edge resource
    total_edge = n_edge_cpus + f_edge_cpus
    consumed_n_edge = 0
    consumed_f_edge = 0

    # Derive the resource consumption
    for vf in SFC.nodes:
        if G.nodes[deployment[vf]]['type'] == 'near_edge':
            consumed_n_edge += SFC.nodes[vf]['cpus']
        elif G.nodes[deployment[vf]]['type'] == 'far_edge':
            consumed_f_edge += SFC.nodes[vf]['cpus']
    consumed_edge = consumed_n_edge + consumed_f_edge
            
    # Derive free resources
    free_all_edge = (n_edge_cpus_+ f_edge_cpus_ - consumed_edge) /\
                        (n_edge_cpus + f_edge_cpus)
    free_far_edge = (f_edge_cpus_ - consumed_f_edge) / f_edge_cpus
    free_near_edge = (n_edge_cpus_ - consumed_n_edge) / n_edge_cpus

    return free_all_edge, free_far_edge, free_near_edge
    
    


def print_server_resources(G):
    # prints the CPUs of servers

    cloud_cpus, f_edge_cpus, n_edge_cpus = 0, 0, 0

    for n in G.nodes:
        if 'type' in G.nodes[n]:
            if G.nodes[n]['type'] == 'cloud':
                cloud_cpus += G.nodes[n]['cpus']
            elif G.nodes[n]['type'] == 'far_edge':
                f_edge_cpus += G.nodes[n]['cpus']
            elif G.nodes[n]['type'] == 'near_edge':
                n_edge_cpus += G.nodes[n]['cpus']

    print(f'== Server resources @{G} ==')
    print(f'{cloud_cpus}CPUs @cloud')
    print(f'{f_edge_cpus}CPUs @far edge')
    print(f'{n_edge_cpus}CPUs @near edge')
            




#########################
# STRESS-TEST FUNCTIONS #
#########################

def stress_network(G, p_step=0.1):
    # Stress G resources at steps of p_step percent

    stressed_networks = {0: copy.deepcopy(G)}

    # Get the server nodes
    n_edges = [n for n,d in G.nodes(data=True)\
               if 'type' in d and d['type']=='near_edge']
    f_edges = [n for n,d in G.nodes(data=True)\
               if 'type' in d and d['type']=='far_edge']
    clouds = [n for n,d in G.nodes(data=True)\
               if 'type' in d and d['type']=='cloud']

    # CPU sums
    n_edge_cpus = sum([G.nodes[s]['cpus'] for s in n_edges])
    f_edge_cpus = sum([G.nodes[s]['cpus'] for s in f_edges])
    cloud_cpus = sum([G.nodes[s]['cpus'] for s in clouds])

    for p in np.arange(p_step, 1, p_step):
        # Get the copy for this p and store it
        G_ = copy.deepcopy(G)
        stressed_networks[round(p,2)] = G_
        print(f'stress @{p}')

        # Compute #edges & CPUs to remove
        edges_to_remove = round(p * len(G.edges))
        n_edge_cpus_to_remove = round(p * n_edge_cpus)
        f_edge_cpus_to_remove = round(p * f_edge_cpus)
        cloud_cpus_to_remove = round(p * cloud_cpus)
    
        # Remove edge from the highest degree nodes
        for _ in range(edges_to_remove):
            nodes_deg = sorted([(n, len(G_[n])) for n in G_.nodes],
                           key=lambda x: x[1], reverse=True)
            G_.remove_edge(nodes_deg[0][0], list(G_[nodes_deg[0][0]])[0])

        # Remove near edge CPUs
        i = 0
        while n_edge_cpus_to_remove > 0:
            s = n_edges[i]
            G_.nodes[s]['cpus'] -= 1
            i = (i+1) % len(n_edges)
            n_edge_cpus_to_remove -= 1

        # Remove far edge CPUs
        i = 0
        while f_edge_cpus_to_remove > 0:
            s = f_edges[i]
            G_.nodes[s]['cpus'] -= 1
            i = (i+1) % len(f_edges)
            f_edge_cpus_to_remove -= 1

        # Remove cloud CPUs
        i = 0
        while cloud_cpus_to_remove > 0:
            s = clouds[i]
            G_.nodes[s]['cpus'] -= 1
            i = (i+1) % len(clouds)
            cloud_cpus_to_remove -= 1

    return stressed_networks






if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('graphGML', type=str,
                        help='path to the infra graph GML')
    args = parser.parse_args()



    # Read the infrastructure CSV and set cell CPUs to 0
    G = nx.read_gml(args.graphGML)
    G_name = args.graphGML.split('/')[-1].split('.')[0]
    cells = [n for n,d in G.nodes(data=True)\
            if 'type' in d and d['type'] == 'cell']
    nx.set_node_attributes(G, {cell: 0 for cell in cells}, 'cpus')
    nx.set_edge_attributes(G, {e: 0 for e in G.edges}, 'used_bw')
    nx.set_edge_attributes(G, {e: 1 for e in G.edges}, 'delay')

    # Create the SFC
    SFC_len = 4
    SFC = nx.path_graph(SFC_len)
    VF_cpus = 1
    nx.set_edge_attributes(SFC, {e: 1 for e in SFC.edges}, 'bandwidth')
    nx.set_node_attributes(SFC, {n: VF_cpus for n in range(SFC_len)}, 'cpus')
    SFC.nodes[0]['cpus'] = 0 # the PoA
    print('SFC created ')

    # Store the stress-test results
    p_step = 0.01
    stress_test = {}

    # Create the stressed networks
    for p, G_ in stress_network(G, p_step).items():
        print(f'G stress: p={p} with {len(list(nx.connected_components(G_)))}')
        print_server_resources(G_)

        PoAs= [n for n,d in G_.nodes(data=True)\
                if 'type' in d and d['type']=='cell']
        stress_test[p] = {}

        # Store the available resources at this step
        av_all_edge, av_far_edge, av_near_edge =\
            deployment_free_edge(G, G_, nx.Graph(), {})
        stress_test[p][f'available_edge'] = av_all_edge
        stress_test[p][f'available_far_edge'] = av_far_edge
        stress_test[p][f'available_near_edge'] = av_near_edge

        # Deploy as the robot moves
        for PoA in PoAs:
            # Execute DLMD
            print(f' DLMD@PoA={PoA}')
            tic = time.time()
            deployment, completed = dlmd(G_, SFC, PoA)
            tac = time.time()

            # Store deployment results
            stress_test[p][f'completed_{PoA}'] = completed
            stress_test[p][f'delay_{PoA}'] =\
                deployment_delay(G, deployment) if completed else 30
            free_all_edge, free_far_edge, free_near_edge =\
                deployment_free_edge(G, G_,
                     SFC if completed else nx.Graph(), deployment)
            stress_test[p][f'free_edge_{PoA}'] = free_all_edge
            stress_test[p][f'free_far_edge_{PoA}'] = free_far_edge
            stress_test[p][f'free_near_edge_{PoA}'] = free_near_edge
            stress_test[p][f'dlmd_runtime_{PoA}'] = tac - tic




    ##################################
    # Store the stress-test in a CSV #
    ##################################
    df_dict = {p: [] for p in stress_test.keys()}
    for p in df_dict:
        columns = []

        p_completions, p_delays, p_runtimes = [], [], []
        p_free_edges, p_free_far_edges, p_free_near_edges = [], [], []

        # Specify the available resources
        df_dict[p] += [
            stress_test[p][f'available_edge'], 
            stress_test[p][f'available_far_edge'],
            stress_test[p][f'available_near_edge']
        ]
        columns += [
            'available_edge', 
            'available_far_edge',
            'available_near_edge'
        ]

        # Specify results for each PoA
        for PoA in PoAs:
            p_completions += [stress_test[p][f'completed_{PoA}']]
            p_delays += [stress_test[p][f'delay_{PoA}']]
            p_free_edges += [stress_test[p][f'free_edge_{PoA}']]
            p_free_far_edges += [stress_test[p][f'free_far_edge_{PoA}']]
            p_free_near_edges += [stress_test[p][f'free_near_edge_{PoA}']]
            p_runtimes += [stress_test[p][f'dlmd_runtime_{PoA}']]

            df_dict[p] += [
                stress_test[p][f'completed_{PoA}'],
                stress_test[p][f'delay_{PoA}'],
                stress_test[p][f'free_edge_{PoA}'],
                stress_test[p][f'free_far_edge_{PoA}'],
                stress_test[p][f'free_near_edge_{PoA}'],
                stress_test[p][f'dlmd_runtime_{PoA}'],
            ]
            columns += [
                f'completed_{PoA}',
                f'delay_{PoA}',
                f'free_edge_{PoA}',
                f'free_far_edge_{PoA}',
                f'free_near_edge_{PoA}',
                f'dlmd_runtime_{PoA}',
            ]

        #############
        # Get stats #
        #############
        percentiles = list(range(0, 101, 5))
        # Completion
        columns += ['completion_percentage']
        df_dict[p] += [sum(p_completions) / len(p_completions)]
        # Delay
        columns += ['delay_avg']
        df_dict[p] += [np.mean(p_delays)]
        columns += ['delay_median']
        df_dict[p] += [np.median(p_delays)]
        columns += [f'delay_percentile_{q:.2f}' for q in percentiles]
        df_dict[p] += list(np.percentile(p_delays, percentiles))
        # Free edge
        columns += ['free_edge_avg']
        df_dict[p] += [np.mean(p_free_edges)]
        columns += ['free_edge_median']
        df_dict[p] += [np.median(p_free_edges)]
        columns += ['free_edge_min']
        df_dict[p] += [min(p_free_edges)]
        columns += [f'free_edge_percentile_{q:.2f}' for q in percentiles]
        df_dict[p] += list(np.percentile(p_free_edges, percentiles))
        # Free far edge
        columns += ['free_far_edge_avg']
        df_dict[p] += [np.mean(p_free_far_edges)]
        columns += ['free_far_edge_median']
        df_dict[p] += [np.median(p_free_far_edges)]
        columns += ['free_far_edge_min']
        df_dict[p] += [min(p_free_far_edges)]
        columns += [f'free_far_edge_percentile_{q:.2f}' for q in percentiles]
        df_dict[p] += list(np.percentile(p_free_far_edges, percentiles))
        # Free near edge
        columns += ['free_near_edge_avg']
        df_dict[p] += [np.mean(p_free_near_edges)]
        columns += ['free_near_edge_median']
        df_dict[p] += [np.median(p_free_near_edges)]
        columns += ['free_near_edge_min']
        df_dict[p] += [min(p_free_near_edges)]
        columns += [f'free_near_edge_percentile_{q:.2f}' for q in percentiles]
        df_dict[p] += list(np.percentile(p_free_near_edges, percentiles))
        # run-time
        columns += [f'dlmd_runtime_percentile_{q:.2f}' for q in percentiles]
        df_dict[p] += list(np.percentile(p_runtimes, percentiles))
        columns += ['median_dlmd_runtime']
        df_dict[p] += [np.median(p_runtimes)]
        columns += ['max_dlmd_runtime']
        df_dict[p] += [max(p_runtimes)]

    # Print it all out
    for i,col in enumerate(columns):
        print('column:', i+2, '=', col)
    out = f'stress-test-{G_name}.csv'
    print('writing stress metrics at:', out)
    pd.DataFrame.from_dict(df_dict, columns=columns,
            orient='index').to_csv(out, index_label='p')

