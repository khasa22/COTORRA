set V; # set of graph nodes
set S; # set of services
set E; # graph edges
#set A; #set of VFs
set ES; # service graph edges
param n;
set N :={1..n};
param comput_res {V};
#PoA
param R {i in N};
param throughput{n1 in E, n2 in E};
param delay;
param r {i in N};
param signal_strength{r[i]};
param sensor_data;
# transmission gain
param T{R[i]} ;
param vf_throughput{v1 in ES, v2 in ES};  # links throughtput between VFs
param c { v in S};                         #VF computational resources
param attachment{r[i],R[i]};

var avf {V};                       # set of VFs hosted at node n
var avl{n1 in E, n2 in E};              #set of VL hosted at node(n1,n2)
var P{v in S,n in V};                   #VF or VL placement
#var indicator_func {a[n] ,r[i]};
maximize resources: sum {n in V} comput_res[n]-
sum {v in S: v in avf} c[v] + sum {(n1, n2) in E} throughput[n1,n2]-
sum {(v1,v2) in ES:(v1,v2) in avl} vf_throughput[v1,v2];
