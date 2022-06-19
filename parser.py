import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import os
import json
from collections import Counter
from datetime import datetime, timedelta
from random import uniform

TIME_DELTA = timedelta(hours=-8)
DELTAS = [0.00, 0.01, -0.01, 0.02, -0.02]
COLORS = iter(["blue", "green", "red", "orange", "black"])
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

    fig_all, ax_all = plt.subplots(figsize=(12,12))
    ax_all.set_title('All users', fontsize=20)
    pos = nx.circular_layout(G)
    pos = nx.rescale_layout_dict(pos)
    pos_labels = dict()
    for k, p in pos.items():
        pos_labels[k] = pos[k] + (0.25, 0.0) if pos[k][0] > 0.0 else pos[k] + (-0.25, 0.0)
    pos_labels['ts-inside-payment-service'] += (-0.06, 0.00)
    pos_labels['ts-consign-price-service'] += (+0.04, 0.00)
    pos_labels['ts-basic-service'] = pos['ts-basic-service'] + (0.0, 0.05)
    pos_labels['ts-contacts-service'] = pos['ts-contacts-service'] + (0.0, -0.05)
    nx.draw_networkx_nodes(G, ax=ax_all, pos=pos, node_size=50, node_color='black')
    nx.draw_networkx_labels(G, ax=ax_all, pos=pos_labels, clip_on=False)#, verticalalignment='bottom')
    user_colors = dict()
    link_counter = Counter()

    for user in INTERVALS.keys():
        user_colors[user] = next(colors)    

    for i, j, user in G.edges(keys=True):
        p1 = pos[i]
        p2 = pos[j]
        diff = p2-p1
        l = np.linalg.norm(diff)
        diff = (diff[1]/l, -diff[0]/l)
        new_pos = dict()
        delta = DELTAS[link_counter[(i,j)]]
        new_pos[i] =  np.array((p1[0]+delta*diff[0], p1[1]+delta*diff[1]))
        new_pos[j] =  np.array((p2[0]+delta*diff[0], p2[1]+delta*diff[1]))
        color = user_colors[user]
        nx.draw_networkx_edges(G, ax=ax_all, pos=new_pos, label=user, edge_color=color, edgelist = [(i,j)])
        link_counter[(i,j)] += 1

        
    '''
    for user in INTERVALS.keys():
        pos = {k: (p[0]*1.01, p[1]*1.01) for k, p in pos.items()}
        nx.draw_networkx_edges(G, pos=pos, label=user, edge_color=next(colors), edgelist = [(i,j) for i,j,k in G.edges(keys=True) if k  == user])
    '''
    ax_all.axis('off')
    plt.show()


if __name__ == '__main__':

    counters = dict()
    for k, i in INTERVALS.items():
        INTERVALS[k] = (datetime.fromisoformat(i[0])+TIME_DELTA,
                        datetime.fromisoformat(i[1])+TIME_DELTA)
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
