
from pysat.solvers import MinisatGH

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

def neighborhood(vec):
    "The middle cell is the first one yielded."
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

def gol_nth_preimage(pattern, temp):
    """Clauses and names for the nth preimage of a single pattern, n >= 1."""
    cells = pattern
    var_cells = set()
    for t in range(1,temp+1):
        cells = set(nbr for vec in cells for nbr in neighborhood(vec))
        var_cells |= set((i,j,t) for (i,j) in cells)
    variables = {vec : gen_var() for vec in var_cells}
    clauses = [clause
               for (vec, value) in pattern.items()
               for clause in gol_local_preimage([variables[i,j,1]
                                                 for (i,j) in neighborhood(vec)],
                                                value)]
    clauses += [clause
                for ((x,y,t), var) in variables.items()
                if t < temp
                for clause in gol_local_preimage_var([variables[i,j,t+1]
                                                      for (i,j) in neighborhood((x,y))],
                                                     var)]
    reset_var()

    ret_vars = {(x,y) : var
                for ((x,y,t), var) in variables.items()
                if t == temp}
    return clauses, ret_vars

def lex_leq(least, greaters):
    """Clauses for variable vector l being lexicographically less or equal to
        every variable vector in gs."""
    lex_vars = {}
    # define new vars lv[a,b] <=> (a == b) as needed
    for vs in greaters:
        for (i,(a,b)) in enumerate(zip(least, vs)):
            # if equal up to i, then leq at i
            clause = []
            for j in range(i):
                c, d = least[j], vs[j]
                if (c,d) not in lex_vars:
                    v = lex_vars[c,d] = gen_var()
                    yield [-v,  c, -d]
                    yield [-v, -c,  d]
                    yield [ v,  c,  d]
                    yield [ v, -c, -d]
                clause.append(-lex_vars[c,d])
            yield clause + [-a, b]

def periodic_agars(width, height, temp, xshift, yshift, period_func=None, lex_funcs=None):
    """All w x h-periodic configurations that map to (sx,sy)-translated
       versions of themselves in t steps.
       Discard those that are not lexicographically minimal in their orbit.
       period_func enforces a symmetry.
       lex_funcs modfies the lexicographical minimality check."""
    if period_func is None:
        variables = {(i,j,t) : gen_var()
                     for i in range(width)
                     for j in range(height)
                     for t in range(temp)}
        fund_domain = set((i,j) for i in range(width) for j in range(height))
    else:
        variables = dict()
        todo = set((i,j) for i in range(width) for j in range(height))
        dones = set(vec for vec in todo
                    if period_func(*vec) is None
                    or period_func(*vec) == vec
                    or period_func(*vec) not in todo)
        fund_domain = set(dones)
        for (i,j) in dones:
            for t in range(temp):
                variables[i,j,t] = gen_var()
        todo = todo - dones
        while todo:
            found = False
            for (i,j) in todo:
                x,y = period_func(i,j)
                if (x,y) in dones:
                    found = True
                    for t in range(temp):
                        variables[i,j,t] = variables[x,y,t]
                    dones.add((i,j))
            if not found:
                raise Exception("Circular dependencies")
            todo = todo - dones
            
    clauses = []
    for t in range(temp):
        for i in range(width):
            for j in range(height):
                if t == temp-1:
                    sx, sy = xshift, yshift
                else:
                    sx, sy = 0, 0
                for clause in gol_local_preimage_var([variables[x%width,y%height,t]
                                                      for (x,y) in neighborhood((i,j))],
                                                     variables[(i+sx)%width,
                                                               (j+sy)%height,
                                                               (t+1)%temp]):
                        clauses.append(clause)
    
    # Pat is lex. smallest among shifts (incl. temporal) and symmetries
    if lex_funcs is None:
        syms = [lambda x,y: (x,y),
                lambda x,y: (x, height-y-1),
                lambda x,y: (width-x-1, y),
                lambda x,y: (width-x-1, height-y-1)]
        if width == height:
            syms += [
                lambda x,y: (y,x),
                lambda x,y: (height-y-1,x),
                lambda x,y: (y,width-x-1),
                lambda x,y: (height-y-1,width-x-1)]
        base_vars = [variables[i,j,0] for i in range(width) for j in range(height)]
        other_vars = [[variables[sym((i+sx)%width,(j+sy)%height) + (t,)]
                       for i in range(width) for j in range(height)]
                      for (ns,sym) in enumerate(syms)
                      for sx in range(width)
                      for sy in range(height)
                      for t in range(1 if sx==sy==ns==0 else 0, temp)]                        
        lex_clauses = list(lex_leq(base_vars, other_vars))
    else:
        base_vars = [variables[i,j,0] for i in range(width) for j in range(height)]
        other_vars = [[variables[sym(i,j)+(t,)]
                       for i in range(width) for j in range(height)]
                      for (k,sym) in enumerate(lex_funcs)
                      for t in range(1 if k==0 else 0, temp)]
        lex_clauses = list(lex_leq(base_vars, other_vars))
    
    reset_var()
    with MinisatGH(bootstrap_with=clauses+lex_clauses) as solver:
        while solver.solve():
            model = solver.get_model()
            yield (fund_domain, model_to_pattern(model, variables))
            solver.add_clause([-model[variables[vec]] for vec in variables])

def model_to_pattern(model, names):
    "Convert a model to a pattern or orbit."
    return {vec : (0 if model[name-1] < 0 else 1) for (vec, name) in names.items()}

def mat_to_pattern(mat):
    return {(i,j) : b for (j, row) in enumerate(mat) for (i, b) in enumerate(row)}

def print_pattern(pat):
    "Print a pattern."
    if pat is None:
        print("No pattern")
    elif not pat:
        print("Empty pattern")
    else:
        minx = min(p[0] for p in pat)
        maxx = max(p[0] for p in pat)
        miny = min(p[1] for p in pat)
        maxy = max(p[1] for p in pat)
        for y in range(miny, maxy+1):
            for x in range(minx, maxx+1):
                if (x,y) in pat:
                    print(pat[x,y], end="")
                else:
                    print(" ", end="")
            print()

def print_temp_pattern(temp_pat):
    "Print an orbit."
    if temp_pat is None:
        print("No pattern")
    elif not temp_pat:
        print("Empty pattern")
    else:
        minx = min(p[0] for p in temp_pat)
        maxx = max(p[0] for p in temp_pat)
        miny = min(p[1] for p in temp_pat)
        maxy = max(p[1] for p in temp_pat)
        mint = min(p[2] for p in temp_pat)
        maxt = max(p[2] for p in temp_pat)
        for t in range(mint, maxt+1):
            for y in range(miny, maxy+1):
                for x in range(minx, maxx+1):
                    if (x,y,t) in temp_pat:
                        print(temp_pat[x,y,t], end="")
                    else:
                        print(" ", end="")
                print()
            if t < maxt:
                print("-->")

def has_unique_periodic_orbit(temp_pat, width, height, temp, xper, yper):
    "Does each configuration in this orbit have a unique w*xp × h*yp -periodic preimage?"
    for t in range(temp):
        variables = {(i,j) : gen_var()
                     for i in range(xper*width)
                     for j in range(yper*height)}
        clauses = [clause
                   for (i,j) in variables
                   for clause in gol_local_preimage([variables[x%(xper*width),y%(yper*height)]
                                                     for (x,y) in neighborhood((i,j))],
                                                    temp_pat[i%width,j%height,t])]
        
        # force lexicographic minimality among shifts along periods
        base_vars = [variables[i,j] for i in range(width) for j in range(height)]
        other_vars = [[variables[i+x*width,j+y*height] for i in range(width) for j in range(height)]
                      for x in range(xper)
                      for y in range(1 if x==0 else 0, yper)]
        lex_clauses = list(lex_leq(base_vars, other_vars))
        
        reset_var()
        with MinisatGH(bootstrap_with=clauses+lex_clauses) as solver:
            solver.solve()
            first = model_to_pattern(solver.get_model(), variables)
            solver.add_clause([(-1 if first[vec] else 1)*variables[vec] for vec in first])
            if solver.solve():
                return False
    return True

def has_unique_extended_orbit(temp_pat, width, height, temp, padcol, padrow, to_force=None):
    """Does each configuration in this orbit have a unique w×h-patch in the preimage
       if it's continued periodically for the given number of rows and columns?"""
    if to_force is None:
        to_force = set((i,j) for i in range(width) for j in range(height))
        min_x = min_y = 0
        max_x = width-1
        max_y = height-1
    else:
        min_x = min(x for (x,_) in to_force)
        max_x = max(x for (x,_) in to_force)
        min_y = min(y for (_,y) in to_force)
        max_y = max(y for (_,y) in to_force)
    for t in range(temp):
        tiled = {(i,j) : temp_pat[i%width,j%height,t]
                 for i in range(min_x-padcol,max_x+padcol+1)
                 for j in range(min_y-padrow,max_y+padrow+1)}
        clauses, variables = gol_nth_preimage(tiled, 1)
        with MinisatGH(bootstrap_with=clauses) as solver:
            solver.solve()
            first = model_to_pattern(solver.get_model(), variables)
            solver.add_clause([(-1 if first[vec] else 1)*variables[vec]
                               for vec in to_force])
            if solver.solve():
                return False
    return True

def find_ragas(width, height, temp, padcol, padrow, xshift, yshift, period_func=lambda x,y: None, lex_funcs=None):
    """Search for self-forcing agars of given spatial and temporal periods."""
    n = 0
    print("Checking {}x{}x{}-periodic points with shift ({},{})".format(width, height, temp, xshift, yshift))
    candidates = []
    for (domain, temp_pat) in periodic_agars(width, height, temp, xshift, yshift, period_func, lex_funcs):
        to_force = domain
        if temp == 1 or any(temp_pat[i,j,t] != temp_pat[i,j,(t+1)%temp]
                            for i in range(width) for j in range(height) for t in range(temp)):
            print("Testing pattern")
            print_temp_pattern(temp_pat)
            if has_unique_periodic_orbit(temp_pat, width, height, temp, 1, 1):
                print("Qualified")
                candidates.append(temp_pat)
            n += 1
            if n%250 == 0:
                print("Checked", n, "orbits,", len(candidates), "passed")
    i = 1
    g = 0
    while candidates:
        print("Round {}: {}/{} orbits remain".format(i, len(candidates), n))
        news = []
        for (m, temp_pat) in enumerate(candidates):
            print("Testing pattern {}/{}".format(m+1, len(candidates)))
            print_temp_pattern(temp_pat)
            if has_unique_extended_orbit(temp_pat, width, height, temp, i*padcol, i*padrow, to_force=to_force):
                g += 1
                print("It forced itself! ({} so far)".format(g))
                yield (temp_pat, i*padcol, i*padrow)
                continue
            print("It didn't yet force itself")
            for (a,b) in [(i,i+1),(i,i+2),(i+1,i+1)]:
                if not has_unique_periodic_orbit(temp_pat, width, height, temp, a, b):
                    print("Found periodic preimage, discarded")
                    break
            else:
                print("No periodic preimage found")
                news.append(temp_pat)
        candidates = news
        i += 1

def common_forced_part(pats, temp, return_pat=False):
    """Compute the set of cells that all patterns force in their nth preimages.
       Return None if any of the patterns have no nth preimage."""
    # Assume pats have common domain
    domain = set(pats[0])
    pre_domain = domain
    for t in range(temp):
        pre_domain = set(nbr for vec in pre_domain for nbr in neighborhood(vec))
    maybe_forced = set(pre_domain)
    for (k, pat) in enumerate(pats):
        if len(pats) > 1:
            print("Pattern {}/{}, {} cells potentially forced".format(k+1, len(pats), len(maybe_forced)))
        clauses, variables = gol_nth_preimage(pat, temp)
        with MinisatGH(bootstrap_with=clauses) as solver:
            i = 0
            while solver.solve():
                i += 1
                if i == 1:
                    # Get initial preimage
                    pre = model_to_pattern(solver.get_model(), variables)
                else:
                    new = model_to_pattern(solver.get_model(), variables)
                    maybe_forced -= set(vec for vec in new if new[vec] != pre[vec])
                solver.add_clause([(-1 if pre[vec] else 1)*variables[vec]
                                   for vec in maybe_forced])
            if i == 0:
                # No preimages exist
                return None
    if return_pat:
        return {vec: (1 if vec in domain else '+') if vec in maybe_forced else (0 if vec in domain else '.')
                for vec in pre_domain}
    else:
        return maybe_forced

def find_self_forcing(pat, temp, shift=(0,0)):
    """Find the maximal nonempty subpattern that forces itself in its nth preimages.
       If pat is a nth-generation orphan, return None."""
    sx, sy = shift
    while True:
        fp = common_forced_part([pat], temp)
        if fp is None:
            return None
        print("Now forcing", len(fp), "cells")
        if any(vec not in fp for vec in pat):
            pat = {(x,y):val for ((x,y),val) in pat.items() if (x-sx,y-sy) in fp}
            if not pat:
                return pat
        else:
            return pat
        
if __name__ == "__main__":
    ragas = []
    # dimensions of periodic orbit
    width, height, temp = 6, 4, 2
    # speed of increasing extra rows and columns
    padrow, padcol = 3, 3
    # the orbit can also be shift-periodic
    xshift, yshift = 0, 0
    # let's also find out if a 50x50 patch contains a self-forcing pattern
    check_forcing = True
    tot_width, tot_height = 50, 50
    for (raga,pc,pr) in find_ragas(width, height, temp, padrow, padcol, xshift, yshift):
        ragas.append(raga)
        if check_forcing:
            print("Computing maximal self-forcing patch")
            large_patch = {(x,y):raga[x%width,y%height,0]
                           for x in range(tot_width)
                           for y in range(tot_height)}
            sf = find_self_forcing(large_patch, temp, return_pat=True)
            if sf is not None:
                print("Self-forcing patch found!")
                print_temp
        with open("output.txt",'a') as f:
            f.write("{} {} {} {} {} ".format(width,height,temp,pc,pr,0 if sf is None else 1))
            f.write(str(raga))
            f.write("\n")
    print("Done, found", len(ragas))
