import struct
import time
import numpy as np
import serial
from toon.input.base_input import BaseInput

class BlamBirds(BaseInput):
    """Minimalist Flock of Birds implementation.
    Note: There are a few magic numbers/values currently involved:
        - Calibration values (offset and rotation) only apply to the Kinereach in the BLAM Lab.
        - Currently only support position -- in principle, not impossible to extend.
    If you're having trouble finding the right serial ports, try::
        from serial.tools import list_ports
        for i in list_ports.comports():
            print((i.hwid, i.device))
    """
    def __init__(self, ports=None, sample_ports=None,
                 master=None, data_mode='position',
                 sampling_frequency=130, **kwargs):
        """
        Args:
            ports (list of strings): List of *all* of the attached birds, e.g. ['COM4', 'COM5', 'COM6']
            sample_ports (list of strings): List of the relevant ports, e.g. ['COM4', 'COM6'].
                Defaults to all `ports`.
            master (str): The master bird. Defaults to the first port in `ports`.
            data_mode (str): Type of data returned by the flock. Default (and only implementation)
                is 'position'.
            sampling_frequency (int): Number of times a second all birds are sampled.
        """

        self.ports = ports  #  need to say at least *some* port
        self.sample_ports = sample_ports  # read all ports by default
        self.master = master  # the master is assumed to be first, unless otherwise stated
        self.data_mode = data_mode
        self.sampling_frequency = sampling_frequency

        # check inputs
        if not isinstance(self.ports, list):
            raise ValueError('`ports` expected to be a list of ports.')
        if not isinstance(self.master, str):
            self.master = self.ports[0]
        if not isinstance(self.sample_ports, list):
            self.sample_ports = self.ports
        if not set(self.sample_ports).issubset(self.ports):
            raise ValueError('`sample_ports` must be a subset of `ports`.')
        if self.master not in self.ports:
            raise ValueError('The master must be named amongst the ports.')
        if self.data_mode not in ['position']:
            raise ValueError('Invalid or unimplemented data mode.')
        if self.sampling_frequency > 140:
            raise ValueError('sampling_frequency is too high. Please set below 140 Hz.')

        self._birds = None  # Serial connections land here
        self._master_index = self.ports.index(self.master)
        self._sample_ports_indices = [self.ports.index(sp) for sp in self.sample_ports]
        self._ndata = 3 * len(self.sample_ports)  # 3 axes per bird of interest
        self._data_buffer = np.full(self._ndata, np.nan)
        BaseInput.__init__(self, **kwargs)

        # handle the reordering of axes (bird is [y, z, x] relative to screen)
        # TODO: clean this up (far too complicated)
        lp = len(self.sample_ports)
        self._reindex = (np.array([range(lp)]).reshape((lp, 1)) * 3 + np.tile([1, 2, 0], (lp, 1))).reshape(self._ndata)

    def __enter__(self):
        self._birds = [serial.Serial(port, baudrate=115200,
                                     bytesize=serial.EIGHTBITS,
                                     xonxoff=0,
                                     rtscts=0,
                                     timeout=(1.0/self.sampling_frequency) * 2.0)
                       for port in self.ports]

        for bird in self._birds:
            bird.setRTS(0)

        # try to figure out if the device is on -- query the device status
        self._birds[self._master_index].write(b'O' + b'\x24')
        time.sleep(0.2)
        data = self._birds[self._master_index].read(14)
        if data == b'':
            raise ValueError('Make sure the birds are in "fly" mode.')
        # run the fbb auto-config (include all ports)
        time.sleep(1)
        self._birds[self._master_index].write(('P' + chr(0x32) + chr(len(self.ports))).encode('UTF-8'))
        time.sleep(1)
        # set sampling frequency (130 by default)
        self._birds[self._master_index].write(b'P' + b'\x07' + struct.pack('<H', int(self.sampling_frequency * 256)))

        for bird in self._birds:
            # position as output type. TODO: allow different out data types
            bird.write(b'V')
            # change Vm table to Ascension's "snappy" settings
            bird.write(b'P' + b'\x0C' + struct.pack('<HHHHHHH', *[2, 2, 2, 10, 10, 40, 200]))
            # first 5 bits are meaningless, B2 is 0 (AC narrow ON), B1 is 1 (AC wide OFF), B0 is 0 (DC ON)
            bird.write(b'P' + b'\x04' + b'\x02' + b'\x00')

        # signal to all birds to start streaming (should this only go to the sample_ports?)
        for bird in self._birds:
            bird.write(b'@')
        return self

    def read(self):
        _data_list = list()
        for bird in self._sample_ports_indices:
            _data_list.append(self._birds[bird].read(6))  # assumes position data
        # only convert data if it's there
        timestamp = self.time()
        if not any(b'' == s for s in _data_list):
            _data_list = [self.decode(msg) for msg in _data_list]
            self._data_buffer[:] = np.array(_data_list).reshape(self._ndata)
            self._data_buffer[:] = self._data_buffer[self._reindex[:self._ndata]]
            temp_x = self._data_buffer[::3]
            temp_y = self._data_buffer[1::3]
            # here be magic numbers (very Kinereach-specific)
            self._data_buffer[::3] = temp_x * np.cos(-0.01938) - temp_y * np.sin(-0.01938)
            self._data_buffer[1::3] = temp_y * np.sin(-0.01938) + temp_y * np.cos(-0.01938)
            self._data_buffer[::3] += 61.35 - 60.5
            self._data_buffer[1::3] += 17.69 - 34.0
            return {'time': timestamp, 'data': np.copy(self._data_buffer)}
        return None


    def __exit__(self, type, value, traceback):
        for bird in self._birds:
            bird.write(b'?') # stops stream
        self._birds[self._master_index].write(b'G') # sleep (master only)
        for bird in self._birds:
            bird.close()

    def decode(self, msg, n_words=3):
        """Convert from word to data."""
        return [self._decode_words(msg, i) for i in range(int(n_words))]

    def _decode_words(self, s, i):
        v = self._decode_word(s[2 * i:2 * i + 2])
        v *= 36 * 2.54  # scaling to cm
        return v / 32768.0

    def _decode_word(self, msg):
        lsb = msg[0] & 0x7f
        msb = msg[1]
        v = (msb << 9) | (lsb << 2)
        if v < 0x8000:
            return v
return v - 0x10000