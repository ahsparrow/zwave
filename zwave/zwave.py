# Frame structure examples -
#
# 0   SOF
# 1   Length
# 2   RESPONSE/REQUEST
# 3   API_ZW_SEND_DATA (API function)
# 4   Destination node id
# 5   Payload length
# 6   Comannd class
# 7   Command type
# 8-  Payload data
# N   Checksum
#
# 0   SOF
# 1   Length
# 2   RESPONSE/REQUEST
# 3   API_APP_COMMAND_HANDLER (API function)
# 4   Source node id
# 5   Destination node id
# 6   Payload length
# 7   Commmand class
# 8   Command type
# 9-  Payload data
# N   Checksum

import functools

#----------------------------------------------------------------------
# Frame parameters

# Frame type
SOF = 0x01
ACK = 0x06
NAK = 0x15
CAN = 0x18

# Request/response frame type
RESPONSE = 0
REQUEST = 1

#----------------------------------------------------------------------
# Utility functions

# Format bytes as hex string
def msg_str(data):
    return ":".join(["{:02x}".format(x) for x in data])

# Calculate message checksum
def checksum(data):
    checksum = 0xff
    for b in data:
        checksum = checksum ^ b
    return checksum

# Make request message
def request_msg(func, data):
    out = [len(data) + 3, REQUEST, func] + data
    out += [checksum(out)]
    return bytes(out)

#----------------------------------------------------------------------
# API functions

API_APP_COMMAND_HANDLER = 0x04
API_ZW_SEND_DATA = 0x13
API_ZW_GET_VERSION = 0x15

#----------------------------------------------------------------------
# Command classes/types

COMMAND_CLASS_BASIC = 0x20
BASIC_SET = 0x01
BASIC_GET = 0x02
BASIC_REPORT = 0x03

COMMAND_CLASS_SWITCH_BINARY = 0x25
SWITCH_BINARY_SET = 0x01
SWITCH_BINARY_GET = 0x02
SWITCH_BINARY_REPORT = 0x03

COMMAND_CLASS_MULTI_CHANNEL = 0x60
MULTI_CHANNEL_CMD_ENCAP = 0x0D

COMMAND_CLASS_CONFIGURATION = 0x70
CONFIGURATION_SET = 0x04
CONFIGURATION_GET = 0x05
CONFIGURATION_REPORT = 0x06

COMMAND_CLASS_ASSOCIATION = 0x85
ASSOCIATION_SET = 0x01
ASSOCIATION_GET = 0x02
ASSOCIATION_REMOVE = 0x04

COMMAND_CLASS_MULTI_CHANNEL_ASSOCIATION_V2 = 0x8e
MULTI_CHANNEL_ASSOCIATION_SET_V2 = 0x01
MULTI_CHANNEL_ASSOCIATION_GET_V2 = 0x02
MULTI_CHANNEL_ASSOCIATION_REMOVE_V2 = 0x04
MULTI_CHANNEL_ASSOCIATION_SET_MARKER_V2 = 0x00
MULTI_CHANNEL_ASSOCIATION_REMOVE_MARKER_V2 = 0x00

#----------------------------------------------------------------------

class Command:
    @classmethod
    def decode(cls, payload):
        assert len(payload) == 1
        c = cls(int(payload[0]))
        return c

    @classmethod
    def sig(cls):
        return [cls.CLASS, cls.COMMAND]

class BasicCommand(Command):
    CLASS = COMMAND_CLASS_BASIC

class BasicSet(BasicCommand):
    COMMAND = BASIC_SET

    def __init__(self, value):
        self.value = value

class BasicGet(BasicCommand):
    COMMAND = BASIC_GET

class BasicReport(BasicCommand):
    COMMAND = BASIC_REPORT

    def __init__(self, value):
        self.value = value

class BinarySwitchCommand(Command):
    CLASS = COMMAND_CLASS_SWITCH_BINARY

class BinarySwitchGet(BinarySwitchCommand):
    COMMAND = SWITCH_BINARY_GET

class BinarySwitchSet(BinarySwitchCommand):
    COMMAND = SWITCH_BINARY_SET

    def __init__(self, value):
        self.value = value

class BinarySwitchReport(BinarySwitchCommand):
    COMMAND = SWITCH_BINARY_REPORT

    def __init__(self, value):
        self.value = value

class ConfigurationGet:
    def __init__(self, parameter):
        self.parameter = parameter

    def raw(self):
        return [COMMAND_CLASS_CONFIGURATION, CONFIGURATION_GET, self.parameter]

class MultiChannel(Command):
    CLASS = COMMAND_CLASS_MULTI_CHANNEL

class MultiChannelEncap(MultiChannel):
    COMMAND = MULTI_CHANNEL_CMD_ENCAP

    def __init__(self, endpoint, command):
        self.endpoint = endpoint
        self.command = command

    def decode(self, payload):
        self.endpoint = payload[1]
        self.command = decode(payload[2:])

#----------------------------------------------------------------------

@functools.singledispatch
def serialize(cmd):
    return cmd.sig()

@serialize.register(BasicSet)
@serialize.register(BinarySwitchSet)
def _(cmd):
    return cmd.sig() + [cmd.value]

@serialize.register(MultiChannelEncap)
def _(cmd):
    return cmd.sig() + serialise(cmd.command)

#----------------------------------------------------------------------

LOOKUP = {
    COMMAND_CLASS_BASIC: {
        BASIC_SET: BasicSet,
        BASIC_GET: BasicGet,
        BASIC_REPORT: BasicReport},

    COMMAND_CLASS_SWITCH_BINARY: {
        SWITCH_BINARY_SET: BinarySwitchSet,
        SWITCH_BINARY_GET: BinarySwitchGet,
        SWITCH_BINARY_REPORT: BinarySwitchReport},

    COMMAND_CLASS_MULTI_CHANNEL: {
        MULTI_CHANNEL_CMD_ENCAP: MultiChannelEncap
    }
}

def decode(data):
    cls = LOOKUP.get(data[0], {})
    command = cls.get(data[1])

    if command:
        deserialize(command, data[2:])

    return command

@functools.singledispatch
def deserialize(cmd, data):
    pass

@deserialize.register(BasicReport)
@deserialize.register(BinarySwitchReport)
def _(cmd, data):
    cmd.value = msg[2]

@deserialize.register(MultiChannelEncap)
def _(cmd, data):
    cmd.endpoint = data[1]
    cmd.command = decode(data[2:])
