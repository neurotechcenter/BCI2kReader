# BCI2kReader   [![Build Status](https://travis-ci.com/neurotechcenter/BCI2kReader.svg?branch=master)](https://travis-ci.com/neurotechcenter/BCI2kReader)
Python 3 and Python 2 compatible BCI2000 .dat file reader.

Reader for BCI2000 (https://www.neurotechcenter.org/research/bci2000/dissemination) .dat files.
This project is a wrapper using the reader developed for the BcPy2000 project 
(http://bci2000.org/downloads/BCPy2000/BCPy2000.html)

to install the current release package use:

pip install BCI2kReader

This package is still under development, use with caution!

### USAGE:

    from BCI2kReader import BCI2kReader as b2k

    with b2k.BCI2kReader('yourbci2000testfile.dat') as test: #opens a stream to the dat file
         test.samplingrate # sampling rate
##### # you can use the reader for random access using read(), seek()
        my_signals=test.signals #reads the whole file and stores it in a numpy matrix channels (channels,datapoints)
        my_states=test.states #reads all states as a dictionary ..
        my_signals, my_states=test.readall() #
        my_signals, my_states=test.read(-1) # reads from current position until end
        my_states['Running'] # access to the Running state
##### # By default calling test.signals, test.states and test.readall() caches all data in the object, this default behaviour can be changed by either calling the constructor with usecache=false or by calling .usecache(False). The cache can be cleared by calling .purge(), which should be called after you set usecache to false to free the memory.
#### # the reader object also supports direct slicing
        signalslice, stateslice = test[0:100] #returns the first 100 items,
        # this works with cached and non cached mode and does not alter the current position of the file pointer

#### # Slicing with states
        test.states[:100] # returns all states within the slice frame 
        # test.states['Running'][:,:100] is equivalent to test.states[:100]['Running']
        signals, states=test[test.States['StimulusCode'] == 1] # binary masks work in cached and uncached mode
