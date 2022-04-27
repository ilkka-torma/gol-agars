running = 0
lock = False
#constraints = []

import copy
from pattern_basics import *


def lock_var():
    global lock
    lock = True

def reset_var():
    global lock, running
    lock = False
    running = 0

# this is just for naming our basic variables
def gen_var():
    global lock, running
    if lock:
        raise Exception("Variables are locked")
    running += 1
    return running

# nbhd is a list of basic variables with center first
def generate_gol_one(nbhd):
    center = nbhd[0]
    others = nbhd[1:]
    return AND(OR([[center]], generate_s(others, 3)),
               OR(generate_s(others, 2), generate_s(others, 3)))

def generate_gol_ker(nbhd):
    center = nbhd[0]
    others = nbhd[1:]
    #print (generate_not_s(others, 3))
    return AND(generate_not_s(others, 3), OR([[-center]], generate_not_s(others, 2)))

# 0 with NOT 3 nbrs or
# 1 with 2 nbrs or 1 with 3 nbrs
def generate_gol_ide(nbhd):
    center = nbhd[0]
    others = nbhd[1:]
    return OR(AND([[-center]], generate_not_s(others, 3)),
              AND([[center]], OR(generate_s(others, 2),
                                 generate_s(others, 3))))
    #return AND(generate_not_s(others, 3), OR([[-center]], generate_not_s(others, 2)))

# image is first, then center, then rest
def generate_gol_img(nbhd):
    img = nbhd[0]
    center = nbhd[1]
    others = nbhd[2:]
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

def local_preimage(cells, value, rule=([3], [2,3])):
    if rule != ([3], [2,3]):
        print("Bisector supports only B3/S23")
    if value:
        for clause in substi(one, cells):
            yield clause
    else:
        for clause in substi(ker, cells):
            yield clause

def local_fixp(cells, rule=([3], [2,3])):
    if rule != ([3], [2,3]):
        print("Bisector supports only B3/S23")
    for clause in substi(ide, cells):
        yield clause

def local_preimage_var(cells, var, rule=([3], [2,3])):
    if rule != ([3], [2,3]):
        print("Bisector supports only B3/S23")
    for clause in substi(img, [var]+cells):
        yield clause
