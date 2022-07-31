import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import os
import json
from collections import Counter
from datetime import datetime, timedelta


def detect_users(directory, time_delta = None):
    '''Detect all Users appearing in pptam logs.
    Each user must have an own directory with locust configuration/log.

    :param str directory: A directory which stores all users' configurations
    :param time_delta: Time difference to add to all parsed timestamps (default: 0)
    :type time_delta: datetime.timedelta

    :return: user_boundaries - for each user tells the couple of timestamps
             defining that user's begining and end of activity;
             instance_boundaries - for each user tells the timestamps when a new instance
             of that user begins activity.
    :rtype: dict
    '''

    # Default time_delta is 0
    if time_delta is None: time_delta = timedelta(0)

    def get_time(line):
        '''Convert locustlog timestamp string to datetime object.'''
        return datetime.fromisoformat('.'.join(line[1:24].split(',')))

    # Each user is defined by a separate directory
    users = os.listdir(directory)
    instance_boundaries = dict()
    user_boundaries = dict()

    for user in users:
        # Read locustlog of a user
        pptam_log = os.path.join(directory, user, 'locustfile.log')
        with open(pptam_log, 'r') as file:
            lines = file.readlines()
        # First and last timestamps in file define the interval when the user was active
        user_boundaries[user] = (get_time(lines[0])+time_delta, get_time(lines[-1])+time_delta)
        # Each line with 'Running user' begins a new instance of the particular user
        l = []
        for line in lines:
            if "Running user" in line:
                l.append(get_time(line) + time_delta)
        instance_boundaries[user] = tuple(l)

    return user_boundaries, instance_boundaries


def parse_logs(directory, filename, user_boundaries, instance_boundaries, call_counters, pipelines):

    from_service = filename.split('.')[0]
    f = open(os.path.join(directory, filename), 'r')
    for line in f:
        if line[0] == '{':
            obj = json.loads(line)
            start_time = obj["start_time"]
            start_time = datetime.fromisoformat(start_time[:-1])
            user = None
            for k, i in user_boundaries.items():
                if start_time > i[0] and start_time < i[1]:
                    user = k
                    break
            if user is None: continue
            user_intervals = instance_boundaries[user]
            for i in range(len(user_intervals)):
                if start_time < user_intervals[i]:
                    user_instance = user +"_"+str(i-1)
                    break
            if user not in call_counters: call_counters[user] = Counter()
            if user_instance not in call_counters: call_counters[user_instance] = Counter()
            if user not in pipelines: pipelines[user] = []
            if user_instance not in pipelines: pipelines[user_instance] = []

            to_service = obj["upstream_cluster"]
            to_service = to_service.split('|')
            if to_service[0] == 'outbound':
                to_service = to_service[3].split('.')[0]
                call_counters[user][(from_service, to_service)] += 1
                call_counters[user_instance][(from_service, to_service)] += 1
                endpoint = obj['path']
                if endpoint is not None:
                    endpoint = endpoint.split('/')
                    if len(endpoint) >= 5:
                        endpoint = endpoint[4]
                    else:
                        endpoint = endpoint[-1]
                else:
                    endpoint = ''
                pipelines[user].append((start_time.isoformat(), from_service, to_service, endpoint))
                pipelines[user_instance].append((start_time.isoformat(), from_service, to_service, endpoint))


def write_pipelines(pipelines):

    for k, l in pipelines.items():
        p = os.path.join("pipelines", k+"_pipeline.csv")
        os.makedirs("pipelines", exist_ok=True)
        file = open(p,'w')
        file.write("ISO_TIME,FROM_SERVICE,TO_SERVICE,ENDPOINT\n")
        for t in l:
            file.write(",".join(t)+"\n")
        file.close()


def draw_graph(G, intervals, curved_arrows=True):

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

    # Draw nodes figure for all users
    nx.draw_networkx_nodes(G, ax=ax_all, pos=pos, node_size=50, node_color='black')
    nx.draw_networkx_labels(G, ax=ax_all, pos=pos_labels, clip_on=False)


    # Assign colors and create figures for separate users
    colors = iter(['b','r','g','c','m','y'])
    user_colors = dict()
    user_figures = dict()
    for user in intervals.keys():
        user_colors[user] = next(colors)    
        fig_u, ax_u = plt.subplots(figsize=(12,12))
        ax_u.set_title(user, fontsize=20)
        user_figures[user] = (fig_u, ax_u)
        nx.draw_networkx_nodes(G, ax=ax_u, pos=pos, node_size=50, node_color='black')
        nx.draw_networkx_labels(G, ax=ax_u, pos=pos_labels, clip_on=False)
        ax_u.axis('off')

    # Iterate over edges add draw them to appropriate figures
    link_counter = Counter()
    deltas = [0.0]
    for i in range(1, (len(intervals)+1)//2):
        deltas.append(i/100)
        deltas.append(-i/100)

    for i, j, user in G.edges(keys=True):
        p1 = pos[i]
        p2 = pos[j]
        diff = p2-p1
        l = np.linalg.norm(diff)
        new_pos = dict()
        delta = deltas[link_counter[(i,j)]]
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



def generate_call_graph(directory, time_delta):
    call_counters = dict()
    pipelines = dict()
    pptam_dir = os.path.join(directory, 'pptam')
    user_boundaries, instance_boundaries = detect_users(pptam_dir, time_delta)
    tracing_dir = os.path.join(directory, 'tracing-log') 
    for file in os.listdir(tracing_dir):
        if file.endswith(".log"):
            parse_logs(tracing_dir, file, user_boundaries, instance_boundaries, call_counters, pipelines)

    for l in pipelines.values():
        l.sort(key = lambda x: x[0])

    # Create networkx' multigraph, edges are identified by User
    G = nx.MultiDiGraph()
    for user, counter in call_counters.items():
        for keys, weight in counter.items():
            G.add_edge(keys[0], keys[1], key=user, weight=weight)

    return G, pipelines

if __name__ == '__main__':
    
    directory = "kubernetes-istio-sleuth-v0.2.1-separate-load"
    time_delta = timedelta(hours=-8)
    G, pipelines = generate_call_graph(directory, time_delta)
    write_pipelines(pipelines)
    #draw_graph(G, intervals)

