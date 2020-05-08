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


import os
import numpy as np
#####
##### define the number of cycles for each number of shares
D = np.array([3,4,6,8])
N_cycles = np.zeros(len(D),dtype=int)
N_cycles[0] = 5000
N_cycles[1] = 8000
N_cycles[2] = 15000
N_cycles[3] = 25000
Nm_p = 10000
Nm_p_w = 2000
Nm_a = 10000

N_warmup = 1
N_per_attack = 10
N_attacks = 1
N_profile = 10

for i,d in enumerate(D):

    if d != 2 and d!= 3:
        continue

    os.system("make D=%d USE_ASM=1 ROUNDREDUCED=1 board burn"%(d))
    if d == 4 or d == 2:
        DIR = "d%d/"%(d)
    else:
        DIR = "/run/media/obronchain/Transcend/sw_ctf/d%d/"%(d)
    os.system("rm -rf "+DIR)
    os.system("mkdir -p "+DIR)
    os.system("cp -r build "+DIR)


    DIR_R = DIR+"/random_key/"
    os.system(" mkdir -p "+DIR_R)
    for j in range(N_profile):
        for _ in range(N_warmup):
            os.system("python36 capture/capture.py -b 500 -n %d -k 0 -c %d -f tmp.npz"%(Nm_p_w,N_cycles[i]))

        file_name = DIR_R+"/rkey_D%d_%d.npz"%(d,j)
        os.system("python36 capture/capture.py -b 500 -n %d -k 0 -c %d -f %s"%(Nm_p,N_cycles[i],file_name))

    DIR_F = DIR+"/fixed_key/"
    os.system("mkdir -p "+(DIR_F))
    for a in range(N_attacks):
        DIR_F_i = DIR_F+"/key_%d/"%(a)
        os.system("mkdir -p "+(DIR_F_i))
        secret_key = np.random.randint(0,2**32,4).astype(np.uint32)
        np.savez("secret_key.npz",secret_key=secret_key)
        for j in range(N_per_attack):
            file_name = DIR_F_i+"/fkey_D%d_%d.npz"%(d,j)
            for _ in range(N_warmup):
                os.system("python36 capture/capture.py -b 500 -n %d -k 0 -c %d -f tmp.npz"%(Nm_p_w,N_cycles[i]))

            os.system("python36 capture/capture.py -b 500 -n %d -k 1 -c %d -f %s"%(Nm_p,
                N_cycles[i],file_name))
        os.system("mv secret_key.npz "+DIR_F_i)
