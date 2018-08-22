import functools
import itertools
import struct

from . import command
from . import zwave

class DeserializeError(Exception):
    pass

#----------------------------------------------------------------------

@functools.singledispatch
def serialize(cmd):
    return list(cmd.sig())

@serialize.register(command.AssociationGet)
@serialize.register(command.MultiChannelAssociationGet)
def _(cmd):
    return list(cmd.sig()) + [cmd.group]

@serialize.register(command.BasicSet)
@serialize.register(command.BinarySwitchSet)
def _(cmd):
    return list(cmd.sig()) + [cmd.value]

@serialize.register(command.ConfigurationSet)
def _(cmd):
    return list(cmd.sig()) + \
           [cmd.parameter, struct.calcsize(cmd.fmt)] + \
           list(struct.pack(">%s" % cmd.fmt, cmd.value))

@serialize.register(command.ConfigurationGet)
def _(cmd):
    return list(cmd.sig()) + [cmd.parameter]

@serialize.register(command.MultiChannelAssociationRemove)
@serialize.register(command.MultiChannelAssociationSet)
def _(cmd):
    return list(cmd.sig()) + [cmd.group] + \
           cmd.nodes + [zwave.MULTI_CHANNEL_ASSOCIATION_SET_MARKER_V2] + \
           list(itertools.chain(*cmd.multi_channel_nodes))

@serialize.register(command.MultiChannelEncap)
def _(cmd):
    return list(cmd.sig()) + [0, cmd.endpoint] + serialize(cmd.command)

#----------------------------------------------------------------------

class lookup:
    def __init__(self, func):
        self.func = func
        self.class_dict = {}
        self.func_dict = {}

    def register(self, cmd):
        sig = cmd.sig()
        self.class_dict[sig] = cmd

        def decorate(func):
            self.func_dict[sig] = func
            return func

        return decorate

    def __call__(self, data):
        sig = (data[0], data[1])
        cmd = self.class_dict.get(sig)
        if cmd:
            command = cmd()
            self.func_dict[sig](command, data[2:])
            return command
        else:
            return self.func(data)

@lookup
def deserialize(data):
    raise DeserializeError

@deserialize.register(command.AssociationReport)
def _(cmd, data):
    cmd.group = data[0]
    cmd.max_nodes = data[1]
    cmd.num_reports = data[2]
    cmd.nodes = data[3:]

@deserialize.register(command.BasicReport)
@deserialize.register(command.BinarySwitchReport)
def _(cmd, data):
    cmd.value = data[0]

@deserialize.register(command.MeterReport)
def _(cmd, data):
    pass

@deserialize.register(command.MultiChannelAssociationReport)
def _(cmd, data):
    cmd.group = data[0]
    cmd.max_nodes = data[1]
    cmd.num_reports = data[2]

    cmd.nodes = list(itertools.takewhile(
            lambda x: x != zwave.MULTI_CHANNEL_ASSOCIATION_SET_MARKER_V2,
            data[3:]))

    n = len(cmd.nodes) + 4
    cmd.multi_channel_nodes = list(zip(data[n::2], data[n+1::2]))

@deserialize.register(command.MultiChannelEncap)
def _(cmd, data):
    cmd.endpoint = data[0]
    cmd.command = deserialize(data[2:])

@deserialize.register(command.ConfigurationReport)
def _(cmd, data):
    cmd.parameter = data[0]
    size = data[1]
    fmt = ">b" if size == 1 else ">h" if size == 2 else ">i"
    cmd.value = struct.unpack(fmt, data[2:])[0]
