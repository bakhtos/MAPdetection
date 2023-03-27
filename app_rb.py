import os
import json

from flask import Flask, jsonify
from flask import request

with open(os.path.join("app_data", "fields_rb.json"), 'r') as f:
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
    endpoint_threshold = int(request.args.get("endpoint_threshold", 2))
    service_threshold = int(request.args.get("service_threshold", 2))
    p = os.path.join("edgelists", edgelist)
    bs, be = map_detection.detectors.request_bundle(p, service_threshold,
                                                    endpoint_threshold)
    G = map_detection.read_edgelist(p)
    discovered = set()
    for f, t, e, c in be:
        if f not in discovered:
            nodes.append({"id": f, "title": f, "arc__rb_v": 1.0,
                          "arc__rb_n": 0.0})
            discovered.add(f)
        if t not in discovered:
            nodes.append({"id": t, "title": t, "arc__rb_v": 1.0,
                          "arc__rb_n": 0.0})
            discovered.add(t)
    for node in G.nodes:
        if node not in discovered:
            nodes.append({"id": node, "title": node, "arc__rb_v": 0.0,
                          "arc__rb_n": 1.0})
    id_ = 0
    for edge in G.edges(data=True):
        edges.append({"id": id_, "source": edge[0], "target": edge[1],
                      "mainStat": edge[2]["weight"]})
        id_ += 1

    return jsonify({"nodes": nodes, "edges": edges})

app.run(port=5001)