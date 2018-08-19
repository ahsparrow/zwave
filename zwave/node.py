import logging
import yaml

from . import command
from . import serialize
from . import zwave

class Node:
    def __init__(self, id, controller, config=None):
        self.id = id
        self.controller = controller
        if config is None:
            self.config = {}
        elif type(config) is dict:
            self.config = config
        else:
            self.config = yaml.load(config).get('config', {})

        controller.register_node(self)
        self.endpoints = {}

    def register_endpoint(self, endpoint):
        self.endpoints[endpoint.id] = endpoint

    def send_command(self, cmd):
        cmd_frame = serialize.serialize(cmd)
        msg_data = [self.id, len(cmd_frame)] + cmd_frame
        msg = zwave.request_msg(zwave.API_ZW_SEND_DATA, msg_data)

        self.controller.send_msg(msg)

    def send_endpoint_command(self, endpoint, cmd):
        if len(self.endpoints) > 1:
            cmd = command.MultiChannelEncap(endpoint.id, cmd)
            self.send_command(cmd)
        else:
            self.send_command(cmd)

    def response(self, data):
        try:
            cmd = serialize.deserialize(data)
            logging.debug(cmd)
        except serialize.DeserializeError:
            logging.warning("Can't deserialize " + zwave.msg_str(data))
            return

        if type(cmd) is command.ConfigurationReport:
            self.configuration_response(cmd)

        elif type(cmd) is command.MultiChannelEncap:
            if self.endpoints.get(cmd.endpoint):
                self.endpoints[cmd.endpoint].response(cmd.command)
            else:
                logging.warning("Unknown endpoint: %s" % zwave.msg_str(data))

        elif self.endpoints.get(1):
            self.endpoints[1].response(cmd)

        else:
            logging.warning("Unhandled response: %s" % zwave.msg_str(data))

    def get_configuration(self, parameter):
        config = self.config.get(parameter)
        if config:
            addr = config['address']
        elif type(parameter) is int:
            addr = parameter
        else:
            logging.warning("Unknown parameter %s" % str(parameter))
            return

        self.send_command(command.ConfigurationGet(addr))

    def configuration_response(self, cmd):
        pass

    def set_configuration(self, parameter, value, format=None):
        config = self.config.get(parameter)

        if config:
            addr = config['address']
            format = config['format']
        elif type(parameter) is int and format:
            addr = parameter
        else:
            logging.warning("Unknown parameter %s" % str(parameter))
            return

        self.send_command(command.ConfigurationSet(addr, value, format))

"""
    def set_association(self, group, node_ids):
        self.send_command(self.id,
                zwave.COMMAND_CLASS_ASSOCIATION, zwave.ASSOCIATION_SET,
                [group] + node_ids)

    def get_association(self, group):
        self.send_command(self.id,
                zwave.COMMAND_CLASS_ASSOCIATION, zwave.ASSOCIATION_GET,
                [group])

    def remove_association(self, group, node_ids):
        self.send_command(self.id,
                zwave.COMMAND_CLASS_ASSOCIATION, zwave.ASSOCIATION_REMOVE,
                [group] + node_ids)

    def set_multi_channel_association(self, group, node_ids, endpoints):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_MULTI_CHANNEL_ASSOCIATION_V2,
                zwave.MULTI_CHANNEL_ASSOCIATION_SET_V2,
                [group] + node_ids + [zwave.MULTI_CHANNEL_ASSOCIATION_SET_MARKER_V2] + endpoints)

    def get_multi_channel_association(self, group):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_MULTI_CHANNEL_ASSOCIATION_V2,
                zwave.MULTI_CHANNEL_ASSOCIATION_GET_V2,
                [group])

    def remove_multi_channel_association(self, group, node_ids, endpoints):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_MULTI_CHANNEL_ASSOCIATION_V2,
                zwave.MULTI_CHANNEL_ASSOCIATION_REMOVE_V2,
                [group] + node_ids + [zwave.MULTI_CHANNEL_ASSOCIATION_REMOVE_MARKER_V2] + endpoints)
"""
