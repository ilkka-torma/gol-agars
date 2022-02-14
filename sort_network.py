from pattern_basics import *

VARIABLE = 0

def gen_var():
    "Returns a fresh odd positive integer"
    global VARIABLE
    VARIABLE += 1
    return VARIABLE

def reset_var():
    global VARIABLE
    VARIABLE = 0

def sort_pair(x, y, p, q):
    "Constraints for p = max(x,y), q = min(x,y), if not None"
    # p = x OR y
    if p is not None:
        yield [x, y, -p]
        yield [-x, p]
        yield [-y, p]
    # q = x AND y
    if q is not None:
        yield [-x, -y, q]
        yield [x, -q]
        yield [y, -q]

def sort_eight_three(inputs, outputs):
    "Partial odd-even mergesort network"

    v = inputs + [gen_var() for _ in range(29)] + outputs + [None]
    #print("Network vars", v)

    # Higher values go up
    # v0-v8--v16---------N
    #   |   |           |
    # v1-v9-|----v20-v24|----v29-----------------v37
    #       |   |   |   |   |                   |
    # v2-v10-v17|----v25|---|----v31-----v34-----v38
    #   |       |       |   |   |       |
    # v3-v11-----v21----|---|---|----v33|----v36-v39
    #                   |   |   |   |   |   |   |
    # v4-v12-v18---------v28|---|---|----v35|----N
    #   |   |               |   |   |       |
    # v5-v13|----v22-v26-----v30|---|--------N---N
    #       |   |   |           |   |           |
    # v6-v14-v19|----v27---------v32|------------N
    #   |       |                   |
    # v7-v15-----v23-----------------N

    for (a,b,c,d) in [(0,1,8,9), (2,3,10,11), (4,5,12,13), (6,7,14,15),
                      (8,10,16,17), (12,14,18,19), (9,11,20,21), (13,15,22,23),
                      (20,17,24,25), (22,19,26,27),
                      (16,18,-1,28), (24,26,29,30), (25,27,31,32), (21,23,33,-1),
                      (31,28,34,35), (33,30,36,-1),
                      (29,34,37,38), (36,35,39,-1)]:
        for clause in sort_pair(v[a], v[b], v[c], v[d]):
            yield clause

def gol_local_preimage(cells, value):
    "Clauses for the local rule evaluating to a given value."
    n2, n3, n4 = gen_var(), gen_var(), gen_var()
    for clause in sort_eight_three(cells[1:], [n2, n3, n4]):
        yield clause
    c = cells[0]
    if value:
        yield [n2] # At least 2
        yield [-n4] # At most 3
        yield [c, n3] # If c==0, at least 3
    else:
        yield [-n3, n4] # Not exactly 3
        yield [-c, -n2, n3] # If c==1, not exactly 2

def gol_local_fixp(cells):
    "Clauses for the local rule evaluating to the middle cell."
    n2, n3, n4 = gen_var(), gen_var(), gen_var()
    for clause in sort_eight_three(cells[1:], [n2, n3, n4]):
        yield clause
    c = cells[0]
    yield [c, -n3, n4] # If c==0, not exactly 3
    yield [-c, n2] # If c==1, at least 2
    yield [-c, -n4] # If c==1, at most 3

def gol_local_preimage_var(cells, b):
    "Clauses for the local rule evaluating to a given variable."
    n2, n3, n4 = gen_var(), gen_var(), gen_var()
    for clause in sort_eight_three(cells[1:], [n2, n3, n4]):
        yield clause
    c = cells[0]
    # If b is live
    yield [-b, n2] # At least 2
    yield [-b, -n4] # At most 3
    yield [-b, c, n3] # If c==0, at least 3
    # If b is dead
    yield [b, -n3, n4] # Not exactly 3
    yield [b, -c, -n2, n3] # If c==1, not exactly 2
