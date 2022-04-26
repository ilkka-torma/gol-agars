
from pysat.solvers import MinisatGH
from pattern_basics import *
import bisector
import sort_network

def gol_nth_preimage(pattern, temp, instance="sort_network"):
    """Clauses and names for the nth preimage of a single pattern, n >= 1."""
    if instance == "sort_network":
        mod = sort_network
    elif instance == "bisector":
        mod = bisector
    cells = pattern
    var_cells = set()
    for t in range(1,temp+1):
        cells = set(nbr for vec in cells for nbr in neighborhood(vec))
        var_cells |= set((i,j,t) for (i,j) in cells)
    variables = {vec : mod.gen_var() for vec in var_cells}
    clauses = [clause
               for (vec, value) in pattern.items()
               for clause in mod.gol_local_preimage([variables[i,j,1]
                                                     for (i,j) in neighborhood(vec)],
                                                    value)]
    clauses += [clause
                for ((x,y,t), var) in variables.items()
                if t < temp
                for clause in mod.gol_local_preimage_var([variables[i,j,t+1]
                                                          for (i,j) in neighborhood((x,y))],
                                                         var)]
    mod.reset_var()

    ret_vars = {(x,y) : var
                for ((x,y,t), var) in variables.items()
                if t == temp}
    return clauses, ret_vars

def lex_leq(least, greaters, instance="sort_network"):
    """Clauses for variable vector l being lexicographically less or equal to
        every variable vector in gs."""
    if instance == "sort_network":
        mod = sort_network
    elif instance == "bisector":
        mod = bisector
    lex_vars = {}
    # define new vars lv[a,b] <=> (a == b) as needed
    for vs in greaters:
        for (i,(a,b)) in enumerate(zip(least, vs)):
            # if equal up to i, then leq at i
            clause = []
            for j in range(i):
                c, d = least[j], vs[j]
                if (c,d) not in lex_vars:
                    v = lex_vars[c,d] = mod.gen_var()
                    yield [-v,  c, -d]
                    yield [-v, -c,  d]
                    yield [ v,  c,  d]
                    yield [ v, -c, -d]
                clause.append(-lex_vars[c,d])
            yield clause + [-a, b]

def periodic_agars(width, height, temp, xshift, yshift, period_func=None, lex_funcs=None, instance="sort_network"):
    """All w x h-periodic configurations that map to (sx,sy)-translated
       versions of themselves in t steps.
       Discard those that are not lexicographically minimal in their orbit.
       period_func enforces a symmetry.
       lex_funcs modfies the lexicographical minimality check."""
    if instance == "sort_network":
        mod = sort_network
    elif instance == "bisector":
        mod = bisector
    if period_func is None:
        variables = {(i,j,t) : mod.gen_var()
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
                variables[i,j,t] = mod.gen_var()
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
                for clause in mod.gol_local_preimage_var([variables[x%width,y%height,t]
                                                          for (x,y) in neighborhood((i,j))],
                                                         variables[(i+sx)%width,
                                                                   (j+sy)%height,
                                                                   (t+1)%temp]):
                        clauses.append(clause)
    
    # Pat is lex. smallest among shifts (incl. temporal) and symmetries
    if lex_funcs is None:
        if xshift == yshift == 0:
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
        else:
            syms = [lambda x,y: (x,y)]
        base_vars = [variables[i,j,0] for i in range(width) for j in range(height)]
        other_vars = [[variables[sym((i+sx)%width,(j+sy)%height) + (t,)]
                       for i in range(width) for j in range(height)]
                      for (ns,sym) in enumerate(syms)
                      for sx in range(width)
                      for sy in range(height)
                      for t in range(1 if sx==sy==ns==0 else 0, temp)]                        
        lex_clauses = list(lex_leq(base_vars, other_vars, instance=instance))
    else:
        base_vars = [variables[i,j,0] for i in range(width) for j in range(height)]
        other_vars = [[variables[sym(i,j)+(t,)]
                       for i in range(width) for j in range(height)]
                      for (k,sym) in enumerate(lex_funcs)
                      for t in range(1 if k==0 else 0, temp)]
        lex_clauses = list(lex_leq(base_vars, other_vars, instance=instance))
    
    mod.reset_var()
    with MinisatGH(bootstrap_with=clauses+lex_clauses) as solver:
        while solver.solve():
            model = solver.get_model()
            yield (fund_domain, model_to_pattern(model, variables))
            solver.add_clause([-model[variables[vec]-1] for vec in variables])

def model_to_pattern(model, names):
    "Convert a model to a pattern or orbit."
    return {vec : (0 if model[name-1] < 0 else 1) for (vec, name) in names.items()}

def has_unique_periodic_orbit(temp_pat, width, height, temp, xper, yper, instance="sort_network"):
    "Does each configuration in this orbit have a unique w*xp × h*yp -periodic preimage?"
    if instance == "sort_network":
        mod = sort_network
    elif instance == "bisector":
        mod = bisector
    for t in range(temp):
        variables = {(i,j) : mod.gen_var()
                     for i in range(xper*width)
                     for j in range(yper*height)}
        clauses = [clause
                   for (i,j) in variables
                   for clause in mod.gol_local_preimage([variables[x%(xper*width),y%(yper*height)]
                                                         for (x,y) in neighborhood((i,j))],
                                                        temp_pat[i%width,j%height,t])]
        
        # force lexicographic minimality among shifts along periods
        base_vars = [variables[i,j] for i in range(width) for j in range(height)]
        other_vars = [[variables[i+x*width,j+y*height] for i in range(width) for j in range(height)]
                      for x in range(xper)
                      for y in range(1 if x==0 else 0, yper)]
        lex_clauses = list(lex_leq(base_vars, other_vars, instance=instance))
        
        mod.reset_var()
        with MinisatGH(bootstrap_with=clauses+lex_clauses) as solver:
            solver.solve()
            first = model_to_pattern(solver.get_model(), variables)
            solver.add_clause([(-1 if first[vec] else 1)*variables[vec] for vec in first])
            if solver.solve():
                return False
    return True

def has_unique_extended_orbit(temp_pat, width, height, temp, padcol, padrow, to_force=None, instance="sort_network"):
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
        clauses, variables = gol_nth_preimage(tiled, 1, instance=instance)
        with MinisatGH(bootstrap_with=clauses) as solver:
            solver.solve()
            first = model_to_pattern(solver.get_model(), variables)
            solver.add_clause([(-1 if first[vec] else 1)*variables[vec]
                               for vec in to_force])
            if solver.solve():
                return False
    return True

def find_ragas(width, height, temp, padcol, padrow, xshift, yshift, period_func=lambda x,y: None, lex_funcs=None, instance="sort_network"):
    """Search for self-forcing agars of given spatial and temporal periods."""
    n = 0
    print("Checking {}x{}x{}-periodic points with shift ({},{})".format(width, height, temp, xshift, yshift))
    candidates = []
    for (domain, temp_pat) in periodic_agars(width, height, temp, xshift, yshift, period_func, lex_funcs, instance=instance):
        to_force = domain
        if temp == 1 or any(temp_pat[i,j,t] != temp_pat[i,j,(t+1)%temp]
                            for i in range(width) for j in range(height) for t in range(temp)):
            print("Testing pattern")
            print_temp_pattern(temp_pat)
            if has_unique_periodic_orbit(temp_pat, width, height, temp, 1, 1, instance=instance):
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
            if has_unique_extended_orbit(temp_pat, width, height, temp, i*padcol, i*padrow, to_force=to_force, instance=instance):
                g += 1
                print("It forced itself! ({} so far)".format(g))
                yield (temp_pat, i*padcol, i*padrow)
                continue
            print("It didn't yet force itself")
            for (a,b) in [(i,i+1),(i,i+2),(i+1,i+1)]:
                if not has_unique_periodic_orbit(temp_pat, width, height, temp, a, b, instance=instance):
                    print("Found periodic preimage, discarded")
                    break
            else:
                print("No periodic preimage found")
                news.append(temp_pat)
        candidates = news
        i += 1

def common_forced_part(pats, temp, return_pat=False, chars="nfNF", instance="sort_network"):
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
        clauses, variables = gol_nth_preimage(pat, temp, instance=instance)
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
        return {vec: chars[2*(vec in domain) + (vec in maybe_forced)] for vec in pre_domain}
    else:
        return maybe_forced

def find_self_forcing(pat, temp, shift=(0,0), instance="sort_network"):
    """Find the maximal nonempty subpattern that forces itself in its nth preimages.
       If pat is a nth-generation orphan, return None."""
    sx, sy = shift
    while True:
        fp = common_forced_part([pat], temp, instance=instance)
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
    instance = "bisector"
    # dimensions of periodic orbit
    width, height, temp = 6, 4, 2
    # speed of increasing extra rows and columns
    padrow, padcol = 3, 3
    # the orbit can also be shift-periodic
    xshift, yshift = 0, 0
    # let's also find out if a 50x50 patch contains a self-forcing pattern
    check_forcing = True
    tot_width, tot_height = 50, 50
    # output as rle (as opposed to Python dict)
    rle_output = True
    for (raga,pc,pr) in find_ragas(width, height, temp, padrow, padcol, xshift, yshift, instance=instance):
        ragas.append(raga)
        if check_forcing:
            print("Computing maximal self-forcing patch")
            large_patch = {(x,y):raga[x%width,y%height,0]
                           for x in range(tot_width)
                           for y in range(tot_height)}
            sf = find_self_forcing(large_patch, temp, instance=instance)
            if sf:
                print("Self-forcing patch found!")
                print_pattern(sf)
        with open("output.txt",'a') as f:
            if rle_output:
                if check_forcing:
                    if sf:
                        lox, hix, loy, hiy, _ = pextend(sf)
                        f.write("# self-forcing patch of size {}x{}\n".format(hix-lox, hiy-loy))
                    else:
                        f.write("# no self-forcing patch found\n")
                f.write("# temporal period {}\n".format(temp))
                f.write("# {} extra columns, {} rows to force fundamental domain\n".format(pc, pr))
                f.write(gollify(ppattern_to_matrix(raga), string=False, torus=True))
                f.write("\n")
            else:
                if check_forcing:
                    f.write("{} {} {} {} {} ".format(width,height,temp,pc,pr,0 if sf is None else 1))
                else:
                    f.write("{} {} {} {} {} ".format(width,height,temp,pc,pr,'?'))
                    f.write(str(raga))
                    f.write("\n")
    print("Done, found", len(ragas))
