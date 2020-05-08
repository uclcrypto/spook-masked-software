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


from interface.SpookTopLevel import *
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import argparse
from interface.parameters import *

if __name__=="__main__":
    ##########################################
    # Argument Parsing
    parser = argparse.ArgumentParser(description='Trace collecting script')
    parser.add_argument(
            '-f',
            '--fname',
            default='traces.npz',
            help='file name where traces are saved'
            )
    parser.add_argument(
            '-k',
            '--keyfixed',
            default=1,
            type=int,
            help='is the key fixed'
            )
    parser.add_argument(
            '-n',
            '--number',
            default=1000,
            type=int,
            help='number of traces collected'
    )
    parser.add_argument(
            '-b',
            '--batch',
            default=1000,
            type=int,
            help='Number of traces in a batch'
    )
    parser.add_argument(
            '-c',
            '--cycles',
            default=4000,
            type=int,
            help='Number of cycles to measure'
    )
    parser.add_argument('--capture', dest='capture', action='store_true', help='Capture the traces')
    parser.add_argument('--no-capture', dest='capture', action='store_false')
    parser.set_defaults(capture=True)
    args = parser.parse_args()

    N = args.number
    fname = args.fname
    capture = args.capture
    batch_size = args.batch
    n_clk_cycles= args.cycles
    assert N%batch_size == 0
    fixed_key = args.keyfixed
    ###########################################

    # Create device
    dev = SpookTopLevel(target="MCU",PORT="/dev/ttyUSB0")

    ### Setup up the scope
    if capture:
        import scope
        sample_freq = 500e6
        clk_cycle = 1/48E6
        samples_per_clk_cycle = sample_freq*clk_cycle

        n_clk_delay = 0

        vrange = 0.02
        voffset = 0.000
        resolution="12"
        n_samples = int(n_clk_cycles * samples_per_clk_cycle)
        ps = scope.SCAScope(batch_size=batch_size, n_samples=n_samples,
                sample_freq=sample_freq,resolution=resolution,voffset=voffset,
                vrange=vrange,delay=int(n_clk_delay*samples_per_clk_cycle))
        Ns = ps.noSamples

        traces = np.zeros((N,Ns),dtype=np.int16)
    keys = np.zeros((N,4*D),dtype=np.uint32)
    nonces = np.zeros((N,4),dtype=np.uint32)
    seeds = np.zeros((N,4),dtype=np.uint32)

    # set batch size to the target
    seed = np.random.randint(0,2**32,4,dtype=np.uint32)
    npub = np.random.randint(0,2**32,4,dtype=np.uint32)
    if fixed_key == 1:
        k = np.load("secret_key.npz")["secret_key"]
        k = np.frombuffer(mask(k.tobytes(),D),dtype=np.uint32)
    else:
        k= np.random.randint(0,2**32,4*D,dtype=np.uint32)
    m = np.zeros(1,dtype=np.uint32)
    ad = np.zeros(1,dtype=np.uint32)

    # send data to the chip
    dev.set_data(np.array([batch_size],dtype=np.uint32).tobytes(),"N",enc_flag=0)
    dev.set_data(np.array([fixed_key],dtype=np.uint32).tobytes(),"f",enc_flag=0)
    dev.set_data(seed.tobytes(),"s",enc_flag=0)   #initial seed, will be updated on chip
    dev.set_data(npub.tobytes(),"npub",enc_flag=0) #initial nonce, that will be update on chip
    dev.set_data(k.tobytes(),"k",enc_flag=0)    #initial key, will be refreshed/randomized according to fixed_key
    dev.set_data(m.tobytes(),"m",enc_flag=0)
    dev.set_data(ad.tobytes(),"ad",enc_flag=0)

    for i in tqdm(range(0, N, batch_size),desc="recording traces",smoothing=0):
        if capture:
            ps.start_acquire()

        #trig encryption on the target
        enc_cor = dev.set_data(m.tobytes(),"m",enc_flag=1)

        #get input data to the chip, next uses spook_masked.py to generate all intermediate data
        keys[i:(i+batch_size)],seeds[i:(i+batch_size)],nonces[i:(i+batch_size)] = dev.unroll_inputs(batch_size)

        if capture:
            ps.result_acquire(traces[i:(i+batch_size),:])

    um_keys = umask(keys);
    dev.close()
    if capture:
        del scope
        with open(fname, 'wb') as f:
            np.savez(f, msk_keys=keys,umsk_keys = um_keys,
                    seeds=seeds,
                    nonces=nonces,
                    m=m,
                    ad=ad,
                    traces=traces)
