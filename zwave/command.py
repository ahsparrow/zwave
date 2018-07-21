import pprint

from . import zwave

class Command:
    @classmethod
    def sig(cls):
        return (cls.CLASS, cls.COMMAND)

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, pprint.pformat(self.__dict__))

class BasicCommand(Command):
    CLASS = zwave.COMMAND_CLASS_BASIC

class BasicSet(BasicCommand):
    COMMAND = zwave.BASIC_SET

    def __init__(self, value=True):
        self.value = value

class BasicGet(BasicCommand):
    COMMAND = zwave.BASIC_GET

class BasicReport(BasicCommand):
    COMMAND = zwave.BASIC_REPORT

    def __init__(self, value=False):
        self.value = value

class BinarySwitchCommand(Command):
    CLASS = zwave.COMMAND_CLASS_SWITCH_BINARY

class BinarySwitchGet(BinarySwitchCommand):
    COMMAND = zwave.SWITCH_BINARY_GET

class BinarySwitchSet(BinarySwitchCommand):
    COMMAND = zwave.SWITCH_BINARY_SET

    def __init__(self, value=True):
        self.value = value

class BinarySwitchReport(BinarySwitchCommand):
    COMMAND = zwave.SWITCH_BINARY_REPORT

    def __init__(self, value=False):
        self.value = value

class ConfigurationClass(Command):
    CLASS = zwave.COMMAND_CLASS_CONFIGURATION

class ConfigurationSet(ConfigurationClass):
    COMMAND = zwave.CONFIGURATION_SET

    def __init__(self, parameter, value, fmt):
        self.parameter = parameter
        self.value = value
        self.fmt = fmt

class ConfigurationGet(ConfigurationClass):
    COMMAND = zwave.CONFIGURATION_GET

    def __init__(self, parameter):
        self.parameter = parameter

class ConfigurationReport(ConfigurationClass):
    COMMAND = zwave.CONFIGURATION_REPORT

    def __init__(self):
        self.parameter = -1
        self.value = 0

class MultiChannel(Command):
    CLASS = zwave.COMMAND_CLASS_MULTI_CHANNEL

class MultiChannelEncap(MultiChannel):
    COMMAND = zwave.MULTI_CHANNEL_CMD_ENCAP

    def __init__(self, endpoint=0, command=None):
        self.endpoint = endpoint
        self.command = command

