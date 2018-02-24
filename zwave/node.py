import logging

from . import zwave

def msg_str(data):
    return ":".join(["{:02x}".format(x) for x in data])

class Node:
    def __init__(self, id, controller):
        self.id = id
        self.controller = controller

        controller.register_node(self)

    def set(self, value, endpoint=0):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_BASIC, zwave.BASIC_SET, [value],
                endpoint=endpoint)

    def get(self):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_BASIC, zwave.BASIC_GET, [])

    def response(self, data):
        print("response", msg_str(data))

    def set_association(self, group, node_ids, endpoint=0):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_ASSOCIATION, zwave.ASSOCIATION_SET,
                [group] + node_ids,
                endpoint=endpoint)

    def get_association(self, group, endpoint=0):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_ASSOCIATION, zwave.ASSOCIATION_GET,
                [group],
                endpoint=endpoint)

    def remove_association(self, group, node_ids):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_ASSOCIATION, zwave.ASSOCIATION_REMOVE,
                [group] + node_ids)

    def get_multi_channel_association(self, group):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_MULTI_CHANNEL_ASSOCIATION_V2,
                zwave.MULTI_CHANNEL_ASSOCIATION_GET_V2,
                [group])

    def set_multi_channel_association(self, group, node_ids, endpoints):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_MULTI_CHANNEL_ASSOCIATION_V2,
                zwave.MULTI_CHANNEL_ASSOCIATION_SET_V2,
                [group] + node_ids + [zwave.MULTI_CHANNEL_ASSOCIATION_SET_MARKER_V2] + endpoints)

    def remove_multi_channel_association(self, group, node_ids, endpoints):
        self.controller.send_command(
                self.id,
                zwave.COMMAND_CLASS_MULTI_CHANNEL_ASSOCIATION_V2,
                zwave.MULTI_CHANNEL_ASSOCIATION_REMOVE_V2,
                [group] + node_ids + [zwave.MULTI_CHANNEL_ASSOCIATION_REMOVE_MARKER_V2] + endpoints)
