from pattern_basics import *

VARIABLE = 0
SHARED = {}

def gen_var():
    "Returns a fresh odd positive integer"
    global VARIABLE
    VARIABLE += 1
    return VARIABLE

def reset_var():
    global VARIABLE, SHARED
    VARIABLE = 0
    SHARED = {}

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

def sort_eight(inputs, outputs):
    """Generator for clauses in partial odd-even mergesort network.
       inputs: list of 8 variables
       outputs: dict from subset of range(8) to variables"""
    global SHARED
    
    #v = inputs + [gen_var() for _ in range(29)] + outputs + [None]
    #print("Network vars", v)

    # Higher values go up
    #   1   2       3   4               5       6
    # v0-v8--v16---------------------------------v38
    #   |   |           |
    # v1-v9-|----v20-v24|----v29-----------------v39
    #       |   |   |   |   |                   |
    # v2-v10-v17|----v25|---|----v31-----v34-----v40
    #   |       |       |   |   |       |
    # v3-v11-----v21----|---|---|----v33|----v36-v41
    #                   |   |   |   |   |   |   |
    # v4-v12-v18---------v28|---|---|----v35|----v42
    #   |   |               |   |   |       |
    # v5-v13|----v22-v26-----v30|---|--------v37-v43
    #       |   |   |           |   |           |
    # v6-v14-v19|----v27---------v32|------------v44
    #   |       |                   |
    # v7-v15-----v23-----------------------------v45

    v = inputs + [None for _ in range(30)] + [outputs.get(i+1, None) for i in range(8)]
    gates = [(0,1,8,9), (2,3,10,11), (4,5,12,13), (6,7,14,15),
             (8,10,16,17), (9,11,20,21), (12,14,18,19), (13,15,22,23),
             (20,17,24,25), (22,19,26,27),
             (16,18,38,28), (24,26,29,30), (25,27,31,32), (21,23,33,45),
             (31,28,34,35), (33,30,36,37),
             (29,34,39,40), (36,35,41,42), (37,32,43,44)]
    # Check shared variables
    for (a,b,c,d) in gates:
        va, vb = v[a], v[b]
        if va is not None and vb is not None:
            va, vb = list(sorted([v[a], v[b]]))
            try:
                v[c] = SHARED[va, vb, 0]
            except KeyError:
                pass
            try:
                v[d] = SHARED[va, vb, 1]
            except KeyError:
                pass
    # Process gates in reverse order of depth, propagating non-Noneness
    for (a,b,c,d) in reversed(gates):
        if v[c] is not None or v[d] is not None:
            if v[a] is None:
                v[a] = gen_var()
            if v[b] is None:
                v[b] = gen_var()
            va, vb = list(sorted([v[a], v[b]]))
            compute = False
            if (va, vb, 0) not in SHARED and v[c] is not None:
                SHARED[va, vb, 0] = v[c]
                compute = True
            if (va, vb, 1) not in SHARED and v[d] is not None:
                SHARED[va, vb, 1] = v[d]
                compute = True
            if compute:
                for clause in sort_pair(v[a], v[b], v[c], v[d]):
                    yield clause

def intervals(lst):
    "Intervals in [0..8] based on membership in lst"
    ret = []
    bot = 0
    elem = bot in lst
    for i in range(1,9):
        if elem != (i in lst):
            ret.append((bot,i-1,elem))
            elem = i in lst
            bot = i
    ret.append((bot,8,elem))
    return ret

def local_preimage_var(cells, img, rule=([3],[2,3])):
    "Clauses for the local rule evaluating to a given variable."
    
    birth = intervals(rule[0])
    survive = intervals(rule[1])
    #print(birth, survive)
    
    count_vars = {}
    for (bot,top,_) in birth+survive:
        if bot > 0 and bot not in count_vars:
            count_vars[bot] = gen_var()
        if top < 8 and top+1 not in count_vars:
            count_vars[top+1] = gen_var()
    #print(count_vars)
    
    for clause in sort_eight(cells[1:], count_vars):
        yield clause
        
    cur = cells[0]
    for (bot, top, born) in birth:
        # cur is dead
        sign = 1 if born else -1
        if bot > 0 and top < 8:
            yield [cur, -count_vars[bot], count_vars[top+1], sign*img]
        elif bot > 0:
            yield [cur, -count_vars[bot], sign*img]
        elif top < 8:
            yield [cur, count_vars[top+1], sign*img]
        else:
            yield [cur, sign*img]
    for (bot, top, surv) in survive:
        # cur is alive
        sign = 1 if surv else -1
        if bot > 0 and top < 8:
            #print([-cur, -count_vars[bot], count_vars[top+1], sign*img])
            yield [-cur, -count_vars[bot], count_vars[top+1], sign*img]
        elif bot > 0:
            #print([-cur, -count_vars[bot], sign*img])
            yield [-cur, -count_vars[bot], sign*img]
        elif top < 8:
            #print([-cur, count_vars[top+1], sign*img])
            yield [-cur, count_vars[top+1], sign*img]
        else:
            yield [-cur, sign*img]


def local_fixp(cells, rule=([3],[2,3])):
    "Clauses for the local rule evaluating to the middle cell."
    for clause in local_perimage_var(cells, cells[0], rule):
        yield clause

def local_preimage(cells, val, rule=([3],[2,3])):
    "Clauses for the local rule evaluating to a given fixed value."

    birth = intervals(rule[0])
    survive = intervals(rule[1])
    
    count_vars = {}
    for (bot,top,_) in birth+survive:
        if bot > 0 and bot not in count_vars:
            count_vars[bot] = gen_var()
        if top < 8 and top+1 not in count_vars:
            count_vars[top+1] = gen_var()
    
    for clause in sort_eight(cells[1:], count_vars):
        yield clause
        
    cur = cells[0]
    for (bot, top, born) in birth:
        # cur is dead
        if int(born) != val:
            if bot > 0 and top < 8:
                yield [cur, -count_vars[bot], count_vars[top+1]]
            elif bot > 0:
                yield [cur, -count_vars[bot]]
            elif top < 8:
                yield [cur, count_vars[top+1]]
            else:
                yield [cur]
    for (bot, top, surv) in survive:
        # cur is alive
        if int(surv) != val:
            if bot > 0 and top < 8:
                yield [-cur, -count_vars[bot], count_vars[top+1]]
            elif bot > 0:
                yield [-cur, -count_vars[bot]]
            elif top < 8:
                yield [-cur, count_vars[top+1]]
            else:
                yield [-cur]
