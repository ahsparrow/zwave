import logging

import gevent
import gevent.queue
import gevent.event

import serial

from . import zwave

ACK_TIMEOUT = 1.0

MAX_TX_RETRIES = 100

def checksum(data):
    checksum = 0xff
    for b in data:
        checksum = checksum ^ b
    return checksum

def raw_msg(func, data):
    out = [len(data) + 3, zwave.REQUEST, func] + data
    out += [checksum(out)]
    return bytes(out)

def msg_str(data):
    return ":".join(["{:02x}".format(x) for x in data])

class Controller:
    def __init__(self, dev):
        self.dev = dev
        self.msg_q = gevent.queue.Queue()
        self.nodes = {}

    def register_node(self, node):
        self.nodes[node.id] = node

    def open(self):
        self.ser = serial.Serial(self.dev, timeout=1.0)

    def transmit(self):
        while 1:
            msg = self.msg_q.get()
            logging.debug("Tx: " + msg_str(msg))

            try:
                for i in range(MAX_TX_RETRIES):
                    res = self.transmit_msg(msg)
                    if res == zwave.CAN:
                        logging.debug("T/X cancelled, retrying...")
                        self.transmit_msg(msg)
                    else:
                        if res == zwave.NAK:
                            logging.error("T/x NAK: " + msg_str(msg))
                        break

            except gevent.Timeout:
                logging.error("T/x timeout: " + msg_str(msg))

    def transmit_msg(self, msg):
        buf = bytes([zwave.SOF]) + msg

        self.tx_result = gevent.event.AsyncResult()
        self.ser.write(buf)

        return self.tx_result.get(timeout=ACK_TIMEOUT)

    def receive(self):
        while 1:
            b = self.ser.read()
            if not b:
                continue

            if b[0] == zwave.SOF:
                self.read_msg()
            elif b[0] in [zwave.ACK, zwave.NAK, zwave.CAN]:
                self.tx_result.set(b[0])
            else:
                logging.warning(
                        "Unexpected start character {0x:02x}".format(b[0]))

    def read_msg(self):
        b = self.ser.read()
        if not b:
            logging.warning("Timeout waiting for length")
        else:
            msg_len = b[0]
            msg = self.ser.read(msg_len)
            if len(msg) != msg_len:
                logging.warning(
                    "Message length mismatach {}/{}".format(len(msg), msg_len))
            else:
                logging.debug("Rx: {:02x}:{}".format(msg_len, msg_str(msg)))
                self.ser.write(bytes([zwave.ACK]))

                if msg[1] == zwave.API_APP_COMMAND_HANDLER:
                    node = msg[3]
                    if node in self.nodes:
                        self.nodes[node].response(msg[5:-1])

    def send_msg(self, msg):
        self.msg_q.put(msg)

    def send_command(self, node_id, command_cls, command, data, endpoint=0):
        if endpoint:
            msg = raw_msg(zwave.API_ZW_SEND_DATA,
                [node_id, len(data) + 6,
                 zwave.COMMAND_CLASS_MULTI_CHANNEL, zwave.MULTI_CHANNEL_CMD_ENCAP,
                 0, endpoint,
                 command_cls, command] + data)

        else:
            msg = raw_msg(zwave.API_ZW_SEND_DATA,
                    [node_id, len(data) + 2, command_cls, command] + data)

        self.send_msg(msg)
