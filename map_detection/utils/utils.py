import os
import json
from collections import Counter
from datetime import datetime, timedelta

__all__ = ['detect_users', 'parse_logs', 'write_pipelines']


def detect_users(directory, time_delta=None):
    """Detect all Users appearing in locust logs.
    Each user must have an own directory with locust configuration/log.

    Parameters
    __________
    directory : str,
        A directory which stores all users' configurations and logs
    time_delta: datetime.timedelta, optional (default None)
        Time difference to add to all parsed timestamps (if None, defaults to 0
                                                         delta)

    Returns
    _______
    user_boundaries : dict[str] ->  tuple(datetime),
        for each user tells the couple of timestamps defining that user's
        beginning and end of activity;
    instance_boundaries : dict[str] -> dict[str] -> datetime,
        for each user stores the dictionary from user instances' uuids
        to the datetime of that instance's beginning of activity
    """

    # Default time_delta is 0
    if time_delta is None: time_delta = timedelta(0)

    def get_time(line):
        """Convert locustlog timestamp string to datetime object."""
        return datetime.fromisoformat('.'.join(line[1:24].split(',')))

    # Each user is defined by a separate directory
    users = os.listdir(directory)
    instance_boundaries = dict()
    user_boundaries = dict()

    for user in users:
        # Read locustlog of a user
        locustlog = os.path.join(directory, user, 'locustfile.log')
        with open(locustlog, 'r') as file:
            lines = file.readlines()

        # First and last timestamps in file define the interval when the user was active
        user_boundaries[user] = (get_time(lines[0])+time_delta, get_time(lines[-1])+time_delta)

        # Each line with 'Running user' begins a new instance of the particular user
        user_instance_boundaries = dict()
        for line in lines:
            if "Running user" in line:
                user_instance_boundaries[line[-40:-4]] = (get_time(line) +
                                                          time_delta)
        instance_boundaries[user] = user_instance_boundaries
        print(f"{user}: {len(user_instance_boundaries)} instances detected")

    return user_boundaries, instance_boundaries


def parse_logs(directory, user_boundaries, instance_boundaries):

    pipelines = dict()
    call_counters = dict()
    services = os.listdir(directory)
    for from_service in services:
        # Read log line by line
        f = open(os.path.join(directory, from_service), 'r')
        from_service = from_service.split('.')[0]
        for line in f:
            # Parse lines containing json bodies
            if line[0] == '{':
                obj = json.loads(line)
                # Get the time of the API call
                start_time = obj["start_time"]
                start_time = datetime.fromisoformat(start_time[:-1])

                # Find user whose interval of activity captures start_time
                user = None
                for user, i in user_boundaries.items():
                    if i[0] <= start_time < i[1]:
                        break
                if user is None: continue

                # Find the particular user instances whose interval of activity captures start_time
                for user_instance, timestamp in instance_boundaries[user].items():
                    if timestamp > start_time:
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
        f.close()

    for l in pipelines.values():
        l.sort(key=lambda x: x[0])

    return pipelines, call_counters



def write_pipelines(pipelines):

    for k, l in pipelines.items():
        p = os.path.join("pipelines", k+"_pipeline.csv")
        os.makedirs("pipelines", exist_ok=True)
        file = open(p,'w')
        file.write("ISO_TIME,FROM_SERVICE,TO_SERVICE,ENDPOINT\n")
        for t in l:
            file.write(",".join(t)+"\n")
        file.close()
