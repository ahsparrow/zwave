import logging

from . import zwave

class Node:
    def __init__(self, id, controller):
        self.id = id
        self.controller = controller

        controller.register_node(self)
        self.endpoints = {}

    def register_endpoint(self, endpoint):
        self.endpoints[endpoint.id] = endpoint

    def send_command(self, command):
        cmd_frame = zwave.serialize(command)
        msg_data = [self.id, len(cmd_frame)] + cmd_frame
        msg = zwave.request_msg(zwave.API_ZW_SEND_DATA, msg_data)

        self.controller.send_msg(msg)

    def send_endpoint_command(self, endpoint, command):
        if len(self.endpoints) > 1:
            cmd = zwave.MultiChannelEncap(endpoint.id, command)
            self.send_command(cmd)
        else:
            self.send_command(command)

    def response(self, data):
        x = zwave.decode(data)
        print(x)
        if data[0] == zwave.COMMAND_CLASS_MULTI_CHANNEL and \
           data[1] == zwave.MULTI_CHANNEL_CMD_ENCAP:

            endpoint = data[2]
            self.endpoints[endpoint].response(data[4:])

        elif self.endpoints.get(1):
            self.endpoints[1].response(data)

        else:
            logging.warning("Unhandled response: %s" % zwave.msg_str(data))

    def get_config(self, parameter):
        self.send_command(zwave.ConfigurationGet(parameter))

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
