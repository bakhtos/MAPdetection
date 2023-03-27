import os
import json

from flask import Flask, jsonify
from flask import request

with open(os.path.join("app_data", "fields_ihr.json"), 'r') as f:
    FIELDS = json.load(f)

import map_detection
app = Flask(__name__)


@app.route("/api/health")
def health():
    return "Working fine"


@app.route("/api/graph/fields")
def fields():
    return jsonify(FIELDS)


@app.route("/api/graph/data")
def data():
    edgelist = request.args.get("edgelist", None)
    if edgelist is None:
        return "No graph edgelist given"
    nodes = []
    edges = []
    databases = request.args.get('databases', None)
    databases = set(databases.split(',')) if databases is not None else \
        set()
    p = os.path.join("edgelists", edgelist)
    G = map_detection.read_edgelist(p)
    ihr_c, ihr_v, db_v, db_no_ihr = \
        map_detection.detectors.information_holder_resource(G, databases)
    ihr_c = {t[0] for t in ihr_c}
    ihr_v = {t[0] for t in ihr_v}
    for node in G.nodes:
        a_n = a_ihr_c = a_ihr_v = a_db_h = a_db_v = a_db_no_ihr = 0.0
        if node in databases:
            if node in db_v:
                if node in db_no_ihr:
                    a_db_v = 0.5
                    a_db_no_ihr = 0.5
                else:
                    a_db_v = 1.0
            elif node in db_no_ihr:
                a_db_no_ihr = 1.0
            else:
                a_db_h = 1.0
        elif node in ihr_c:
            a_ihr_c = 1.0
        elif node in ihr_v:
            a_ihr_v = 1.0
        else:
            a_n = 1.0
        nodes.append({"id": node, "title": node, "arc__db_normal": a_n,
                      "arc__ihr_candidate": a_ihr_c,
                      "arc__ihr_violator": a_ihr_v,
                      "arc__db_violator": a_db_v,
                      "arc__db_no_ihr": a_db_no_ihr,
                      "arc__db_healthy": a_db_h})
    id_ = 0
    for edge in G.edges(data=True):
        edges.append({"id": id_, "source": edge[0], "target": edge[1],
                      "mainStat": edge[2]["weight"]})
        id_ += 1

    return jsonify({"nodes": nodes, "edges": edges})


app.run(port=5002)