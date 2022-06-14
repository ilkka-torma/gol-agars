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

def merge_into(l1, l2, lm):
    """Constraints for merging two sorted lists of variables.
       assume len(list1) == len(list2) == len(merged)/2.
       merged may contain Nones."""
    L = len(l1)
    assert L == len(l2)
    assert 2*L == len(lm)
    for k in range(2*L):
        if k < L:
            if lm[k] is not None:
                yield [-l1[k], lm[k]]
                yield [-l2[k], lm[k]]
            if lm[2*L-1-k] is not None:
                yield [l1[L-1-k], -lm[2*L-1-k]]
                yield [l2[L-1-k], -lm[2*L-1-k]]
        for i in range(L):
            j = k-i-1
            if 0 <= j < L:
                if lm[k] is not None:
                    yield [-l1[i], -l2[j], lm[k]]
                if lm[2*L-1-k] is not None:
                    yield [l1[L-1-i], l2[L-1-j], -lm[2*L-1-k]]

def sort_eight(inputs, outputs):
    """Generator for clauses in partial totalizer sorter.
       inputs: list of 8 variables
       outputs: dict from subset of range(8) to variables"""
    global SHARED
    
    #v = inputs + [gen_var() for _ in range(29)] + outputs + [None]
    #print("Network vars", v)

    # Higher values go up
    #   1   2   3
    # v0-v8--v16-v24
    #   |   |   |
    # v1-v9-+v17+v25
    #       |   |
    # v2-v10+v18+v26
    #   |   |   |
    # v3-v11-v19+v27
    #           |
    # v4-v12-v20+v28
    #   |   |   |
    # v5-v13+v21+v29
    #       |   |
    # v6-v14+v22+v30
    #   |   |   |
    # v7-v15-v23-v31

    v = inputs + [None for _ in range(16)] + [outputs.get(i+1, None) for i in range(8)]
    gates = [([0],[1],[8,9]), ([2],[3],[10,11]), ([4],[5],[12,13]), ([6],[7],[14,15]),
             ([8,9],[10,11],[16,17,18,19]), ([12,13],[14,15],[20,21,22,23]),
             ([16,17,18,19],[20,21,22,23],[24,25,26,27,28,29,30,31])]
    # Check shared variables
    for (l1, l2, lm) in gates:
        inputs = tuple(sorted(tuple(v[i] for i in l) for l in [l1,l2]))
        try:
            #assert False
            assert all(x is not None for lst in inputs for x in lst)
            for (i, var) in zip(lm, SHARED[inputs]):
                v[i] = var
        except (AssertionError,KeyError):
            for i in lm:
                if i < 24:
                    v[i] = gen_var()
            vlm = SHARED[inputs] = [v[i] for i in lm]
            for clause in merge_into([v[i] for i in l1], [v[i] for i in l2], vlm):
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
