#hardware graph V(G) nodes (i.e. PoA,robot,switches,servers)
set N := R union r union w union s;
# graph edges of hardware graph
set E:={n1 in N, n2 in N}; 
# service graph
set S; 
# vertices (VNFs) of service graph
set ES:={v1 in S,v2 in S}; 
#set of VNFs
set VNF; 
#PoA(p1...pn)
set R :={1..n};
#robot
set r :={1..n};
#switches 
set w :={1..n};
;#servers
set s :={1..n};
param n;
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
param signal_strength{r[i]};
param background_noise;
# transmission gain
param T;	
param attachment{r,R} binary; 

# set of VFs hosted at node n or placement variable P(v,n)
var avf {v in S,n in N} binary; 
#set of VL hosted at node(n1,n2)   
var avl{ES,E};     
#var indicator_func {a[n] ,r[i]};

maximize resources: sum {n in N} comput_res[n]-
sum {v in S: v in avf} c[v] + sum {(n1, n2) in E} throughput[(n1,n2)in E]-
sum {(v1,v2) in ES:(v1,v2) in avl} vf_throughput[(v1,v2) in ES];

subject to Consrtaint{i in r}: sum {p in R} attachment{i,p}=1;
