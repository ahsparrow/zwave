from gevent import monkey
monkey.patch_all()

from flask import Flask, jsonify, current_app, request
from gevent import wsgi
import yaml
import zwave

def index():
    return "Hello World!"

def get_switches():
    switches = current_app.config['ZWAVE']['switches']

    ret = {s: switches[s].name for s in switches}
    return jsonify(ret)

def get_switch(switch_id):
    switches = current_app.config['ZWAVE']['switches']
    value = switches[switch_id].value
    return jsonify({'value': value})

def set_switch(switch_id):
    value = request.form.get('value', "off")

    switches = current_app.config['ZWAVE']['switches']
    switches[switch_id].set(0xff if value == "on" else 0)

    return jsonify({})

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

    return {'nodes': nodes, 'switches': switches}

def create_app():
    app = Flask(__name__)
    app.add_url_rule("/", view_func=index)
    app.add_url_rule("/api/switch", view_func=get_switches, methods=['GET'])
    app.add_url_rule("/api/switch/<int:switch_id>", view_func=set_switch, methods=['PUT'])
    app.add_url_rule("/api/switch/<int:switch_id>", view_func=get_switch, methods=['GET'])

    return app

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Z-Wave configuration file",
                        type=argparse.FileType("r"))
    parser.add_argument("-p", "--port", default="/dev/ttyACM0",
                        help="Z-Wave controller serial port")
    args = parser.parse_args()

    controller = zwave.Controller()

    zw = build_zwave(args.config_file, controller)

    controller.open(args.port)
    controller.start()

    app = create_app()
    app.config['ZWAVE'] = zw

    server = wsgi.WSGIServer(('127.0.0.1', 5000), app)
    server.serve_forever()
