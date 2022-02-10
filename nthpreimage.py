vrs = {} #[0]
running = 1
#constraints = []

import sys
import pycosat
#import GoLGoETools
import time
import random
import copy
import math
from pattern_basics import *

lock = [False]
def lock_names():
    lock[0] = True

def reset():
    lock[0] = False
    global vrs, running
    vrs = {}
    running = 1

# this is just for naming our basic variables
def name_basic(o):
    global vrs, running
    if o not in vrs:
        if lock[0]:
            print(o)
            a = bbb
        vrs[o] = running
        running += 1
    return vrs[o]

# nbhd is a list of basic variables
def generate_gol_one(nbhd):
    center = nbhd[4]
    others = nbhd[:4] + nbhd[5:]
    return AND(OR([[center]], generate_s(others, 3)),
               OR(generate_s(others, 2), generate_s(others, 3)))

def generate_gol_ker(nbhd):
    center = nbhd[4]
    others = nbhd[:4] + nbhd[5:]
    #print (generate_not_s(others, 3))
    return AND(generate_not_s(others, 3), OR([[-center]], generate_not_s(others, 2)))

# 0 with NOT 3 nbrs or
# 1 with 2 nbrs or 1 with 3 nbrs
def generate_gol_ide(nbhd):
    center = nbhd[4]
    others = nbhd[:4] + nbhd[5:]
    return OR(AND([[-center]], generate_not_s(others, 3)),
              AND([[center]], OR(generate_s(others, 2),
                                 generate_s(others, 3))))
    #return AND(generate_not_s(others, 3), OR([[-center]], generate_not_s(others, 2)))

def generate_gol_img(nbhd):
    img = nbhd[0]
    center = nbhd[5]
    others = nbhd[1:5] + nbhd[6:]
    return OR(OR(AND([[img], [center]], OR(generate_s(others, 2),
                                         generate_s(others, 3))),
                 AND([[img], [-center]], generate_s(others, 3))),
              OR(AND([[-img], [center]], OR(generate_leq_s(others, 1),
                                          generate_geq_s(others, 4))),
                 AND([[-img], [-center]], generate_not_s(others, 3))))

def generate_s(V, n):
    if n == 0:
        return list([-v] for v in V)
    if len(V) < n:
        return [[]]
    if len(V) == n:
        return list([v] for v in V)
    left = V[:len(V)//2]
    right = V[len(V)//2:]
    inst = [[]]
    for i in range(0, n+1):
        inst = OR(inst, AND(generate_s(left, i), generate_s(right, n-i)))
    return inst

def generate_geq_s(V, n):
    #print (V, n)
    if n == 0:
        #print (V, n, [])
        return []
    if len(V) < n:
        #print (V, n, [[]])
        return [[]]
    if len(V) == n:
        #print (V, n, list([v] for v in V))
        return list([v] for v in V)
    left = V[:len(V)//2]
    right = V[len(V)//2:]
    inst = [[]]
    for i in range(0, n+1):
        inst = OR(inst, AND(generate_geq_s(left, i), generate_geq_s(right, n-i)))
    #print (V, n, inst)
    return inst

def generate_leq_s(V, n):
    #print (V, n)
    if n == 0:
        return list([[-v] for v in V])
    if len(V) <= n:
        return []
    left = V[:len(V)//2]
    right = V[len(V)//2:]
    inst = [[]]
    for i in range(0, n+1):
        inst = OR(inst, AND(generate_leq_s(left, i), generate_leq_s(right, n-i)))
    return inst

def generate_not_s(V, n):
    if n == 0:
        return [V]
    if len(V) < n:
        return []
    if len(V) == n:
        return [list(-v for v in V)]
    inst = [[]]
    for i in range(0, n):
        #print (i)
        #print ( generate_s(V, i))
        #print ( "ij", inst, OR(inst, generate_s(V, i)))
        inst = OR(inst, generate_s(V, i))
    #print ("jyg", generate_geq_s(V, n+1))
    inst = OR(inst, generate_geq_s(V, n+1))
    return inst

def simplify(L):
    L = list(map(list, set(map(frozenset, L)))) # absolute lol
    LL = []
    for a in L:
        if len(set(map(abs, a))) != len(a): # automatically true then...
            continue
        LL.append(a)
    LLL = []
    for a in LL:
        for b in LL:
            if a == b:
                continue
            if set(b).issubset(set(a)):
                break
        else:
            LLL.append(a)
    return LLL

# and of two cnfs...
def AND(a, b):
    return simplify(a + b)

def OR(a, b):
    r = []
    for ai in a:
        for bi in b:
            r.append(ai + bi)
    return simplify(r)

def check(cnf, vals):
    for c in cnf:
        for a in c:
            if a < 0 and vals[-a-1] == 0 or a > 0 and vals[a-1] == 1:
                break
        else:
            return False
    return True

# 1,2,... replaced by names
def substi(cnf, names):
    newcnf = []
    for l in cnf:
        newcnf.append([])
        for i in l:
            if i > 0:
                newcnf[-1].append(names[i-1])
            else:
                newcnf[-1].append(-names[-i-1])
    return newcnf

one = generate_gol_one([1,2,3,4,5,6,7,8,9])
ker = generate_gol_ker([1,2,3,4,5,6,7,8,9])
ide = generate_gol_ide([1,2,3,4,5,6,7,8,9])
img = generate_gol_img([1,2,3,4,5,6,7,8,9,10])

def gol_preimage(pat, iterations=1):
    reset()
    inst = []
    minx, maxx, miny, maxy = extent(pat)
    for p in pat:
        x,y = p
        if iterations == 1:
            iext = ()
        else:
            iext = (1,)
        imv = name_basic((x, y) + iext)
        v00 = name_basic((x-1, y-1) + iext)
        v01 = name_basic((x-1, y) + iext)
        v02 = name_basic((x-1, y+1) + iext)
        v10 = name_basic((x, y-1) + iext)
        v11 = name_basic((x, y) + iext)
        v12 = name_basic((x, y+1) + iext)
        v20 = name_basic((x+1, y-1) + iext)
        v21 = name_basic((x+1, y) + iext)
        v22 = name_basic((x+1, y+1) + iext)
        nbhd = [v00, v01, v02, v10, v11, v12, v20, v21, v22]
        if pat[p] == 1:
            inst.extend(substi(one, nbhd))
        if pat[p] == 0:
            inst.extend(substi(ker, nbhd))
    # if iterations = 2 then we'll just have 2
    for i in range(2, iterations+1):
        for x in range(minx-i+1, maxx+i):
            for y in range(miny-i+1, maxy+i):
                imv = name_basic((x, y, i-1))
                if i == iterations:
                     iext = ()
                else:
                    iext = (i,)
                v00 = name_basic((x-1, y-1) + iext)
                v01 = name_basic((x-1, y) + iext)
                v02 = name_basic((x-1, y+1) + iext)
                v10 = name_basic((x, y-1) + iext)
                v11 = name_basic((x, y) + iext)
                v12 = name_basic((x, y+1) + iext)
                v20 = name_basic((x+1, y-1) + iext)
                v21 = name_basic((x+1, y) + iext)
                v22 = name_basic((x+1, y+1) + iext)
                nbhd = [imv, v00, v01, v02, v10, v11, v12, v20, v21, v22]
                inst.extend(substi(img, nbhd))
    lock_names()
    return inst, vrs

def neighborhood(vec, iterations=1):
    if iterations == 1:
        yield vec
        x, y = vec
        yield (x-1,y-1)
        yield (x,y-1)
        yield (x+1,y-1)
        yield (x-1,y)
        yield (x+1,y)
        yield (x-1,y+1)
        yield (x,y+1)
        yield (x+1,y+1)
    else:
        for x in range(vec[0]-iterations, vec[0]+iterations+1):
            for y in range(vec[1]-iterations, vec[1]+iterations+1):
                yield (x,y)

# could be in pattern_basics but specific to SAT solving anyway
def model_to_pattern(model, variables):
    return {vec : (0 if model[name-1] < 0 else 1) for (vec, name) in variables.items() if len(vec) == 2}




