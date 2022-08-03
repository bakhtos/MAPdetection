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
        print(f"{user}: {len(l)} instances detected")

    return user_boundaries, instance_boundaries


def parse_logs(directory, filename, user_boundaries, instance_boundaries, call_counters, pipelines):

    # Each logfile is named after the service
    from_service = filename.split('.')[0]
    # Read log line by line
    f = open(os.path.join(directory, filename), 'r')
    for line in f:
        # Parse lines contaning json bodies
        if line[0] == '{':
            obj = json.loads(line)
            # Get the time of the API call
            start_time = obj["start_time"]
            start_time = datetime.fromisoformat(start_time[:-1])

            # Find user whose interval of activity captures start_time
            user = None
            for k, i in user_boundaries.items():
                if start_time > i[0] and start_time < i[1]:
                    user = k
                    break
            if user is None: continue

            # Find the particular user instances whose interval of activity captures start_time
            user_intervals = instance_boundaries[user]
            for i in range(len(user_intervals)):
                if start_time < user_intervals[i]:
                    user_instance = user +"_"+str(i-1)
                    break

            # Insert user [instance] in all necessary datastructures
            if user not in call_counters: call_counters[user] = Counter()
            if user_instance not in call_counters: call_counters[user_instance] = Counter()
            if user not in pipelines: pipelines[user] = []
            if user_instance not in pipelines: pipelines[user_instance] = []

            # If calling another service, store the call and the pipeline
            to_service = obj["upstream_cluster"]
            to_service = to_service.split('|')
            if to_service[0] == 'outbound':
                to_service = to_service[3].split('.')[0]
                endpoint = obj['path']
                if endpoint is None: endpoint = '/'
                endpoint = endpoint.split('/')
                endpoint = '/'.join(endpoint[0:5])

                call_counters[user][(from_service, to_service, endpoint)] += 1
                call_counters[user_instance][(from_service, to_service, endpoint)] += 1
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



def generate_call_graph(pptam_dir, tracing_dir, time_delta):
    user_boundaries, instance_boundaries = detect_users(pptam_dir, time_delta)

    # Get calls and pipelines for each user using logs of each service
    call_counters = dict()
    pipelines = dict()
    for file in os.listdir(tracing_dir):
        if file.endswith(".log"):
            parse_logs(tracing_dir, file, user_boundaries, instance_boundaries, call_counters, pipelines)

    # Sort pipelines by time of call
    for l in pipelines.values():
        l.sort(key = lambda x: x[0])

    # Create networkx' multigraph, edges are identified by User
    user_graphs = dict()
    for user, counter in call_counters.items():
        G = nx.MultiDiGraph()
        user_graphs[user] = G
        for keys, weight in counter.items():
            G.add_edge(keys[0], keys[1], key=keys[2], weight=weight)

    return user_graphs, pipelines


def detect_request_bundle(pipelines, threshold_service=2, threshold_endpoint=2):
    '''Detect request bundle anti-pattern, i.e. consecutive calls between same services.

    Bundles are detected on service level (service A repeatedly calls same service B)
    and endpoint level (service A repeatedly calls same endpoint of same service B).
    Results are returned as dicts from users to a list of detected bundles, each
    bundle is a tuple of the form (from_service, to_service, count) for service-level detection
    and (from_service, to_service, endpoint, count) for endpoint-level detection.
    
    :param dict pipelines: A dictionary of users and their service call pipelines
    as returned by :py:func:parse_logs
    :param int threshold_service: Minimum count of consecutive calls necessary 
    to make up a bundle in service-level detection (default = 2, i.e. any repeated call makes a bundle)
    :param int threshold_endpoint: Minimum count of consecutive calls necessary 
    to make up a bundle in endpoint-level detection (default = 2, i.e. any repeated call makes a bundle)
    
    :return: bundles_service - detected bundles for each user in service-level detection,
             bundles_endpoint - detected bundles for each user in endpoint-level detecton
    :rtype: dict
    '''

    bundles_service = dict()
    bundles_endpoint = dict()
    for user, pipeline in pipelines.items():
        bundles_service[user] = []
        bundles_endpoint[user] = []
        last_call_service = (pipeline[0][1],pipeline[0][2])
        last_call_endpoint = (pipeline[0][1],pipeline[0][2], pipeline[0][3])
        count_service = 1
        count_endpoint = 1
        for i in range(1, len(pipeline)):
            current_call_service = (pipeline[i][1], pipeline[i][2])
            current_call_endpoint = (pipeline[i][1], pipeline[i][2], pipeline[i][3])
            if current_call_service == last_call_service:
                count_service += 1
            else:
                if count_service >= threshold_service:
                    bundles_service[user].append((*last_call_service, count_service))
                    print(f"{user}: Service-level request bundle detected between"
                          f"{last_call_service[0]} and {last_call_service[1]}"
                          f"with count {count_service}")
                count_service = 1
                last_call_service = current_call_service
                    
            if current_call_endpoint == last_call_endpoint:
                count_endpoint += 1
            else:
                if count_endpoint >= threshold_endpoint:
                    bundles_endpoint[user].append((*last_call_endpoint, count_endpoint))
                    print(f"{user}: Endpoint-level request bundle detected between"
                          f"{last_call_endpoint[0]} and {last_call_endpoint[1]}"
                          f"{last_call_endpoint[2]} with count {count_endpoint}")
                count_endpoint = 1
                last_call_endpoint = current_call_endpoint

    return bundles_service, bundles_endpoint

def detect_frontend_integration(G, frontend_services=None, user=None):

    if frontend_services is None: frontend_services = set()
    if user is None: user = "NoUser"

    D = nx.DiGraph(G)

    frontend_candidates = set()
    frontend_violators = set()

    for node, in_degree in D.in_degree():
        if in_degree == 0:
            if D.out_degree(node) > 0:
                frontend_candidates.add(node)
                print(f"{user}: Frontend Integreation - potential frontend service '{node}' found.")
        elif node in frontend_services:
            frontend_violators.add(node)
            print(f"{user}: Frontend Integration Violation - service '{node}' "
                  f"is designated as frontend service but has incoming calls "
                  f"(in-degree = {in_degree})")

    return frontend_candidates, frontend_violators


def detect_information_holder_resource(G, database_services=None, user=None):

    if database_services is None: database_services = set()
    if user is None: user = "NoUser"

    D = nx.DiGraph(G)

    ihr_candidates = set()
    ihr_violators = set()
    database_call_violators = set()
    database_no_ihr_violators = database_services.copy()

    for node, out_degree in D.out_degree():
        zero_degree = out_degree == 0
        is_database = node in database_services
        if zero_degree or is_database:
            if len(preds := D.pred[node]) == 1:
                pred = [n for n in preds.keys()]
                pred = pred[0]
                if len(D.succ[pred]) == 1:
                    ihr_candidates.add((pred, node))
                    print(f"{user}: Information Holder Resource - '{pred}' is a "
                          f"potential IHR for '{node}'")
                else:
                    ihr_violators.add((pred, node))
                    print(f"{user}: Information Holder Resouce Violation - "
                          f"'{node}' is only accessed through '{pred}', but "
                          f"'{pred}' calls other services as well.")
                database_no_ihr_violators.discard(node)
        if not zero_degree and is_database:
            database_call_violators.add(node)
            print(f"{user}: Information Holder Resource Violation - '{node}' is designated"
                  f" as database service but has outgoing calls (out-dergee = {out_degree})")

    for service in database_services:
        print(f"{user}: Information Holder Resource Violation - '{service}' "
              f"is designated as database service but no IHR detected.")
    
    return ihr_candidates, ihr_violators, database_call_violators, database_no_ihr_violators
    


if __name__ == '__main__':
    
    directory = "kubernetes-istio-sleuth-v0.2.1-separate-load"
    pptam_dir = os.path.join(directory, 'pptam')
    tracing_dir = os.path.join(directory, 'tracing-log')
    time_delta = timedelta(hours=-8)
    G, pipelines = generate_call_graph(pptam_dir, tracing_dir, time_delta)
    bundles_service, bundles_endpoint = detect_request_bundle(pipelines)
    #write_pipelines(pipelines)
    #draw_graph(G, intervals)
