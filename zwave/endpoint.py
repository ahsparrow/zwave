from . import zwave

class Endpoint:
    def __init__(self, node, id=0):
        self.node = node
        self.id = id

        node.register_endpoint(self)

    def set(self, value):
        self.node.send_command(self,
                               zwave.COMMAND_CLASS_BASIC, zwave.BASIC_SET,
                               [value])

    def get(self):
        self.node.send_command(self,
                               zwave.COMMAND_CLASS_BASIC, zwave.BASIC_GET,
                               [])
