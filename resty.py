from gevent import monkey
monkey.patch_all()

from flask import Flask, jsonify, current_app, request
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

    ret = [{'id': n, 'name': nodes[n].name} for n in nodes]
    return jsonify(ret)

def get_config_params(node_id):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        params = list(node.config.keys())
    else:
        params = []

    return jsonify(params)

def get_config(node_id, param):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        value = node.get_configuration(param)
    else:
        logging.warning("Unknown node: %s" % node_id)
        value = None

    return jsonify(value)

def set_config(node_id, param):
    node = current_app.config['ZWAVE']['nodes'].get(node_id)
    if node:
        try:
            value = int(request.form.get('value'))
        except:
            value = None
            logging.warning("Bad configuration value")
            return jsonify("error")

        if value:
            if node.set_configuration(param, value):
                return jsonify("ok")
            else:
                return jsonify("error")
    else:
        logging.warning("Unknown node: %s" % node_id)
        return jsonify("error")

#----------------------------------------------------------------------
# Switch access

# List of switch node/names
def get_switches():
    switches = current_app.config['ZWAVE']['switches']

    ret = [{'id': s, 'name': switches[s].name} for s in switches]
    return jsonify(ret)

# Get current switch state
def get_switch(switch_id):
    switch = current_app.config['ZWAVE']['switches'].get(switch_id)
    if switch:
        value = switch.get()
    else:
        logging.warning("Unknown switch: %s" % switch_id)
        value = None

    return jsonify(value)

# Set switch state
def set_switch(switch_id):
    value = request.form.get('value', "off")

    switch = current_app.config['ZWAVE']['switches'].get(switch_id)
    if switch:
        switch.set(0xff if value == "on" else 0)
        return jsonify("ok")
    else:
        logging.warning("Unknown switch: %d" % switch_id)
        return jsonify("error")

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
    app.add_url_rule("/api/switch/<int:switch_id>", view_func=set_switch, methods=['PUT'])
    app.add_url_rule("/api/switch/<int:switch_id>", view_func=get_switch, methods=['GET'])

    app.add_url_rule("/api/node/", view_func=get_nodes, methods=['GET'])
    app.add_url_rule("/api/node/<int:node_id>/config/", view_func=get_config_params, methods=['GET'])
    app.add_url_rule("/api/node/<int:node_id>/config/<param>", view_func=get_config, methods=['GET'])
    app.add_url_rule("/api/node/<int:node_id>/config/<param>", view_func=set_config, methods=['PUT'])

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
