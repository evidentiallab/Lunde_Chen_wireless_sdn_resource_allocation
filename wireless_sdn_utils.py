# coding: utf-8
from __future__ import print_function
from random import randint
from wireless_sdn_heapdict import *
import time

def demical_to_str(demical, len_demical=1):
    multiplier = 10 ** len_demical
    return str(1000 + int(multiplier * demical))[-2:]

def sph_steiner_dijkstra(g, z, metric='weight'):
    start_time = time.time()
    cost = 0
    T = set()
    pred = {}
    node = z[randint(0, len(z) - 1)]
    T.add(node)
    count = len(z) - 1
    hd = heapdict()
    dist = {}
    for n in g.nodes():
        dist[n] = float("inf")
    dist[node] = 0
    unvisited = g.nodes()
    unvisited.remove(node)
    steiner_edges = []
    nodes = [node]

    while 1:
        for node in nodes:
            for v in g[node]:
                if v in unvisited:
                    # The only difference between Prime and Dijkstra is here:
                    # Dijkstra : + dist[node]
                    tmp = g[node][v].get(metric) + dist[node]
                    if tmp < dist[v]:
                        dist[v] = tmp
                        hd[v] = (dist[v], node)
        nodes = []
        pop = hd.popitem()
        v = pop[0]
        pred[v] = pop[1][1]
        unvisited.remove(v)
        nodes = [v]
        if v in z:
            count -= 1
            nodes = []
            while v not in T:
                steiner_edges.append(tuple(sorted(list((pred[v], v)))))
                cost += g[pred[v]][v].get(metric)
                dist[v] = 0
                T.add(v)
                # If a node's minimum dijkstra path value is to be changed,
                # the node must be among the neighbors of newly added nodes.
                nodes.append(v)
                v = pred[v]
            unvisited = list(set(g.nodes()) - set(T))
        if count == 0:
            break

    elasped_time = time.time() - start_time
    # print 'finished, time elasped: ', elasped_time
    return (steiner_edges, cost)

def minimum_vol_ellipsoid(P=None, tolerance=0.01):
    """ 
    @ref: 
    This EllipsoidTool comes from github:
    https://github.com/minillinim/ellipsoid
    @paper: 
    On Khachiyan s Algorithm for the Computation of Minimum Volume Enclosing Ellipsoids
    """
    import numpy as np
    from numpy import linalg
    (N, d) = np.shape(P)
    d = float(d)
    Q = np.vstack([np.copy(P.T), np.ones(N)])
    QT = Q.T
    err = 1.0 + tolerance
    u = (1.0 / N) * np.ones(N)
    while err > tolerance:
        V = np.dot(Q, np.dot(np.diag(u), QT))
        M = np.diag(np.dot(QT, np.dot(linalg.inv(V), Q)))
        j = np.argmax(M)
        maximum = M[j]
        step_size = (maximum - d - 1.0) / ((d + 1.0) * (maximum - 1.0))
        new_u = (1.0 - step_size) * u
        new_u[j] += step_size
        err = np.linalg.norm(new_u - u)
        u = new_u
    center = np.dot(P.T, u)
    A = linalg.inv(
            np.dot(P.T, np.dot(np.diag(u), P)) -
            np.array([[a * b for b in center] for a in center])) / d
    U, s, rotation = linalg.svd(A)
    radii = 1.0 / np.sqrt(s)
    return (center, radii, rotation)


def test_heapdict_heap():
    hd = heapdict()
    hd[1] = 999
    hd[2] = 888
    hd[3] = 1111
    hd[4] = 3333
    hd[5] = 2222
    print(hd.heap, '\n')
    hd[4] = 333
    print(hd.heap, '\n')
    hd[1] = 9999
    hd[5] = 2222
    print(hd.heap, '\n')



