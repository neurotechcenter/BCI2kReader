# -*- coding: utf-8 -*-

#   The BCPyReader is free software: you can redistribute it
#   and/or modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import io as io
from .FileReader import bcistream
import numpy as np


class BCI2kReader(io.IOBase):
    """" The BCI2kReader reads a BCI20000 .dat file. It inherits from io.IOBase and can use the with clause """
    def __init__(self, filename, usecache=True):
        """Constructor


        Parameters
        ----------
        filename : str
            Path to the BCI2000 .dat file
        usecache : bool
            enables the object to cache the signal and states data internally.
            After a readall() (or the signals or states property is called) is called
            the values are stored in the object and all subsequent data queries will be performed with the cached data.
            If caching is disabled, all queries will be read directly from the file.
            To delete the cached data call .purge()
        """
        self.__reader = bcistream(filename)
        self.__states = None
        self.__signals = None
        self.__usecache = usecache

    def close(self):
        """ Close the file

            If caching is enabled, the data will stay in the cache
        """
        self.__reader.close()

    def _getclosed(self):
        return self.__reader.file.closed

    closed = property(_getclosed)

    def fileno(self):
        return self.__reader.file.fileno()

    def readable(self):
        return self.__reader.file.readable()

    def seek(self, offset, whence=0):
        """ Set the file pointer to a specific position

        Parameters
        ----------
        offset : int
            Offset in data samples
        whence : int
            counting position
            io.SEEK_SET | 0 relative to start
            io.SEEK_CUR = 1 | relative to current position
            io.SEEK_END = 2 | relative to end
        """
        if whence == 0:  # do not use io. variables for comparability
            wrt = 'bof'
        elif whence == 1:
            wrt = 'eof'
        elif whence == 2:
            wrt = 'cof'
        else:
            raise IOError('unknown search origin')

        self.__reader.seek(offset, wrt)

    def seekable(self):
        return True

    def tell(self):
        """
        File pointer position
        
        Parameters
        ----------
        
        
        Returns
        -------
         int
         returns the current position of the file pointer """
        return self.__reader.tell()

    def writable(self):
        return False

    def usecache(self, flag):
        self.__usecache = flag

    def _parameters(self):
        return self.__reader.params

    parameters = property(_parameters)
    """ Returns the parameters """

    def _signals(self):
        if self.__signals is not None:
            return self.__signals
        # save current position
        pos = self.tell()
        if self.__usecache:
            self.__signals, self.__states = self.__reader.decode('all')
            self.__states = StateDictionary(self.__states)
            self.seek(pos, 0)
            return self.__signals
        else:
            signalbuffer, statebuffer = self.__reader.decode('all')
            self.seek(pos, 0)
            return signalbuffer

    signals = property(_signals)
    """ Returns the signals in the format (channels x samples),
        if caching is enabled, this will cause the signals and states to be cached
    """

    def _states(self):
        if self.__states is not None:
            return self.__states
        pos = self.tell()
        if self.__usecache:
            self.__signals, self.__states = self.__reader.decode('all')
            self.__states = StateDictionary(self.__states)
            self.seek(pos, 0)
            return self.__states
        else:
            signalbuffer, statebuffer = self.__reader.decode('all')
            self.seek(pos, 0)
            return StateDictionary(statebuffer)
        # set position

    states = property(_states)
    """ Returns the states in the format (states x samples),
        if caching is enabled, this will cause the signals and states to be cached
        The states are stored as a StateDictionary (Dict with additional slicing capabilities)
    """

    def purge(self):
        """ Clears cached data

        Parameters
        ----------

        """
        self.__states = None
        self.__signals = None

    def _samplingrate(self):
        return self.__reader.samplingrate()

    samplingrate = property(_samplingrate)
    """ Sampling rate of the signals defined in file """

    def read(self, nsamp=-1, apply_gain=True):
        """Reads an arbitrary amount of data either from cache or file starting at the current file pointer position

        Parameters
        ----------
            nsamp : int
                Number of samples to be read

            apply_gain : bool
                If true data will be multiplied with channel gain
                This parameter is ignored if working with cached data

        Returns
        -------
            signals : ndarray
                channel x samples numpy array
            states : StateDictionary
                Dictionary States x samples

        """
        if self.__states is not None and self.__usecache:
            pos = self.tell()
            if nsamp < 0:
                nsamp = self.__reader.samples()-pos
            return self.__signals[:, pos:pos+nsamp], self.__slicedict[slice(pos, pos+nsamp)]
        else:
            sig, states = self.__reader.decode(nsamp, 'all', apply_gain)
            states = StateDictionary(states)
            return sig, states

    def readall(self, apply_gain=True):
        """Reads all data from the file and caches the data if caching is enabled

        Parameters
        ----------
            apply_gain : bool
                If True, signal data will be multiplied with gain specified in parameter file

         Returns
        -------
            signals : ndarray
                channel x samples numpy array
            states : StateDictionary
                Dictionary States x samples

        """

        if self.__states is not None and self.__usecache:
            return self.__signals, self.__states
        else:
            if self.__usecache:
                self.__signals, statebuffer = self.__reader.decode('all', 'all', apply_gain)
                self.__states = StateDictionary(statebuffer)
                return self.__signals, self.__states
            else:
                buffsignals, buffstates =  self.__reader.decode('all', 'all', apply_gain)
                return buffsignals, StateDictionary(buffstates)

    def __len__(self):
        """
        Returns
        ------
            int
            Number of samples
        """
        return len(self.__reader.samples())

    def __repr__(self):
        return self._signals, self._states

    def __getitem__(self, sliced):
        if isinstance(sliced, np.ndarray):
            if sliced.dtype != bool:
                raise IndexError('Expected array to be of type bool')

            if sliced.shape[0] == 1:
                sliced = np.transpose(sliced)

            if self.__states is not None and self.__usecache:
                return self.__signals[:, sliced[:, 0]], self.__states[sliced[:, 0]]
            else:
                data = np.zeros((self.__reader.channels(), sum(sliced[:, 0])))
                states = StateDictionary()
                sliced = np.r_[False, sliced[:, 0], False]
                idx = np.flatnonzero(sliced[:-1] != sliced[1:])
                idx = zip(idx[:-1:2], idx[1::2])
                curr_pos = 0
                for start, stop in idx:
                    dat_len = stop-start
                    self.seek(start, 0)
                    data[:, curr_pos:curr_pos + dat_len], buff_states = self.read(dat_len)
                    for key in buff_states.keys():
                        if key in states:
                            states[key] = np.append(states[key], buff_states[key], axis=1)
                        else:
                            states[key] = buff_states[key]
                    curr_pos = curr_pos+dat_len
                return data, states

        sliced = sliced if isinstance(sliced, slice) else slice(sliced, sliced+1, 1)
        ind = sliced.indices(self.__reader.samples())
        sliced = slice(ind[0], ind[1], ind[2])
        if self.__states is not None and self.__usecache:
            return self.__signals[:, sliced], self.__states[sliced]
        else:
            old = self.tell()
            self.seek(sliced.start, 0)
            data, states = self.read((sliced.stop-sliced.start))
            self.seek(old, 0)
            newslice = slice(0,(sliced.stop-sliced.start), sliced.step)
            return data[:, newslice], states[newslice]


try:  # Python 2
    str_base = basestring
    items = 'iteritems'
except NameError:  # Python 3
    str_base = str, bytes, bytearray
    items = 'items'


class StateDictionary(dict):
    """ StateDictionary is a Dict with extended slicing behaviour for working with states

     dict['State'] returns the state as ndarray 1 x samples
     dict[0:100] returns a slice of all states as StateDictionary


     dict['State'][:,:100] is equivalent to dict[:100]['State']
     """

    def __getitem__(self, slice_var):
        if isinstance(slice_var, str_base):  # standard dict behaviour
            return super(StateDictionary, self).__getitem__(slice_var)
        else:  # slice states instead of getting key
            return self.__slicedict(slice_var)

    def __slicedict(self, slice_idx):
        retdict = StateDictionary.fromkeys(self.keys())
        for key in self:
            retdict[key] = self[key][:, slice_idx]
        return retdict

    def _getshape(self):
        return len(self.keys()), self[list(self.keys())[0]].shape[1]

    shape = property(_getshape)
    """ 
    Returns the shape as Number of States x samples
    
    """
