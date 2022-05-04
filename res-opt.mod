#param n;
#PoA(p1..pn)
set R;
#robot
set r;
#switches
set w;
#servers
set s;
#hardware graph V(G) nodes (i.e. PoA,robot,switches,servers)
set N := {R union r union w union s};
# graph edges of hardware graph
set E:={n1 in N, n2 in N};
# service graph
set S;
#set of VNFs
set VNF{S};
# Edges (VNFs) of service graph
set VL{si in S}:={v1 in VNF[si],v2 in VNF[si]};
#total computational resources
param comput_res{n in N};
#VNF computational resources
param c { si in S,v in VNF[si]};
#throughtput between VFs links (v1,v2)
param vf_throughput{si in S,VL[si]};
#total bandwidth of (n1,n2)
param lambda{E};
#artificial queuing delay
param qd{E};
#delay associated with nodes at E(G)
param d{E};
#Mbps one CPU can process
param mu;
#processing delay of VNFs
param Pdelay{si in S,vf in VNF[si]}:= sum {(v1,v2)in VL[si]} (1/(vf_throughput[si,v1,v2]-c[si,vf]*mu));
#network delay of individual links at E(G)
param Ndelay{(n1,n2) in E}:= sum{si in S} sum {(v1,v2) in VL[si]}d[n1,n2]+qd[n1,n2];
#total service delay
param DS{S};
param signal_strength{i in r, p in R};
param background_noise;
# transmission gain
param T{i in r, p in R}:=lambda[i,p]*(log (1+(signal_strength[i,p]/background_noise)));
var attachment{r,R} binary;
#placement variable
#var P {si in S,VL[si],r,R} binary;
# set of VFs hosted at node n
var avf {s1 in S,vf in VNF[s1],n in N} binary;
#set of VL hosted at node(n1,n2)
var avl{si in S, VL[si],E} binary ;
#var indicator_func {a[n] ,r[i]};
maximize resources: sum {n in N} comput_res[n]-
sum {s1 in S,n in N}
        sum {vf in VNF[s1]} avf[s1,vf,n]*c[s1,vf]
+ sum {(n1, n2) in E} lambda[n1,n2]-
sum{si in S,(n1,n2) in E}
                sum {(v1,v2) in VL[si]}avl[si, v1,v2, n1,n2]*vf_throughput[si,v1,v2];
subject to Consrtaint{i in r}:
                            sum {p in R} attachment[i,p]=1;
 subject to radio_attachment{si in S,(v1,v2) in VL[si],ri in r, p in R}:
                             avl[si,v1,v2,ri,p]=attachment[ri,p]*avf[si,v1,ri];
subject to capacity{n in N}:
                            sum{si in S} sum {v in VNF[si]} avf[si,v,n]*c[si,v] <= comput_res[n];
subject to throughput{(n1,n2) in E}:
                            sum{si in S}sum {(v1, v2) in VL[si]} vf_throughput[si, v1,v2] <=lambda[n1,n2];
subject to PoA_feasiblity{i in r, p in R}:
                            sum{si in S}sum {(v1,v2) in VL[si]} vf_throughput[si, v1,v2]<= T[i,p];
subject to delay{j in S}:
                            sum {v in VNF[j]} Pdelay[j,v] + sum {(v1,v2) in VL[j]} Ndelay[v1,v2] <=DS[j];
