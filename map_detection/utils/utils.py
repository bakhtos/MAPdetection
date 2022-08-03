import os
import json
from collections import Counter
from datetime import datetime, timedelta

__all__ = ['detect_users', 'parse_logs', 'write_pipelines']

def detect_users(directory, time_delta=None):
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
