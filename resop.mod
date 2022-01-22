set V; # set of graph nodes
set S; # set of services 
set E; # graph edges
#set A; #set of VFs 

param comput_res {n in V};
param R {i in N}; #PoA
param throughput;
param delay;
param r {i in N};
param signal_strength;
param sensor_data
param T;# transmission gain

var c {v in S}; #VF computational resources
var a {n in V}; # set of VFs hosted at node n
var attachment{r[i], R[i] };
var P{v in S,n in V}; #VF or VL placement
#var indicator_func {a[n] ,r[i]};
