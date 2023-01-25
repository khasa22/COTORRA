# This script finds a feasibility region N,p where the Erdos-Renyi graph
# satisfies having D_i nodes of degree D

import numpy as np
import pandas as pd
import json


def fact(n):
    # returns n!
    return n*fact(n-1) if n>1 else 1

def erdos_renyi_degree(p,n,k):
    # P(deg(v) = k) on an Erdos-Renyi graph of n nodes with prob. p of link
    binom = fact(n-1) / ( fact(k) * fact(n-1-k) )
    return binom * p**k * (1-p)**(n-1-k)


if __name__ == '__main__':

    # Load URTINSA cells & remove GSM (2G) cells
    urtinsa_df = pd.read_csv('urtinsa_cells.csv')
    urtinsa_df = urtinsa_df[(urtinsa_df['Radio'] == 'LTE')]
    print(f'There are {len(urtinsa_df)} cells @Urtinsa')

  
    # Opening JSON file with server specifications
    # how many of each one, and the degree they should've in the graph
    with open('server-specs.json') as f:
        server_specs = json.load(f)
    number_of = server_spects['number_of']
    degree_of = server_spects['degree_of']

    feasibles = {
        'p': [],
        'n': []
    }



    # look for (n,p) pairs of Erdos-Renyi graphs satisfying
    # number_of servers at each layer, and their degree
    for n in range(len(urtinsa_df), len(urtinsa_df)*10):
        for p in np.arange(0,1,0.0005):
            ok_for_N_servers = 0

            print(f'n={n} p={p} -> ok={ok_for_N_servers}')
            for server in number_of.keys():
                print(f' {server}: {n*erdos_renyi_degree(p,n,degree_of[server])}  ')
                if n*erdos_renyi_degree(p,n,degree_of[server]) >=\
                        number_of[server]:
                    ok_for_N_servers += 1
            print(f'      -> ok={ok_for_N_servers}')


            if ok_for_N_servers == len(number_of.keys()):
                feasibles['p'].append(p)
                feasibles['n'].append(n)

    # Store the feasible region
    df = pd.DataFrame(feasibles, columns=['p','n'])
    df.sort_values(by='p')
    df.to_csv(f'pareto-front.csv')


