#param n
#PoA(p1...pn)
set R;
#robot
set r;
#switches 
set w ;
;#servers
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
set VNF; 
#total computational resources
param comput_res{n in N};	
#VNF computational resources
param c { v in S};  
#throughtput between VFs links (v1,v2) 
param vf_throughput{ES};
#total bandwidth of (n1,n2)	
param throughput{E};	
#processing delay of VNFs		
param Pdelay{v in S}; 
#network delay of individual links at E(G)
param Ndelay{ES};
#total service delay
param DS{S}; 
param signal_strength{i in r,p in R};
param background_noise;
# transmission gain
param T;	
param attachment{r,R} binary; 
#Placement variable P(v,n)
param P{v in S, n in N}binary;
# set of VFs hosted at node n 
var avf {v in VNF,n in N}; 
#set of VL hosted at node(n1,n2)   
var avl{ES,E};     
#var indicator_func {a[n] ,r[i]};

maximize resources: sum {n in N} comput_res[n]-
sum {v in S: (v,n) in avf} c[v] + sum {(n1, n2) in E} throughput[(n1,n2)in E]-
sum {(v1,v2) in ES:(ES,E) in avl} vf_throughput[(v1,v2) in ES];

subject to Consrtaint{i in r}: 
					sum {p in R} attachment[i,p]=1;
subject to palcement{n in N}: 
				    sum {v in S} P[v,n]*c[v] <= comput_res[n];
subject to capacity{(n1,n2) in E}: 
					sum {(v1, v2) in avl} vf_throughput[v1,v2] <=throughput[n1,n2];
subject to T{i in r, p in R}: 
					throughput[i,p]*log2 (1+(signal_strength[i,p]/background_noise));
subject to PoA_feasiblity{i in r, p in j}: 
					sum {(v1,v2) in ES} vf_throughput[v1,v2]<= T[i,p];
subject to delay{j in S}: 
			sum {v in S} Pdelay[v] + sum {(v1,v2) in ES} Ndelay[v1,v2] <=DS[j];
#subject to Pdelay {v in S}:
			#sum {(v1,v2)in ES} vf_throughput[v1,v2]*c[v];	
#subject to Ndelay{(v1,v2) in ES}		
