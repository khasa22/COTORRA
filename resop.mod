set N := R union r union w union s; #hardware graph V(G) nodes (i.e. PoA,robot,switches,servers)
set S; # service graph
set E:={n1 in N, n2 in N}; # graph edges of hardware graph
#set A; #set of VFs
set ES:={v1 in S,v2 in S}; # vertices of service graph
set R :={1..n};
set r ;
set w ;
set s ;
param n;
param comput_res {V};
#PoA
param throughput{n1 in E, n2 in E};
param delay;
param signal_strength{r[i]};
param sensor_data;
# transmission gain
var T{R[i]} ;
var vf_throughput{v1 in ES, v2 in ES};  # links throughtput between VFs
var c { v in S};                         #VF computational resources
var avf {V};                       # set of VFs hosted at node n
var avl{n1 in E, n2 in E};              #set of VL hosted at node(n1,n2)
var attachment{r[i],R[i]};
var P{v in S,n in V};                   #VF or VL placement
 #var indicator_func {a[n] ,r[i]};
maximize resources: sum {n in V} comput_res[n]-
sum {v in S: v in avf} c[v] + sum {(n1, n2) in E} throughput[n1,n2]-
sum {(v1,v2) in ES:(v1,v2) in avl} vf_throughput[v1,v2];
