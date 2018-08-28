from gevent.event import AsyncResult
import logging

from . import command
from . import serialize
from . import zwave

class Node:
    def __init__(self, controller, id, name="", config=None):
        self.controller = controller
        self.id = id
        self.name = name

        if config is None:
            self.config = {}
        else:
            self.config = config
        self.config_result = {}

        controller.register_node(self)
        self.endpoints = {}

    def register_endpoint(self, endpoint):
        self.endpoints[endpoint.endpoint] = endpoint

    def send_command(self, cmd):
        cmd_frame = serialize.serialize(cmd)
        msg_data = [self.id, len(cmd_frame)] + cmd_frame
        self.controller.send_data(msg_data)

    def send_endpoint_command(self, endpoint, cmd):
        if len(self.endpoints) > 1:
            cmd = command.MultiChannelEncap(endpoint.endpoint, cmd)
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

    # Configuration
    def set_configuration(self, parameter, value, format=None):
        config = self.config.get(parameter)

        if config:
            addr = config['address']
            format = config['format']
        elif type(parameter) is int and format:
            addr = parameter
        else:
            logging.warning("Unknown parameter %s" % str(parameter))
            return False

        self.send_command(command.ConfigurationSet(addr, value, format))
        return True

    def get_configuration(self, parameter):
        config = self.config.get(parameter)
        if config:
            addr = config['address']
        elif type(parameter) is int:
            addr = parameter
        else:
            logging.warning("Unknown parameter %s" % str(parameter))
            return None

        async_res = AsyncResult()
        self.config_result[addr] = async_res
        self.send_command(command.ConfigurationGet(addr))

        try:
            result = async_res.get(timeout=1.0)
        except gevent.Timeout:
            logging.error("Config get timeout: %s" % self.name)
            result = None

        return result

    def configuration_response(self, cmd):
        self.config_result[cmd.parameter].set(cmd.value)

    # Association
    def get_association(self, group):
        self.send_command(command.AssociationGet(group))

    # Multi-channel association
    def get_multi_channel_association(self, group):
        self.send_command(command.MultiChannelAssociationGet(group))

    def remove_multi_channel_association(self, group, nodes, multi_channel_nodes):
        self.send_command(command.MultiChannelAssociationRemove(group, nodes, multi_channel_nodes))

    def set_multi_channel_association(self, group, nodes, multi_channel_nodes):
        self.send_command(command.MultiChannelAssociationSet(group, nodes, multi_channel_nodes))
