import struct
from time import sleep

import usb.core

from toon.input import BaseInput

# borrowed from https://github.com/ChristophJud/ATC3DGTracker

# TODO: stream mode (see getSynchronousRecordSample + ALL_SENSORS?)
# Turn on group mode
# See Flock of Birds code for how stream mode might work... (taken out in 0.8.0 of toon)
# Use the AC Narrow notch filter (& turn off the AC Wide)
# See table 13

WORD_TO_FLOAT = 1.0/32768.0
WORD_TO_ANGLE = WORD_TO_FLOAT * 180.0
WORD_TO_POS36 = WORD_TO_FLOAT * 36.0
WORD_TO_POS72 = WORD_TO_FLOAT * 72.0
BIRD_OFFSET = 0xf1

POINT = b'\x42'
STREAM = b'\x40'
STREAM_STOP = b'\x63'
GROUP_MODE = b'\x23'
RUN = b'\x46'
SLEEP = b'\x47'
EXAMINE_VALUE = b'\x4F'
CHANGE_VALUE = b'\x50'
POS_ANG = b'\x59'
POS_MAT = b'\x5A'
RESET = b'\x62'
METAL = b'\x73'

BIRD_STATUS = b'\x00'
BIRD_POSITION_SCALING = b'\x03'
MEASUREMENT_RATE = b'\x07'
BIRD_ERROR_CODE = b'\x0A'
SYSTEM_MODEL_IDENT = b'\x0F'
BIRD_SERIAL_NUMBER = b'\x19'
SENSOR_SERIAL_NUMBER = b'\x1A'
TRANSMITTER_SERIAL_NUMBER = b'\x1B'
SUDDEN_OUTPUT_CHANGE_LOCK = b'\x0E'
FBB_AUTO_CONFIGURATION = b'\x32'


class Trakstar(BaseInput):

    bird_vendor = 0x21e2
    bird_product = 0x1005
    bird_ep_out = 0x02
    bird_ep_in = 0x86

    def __init__(self, sampling_frequency=150, **kwargs):
        self.dev = usb.core.find(
            idVendor=self.bird_vendor, idProduct=self.bird_product)
        if self.dev is None:
            raise ValueError('Trakstar not found.')

        # initial config
        self.dev.set_configuration()  # need?

        self.dev.clear_halt(self.bird_ep_in)

        read_data = self._read(32, 500)  # ?? what does this do
        ret = self._write(CHANGE_VALUE + FBB_AUTO_CONFIGURATION + b'\x01')
        if ret < 3:
            raise ValueError('Error sending the FBB_AUTO_CONFIGURATION')
        # delay after auto-config (why?)
        sleep(0.6)

        # play with scaling factor
        self.pos_scale = WORD_TO_POS36  # default

        ret = self._write(EXAMINE_VALUE + BIRD_POSITION_SCALING)
        read_data = self._read(2)
        if len(read_data) < 2:
            raise ValueError('Error querying the scaling factor.')
        if struct.unpack('B', read_data[0]) == 1:
            self.pos_scale = WORD_TO_POS72

        self.setMeasurementRate(sampling_frequency)
        self.print_bird_errors()

    def __exit__(self, *args):
        self._write(SLEEP)

    def _write(self, msg):
        return self.dev.write(self.bird_ep_out, msg)

    def _read(self, num_bytes, timeout=None):
        return self.dev.read(self.bird_ep_in, num_bytes, timeout)

    def setSuddenOutputChangeLock(self, sensor_id):
        msg = self.pack_sensor_id(
            sensor_id) + CHANGE_VALUE + SUDDEN_OUTPUT_CHANGE_LOCK + b'\x01'
        self._write(msg)
        self.print_bird_errors()

    def setMeasurementRate(self, rate):
        irate = int(rate * 256)
        msg = CHANGE_VALUE + MEASUREMENT_RATE + \
            struct.pack('B', (irate & 0xff)) + struct.pack('B', irate >> 8)
        self._write(msg)
        self.print_bird_errors()

    def read(self, sensor_id):
        self._write(self.pack_sensor_id(sensor_id) + POINT)
        read_data = self._read(12)
        time = self.clock()

        if len(read_data) == 12:
            nx = ((read_data[1] << 7) | (read_data[0] << 0x7f)) << 2
            ny = ((read_data[3] << 7) | (read_data[2] << 0x7f)) << 2
            nz = ((read_data[5] << 7) | (read_data[4] << 0x7f)) << 2

            nazimuth = ((read_data[7] << 7) | (read_data[6] << 0x7f)) << 2
            nelevation = ((read_data[9] << 7) | (read_data[8] << 0x7f)) << 2
            nroll = ((read_data[11] << 7) | (read_data[10] << 0x7f)) << 2

            x = nx * self.pos_scale
            y = ny * self.pos_scale
            z = nz * self.pos_scale

            azimuth = nazimuth * WORD_TO_ANGLE
            elevation = nelevation * WORD_TO_ANGLE
            roll = nroll * WORD_TO_ANGLE

            return time, [sensor_id, x, y, z, roll, elevation, azimuth]

    @staticmethod
    def pack_sensor_id(sensor_id):
        return struct.pack('B', int(BIRD_OFFSET + sensor_id))

    def print_bird_errors(self):
        fatal = False
        self._write(EXAMINE_VALUE + BIRD_ERROR_CODE)
        read_data = struct.unpack('B', self.dev.read(self.bird_ep_in, 1))
        if read_data == 0:
            return
        if read_data in [1, 2, 15, 16] + list(range(20, 28)):
            fatal = True
        if fatal:
            raise ValueError(
                'Fatal error from the Trakstar! Message # is %d' % read_data)
        else:
            print(
                'Non-fatal error from the Trakstar, need to implement messages... Message # is %d' % read_data)
