import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import os
import json
from collections import Counter
from datetime import datetime, timedelta

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
                if start_time > i[0] and start_time < i[1]:
                    user = k
                    break
            if user is None: continue
            to_service = obj["upstream_cluster"]
            to_service = to_service.split('|')
            if to_service[0] == 'outbound':
                to_service = to_service[3].split('.')[0]
                counters[user][(from_service, to_service)] += 1

def draw_graph(G, curved_arrows=True):

    # Figure for all users
    fig_all, ax_all = plt.subplots(figsize=(12,12))
    ax_all.set_title('All users', fontsize=20)
    ax_all.axis('off')

    # General positions of nodes
    pos = nx.circular_layout(G)
    pos = nx.rescale_layout_dict(pos)

    # Positions for labels to prevent overlapping
    pos_labels = dict()
    for k, p in pos.items():
        pos_labels[k] = pos[k] + (0.25, 0.0) if pos[k][0] > 0.0 else pos[k] + (-0.25, 0.0)
    pos_labels['ts-inside-payment-service'] += (-0.06, 0.00)
    pos_labels['ts-consign-price-service'] += (+0.04, 0.00)
    pos_labels['ts-basic-service'] = pos['ts-basic-service'] + (0.0, 0.05)
    pos_labels['ts-contacts-service'] = pos['ts-contacts-service'] + (0.0, -0.05)

    # Draw nodes figure for all users
    nx.draw_networkx_nodes(G, ax=ax_all, pos=pos, node_size=50, node_color='black')
    nx.draw_networkx_labels(G, ax=ax_all, pos=pos_labels, clip_on=False)


    # Assign colors and create figures for separate users
    user_colors = dict()
    user_figures = dict()
    for user in INTERVALS.keys():
        user_colors[user] = next(COLORS)    
        fig_u, ax_u = plt.subplots(figsize=(12,12))
        ax_u.set_title(user, fontsize=20)
        user_figures[user] = (fig_u, ax_u)
        nx.draw_networkx_nodes(G, ax=ax_u, pos=pos, node_size=50, node_color='black')
        nx.draw_networkx_labels(G, ax=ax_u, pos=pos_labels, clip_on=False)
        ax_u.axis('off')

    # Iterate over edges add draw them to appropriate figures
    link_counter = Counter()
    for i, j, user in G.edges(keys=True):
        p1 = pos[i]
        p2 = pos[j]
        diff = p2-p1
        l = np.linalg.norm(diff)
        new_pos = dict()
        delta = DELTAS[link_counter[(i,j)]]
        connectionstyle = 'arc3'
        color = user_colors[user]
        if curved_arrows:
            connectionstyle += ',rad='+str(delta/(0.6*l))
            new_pos[i] = p1
            new_pos[j] = p2
        else:
            diff = (diff[1]/l, -diff[0]/l)
            new_pos[i] =  (p1[0]+delta*diff[0], p1[1]+delta*diff[1])
            new_pos[j] =  (p2[0]+delta*diff[0], p2[1]+delta*diff[1])
        nx.draw_networkx_edges(G, ax=ax_all, arrowsize=10, arrowstyle='->',
                               connectionstyle=connectionstyle, pos=new_pos,
                               label=user, edge_color=color, edgelist = [(i,j)])
        nx.draw_networkx_edges(G, ax=user_figures[user][1], arrowsize=15,
                               arrowstyle='-|>', pos=pos, label=user,
                               edge_color=color, edgelist = [(i,j)])
        nx.draw_networkx_edge_labels(G, pos=pos, ax=user_figures[user][1],
                                    font_size=8, alpha=0.5,
                                    edge_labels = {(i,j):G[i][j][user]['weight']})
        link_counter[(i,j)] += 1
        
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
    for user, counter in counters.items():
        for keys, weight in counter.items():
            G.add_edge(keys[0], keys[1], key=user, weight=weight)

    draw_graph(G)
