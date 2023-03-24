import os

from flask import Flask, jsonify
from flask import request

import map_detection
app = Flask(__name__)


@app.route("/api/graph/health")
def health():
    return "Working fine"


@app.route("/api/graph/fields")
def fields():
    nodes_fields = [{"field_name": "id", "type": "string"},
                    {"field_name": "title", "type": "string",
                     },
                    {"field_name": "arc__normal", "type": "number", "color":
                        "gray", "display_name": "Microservice"},
                    {"field_name": "arc__frontend_candidate",
                     "type": "number", "color": "orange", "displayName":
                         "Frontend candidate"},
                    {"field_name": "arc__frontend_violator",
                     "type": "number", "color": "red", "displayName":
                         "Frontend violator"}]
    edges_fields = [
        {"field_name": "id", "type": "string"},
        {"field_name": "source", "type": "string"},
        {"field_name": "target", "type": "string"},
        {"field_name": "mainStat", "type": "number"},
    ]
    result = {"nodes_fields": nodes_fields,
              "edges_fields": edges_fields}
    return jsonify(result)


@app.route("/api/graph/data")
def data():
    type = request.args.get("type", None)
    edgelist = request.args.get("edgelist", None)
    if edgelist is None:
        return "No graph edgelist given"
    nodes = []
    edges = []
    if type == "frontend":
        p = os.path.join("edgelists", edgelist)
        G = map_detection.read_edgelist(p)
        c, v = map_detection.detectors.frontend_integration(G, 'ts-ui-dashboard',
                                                            'UserNoLogin')
        print(request.args.get("type"))
        nodes = []
        for node in G:
            if node in c:
                an = 0.0
                ac = 1.0
                av = 0.0
            elif node in v:
                an = 0.0
                ac = 0.0
                av = 1.0
            else:
                an = 1.0
                ac = 0.0
                av = 0.0
            nodes.append({"id":node, "title": node, "arc__normal": an,
                          "arc__candidate": ac, "arc__violator": av})
        edges = []
        id_ = 0
        for edge in G.edges:
            edges.append({"id": id_, "source": edge[0], "target": edge[1]})
            id_ += 1

    return jsonify({"nodes": nodes, "edges": edges})

