import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import os
import json
from collections import Counter
from datetime import datetime, timedelta
from random import uniform

DELTA = timedelta(hours=-8)
INTERVALS = {
    "UserNoLogin": ("2022-06-13 11:58:06.590", "2022-06-13 12:08:06.016"),
    "UserBooking": ("2022-06-13 12:36:47.820", "2022-06-13 12:46:47.202"),
    "UserConsignTicket": ("2022-06-13 12:47:33.280", "2022-06-13 12:57:30.370"),
    "UserCancelNoRefund": ("2022-06-13 13:04:39.409", "2022-06-13 13:14:38.821"),
    "UserRefundVoucher": ("2022-06-13 13:15:16.538", "2022-06-13 13:25:15.964")
}

def parse_logs(directory, filename, counters):

    from_service = filename.split('.')[0]
    f = open(os.path.join(directory, filename), 'r')
    for line in f:
        if line[0] == '{':
            obj = json.loads(line)
            start_time = obj["start_time"]
            start_time = datetime.fromisoformat(start_time[:-1])
            user = None
            for k, i in INTERVALS.items():
                #print(start_time)
                #print(i[0])
                #print(i[1])
                if start_time > i[0] and start_time < i[1]:
                    user = k
                    break
            if user is None: continue
            to_service = obj["upstream_cluster"]
            to_service = to_service.split('|')
            if to_service[0] == 'outbound':
                to_service = to_service[3].split('.')[0]
                counters[user][(from_service, to_service)] += 1

def draw_graph(G):

    fig_all = plt.figure()
    ax_all = fig_all.add_subplot(111)
    ax_all.set_title('All users')
    pos = nx.circular_layout(G)
    pos = nx.rescale_layout_dict(pos)
    colors = iter(["blue", "green", "red", "orange", "black"])
    pos_labels = {k: (p[0]*1.10, p[1]*1.10) for k, p in pos.items()}
    nx.draw_networkx_nodes(G, ax=ax_all, pos=pos, node_size=100)
    nx.draw_networkx_labels(G, ax=ax_all, pos=pos_labels)#, verticalalignment='bottom')
    user_colors = dict()
    for i, j, user in G.edges(keys=True):
        p1 = pos[i]
        p2 = pos[j]
        diff = p2-p1
        diff = (diff[1], -diff[0])
        #print(diff)
        new_pos = dict()
        delta = 0.01
        new_pos[i] =  np.array((p1[0]+delta*diff[0], p1[1]+delta*diff[1]))
        new_pos[j] =  np.array((p2[0]+delta*diff[0], p2[1]+delta*diff[1]))
        if user in user_colors:
            color = user_colors[user]
        else:
            color = next(colors)
            user_colors[user] = color
        nx.draw_networkx_edges(G, ax=ax_all, pos=new_pos, label=user, edge_color=color, edgelist = [(i,j)])

        
    '''
    for user in INTERVALS.keys():
        pos = {k: (p[0]*1.01, p[1]*1.01) for k, p in pos.items()}
        nx.draw_networkx_edges(G, pos=pos, label=user, edge_color=next(colors), edgelist = [(i,j) for i,j,k in G.edges(keys=True) if k  == user])
    '''
    plt.show()


if __name__ == '__main__':

    counters = dict()
    for k, i in INTERVALS.items():
        INTERVALS[k] = (datetime.fromisoformat(i[0])+DELTA, datetime.fromisoformat(i[1])+DELTA)
        counters[k] = Counter()
    directory = "kubernetes-istio-sleuth-v0.2.1-separate-load/tracing-log"
    G = nx.MultiDiGraph()
    for file in os.listdir(directory):
        if file.endswith(".log"):
            parse_logs(directory, file, counters)
    #print(counters)
    for user, counter in counters.items():
        for keys, weight in counter.items():
            G.add_edge(keys[0], keys[1], key=user, weight=weight)
    #print(G.nodes)
    draw_graph(G)
