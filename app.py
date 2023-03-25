import os
import json

from flask import Flask, jsonify
from flask import request

import map_detection
app = Flask(__name__)


@app.route("/api/health")
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
            nodes.append({"id":node, "title": node, "arc__f_normal": an,
                          "arc__frontend_candidate": ac,
                          "arc__frontend_violator": av,
                          "arc__frontend_healthy": ah})
        id_ = 0
        for edge in G.edges(data=True):
            edges.append({"id": id_, "source": edge[0], "target": edge[1],
                          "mainstat": edge[2]["weight"]})
            id_ += 1
    elif detector == "ihr":
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
                          "mainstat": edge[2]["weight"]})
            id_ += 1
    elif detector == "request_bundle":
        endpoint_threshold = request.args.get("endpoint_threshold", 2)
        service_threshold = request.args.get("service_threshold", 2)
        p = os.path.join("edgelists", edgelist)
        bs, be = map_detection.detectors.request_bundle(p, service_threshold,
                                                        endpoint_threshold)
        G = map_detection.read_edgelist(p)
        discovered = set()
        for f, t, e, c in be:
            if f not in discovered:
                nodes.append({"id": f, "title": f, "arc__rb_v": 1.0,
                              "arc__rc_n": 0.0})
                discovered.add(f)
            if t not in discovered:
                nodes.append({"id": t, "title": t, "arc__rb_v": 1.0,
                              "arc__rc_n": 0.0})
                discovered.add(t)
        for node in G.nodes:
            if node not in discovered:
                nodes.append({"id": node, "title": node, "arc__rb_v": 0.0,
                              "arc__rc_n": 1.0})
        id_ = 0
        for edge in G.edges(data=True):
            edges.append({"id": id_, "source": edge[0], "target": edge[1],
                          "maintstat": edge[2]["weight"]})
            id_ += 1

    else:
        return f"Unknown detector '{detector}'"
    return jsonify({"nodes": nodes, "edges": edges})

