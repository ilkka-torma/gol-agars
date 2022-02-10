def string_to_matrix(s):
    s = s.split("\n")
    lines = []
    for l in s:
        ll = l.strip()
        if ll == "":
            continue
        lines.append([])
        for i in ll:
            if i in "01":
                lines[-1].append(int(i))
            else:
                lines[-1].append(2)
    return lines

def pattern_to_string(pattern):
    if pattern is None:
        return "No pattern"
    else:
        ret = ""
        (minx, maxx, miny, maxy) = extent(pattern)
        #ret += str((minx, maxx, miny, maxy)) + "\n"
        for y in range(miny, maxy+1):
            for x in range(minx, maxx+1):
                if (x,y) in pattern:
                    ret += str(pattern[x,y])
            ret += "\n"
        return ret

def pattern_to_matrix(pat):
    xmin, xmax, ymin, ymax = extent(pat)
    mat = []
    for y in range(ymax-ymin+1):
        mat.append([])
        for x in range(xmax-xmin+1):
            mat[-1].append(pat[x-xmin,y-ymin])
    return mat

def ppattern_to_matrix(pat):
    xmin, xmax, ymin, ymax, per = pextent(pat)
    mat = []
    for y in range(ymax-ymin):
        mat.append([])
        for x in range(xmax-xmin):
            mat[-1].append(pat[x-xmin,y-ymin,0])
    return mat

def matrix_to_pattern(mat):
    pat = {}
    for i,l in enumerate(mat):
        for j,k in enumerate(l):
            pat[(j,i)] = k
    return pat

def extent(pat):
    minx = min(p[0] for p in pat)
    maxx = max(p[0] for p in pat)
    miny = min(p[1] for p in pat)
    maxy = max(p[1] for p in pat)
    return (minx, maxx, miny, maxy)

def pextent(pat):
    minx = min(p[0] for p in pat)
    maxx = max(p[0] for p in pat)
    miny = min(p[1] for p in pat)
    maxy = max(p[1] for p in pat)
    per = max(p[2] for p in pat)+1
    return (minx, maxx, miny, maxy, per)

def print_pattern(pattern, highlight=None, show_dimensions=False):
    if pattern is None or len(pattern) == 0:
        print("No pattern")
    else:
        minx = min(p[0] for p in pattern)
        maxx = max(p[0] for p in pattern)
        miny = min(p[1] for p in pattern)
        maxy = max(p[1] for p in pattern)
        if show_dimensions:
            print(minx, maxx, miny, maxy)
        for y in range(miny, maxy+1):
            for x in range(minx, maxx+1):
                if (x,y) in pattern:
                    if highlight is None:
                        print(pattern[x,y], end="")
                    elif (x,y) in highlight and (x-1,y) not in highlight:
                        print("[{}".format(pattern[x,y]), end="")
                    elif (x,y) not in highlight and (x-1,y) in highlight:
                        print("]{}".format(pattern[x,y]), end="")
                    else:
                        print(" {}".format(pattern[x,y]), end="")
                elif highlight is None:
                    print(" ",end="")
                else:
                    print("  ",end="")
            print("]" if highlight is not None and (maxx,y) in highlight else "")


def print_ppattern(pattern, highlight=None):
    if pattern is None:
        print("No pattern")
    else:
        (minx, maxx, miny, maxy, per) = pextent(pattern)
        print(minx, maxx, miny, maxy)
        for p in range(per):
            print("step", p)
            for y in range(miny, maxy+1):
                for x in range(minx, maxx+1):
                    if (x,y,p) in pattern:
                        if highlight is None:
                            print(pattern[x,y,p], end="")
                        elif (x,y,p) in highlight and (x-1,y,p) not in highlight:
                            print("[{}".format(pattern[x,y]), end="")
                        elif (x,y,p) not in highlight and (x-1,y,p) in highlight:
                            print("]{}".format(pattern[x,y]), end="")
                        else:
                            print(" {}".format(pattern[x,y]), end="")
                    elif highlight is None:
                        print(" ",end="")
                    else:
                        print("  ",end="")
                print("]" if highlight is not None and (maxx,y) in highlight else "")
            print()

def print_set(se):
    if se is None:
        print("No set")
    else:
        (minx, maxx, miny, maxy) = extent(se)
        print(minx, maxx, miny, maxy)
        for y in range(miny, maxy+1):
            for x in range(minx, maxx+1):
                if (x,y) in se:
                    print("1 ", end="")
                else:
                    print("  ",end="")
            print()

def gollify(s):
    #print(s)
    rows = []
    for r in s.split("\n"):
        r = r.strip()
        if r == "" or r.isspace():
            continue
        rows.append(r)
    # change rule to Caterpillars if you want 2s and 3s
    golster = "x = %s, y = %s, rule = Life\n" % (len(rows[0]), len(rows))
    for r in rows:
        w = ""
        for k in r:
            if k == "0":
                w += "b"
            elif k == "1":
                w += "A"
            elif k == "2":
                w += "B"
            elif k == "3":
                w += "C"
        golster += w + "$"
    return golster

def ext_per_left(lis, pad):
    cur = len(lis)-1
    ret = []
    for i in range(pad):
        ret.append(lis[cur])
        cur -= 1
        cur %= len(lis)
    return list(reversed(ret))
    
def ext_per_right(lis, pad):
    cur = 0
    ret = []
    for i in range(pad):
        ret.append(lis[cur])
        cur += 1
        cur %= len(lis)
    return ret

def pad_matrix(mat, hpad, vpad):
    mmat = []
    for l in mat:
        mmat.append(ext_per_left(l, hpad) + l + ext_per_right(l, hpad))
    return ext_per_left(mmat, vpad) + mmat + ext_per_right(mmat, vpad)

def hshift(s, n):
    if n == 0:
        return s
    assert n > 0
    ret = []
    for l in s:
        ret.append(l[-n:] + l[:-n])
    return ret

def vshift(s, n):
    if n == 0:
        return s
    assert n > 0
    return s[-n:] + s[:-n]
