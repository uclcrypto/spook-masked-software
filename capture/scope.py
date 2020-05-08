# MIT Licence
#
# Copyright 2020 UCLouvain
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.


import numpy as np
from picoscope import ps5000a

class SCAScope(ps5000a.PS5000a):
    def __init__(self,
            resolution="12", # bits
            vrange=0.10, #V
            voffset=0.000, #V
            n_samples=1000,
            sample_freq=500e6, # Hz
            batch_size=1,
            delay=0 #s
            ):
        super(SCAScope, self).__init__(serialNumber=b"GQ911/0058")

        self.setResolution(resolution) # bits
        self.setChannel(
                channel='A',
                coupling="AC",
                VRange=vrange, # V
                VOffset=voffset, # V
                enabled=True,
                )
        self.setChannel(channel='B', enabled=False)

        self.setSimpleTrigger(
                trigSrc='External',
                threshold_V=2, # V
                direction='Rising',
                delay=delay, #s
                timeout_ms=0, # us (and not ms !), wait time before forced trigger. 0 to disable.
                enabled=True
                )

        (sampling_freq, max_samples) = self.setSamplingFrequency(
                sampleFreq=sample_freq,
                noSamples=n_samples,
                oversample=0,
                segmentIndex=0
                )

        # TODO fix this function in picoscope library
        #if batch_size > self.getMaxMemorySegments():
        #    raise ValueError("Too many batches")

        max_samples = self.memorySegments(batch_size)
        if max_samples < n_samples:
            raise ValueError("Too many batches for the number of samples required.")

        self.setNoOfCaptures(batch_size)

        print("Sampling Freq: {:g} MHz".format(sampling_freq))
        print("maxSamples: {}".format(max_samples))
        print("n_samples: {}".format(n_samples))
        print("resolution: {}".format(self.resolution))

    def start_acquire(self):
        self.runBlock(pretrig=0) # no samples before trigger

    def result_acquire(self, dest=None):
        """Warning: returns the same buffer at every call."""
        self.waitReady() # TODO replace this with non-busy wait and callback
        # https://docs.python.org/2/library/ctypes.html
        # https://stackoverflow.com/questions/5114292/break-interrupt-a-time-sleep-in-python/46346184
        self.getDataRawBulk(data=dest,fromSegment=0)
