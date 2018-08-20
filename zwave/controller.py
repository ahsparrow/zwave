import logging

import gevent
import gevent.queue
import gevent.event

import serial

from . import zwave

ACK_TIMEOUT = 1.0

RETRY_TIME = 0.05
MAX_RETRIES = 20

class Controller:
    def __init__(self):
        self.msg_q = gevent.queue.Queue()
        self.nodes = {}
        self.txmsg_id = 0x20
        self.sent_msgs = {}

    def register_node(self, node):
        self.nodes[node.id] = node

    def open(self, dev):
        self.dev = dev
        self.ser = serial.Serial(self.dev, timeout=1.0)

    def start(self):
        gevent.spawn(self.transmit)
        gevent.spawn(self.receive)

    def transmit(self):
        while 1:
            msg = self.msg_q.get()
            logging.debug("Tx: " + zwave.msg_str(msg))

            try:
                for i in range(MAX_RETRIES):
                    res = self.transmit_msg(msg)
                    if res == zwave.CAN:
                        logging.debug("T/X cancelled, retrying...")
                        gevent.sleep(RETRY_TIME)
                    elif res == zwave.NAK:
                        logging.error("T/x NAK: " + zwave.msg_str(msg))
                        break
                    elif res == zwave.ACK:
                        break
                else:
                    logging.error("T/x max. retries: " + zwave.msg_str(msg))

            except gevent.Timeout:
                logging.error("T/x timeout: " + zwave.msg_str(msg))

    def transmit_msg(self, msg):
        payload = [len(msg) + 1] + msg
        buf = bytes([zwave.SOF] + payload + [zwave.checksum(payload)])

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
            logging.warning("R/x timeout waiting for length")
        else:
            msg_len = b[0]
            msg = self.ser.read(msg_len)

            if len(msg) != msg_len:
                logging.warning(
                    "R/x message length mismatach {}/{}".format(len(msg), msg_len))
            else:
                logging.debug("Rx: " + zwave.msg_str(msg))
                self.ser.write(bytes([zwave.ACK]))

                if msg[0] == zwave.RESPONSE:
                    if msg[1] == zwave.API_APP_COMMAND_HANDLER:
                        node = msg[3]
                        if node in self.nodes:
                            self.nodes[node].response(msg[5:-1])

                    elif msg[1] == zwave.API_ZW_SEND_DATA:
                        if msg[3] != zwave.TRANSMIT_COMPLETE_OK:
                            id = msg[2]
                            logging.warning("Transmit fail: %s",
                                            zwave.msg_str(self.sent_msgs.pop(id, [])))

                elif msg[0] == zwave.REQUEST:
                    if msg[1] == zwave.API_GET_INIT_DATA:
                        num_bitfields = msg[4]

                        nodes = []
                        for n_byte, bitfield in enumerate(msg[5:5 + num_bitfields]):
                            for n_bit in range(8):
                                if bitfield & (1 << n_bit):
                                    nodes.append(n_byte * 8 + n_bit + 1)

    def send_data(self, data):
        msg = [zwave.REQUEST, zwave.API_ZW_SEND_DATA] + data + \
              [zwave.TRANSMIT_OPTION_ACK | zwave.TRANSMIT_OPTION_AUTO_ROUTE, self.txmsg_id]

        self.msg_q.put(msg)
        self.sent_msgs[self.txmsg_id] = data

        if self.txmsg_id == 0xff:
            self.txmsg_id = 0x20
        else:
            self.txmsg_id += 1

    def get_version(self):
        msg = [zwave.REQUEST, zwave.API_ZW_GET_VERSION]
        self.msg_q.put(msg)

    def get_init_data(self):
        msg = [zwave.REQUEST, zwave.API_GET_INIT_DATA]
        self.msg_q.put(msg)
