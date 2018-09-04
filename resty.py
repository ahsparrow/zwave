from gevent import monkey
monkey.patch_all()
import gevent

from flask import Flask, jsonify, current_app, request, abort
from gevent import wsgi
import logging
import yaml
import zwave

def index():
    return "Hello World!"

#----------------------------------------------------------------------
# Node access

def get_nodes():
    nodes = current_app.config['ZWAVE']['nodes']

    response = jsonify([{'id': n, 'name': nodes[n].name} for n in nodes])
    return response

def get_config_params(node_id):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        response = jsonify(list(node.config.keys()))
    else:
        response = "Unknown node", 404

    return response

def get_config(node_id, param):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        try:
            value = node.get_configuration(param)
        except gevent.Timeout:
            resp = "Z-Wave timeout", 500
        else:
            if value:
                resp = jsonify(value)
            else:
                resp = "Unknown parameter", 404
    else:
        logging.warning("Unknown node: %s" % node_id)
        resp = "Unknown node", 404

    return resp

def set_config(node_id, param):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        try:
            value = int(request.get_json())
        except:
            logging.warning("Bad configuration value")
            return "Bad configuration value", 400

        if node.set_configuration(param, value):
            return ""
        else:
            return "Unknown configuration parameter", 404
    else:
        logging.warning("Unknown node: %s" % node_id)
        return "Unknown node", 404

def get_multi_channel_association(node_id, group):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        try:
            value = node.get_multi_channel_association(group)
        except gevent.Timeout:
            resp = "Z-Wave timeout", 500
        else:
            resp = jsonify(value)
    else:
        logging.warning("Unknown node: %s" % node_id)
        resp = "Unknown node", 404

    return resp

def set_multi_channel_association(node_id, group):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        data = request.get_json()
        nodes = data.get('nodes', [])
        mc_nodes = data.get('multi_channel_nodes', [])

        node.set_multi_channel_association(group, nodes, mc_nodes)
        resp = ""
    else:
        logging.warning("Unknown node: %s" % node_id)
        resp = "Unknown node", 404

    return resp

def remove_multi_channel_association(node_id, group):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        data = request.get_json()
        nodes = data.get('nodes', [])
        mc_nodes = data.get('multi_channel_nodes', [])

        node.remove_multi_channel_association(group, nodes, mc_nodes)
        resp = ""
    else:
        logging.warning("Unknown node: %s" % node_id)
        resp = "Unknown node", 404

    return resp

#----------------------------------------------------------------------
# Switch access

# List of switch node/names
def get_switches():
    switches = current_app.config['ZWAVE']['switches']

    switch_info = [{'id': s, 'name': switches[s].name} for s in switches]
    return jsonify(switch_info)

# Get current switch state
def get_switch(switch_id):
    switch = current_app.config['ZWAVE']['switches'].get(switch_id)
    if switch:
        try:
            val = "off" if switch.get() == 0 else "on"
        except gevent.Timeout:
            resp = "Z-Wave timeout", 500
        else:
            resp = jsonify(val)
    else:
        logging.warning("Unknown switch: %s" % switch_id)
        resp = "Unknown switch", 404

    return resp

# Set switch state
def set_switch(switch_id):
    switch = current_app.config['ZWAVE']['switches'].get(switch_id)
    if switch:
        value = request.get_json()
        if value in ["on", "off"]:
            switch.set(0xff if value == "on" else 0)
            resp = ""
        else:
            logging.warning("Bad switch value: %s" % str(value))
            resp = "Bad switch value", 400
    else:
        logging.warning("Unknown switch: %s", switch_id)
        resp = "Unknown switch", 404

    return resp

#----------------------------------------------------------------------
# Network

def build_zwave(config_file, controller):
    network = yaml.load(config_file)

    nodes = {}
    for n in network['nodes']:
        name = n.get('name', "")
        config_file = n.get('config')
        if config_file:
            data = yaml.load(open(config_file))
            config = data.get('config', {})
        else:
            config = {}

        nodes[n['id']] = zwave.Node(controller, n['node'], name, config)

    switches = {}
    for s in network.get('switches'):
        name = s.get('name', "")
        endpoint = s.get('endpoint', 1)

        switches[s['id']] = zwave.BinarySwitch(
                nodes[s['nodeid']], endpoint, name)

    return {'nodes': nodes, 'switches': switches}

def create_app():
    app = Flask(__name__)

    app.add_url_rule("/", view_func=index)

    app.add_url_rule("/api/switch/", view_func=get_switches, methods=['GET'])
    app.add_url_rule("/api/switch/<switch_id>", view_func=set_switch, methods=['PUT'])
    app.add_url_rule("/api/switch/<switch_id>", view_func=get_switch, methods=['GET'])

    app.add_url_rule("/api/node/", view_func=get_nodes, methods=['GET'])
    app.add_url_rule("/api/node/<node_id>/config/", view_func=get_config_params, methods=['GET'])
    app.add_url_rule("/api/node/<node_id>/config/<param>", view_func=get_config, methods=['GET'])
    app.add_url_rule("/api/node/<node_id>/config/<param>", view_func=set_config, methods=['PUT'])

    app.add_url_rule("/api/node/<node_id>/multi_channel_association/<int:group>",
                     view_func=get_multi_channel_association, methods=['GET'])
    app.add_url_rule("/api/node/<node_id>/multi_channel_association/<int:group>",
                     view_func=set_multi_channel_association, methods=['PUT'])
    app.add_url_rule("/api/node/<node_id>/multi_channel_association/<int:group>",
                     view_func=remove_multi_channel_association, methods=['DELETE'])

    return app

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Z-Wave configuration file",
                        type=argparse.FileType("r"))
    parser.add_argument("-p", "--port", default="/dev/ttyACM0",
                        help="Z-Wave controller serial port")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    controller = zwave.Controller()

    zw = build_zwave(args.config_file, controller)

    controller.open(args.port)
    controller.start()

    app = create_app()
    app.config['ZWAVE'] = zw

    server = wsgi.WSGIServer(('127.0.0.1', 5000), app)
    server.serve_forever()
