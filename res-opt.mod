#param n
#PoA(p1...pn)
set R;
#robot
set r;
#switches 
set w ;
#servers
set s;
#hardware graph V(G) nodes (i.e. PoA,robot,switches,servers)
set N := {R union r union w union s};
# graph edges of hardware graph
set E:={n1 in N, n2 in N}; 
# service graph
set S; 
# vertices (VNFs) of service graph
set ES:={v1 in S,v2 in S}; 
#set of VNFs
set VNF{S}; 
#total computational resources
param comput_res{n in N};	
#VNF computational resources
param c { v in S};  
#throughtput between VFs links (v1,v2) 
param vf_throughput{ES};
#total bandwidth of (n1,n2)	
param Pdelay{s1 in S,vf in VNF[s1]}:= sum {(v1,v2)in ES} vf_throughput[v1,v2]*c[vf];
#network delay of individual links at E(G)
param Ndelay{(n1,n2) in E}:= sum {(v1,v2) in ES}d[n1,n2]+qd[n1,n2];
#total service delay
param DS{S};
param signal_strength{i in r, p in R};
param background_noise;
# transmission gain
param T{i in r, p in R}:=throughput[i,p]*(log (1+(signal_strength[i,p]/background_noise)));
param attachment{r,R} binary;
#placement variable
#param P {s1 in S,n in N} binary;

# set of VFs hosted at node n
var avf {s1 in S,vf in VNF[s1],n in N} binary;
#set of VL hosted at node(n1,n2)
var avl{ES,E} binary ;
#var indicator_func {a[n] ,r[i]};
maximize resources: sum {n in N} comput_res[n]-
sum {s1 in S,n in N}
        (sum {vf in VNF[s1]} if avf[s1,vf,n]==1 then c[vf])
+ sum {(n1, n2) in E} throughput[n1,n2]-
sum {(v1,v2) in ES}
        (sum {s1 in S,vf in VNF[s1],n in N} if avf[s1,vf,n]==1 then vf_throughput[v1,v2]);
subject to Consrtaint{i in r}:
                                        sum {p in R} attachment[i,p]=1;
subject to palcement{s1 in S, n in N}:
                                    sum {v in VNF[s1]} avf[s1,v,n]*c[v] <= comput_res[n];
subject to capacity{(n1,n2) in E}:
                                        sum {(v1, v2) in ES} vf_throughput[v1,v2] <=throughput[n1,n2];
subject to PoA_feasiblity{i in r, p in R}:
                                        sum {(v1,v2) in ES} vf_throughput[v1,v2]<= T[i,p];
subject to delay{j in S}:
                        sum {v in VNF[j]} Pdelay[j,v] + sum {(v1,v2) in ES} Ndelay[v1,v2] <=DS[j];
			
			

		
