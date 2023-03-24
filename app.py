import os
import json

from flask import Flask, jsonify
from flask import request

import map_detection
app = Flask(__name__)


@app.route("/api/graph/health")
def health():
    return "Working fine"


@app.route("/api/graph/fields")
def fields():
    with open(os.path.join("app_data", "fields.json"), 'r') as f:
        obj = json.load(f)
    return jsonify(obj)


@app.route("/api/graph/data")
def data():
    detector = request.args.get("detector", None)
    edgelist = request.args.get("edgelist", None)
    if edgelist is None:
        return "No graph edgelist given"
    nodes = []
    edges = []
    if detector == "frontend":
        frontends = request.args.get("frontends", None)
        if frontends is not None:
            frontends = set(frontends.split(","))
        else:
            frontends = set()
        p = os.path.join("edgelists", edgelist)
        G = map_detection.read_edgelist(p)
        c, v = map_detection.detectors.frontend_integration(G, frontends)
        c -= frontends
        for node in G.nodes:
            ac = an = av = ah = 0.0
            if node in c:
                ac = 1.0
            elif node in v:
                av = 1.0
            elif node in frontends:
                ah = 1.0
            else:
                an = 1.0
            nodes.append({"id":node, "title": node, "arc__normal": an,
                          "arc__frontend_candidate": ac,
                          "arc__frontend_violator": av,
                          "arc__frontend_healthy": ah})
        id_ = 0
        for edge in G.edges:
            edges.append({"id": id_, "source": edge[0], "target": edge[1]})
            id_ += 1
    else:
        return f"Unknown detector '{detector}'"
    return jsonify({"nodes": nodes, "edges": edges})

