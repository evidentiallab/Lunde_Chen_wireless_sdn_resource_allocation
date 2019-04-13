
## Embedding and Re-embedding of Virtual Links in Software-Defined Multi-radio Multi-channel Multi-hop Wireless Networks

This repository contains the code for the Chapter 4 of my thesis, "Resource Allocation in Multi-domain Wireless Software-defined Networks".
Part of the work is published in
our [MSWiM 2018 paper](https://dl.acm.org/citation.cfm?id=3242121).


## Integer Linear Programming

The Integer Linear Programming is implemented mainly in [wireless_sdn_ilp.py](./wireless_sdn_ilp.py) and
[wireless_sdn_replay_mode_ilp.py](./wireless_sdn_replay_mode_ilp.py). CPLEX is used 
as the solver. Pypy is not supported in the ILP implementation due to the limit of CPLEX. 

## Genetic Algorithm

The Genetic Programming is implemented mainly in [wireless_sdn_ga.py](./wireless_sdn_ga.py), 
[wireless_sdn_replay_mode_ga.py](./wireless_sdn_replay_mode_ga.py),
 [wireless_sdn_tree_model_ga.py](./wireless_sdn_tree_model_ga.py)
 and [wireless_sdn_replay_mode_base.py](./wireless_sdn_replay_mode_base.py). 
All the representation (chromosome) and operators (cross-over, mutation) are
defined by us.
Pypy is supported for faster computation with its JIT compiler. 

The heuristic for constructing Steiner tree is the same
as presented in our [ISCC 2017 paper](https://ieeexplore.ieee.org/document/8024549).



## Open-source projects used or adapted in the work

[deap](https://deap.readthedocs.io/en/master/) Used for genetic algorithms. 

[dill](https://pypi.org/project/dill/) Used for save and load graph models and request models.

[heapdict](https://pypi.org/project/HeapDict/) Used in the heuristic for 
constructing Steiner tree, as a replacement of Fibonacci heap.
Heapdict is also used in pickling the requests
in an exponential manner.

[NetworkX](https://networkx.github.io/) Used for the graph model that represents networks, trees etc.

[K-shortest path algorithm](https://gist.github.com/guilhermemm/d4623c574d4bccb6bf0c) Used in the genetic algorithm.

[EllipsoidTool](https://github.com/minillinim/ellipsoid) Used for drawing cliques with ellipsoids in the graph models. 

[graph-tool](https://graph-tool.skewed.de/) Used in the genetic algorithm for speeding up graph computations.

[pypy](https://pypy.org/) Used in the genetic algorithm for speeding up.

Many thanks to those projects that have made our implementation easier. 
