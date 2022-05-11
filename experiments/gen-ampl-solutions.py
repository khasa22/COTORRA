import pandas as pd


# Durations at each location
durations = {
    'r1_r3': 50,
    'r3_r2': 50,
    'r2_r4': 50,
    'r4_r5': 25,
    'r5_r6': 25,
}


# latencies [ms] from PoAs to servers
poa_to_server = {
    'R1': {
        'ne': 3,
        'fe': 4,
        'cs': 9,
    },
    'R2': {
        'ne': 9,
        'fe': 8,
        'cs': 18,
    },
    'R5': {
        'ne': 9,
        'fe': 12,
        'cs': 27,
    }
}
poa_to_server['R3'] = poa_to_server['R1']
poa_to_server['R4'] = poa_to_server['R2']
poa_to_server['R6'] = poa_to_server['R5']


# PoA latencies [ms]
poa_latencies = {
    'R1': 2,
    'R2': 2,
    'R3': 2,
    'R4': 2,
    'R5': 2,
    'R6': 2
}

# PoA coverage
poa_coverage = {
    'r1_r3': ['R1', 'R3'],
    'r3_r2': ['R3', 'R2'],
    'r2_r4': ['R2', 'R4'],
    'r4_r5': ['R4', 'R5'],
    'r5_r6': ['R5', 'R6'],
}

# delays fe=far_edge ne=near_edge cs=cloud_server
time = range(1, 1+2*sum(durations.values()))





####################
# OPTIMAL solution #
####################

# Optimal PoA attachments
opt_attachments = {
    'r1_r3': 'R3',
    'r3_r2': 'R3',
    'r2_r4': 'R2',
    'r4_r5': 'R4',
    'r5_r6': 'R5'
}

# Optimal server selections
opt_server = {
    'r1_r3': 'cs',
    'r3_r2': 'fe',
    'r2_r4': 'fe',
    'r4_r5': 'fe',
    'r5_r6': 'fe'
}

# Create a list of OPT decision PoA elections over time
# also list telling wheter it is connected or not
opt_poa_election = []
opt_connected = []
for k in durations.keys():
    opt_poa_election += [opt_attachments[k]]*durations[k]
    opt_connected += [opt_attachments[k] in poa_coverage[k]]*durations[k]
opt_poa_election += opt_poa_election[::-1]
opt_connected += opt_connected[::-1]

# Create a list of OPT servers' selecion
opt_server_election = []
for k in durations.keys():
    opt_server_election += [opt_server[k]]*durations[k]
opt_server_election += opt_server_election[::-1]



# latencies towards servers in the optimal decisions
# latencies towards PoA in the optimal decisions
opt_ne_latencies = [0]*len(opt_poa_election)
opt_fe_latencies = [0]*len(opt_poa_election)
opt_cs_latencies = [0]*len(opt_poa_election)
opt_PoA_latencies = {
    k: [0]*len(time)
    for k in poa_latencies.keys()
}
for t in time:
    t -= 1
    PoA = opt_poa_election[t]
    server = opt_server_election[t]

    if server == 'ne':
        opt_ne_latencies[t] = poa_to_server[PoA][server] * opt_connected[t]
    elif server == 'fe':
        opt_fe_latencies[t] = poa_to_server[PoA][server] * opt_connected[t]
    elif server == 'cs':
        opt_cs_latencies[t] = poa_to_server[PoA][server] * opt_connected[t]

    # Put active the latency towards the elected PoA
    opt_PoA_latencies[PoA][t] = poa_latencies[PoA] * opt_connected[t]





# Create the stacked curves CSV for optimal decision
df_dict_opt = {}
df_dict_opt['time'] = time
for PoA in opt_PoA_latencies.keys():
    df_dict_opt[f'{PoA}_latency'] = opt_PoA_latencies[PoA]
df_dict_opt['PoA'] = opt_poa_election
df_dict_opt['server'] = opt_server_election
df_dict_opt['ne_latency'] = opt_ne_latencies
df_dict_opt['fe_latency'] = opt_fe_latencies
df_dict_opt['cs_latency'] = opt_cs_latencies
pd.DataFrame(df_dict_opt).to_csv('opt-stack-plot.csv', index=False)







###########################################
# Without the channel capacity constraint #
###########################################

# Optimal PoA attachments
noT_attachments = {
    'r1_r3': 'R5',
    'r3_r2': 'R5',
    'r2_r4': 'R5',
    'r4_r5': 'R5',
    'r5_r6': 'R5'
}

# Optimal server selections
noT_server = {
    'r1_r3': 'ne',
    'r3_r2': 'ne',
    'r2_r4': 'ne',
    'r4_r5': 'ne',
    'r5_r6': 'ne'
}

# Create a list of OPT decision PoA elections over time
# also list telling wheter it is connected or not
noT_poa_election = []
noT_connected = []
for k in durations.keys():
    noT_poa_election += [noT_attachments[k]]*durations[k]
    noT_connected += [noT_attachments[k] in poa_coverage[k]]*durations[k]
noT_poa_election += noT_poa_election[::-1]
noT_connected += noT_connected[::-1]

# Create a list of OPT servers' selecion
noT_server_election = []
for k in durations.keys():
    noT_server_election += [noT_server[k]]*durations[k]
noT_server_election += noT_server_election[::-1]



# latencies towards servers in the noTimal decisions
# latencies towards PoA in the noTimal decisions
noT_ne_latencies = [0]*len(noT_poa_election)
noT_fe_latencies = [0]*len(noT_poa_election)
noT_cs_latencies = [0]*len(noT_poa_election)
noT_PoA_latencies = {
    k: [0]*len(time)
    for k in poa_latencies.keys()
}
for t in time:
    t -= 1
    PoA = noT_poa_election[t]
    server = noT_server_election[t]

    if server == 'ne':
        noT_ne_latencies[t] = poa_to_server[PoA][server] * noT_connected[t]
    elif server == 'fe':
        noT_fe_latencies[t] = poa_to_server[PoA][server] * noT_connected[t]
    elif server == 'cs':
        noT_cs_latencies[t] = poa_to_server[PoA][server] * noT_connected[t]

    # Put active the latency towards the elected PoA
    noT_PoA_latencies[PoA][t] = poa_latencies[PoA] * noT_connected[t]





# Create the stacked curves CSV for noTimal decision
df_dict_noT = {}
df_dict_noT['time'] = time
for PoA in noT_PoA_latencies.keys():
    df_dict_noT[f'{PoA}_latency'] = noT_PoA_latencies[PoA]
df_dict_noT['PoA'] = noT_poa_election
df_dict_noT['server'] = noT_server_election
df_dict_noT['ne_latency'] = noT_ne_latencies
df_dict_noT['fe_latency'] = noT_fe_latencies
df_dict_noT['cs_latency'] = noT_cs_latencies
pd.DataFrame(df_dict_noT).to_csv('noT-stack-plot.csv', index=False)









################################
# Without the delay constraint #
################################

# Optimal PoA attachments
noDelay_attachments = {
    'r1_r3': 'R3',
    'r3_r2': 'R3',
    'r2_r4': 'R3',
    'r4_r5': 'R5',
    'r5_r6': 'R6'
}

# Optimal server selections
noDelay_server = {
    'r1_r3': 'cs',
    'r3_r2': 'cs',
    'r2_r4': 'cs',
    'r4_r5': 'cs',
    'r5_r6': 'cs'
}

# Create a list of OPT decision PoA elections over time
# also list telling wheter it is connected or not
noDelay_poa_election = []
noDelay_connected = []
for k in durations.keys():
    noDelay_poa_election += [noDelay_attachments[k]]*durations[k]
    noDelay_connected += [noDelay_attachments[k] in poa_coverage[k]]*durations[k]
noDelay_poa_election += noDelay_poa_election[::-1]
noDelay_connected += noDelay_connected[::-1]

# Create a list of OPT servers' selecion
noDelay_server_election = []
for k in durations.keys():
    noDelay_server_election += [noDelay_server[k]]*durations[k]
noDelay_server_election += noDelay_server_election[::-1]



# latencies towards servers in the noDelayimal decisions
# latencies towards PoA in the noDelayimal decisions
noDelay_ne_latencies = [0]*len(noDelay_poa_election)
noDelay_fe_latencies = [0]*len(noDelay_poa_election)
noDelay_cs_latencies = [0]*len(noDelay_poa_election)
noDelay_PoA_latencies = {
    k: [0]*len(time)
    for k in poa_latencies.keys()
}
for t in time:
    t -= 1
    PoA = noDelay_poa_election[t]
    server = noDelay_server_election[t]

    if server == 'ne':
        noDelay_ne_latencies[t] = poa_to_server[PoA][server] * noDelay_connected[t]
    elif server == 'fe':
        noDelay_fe_latencies[t] = poa_to_server[PoA][server] * noDelay_connected[t]
    elif server == 'cs':
        noDelay_cs_latencies[t] = poa_to_server[PoA][server] * noDelay_connected[t]

    # Put active the latency towards the elected PoA
    noDelay_PoA_latencies[PoA][t] = poa_latencies[PoA] * noDelay_connected[t]





# Create the stacked curves CSV for noDelayimal decision
df_dict_noDelay = {}
df_dict_noDelay['time'] = time
for PoA in noDelay_PoA_latencies.keys():
    df_dict_noDelay[f'{PoA}_latency'] = noDelay_PoA_latencies[PoA]
df_dict_noDelay['PoA'] = noDelay_poa_election
df_dict_noDelay['server'] = noDelay_server_election
df_dict_noDelay['ne_latency'] = noDelay_ne_latencies
df_dict_noDelay['fe_latency'] = noDelay_fe_latencies
df_dict_noDelay['cs_latency'] = noDelay_cs_latencies
pd.DataFrame(df_dict_noDelay).to_csv('noDelay-stack-plot.csv', index=False)

