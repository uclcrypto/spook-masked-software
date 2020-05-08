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


import serial, time
from interface.spook import shadow,bytes2state,state2bytes
import numpy as np
from tqdm import tqdm
import os
from interface.parameters import *
from interface.utils import *
########################
# INTERFACE
########################
class SpookTopLevel:
    def __init__(self,target,PORT="/dev/ttyUSB0"):
        """ This object allows to interact with Spook v2 modules (MCU or Python3 ones).

            It used to trigger encryption/decryption with choosen inputs as well as random ones.
            In the latest, these are generated on board. Multiple encryptions on random values
            can be triggered. This is usefull to speed up measurement process by reducing communication
            time.

            target: "MCU","Python"
            PORT:   serial port for the communication
        """
        if target == "MCU":
            self._ser = init_serial(PORT)
            self._ser.open()

        self._target = target
        self._N = 1 #default batchsize is 1
        self._f = 1 #default with fixed key

    def encrypt_key(self,ad,m,k,n):
        """ encrypt associated data and plaintext
        ad: associated data
        m: message
        k: key
        n: nonce
        """
        self.set_data(ad,dest="ad",enc_flag=0)
        self.set_data(m,dest="m",enc_flag=0)
        self.set_data(k,dest="k",enc_flag=0)
        return self.set_data(n,dest="npub",enc_flag=1)

    def encrypt(self,ad,m,n):
        """ encrypt associated data and plaintext with the preloaded key
        ad: associated data
        m: message
        n: nonce
        """
        self.set_data(ad,dest="ad",enc_flag=0)
        self.set_data(m,dest="m",enc_flag=0)
        return self.set_data(n,dest="npub",enc_flag=1)

    def decrypt_key(self,ad,c,k,n):
        """ decrypt associated data and ciphertext
        ad: associated data
        c: ciphertext
        k: key
        n: nonce
        """
        self.set_data(ad,dest="ad",enc_flag=0)
        self.set_data(k,dest="k",enc_flag=0)
        self.set_data(c,dest="c",enc_flag=0)
        return self.set_data(n,dest="npub",enc_flag=2)


    def decrypt(self,ad,c,n):
        """ decrypt associated data and ciphertext
        ad: associated data
        c: ciphertext
        k: key
        n: nonce
        """
        self.set_data(ad,dest="ad",enc_flag=0)
        self.set_data(c,dest="c",enc_flag=0)
        return self.set_data(n,dest="npub",enc_flag=2)

    def unroll_inputs(self,N):
        """
        This function is used to predict the inputs given to the
        spook module on the MCU for batches of size N.
        These are derived from a PRNG.
        """
        nonces = np.zeros((N,4),dtype=np.uint32)
        key = np.zeros((N,4*D),dtype=np.uint32)
        seeds = np.zeros((N,4),dtype=np.uint32)

        # set inputs to what was in memory
        nonces[0,:] = np.frombuffer(self._npub,dtype=np.uint32)
        key[0,:] = np.frombuffer(self._k,dtype=np.uint32)
        seeds[0,:] = self._prng_state[0]

        for i in tqdm(range(0,N),desc="Derive inputs"):

            #peform encryption on chip
            self._prng_state = shadow(self._prng_state)
            if i != (N-1):
                if self._f == 1:
                    simple_refresh(key[i+1,:],
                            np.frombuffer(self._k,dtype=np.uint32),
                            self._prng_state[2])
                else:
                    key[i+1,:],_ = get_random_tape(self._prng_state[2],D*4)

                seeds[i+1,:] = self._prng_state[0]
                nonces[i+1,:] = self._prng_state[1][:]
            else:
                self._npub = np.array(self._prng_state[1][:],dtype=np.uint32).tobytes()
                tmp = np.zeros(4*D,dtype=np.uint32)
                if self._f == 1:
                    simple_refresh(tmp,
                            np.frombuffer(self._k,dtype=np.uint32),
                            self._prng_state[2])
                else:
                    tmp,_ = get_random_tape(self._prng_state[2],D*4)

                self._k = tmp.tobytes()
                self._seed = self._prng_state[0]
                self._npub = np.array(self._prng_state[1][:],dtype=np.uint32).tobytes()

        return key,seeds,nonces
    def set_data(self,data,dest,enc_flag):
        if dest == "c":
            self._c = data
        elif dest == "ad":
            self._ad = data
        elif dest == "m":
            self._m = data
        elif dest == "npub":
            self._npub = data
        elif dest == "k":
            self._k = data
        elif dest == "s":
            self._seed = data
            self._prng_state = np.zeros((4,4),dtype=np.uint32)
            self._prng_state[0,:] = np.frombuffer(data,dtype=np.uint32)
        elif dest == "N":
            self._N = np.frombuffer(data,dtype=np.uint32)[0]
        elif dest == "f":
            self._f = np.frombuffer(data,dtype=np.uint32)[0]
        else:
            print("Does not match dest")

        if self._target == "MCU":
            send_data_uart(self._ser,data,enc_flag=enc_flag,dest=dest)

            if enc_flag==1:
                return self._ser.read(len(self._m)+16)
            elif enc_flag==2:
                return self._ser.read(len(self._m))
        elif self._target == "Python":
            if enc_flag == 1:
                return spook.spook_encrypt(ad=self._ad, m=self._m, k=self._k, p=self._p,n=self._n)
            elif enc_flag == 2:
                return spook.spook_decrypt(ad=self._ad, c=self._c, k=self._k, p=self._p,n=self._n)
    def close(self):
        self._ser.close()

def init_serial(PORT="/dev/ttyUSB0"):
    ser = serial.Serial()
    ser.port = PORT
    ser.baudrate = 115200
    ser.bytesize = serial.EIGHTBITS #number of bits per bytes
    ser.parity = serial.PARITY_NONE #set parity check: no parity
    ser.stopbits = serial.STOPBITS_ONE #number of stop bits
    # ser.timeout = 0               #non-block read
    ser.xonxoff = False             #disable software flow control
    ser.timeout = True              #block read
    ser.rtscts = False              #disable hardware (RTS/CTS) flow control
    ser.dsrdtr = False              #disable hardware (DSR/DTR) flow control
    return ser

def send_data_uart(ser,data,enc_flag=1,dest="m"):
    """ format the header and the data section
        and transfer it to the MCU on the UART interface.

        data: bytes of the data
        enc_flag: ask to start encryption
        dest: "m"|"ad"|"k"|"npub"|"c"|"N"|"f"|"s"
    """
    stream = np.zeros(4).astype(np.uint8)

    if dest == "c":
        stream[0] = 0
    elif dest == "ad":
        stream[0] = 1
    elif dest == "m":
        stream[0] = 2
    elif dest == "npub":
        stream[0] = 3
    elif dest == "k":
        stream[0] = 4
    elif dest == "s":
        stream[0] = 5
    elif dest == "N":
        stream[0] = 6
    elif dest == "f":
        stream[0] = 7
    else:
        print("Does not match dest")

    stream[1] = enc_flag
    stream[2] = len(data)%256
    stream[3] = len(data)//256

    header= np.ndarray.tobytes(stream)
    ser.write(header+data)
