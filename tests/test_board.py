#! /usr/bin/python3
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

import sys
sys.path.insert(0,'interface/')
from parameters import *
import spook
import os
from SpookTopLevel import SpookTopLevel,mask,send_data_uart
import numpy as np

spookDUT = SpookTopLevel(target="MCU",PORT="/dev/ttyUSB0")

def test_spook_lwc(ad, m, k, n, c):
    p = k[16:]
    k = k[:16]
    print('AD', ad)
    print('M', m)
    print('k', k)
    print('p', p)
    print('n', n)
    print('c', c)
    if len(m)<4 or len(ad)<4:
        return

    mk = mask(k,D)
    s = os.urandom(16)
    print(s)
    spookDUT.set_data(s,dest="s",enc_flag=0)
    c2 = spookDUT.encrypt_key(ad,m,mk,n)
    print("received ciphertext")
    print(c2)
    mk = mask(k,D)
    m2 = spookDUT.decrypt_key(ad,c,mk,n)
    print("received plaintext")
    print(m2)

    assert m2 == m, 'wrong inverse {} {}'.format(m, m2)
    assert c2 == c, 'not matching TV {} {}'.format(c, c2)

def fh(x):
    return bytes.fromhex(x)

def dec_tv_file(s):
    return [
            (d['AD'], d['PT'], d['Key'], d['Nonce'], d['CT'])
            for d in (dict((k, fh(v))
                for k, _, v in (y.split(' ') for y in x.split('\n')) if k != 'Count')
                for x in s.strip().split('\n\n'))
            ]

def test_tv_file(fname):
    tvs = dec_tv_file(open(fname).read())
    for i, tv in enumerate(tvs):
        print('TV', i)
        test_spook_lwc(*tv)

if __name__ == '__main__':
    spook.SMALL_PERM=False
    test_tv_file('tests/LWC_AEAD_KAT_128_128.txt')
