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

