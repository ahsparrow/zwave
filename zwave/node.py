import logging

from . import zwave

class Node:
    def __init__(self, id, controller):
        self.id = id
        self.controller = controller

        controller.register_node(self)

    def register_endpoint(self, endpoint):
        self.endpoint = endpoint

    def send_command(self, endpoint, command_class, command, data):
        msg_data = [self.id, len(data) + 2, command_class, command] + data
        msg = zwave.request_msg(zwave.API_ZW_SEND_DATA, msg_data)

        self.controller.send_msg(msg)

    def response(self, data):
        print("response", zwave.msg_str(data))

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

class MultiChannelNode(Node):
    def __init__(self, id, controller):
        self.id = id
        self.controller = controller

        controller.register_node(self)
        self.endpoints = {}

    def register_endpoint(self, endpoint):
        self.endpoints[endpoint.id] = endpoint

    def send_command(self, endpoint, command_class, command, data):
        msg_data = [
            self.id, len(data) + 6,
            zwave.COMMAND_CLASS_MULTI_CHANNEL, zwave.MULTI_CHANNEL_CMD_ENCAP,
            0, endpoint.id,
            command_class, command] + data
        msg = zwave.request_msg(zwave.API_ZW_SEND_DATA, msg_data)

        self.controller.send_msg(msg)

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

