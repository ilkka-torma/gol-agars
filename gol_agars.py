
from pysat.solvers import MinisatGH
from pattern_basics import *
import argparse as ap
import bisector
import sort_network
import totalizer

def nth_preimage(pattern, temp, hints=[], instance="sort_network",rule=([3],[2,3])):
    """Clauses and names for the nth preimage of a single pattern, n >= 1."""
    if instance == "sort_network":
        mod = sort_network
    elif instance == "bisector":
        mod = bisector
    elif instance == "totalizer":
        mod = totalizer
    cells = pattern
    var_cells = set()
    for t in range(1,temp+1):
        cells = set(nbr for vec in cells for nbr in neighborhood(vec))
        var_cells |= set((i,j,t) for (i,j) in cells)
    variables = {vec : mod.gen_var() for vec in var_cells}
    clauses = [clause
               for (vec, value) in pattern.items()
               for clause in mod.local_preimage([variables[i,j,1]
                                                 for (i,j) in neighborhood(vec)],
                                                value,
                                                rule)]
    clauses += [clause
                for ((x,y,t), var) in variables.items()
                if t < temp
                for clause in mod.local_preimage_var([variables[i,j,t+1]
                                                      for (i,j) in neighborhood((x,y))],
                                                     var,
                                                     rule)]
    # deduce cell values from hints
    known_cells = {(x,y,0) : b for ((x,y), b) in pattern.items()}
    for (x,y,t) in sorted(set(known_cells)|var_cells, key=lambda p:p[2]):
        if t < temp:
            for (subpat, forced) in hints:
                if all(b == known_cells.get((x+i,y+j,t))
                       for ((i,j), b) in subpat.items()):
                    for ((i,j), b) in forced.items():
                        known_cells[x+i,y+j,t+1] = b
    for ((x,y,t), b) in known_cells.items():
        if t > 0:
            clauses.append([(1 if b else -1)*variables[x,y,t]])
            
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
    elif instance == "totalizer":
        mod = totalizer
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

def periodic_agars(width, height, temp, xshift, yshift, period_func=None, lex_funcs=None, instance="sort_network",rule=([3],[2,3])):
    """All w x h-periodic configurations that map to (sx,sy)-translated
       versions of themselves in t steps.
       Discard those that are not lexicographically minimal in their orbit.
       period_func enforces a symmetry.
       lex_funcs modfies the lexicographical minimality check."""
    if instance == "sort_network":
        mod = sort_network
    elif instance == "bisector":
        mod = bisector
    elif instance == "totalizer":
        mod = totalizer
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
                for clause in mod.local_preimage_var([variables[x%width,y%height,t]
                                                      for (x,y) in neighborhood((i,j))],
                                                     variables[(i+sx)%width,
                                                               (j+sy)%height,
                                                               (t+1)%temp],
                                                     rule):
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

def has_unique_periodic_orbit(temp_pat, width, height, temp, each, xper, yper, instance="sort_network", rule=([3],[2,3])):
    "Does each configuration in this orbit have a unique w*xp × h*yp -periodic preimage?"
    if instance == "sort_network":
        mod = sort_network
    elif instance == "bisector":
        mod = bisector
    elif instance == "totalizer":
        mod = totalizer
    if each:
        for t in range(temp):
            variables = {(i,j) : mod.gen_var()
                         for i in range(xper*width)
                         for j in range(yper*height)}
            clauses = [clause
                       for (i,j) in variables
                       for clause in mod.local_preimage([variables[x%(xper*width),y%(yper*height)]
                                                         for (x,y) in neighborhood((i,j))],
                                                        temp_pat[i%width,j%height,t],
                                                        rule)]

            # force lexicographic minimality among shifts along periods
            base_vars = [variables[i,j] for i in range(width) for j in range(height)]
            other_vars = [[variables[i+x*width,j+y*height] for i in range(width) for j in range(height)]
                          for x in range(xper)
                          for y in range(1 if x==0 else 0, yper)]
            lex_clauses = list(lex_leq(base_vars, other_vars, instance=instance))

            # force difference to previous configuration in orbit
            diff_clause = [(-1 if temp_pat[x%width,y%height,(t-1)%temp] else 1)*variables[x,y]
                           for x in range(width*xper)
                           for y in range(height*yper)]

            mod.reset_var()
            with MinisatGH(bootstrap_with=clauses+lex_clauses+[diff_clause]) as solver:
                if solver.solve():
                    #print("Periodic preimage:")
                    #model = model_to_pattern(solver.get_model(), variables)
                    #print_pattern(model)
                    return False
    else:
        variables = {(i,j,t) : mod.gen_var()
                     for i in range(xper*width)
                     for j in range(yper*height)
                     for t in range(1,temp+1)}
        clauses = [clause
                   for (i,j,t) in variables
                   if t > 1
                   for clause in mod.local_preimage_var([variables[x%(xper*width),y%(yper*height),t]
                                                         for (x,y) in neighborhood((i,j))],
                                                        variables[i,j,t-1],
                                                        rule)]
        clauses += [clause
                    for i in range(xper*width)
                    for j in range(yper*height)
                    for clause in mod.local_preimage([variables[x%(xper*width),y%(yper*height),1]
                                                      for (x,y) in neighborhood((i,j))],
                                                     temp_pat[i%width,j%height,0],
                                                     rule)]

        # force lexicographic minimality among shifts along periods
        base_vars = [variables[i,j,t]
                     for i in range(width)
                     for j in range(height)
                     for t in range(1,temp+1)]
        other_vars = [[variables[i+x*width,j+y*height,t]
                       for i in range(width)
                       for j in range(height)
                       for t in range(1,temp+1)]
                      for x in range(xper)
                      for y in range(1 if x==0 else 0, yper)]
        lex_clauses = list(lex_leq(base_vars, other_vars, instance=instance))

        # force difference to base configuration
        diff_clause = [(-1 if temp_pat[x%width,y%height,0] else 1)*variables[x,y,temp]
                       for x in range(width*xper)
                       for y in range(height*yper)]

        mod.reset_var()
        with MinisatGH(bootstrap_with=clauses+lex_clauses+[diff_clause]) as solver:
            if solver.solve():
                #print("Periodic preimage:")
                #model = model_to_pattern(solver.get_model(), variables)
                #print_pattern(model)
                return False
    return True

def has_unique_extended_orbit(temp_pat, width, height, temp, padcol, padrow, each, to_force=None, instance="sort_network",rule=([3],[2,3])):
    """Does each configuration in this orbit have a unique w×h-patch in the preimage
       if it's continued periodically for the given number of rows and columns?
       Alternatively, check only for t'th power."""
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
    if each:
        for t in range(temp):
            tiled = {(i,j) : temp_pat[i%width,j%height,t]
                     for i in range(min_x-padcol,max_x+padcol+1)
                     for j in range(min_y-padrow,max_y+padrow+1)}
            clauses, variables = nth_preimage(tiled, 1, instance=instance, rule=rule)
            diff_clause = [(-1 if temp_pat[i,j,(t-1)%temp] else 1)*variables[i,j]
                           for i in range(width)
                           for j in range(height)]
            with MinisatGH(bootstrap_with=clauses+[diff_clause]) as solver:
                if solver.solve():
                    return False
    else:
        tiled = {(i,j) : temp_pat[i%width,j%height,0]
                 for i in range(min_x-padcol,max_x+padcol+1)
                 for j in range(min_y-padrow,max_y+padrow+1)}
        clauses, variables = nth_preimage(tiled, temp, instance=instance, rule=rule)
        diff_clause = [(-1 if temp_pat[i,j,0] else 1)*variables[i,j]
                       for i in range(width)
                       for j in range(height)]
        with MinisatGH(bootstrap_with=clauses+[diff_clause]) as solver:
            if solver.solve():
                return False
    return True

def find_ragas(width, height, temp, padcol, padrow, xshift, yshift, each, period_func=lambda x,y: None, lex_funcs=None, instance="sort_network",rule=([3],[2,3]), verbose=True):
    """Search for self-forcing agars of given spatial and temporal periods."""
    n = 0
    if verbose:
        print("Checking {}x{}x{}-periodic points with shift ({},{})".format(width, height, temp, xshift, yshift))
    candidates = []
    for (domain, temp_pat) in periodic_agars(width, height, temp, xshift, yshift, period_func, lex_funcs, instance=instance, rule=rule):
        to_force = domain
        if temp == 1 or any(temp_pat[i,j,t] != temp_pat[i,j,(t+1)%temp]
                            for i in range(width) for j in range(height) for t in range(temp)):
            if verbose:
                print("Testing pattern")
                print_temp_pattern(temp_pat)
            if has_unique_periodic_orbit(temp_pat, width, height, temp, each, 1, 1, instance=instance, rule=rule):
                if verbose:
                    print("Qualified")
                candidates.append(temp_pat)
            n += 1
            if verbose and n%250 == 0:
                print("Checked", n, "orbits,", len(candidates), "passed")
    i = 1
    g = 0
    while candidates:
        if verbose:
            print("Round {}: {}/{} orbits remain".format(i, len(candidates), n))
        news = []
        for (m, temp_pat) in enumerate(candidates):
            if verbose:
                print("Testing pattern {}/{}".format(m+1, len(candidates)))
                print_temp_pattern(temp_pat)
            if has_unique_extended_orbit(temp_pat, width, height, temp, i*padcol, i*padrow, each, to_force=to_force, instance=instance, rule=rule):
                g += 1
                if verbose:
                    print("It forced itself! ({} so far)".format(g))
                yield (temp_pat, i*padcol, i*padrow)
                continue
            if verbose:
                print("It didn't yet force itself")
            for (a,b) in [(i,i+1),(i,i+2),(i+1,i+1)]:
                if not has_unique_periodic_orbit(temp_pat, width, height, temp, each, a, b, instance=instance, rule=rule):
                    if verbose:
                        print("Found periodic preimage, discarded")
                    break
            else:
                if verbose:
                    print("No periodic preimage found")
                news.append(temp_pat)
        candidates = news
        i += 1

def common_forced_part(pats, temp, return_pat=False, chars="nfNF", hints=[], instance="sort_network", rule=([3],[2,3]), verbose=True):
    """Compute the set of cells that all patterns force in their nth preimages.
       Return None if any of the patterns have no nth preimage."""
    # Assume pats have common domain
    domain = set(pats[0])
    pre_domain = domain
    for _ in range(temp):
        pre_domain = set(nbr for vec in pre_domain for nbr in neighborhood(vec))
    maybe_forced = set(pre_domain)
    for (k, pat) in enumerate(pats):
        if verbose and len(pats) > 1:
            print("Pattern {}/{}, {} cells potentially forced".format(k+1, len(pats), len(maybe_forced)))
        clauses, variables = nth_preimage(pat, temp, hints=hints, instance=instance, rule=rule)
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

def find_self_forcing(pat, temp, hints=[], shift=(0,0), instance="sort_network", rule=([3],[2,3]), verbose=True):
    """Find the maximal nonempty subpattern that forces itself in its nth preimages.
       If pat is a nth-generation orphan, return None."""
    sx, sy = shift
    while True:
        fp = common_forced_part([pat], temp, hints=hints, instance=instance, rule=rule, verbose=verbose)
        if fp is None:
            return None
        if verbose:
            print("Now forcing", len(fp), "cells")
        if any(vec not in fp for vec in pat):
            pat = {(x,y):val for ((x,y),val) in pat.items() if (x-sx,y-sy) in fp}
            if not pat:
                return pat
        else:
            return pat

def parse_coord(s):
    try:
        a, b = s.split(",")
        return (int(a), int(b))
    except ValueError:
        raise ValueError

def parse_rule(s):
    try:
        birth, survive = s.split("/")
        assert birth[0] == 'B' and survive[0] == 'S'
        return ([int(n) for n in birth[1:]], [int(n) for n in survive[1:]])
    except (ValueError, AssertionError):
        raise ValueError

if __name__ == "__main__":
    parser = ap.ArgumentParser()
    parser.add_argument("width", type=int, help="width of agar")
    parser.add_argument("height", type=int, help="height of agar")
    parser.add_argument("temp", type=int, help="temporal period of agar")
    parser.add_argument("-C", "--pad_columns", default=None, help="number of extra columns per step (default: width)")
    parser.add_argument("-R", "--pad_rows", default=None, help="number of extra rows per step (default_ height)")
    parser.add_argument("-s", "--shift", default=(0,0), type=parse_coord, help="spatial shift of agar (default: (0,0))")
    parser.add_argument("-r", "--rule", default=([3], [2,3]), type=parse_rule, help="CA rule (default: B3/S23)")
    parser.add_argument("-i", "--instance", choices=["sort_network", "bisector", "totalizer"], default="totalizer", help="SAT instance encoding (default: totalizer)")
    parser.add_argument("-j", "--jump", default=False, action="store_true", help="check forcing only for full temporal period (slow)")
    parser.add_argument("-F", "--finite_pattern_size", default=None, type=parse_coord, help="also search for a finite self-forcing pattern of at most given size")
    parser.add_argument("-o", "--output", default="output.txt", help="file to append search results (default: output.txt)")
    parser.add_argument("-g", "--golly_format", default=False, action="store_true", help="output in Golly's rle format")
    parser.add_argument("-q", "--quiet", default=False, action="store_true", help="suppress console output")
    args = parser.parse_args()
    
    ragas = []
    if not args.quiet:
        print("Using rule B{}/S{}".format("".join(map(str,args.rule[0])),
                                          "".join(map(str,args.rule[1]))))
    # dimensions of periodic orbit
    width, height, temp = args.width, args.height, args.temp
    # speed of increasing extra rows and columns
    if args.pad_columns is None:
        padcol = width
    else:
        padcol = args.pad_columns
    if args.pad_rows is None:
        padrow = height
    else:
        padrow = args.pad_rows
    # the orbit can also be shift-periodic
    xshift, yshift = args.shift
    # check every step of the agar vs all at once
    force_every_step = not args.jump
    # let's also find out if a 50x50 patch contains a self-forcing pattern
    check_forcing = args.finite_pattern_size is not None
    if check_forcing:
        tot_width, tot_height = args.finite_pattern_size
    # output as rle (as opposed to Python dict)
    for (raga,pc,pr) in find_ragas(width, height, temp, padrow, padcol, xshift, yshift, force_every_step, rule=args.rule, instance=args.instance, verbose=not args.quiet):
        ragas.append(raga)
        if check_forcing:
            if not args.quiet:
                print("Computing maximal self-forcing patch")
            large_patch = {(x,y):raga[x%width,y%height,0]
                           for x in range(tot_width)
                           for y in range(tot_height)}
            if force_every_step:
                hints = [({(x,y) : raga[x%width,y%height,t]
                           for x in range(-pc, width+pc)
                           for y in range(-pr, height+pr)},
                          {(x,y) : raga[x,y,(t-1)%temp]
                           for x in range(width)
                           for y in range(height)})
                         for t in range(temp)]
            else:
                hints = []
            hints=[]
            sf = find_self_forcing(large_patch, temp, hints=hints, rule=args.rule, instance=args.instance, verbose=not args.quiet)
            if sf and not args.quiet:
                print("Self-forcing patch found!")
                print_pattern(sf)
        with open(args.output,'a') as f:
            if args.golly_format:
                if check_forcing:
                    if sf:
                        lox, hix, loy, hiy = extent(sf)
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
    if not args.quiet:
        print("Done, found", len(ragas))
