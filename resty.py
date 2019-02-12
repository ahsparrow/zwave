from gevent import monkey
monkey.patch_all()
import gevent

from flask import Flask, jsonify, current_app, request, abort
from gevent import pywsgi
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
        value = node.get_configuration(param)

        if value is None:
            resp = "Unknown parameter", 404
        else:
            resp = jsonify(value)
    else:
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
# Dimmer access

# List of dimmer node/names
def get_dimmers():
    dimmers = current_app.config['ZWAVE']['dimmers']

    dimmer_info = [{'id': d, 'name': dimmers[d].name} for d in dimmers]
    return jsonify(dimmer_info)

# Get current dimmer level
def get_dimmer(dimmer_id):
    dimmer = current_app.config['ZWAVE']['dimmers'].get(dimmer_id)
    if dimmer:
        try:
            val = dimmer.get()
        except gevent.Timeout:
            resp = "Z-Wave timeout", 500
        else:
            resp = jsonify(val)
    else:
        logging.warning("Unknown dimmer: %s" % dimmer_id)
        resp = "Unknown dimmer", 404

    return resp

# Set dimmer level
def set_dimmer(dimmer_id):
    dimmer = current_app.config['ZWAVE']['dimmers'].get(dimmer_id)
    if dimmer:
        value = request.get_json()
        try:
            value = int(value)
            if value < 0 or (value > 99 and value != 255):
                raise ValueError
            dimmer.set(value)
            resp = ""

        except ValueError:
            logging.warning("Bad dimmer level: %s" % str(value))
            resp = "Bad dimmer level", 400
    else:
        logging.warning("Unknown dimmer: %s", dimmer_id)
        resp = "Unknown dimmer", 404

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
            config = yaml.load(open(config_file))
        else:
            config = {}

        nodes[n['id']] = zwave.Node(controller, n['node'], name, config)

    switches = {}
    for s in network.get('switches'):
        name = s.get('name', "")
        endpoint = s.get('endpoint', 1)

        switches[s['id']] = zwave.BinarySwitch(
                nodes[s['nodeid']], endpoint, name)

    dimmers = {}
    for d in network.get('dimmers'):
        name = d.get('name', "")
        endpoint = d.get('endpoint', 1)

        dimmers[d['id']] = zwave.MultilevelSwitch(
                nodes[d['nodeid']], endpoint, name)

    return {'nodes': nodes, 'switches': switches, 'dimmers': dimmers}

#----------------------------------------------------------------------
# Flask application

def handle_not_found(e):
    return "", 404

def handle_transmit_error(e):
    return "Z-Wave transmit error", 404

def handle_timeout_error(e):
    return "Z-Wave timeout", 404

def create_app():
    app = Flask(__name__)

    app.add_url_rule("/", view_func=index)

    app.add_url_rule("/api/switch/", view_func=get_switches, methods=['GET'])
    app.add_url_rule("/api/switch/<switch_id>", view_func=set_switch, methods=['PUT'])
    app.add_url_rule("/api/switch/<switch_id>", view_func=get_switch, methods=['GET'])

    app.add_url_rule("/api/dimmer/", view_func=get_dimmers, methods=['GET'])
    app.add_url_rule("/api/dimmer/<dimmer_id>", view_func=set_dimmer, methods=['PUT'])
    app.add_url_rule("/api/dimmer/<dimmer_id>", view_func=get_dimmer, methods=['GET'])

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

    # Error handlers
    app.register_error_handler(404, handle_not_found)
    app.register_error_handler(zwave.TransmitError, handle_transmit_error)
    app.register_error_handler(zwave.Timeout, handle_timeout_error)

    return app

if __name__ == "__main__":
    import argparse
    import logging
    import logging.handlers
    import os.path

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Z-Wave configuration file",
                        type=argparse.FileType("r"))
    parser.add_argument("--loglevel", help="Logging level, DEBUG, etc.",
                        default="WARNING")
    parser.add_argument("--logdir", help="Log file directory")
    parser.add_argument("-s", "--serial", default="/dev/ttyACM0",
                        help="Z-Wave controller serial device")
    parser.add_argument("-p", "--port", default="5000", type=int,
                        help="HTTP server port")
    args = parser.parse_args()

    # Configure logging
    logger = logging.getLogger()

    loglevel = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(loglevel, int):
        parser.error("Unrecognised log level")
    else:
        logger.setLevel(loglevel)

    if args.logdir:
        logfile = os.path.join(args.logdir, "zwave.log")
        handler = logging.handlers.RotatingFileHandler(logfile, "a", 1000000, 5)
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",
                                      datefmt="%y/%m/%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    controller = zwave.Controller()

    zw = build_zwave(args.config_file, controller)

    controller.open(args.serial)
    controller.start()

    app = create_app()
    app.config['ZWAVE'] = zw

    server = pywsgi.WSGIServer(('0.0.0.0', args.port), app)
    server.serve_forever()
