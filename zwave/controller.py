import logging

import gevent
from gevent.queue import PriorityQueue
from gevent.event import AsyncResult

import serial

from . import zwave

ACK_TIMEOUT = 0.1
SEND_TIMEOUT = 5.0

RETRY_TIME = 0.05
MAX_RETRIES = 10

MIN_TXMSG_ID = 0x20
MAX_TXMSG_ID = 0xff

ACK_PRIO = 0

class TransmitError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Z-Wave transmit error: %d" % self.value

class Timeout(Exception):
    def __str__(self):
        return "Z-Wave timeout"

class Controller:
    def __init__(self):
        self.msg_q = PriorityQueue()
        self.nodes = {}
        self.msg_count = 1
        self.txmsg_id = MIN_TXMSG_ID
        self.sent_msgs = {}

    # Register a node (to get received messages)
    def register_node(self, node):
        self.nodes[node.id] = node

    # Open serial device
    def open(self, dev):
        self.dev = dev
        self.ser = serial.Serial(self.dev, timeout=1.0)

    # Start transmit and receive processes
    def start(self):
        gevent.spawn(self.transmit)
        gevent.spawn(self.receive)

    # Send Z-Wave data and wait for acknowledgment from remote node
    def send_data(self, data, timeout=SEND_TIMEOUT):
        msg = [zwave.REQUEST, zwave.API_ZW_SEND_DATA] + data + \
              [zwave.TRANSMIT_OPTION_ACK | zwave.TRANSMIT_OPTION_AUTO_ROUTE,
               self.txmsg_id]

        self.msg_q.put((self.msg_count, msg))
        self.msg_count += 1

        result = AsyncResult()
        self.sent_msgs[self.txmsg_id] = {'data': data, 'result': result}

        # Increment and wrap message ID
        self.txmsg_id += 1
        if self.txmsg_id > MAX_TXMSG_ID:
            self.txmsg_id = MIN_TXMSG_ID

        try:
            value = result.get(timeout=timeout)
        except gevent.Timeout:
            logging.error("Timeout wait for t/x acknowledgement")
            raise Timeout

        if value != zwave.TRANSMIT_COMPLETE_OK:
            raise TransmitError(value)

    def get_version(self):
        msg = [zwave.REQUEST, zwave.API_ZW_GET_VERSION]
        self.msg_q.put(msg)

    def get_init_data(self):
        msg = [zwave.REQUEST, zwave.API_GET_INIT_DATA]
        self.msg_q.put(msg)

    #-------------------------------------------------------------------
    # Internal functions

    def transmit(self):
        while 1:
            prio, msg = self.msg_q.get()

            # ACK is special case
            if prio == ACK_PRIO:
                self.ser.write(msg)
                continue

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

        self.tx_result = AsyncResult()
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
        # Read message length
        b = self.ser.read()

        if not b:
            logging.warning("R/x timeout waiting for length")
        else:
            # Read remainder of message
            msg_len = b[0]
            msg = self.ser.read(msg_len)

            if len(msg) != msg_len:
                # Message length mismatch
                logging.warning(
                    "R/x message length mismatach {}/{}".format(len(msg), msg_len))
            else:
                logging.debug("Rx: " + zwave.msg_str(msg))

                # Queue message acknowledgement for send
                self.msg_q.put((ACK_PRIO, [zwave.ACK]))

                self.process_msg(msg)

    def process_msg(self, msg):
        if msg[0] == zwave.RESPONSE:

            # Message from remote node
            if msg[1] == zwave.API_APP_COMMAND_HANDLER:
                node = msg[3]
                if node in self.nodes:
                    self.nodes[node].response(msg[5:-1])

            # Result of send data
            elif msg[1] == zwave.API_ZW_SEND_DATA:
                id = msg[2]
                sent_msg = self.sent_msgs.pop(id, None)

                if sent_msg:
                    result = msg[3]
                    if result != zwave.TRANSMIT_COMPLETE_OK:
                        logging.warning("Transmit fail: %d, %s",
                                        result,
                                        zwave.msg_str(sent_msg['data']))

                    sent_msg['result'].set(result)

        elif msg[0] == zwave.REQUEST:
            if msg[1] == zwave.API_GET_INIT_DATA:
                num_bitfields = msg[4]

                nodes = []
                for n_byte, bitfield in enumerate(msg[5:5 + num_bitfields]):
                    for n_bit in range(8):
                        if bitfield & (1 << n_bit):
                            nodes.append(n_byte * 8 + n_bit + 1)
