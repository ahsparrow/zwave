import logging

import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult

import serial

from . import zwave

# Time to wait for Z-Wave stick to acknowledge
ACK_TIMEOUT = 0.5

# Time to wait for Z-Wave remote node to acknowlege
TX_TIMEOUT = 2.0

# Max number of retries following CAN or NAK
MAX_TX_RETRIES = 3

MIN_TXMSG_ID = 0x20
MAX_TXMSG_ID = 0xff

ACK_STR = {zwave.ACK: "ACK", zwave.NAK: "NAK", zwave.CAN: "CAN"}

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
        self.msg_q = Queue()
        self.nodes = {}

        self.ack_result = None

        self.txmsg_id = MIN_TXMSG_ID
        self.tx_result = {}

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

    # Queue Z-Wave data for transmission to remote node
    def send_data(self, data):
        msg = [zwave.REQUEST, zwave.API_ZW_SEND_DATA] + data
        self.msg_q.put(msg)

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
            msg = self.msg_q.get()

            # Increment and wrap message ID
            self.txmsg_id += 1
            if self.txmsg_id > MAX_TXMSG_ID:
                self.txmsg_id = MIN_TXMSG_ID

            # tx_result is set by acknowledgement from remote node
            tx_result = AsyncResult()
            self.tx_result[self.txmsg_id] = tx_result

            # Send message and wait for ACK/NAK/CAN from Z-Wave interface
            ack = self.transmit_msg(msg, self.txmsg_id)

            if ack in [zwave.CAN, zwave.NAK]:
                # Re-try send message
                for n in range(MAX_TX_RETRIES):
                    gevent.sleep(0.1 + n)
                    logging.debug("Tx retry #%d..." % (n + 1))

                    ack = self.transmit_msg(msg, self.txmsg_id)
                    if ack == zwave.ACK:
                        break
                else:
                    # Too many retries, give up on this message
                    logging.error("Maximum Tx retries exceeded")

            if ack == zwave.ACK:
                try:
                    # Wait for acknowledgement from remote node
                    tx_result.get(timeout=TX_TIMEOUT)
                except gevent.Timeout:
                    logging.error("Tx timeout, no remote ACK")
            else:
                logging.error("Tx ACK not received")

    # Send message and wait for ACK/NAK/CAN from Z-Wave controller
    def transmit_msg(self, msg, msg_id):
        payload = [len(msg) + 3] + msg + [zwave.TRANSMIT_OPTION_ACK, msg_id]
        buf = bytes([zwave.SOF] + payload + [zwave.checksum(payload)])
        logging.debug("Tx: " + zwave.msg_str(buf[1:]))

        self.ack_result = AsyncResult()
        self.ser.write(buf)
        try:
            result = self.ack_result.get(timeout=ACK_TIMEOUT)
        except gevent.Timeout:
            logging.warning("Tx ACK timeout")
            result = None

        self.ack_result = None
        return result

    def send_ack(self):
        logging.debug("Tx: ACK")
        self.ser.write([zwave.ACK])

    def send_can(self):
        logging.debug("Tx: CAN")
        self.ser.write([zwave.CAN])

    def receive(self):
        while 1:
            b = self.ser.read()
            if not b:
                continue

            frame_type = b[0]
            if frame_type == zwave.SOF:
                # Data frame
                self.read_msg()

            elif frame_type in [zwave.ACK, zwave.NAK, zwave.CAN]:
                # ACK/NAK/CAN frame
                logging.debug("Rx: %s" % ACK_STR[frame_type])

                if self.ack_result is not None:
                    # Return result to t/x thread
                    self.ack_result.set(frame_type)
                else:
                    # Unexpected ACK/NAK/CAN
                    logging.warning("Rx unexpected %s" % ACK_STR[frame_type])

            else:
                # Unknown frame
                logging.warning(
                        "Rx unexpected start character {0x:02x}".format(frame_type))

    def read_msg(self):
        # Get message length
        b = self.ser.read()

        if not b:
            logging.error("Rx timeout waiting for length")
        else:
            # Read remainder of message
            msg_len = b[0]
            msg = self.ser.read(msg_len)

            if len(msg) != msg_len:
                # Message length mismatch
                logging.warning(
                    "Rx message length mismatach {}/{}".format(len(msg), msg_len))
            else:
                logging.debug("Rx: " + zwave.msg_str(msg))

                # Message acknowledgement
                if self.ack_result is None:
                    self.send_ack()
                    self.process_msg(msg)
                else:
                    # Tx in progress, cancel receive
                    self.send_can()

    def process_msg(self, msg):
        if msg[0] == zwave.RESPONSE:

            # Message from remote node
            if msg[1] == zwave.API_APP_COMMAND_HANDLER:
                node = msg[3]
                if node in self.nodes:
                    self.nodes[node].response(msg[5:-1])

            # Tx acknowledgement from remote node
            elif msg[1] == zwave.API_ZW_SEND_DATA:
                msg_id = msg[2]
                tx_result = self.tx_result.pop(msg_id, None)

                if tx_result:
                    result = msg[3]
                    if result != zwave.TRANSMIT_COMPLETE_OK:
                        logging.warning("Tx failed, id: %x", msg_id)

                    tx_result.set(result)
                else:
                    logging.error("Unexpected tx acknowledgment")
