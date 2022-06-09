def neighborhood(vec):
    "The middle cell is the first one yielded."
    yield vec
    x, y = vec
    if int((x%4)/2) == y%2:
        yield (x-1,y-1)
        yield (x,y-1)
        yield (x+1,y-1)
        yield (x+1,y)
        yield (x+1,y+1)
        yield (x,y+1)
        yield (x-1,y+1)
        yield (x-1,y)
    else:
        yield (x,y-1)
        yield (x+1,y-1)
        yield (x+1,y)
        yield (x+1,y+1)
        yield (x,y+1)
        yield (x-1,y+1)
        yield (x-1,y)
        yield (x-1,y-1)

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

def gollify(s, string=True, torus=False):
    "Convert pattern matrix (string) to Golly .rle string"
    #print(s)
    if string:
        rows = []
        for r in s.split("\n"):
            #r = r.strip()
            if r == "" or r.isspace():
                continue
            rows.append(r.replace(" ","0"))
    else:
        rows = [[str(b) for b in r] for r in s]
    # change rule to Caterpillars if you want 2s and 3s
    x, y = len(rows[0]), len(rows)
    init = "x = {}, y = {}, rule = Life{}\n".format(x, y, ":T{},{}".format(x, y) if torus else "")
    golster = []
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
        golster.append(w)
    return init + "$".join(golster) + "!"

def degollify(s, tostr = False):
    "Convert Golly .rle string to pattern matrix (string if tostr=True)"
    a = s.strip().split("\n")
    fl, rest = a[0], "".join(a[1:])
    fl = fl[4:]
    lines = [[]]
    xstr = ""
    while fl[0].isdigit():
        xstr += fl[0]
        fl = fl[1:]
    fl = fl[6:]
    ystr = ""
    while fl[0].isdigit():
        ystr += fl[0]
        fl = fl[1:]
    #print(int(xstr))
    #print(int(ystr))
    x = int(xstr)
    y = int(ystr)
    number = 0
    for s in rest:
        if s.isdigit():
            number *= 10
            number += int(s)
        if s == "$":
            if number == 0:
                number = 1
            #print (number, lines)
            if len(lines) > 0:
                lastlen = len(lines[-1])
            else:
                lastlen = 0
            lines[-1].extend([0]*(x-lastlen))
            #print(lines)
            #print("a",[[0]*x for i in range(number-1)])
            #print(lines)
            lines.extend([[0]*x for i in range(number-1)])
            if len(lines) < y:
                lines.append([])
            number = 0
            #print(lines)
        if s in ".b":
            if number == 0:
                number = 1
            lines[-1].extend([0]*number)
            number = 0
        if s in "Ao":
            if number == 0:
                number = 1
            lines[-1].extend([1]*number)
            number = 0
        if s == "B":
            if number == 0:
                number = 1
            lines[-1].extend([2]*number)
            number = 0
        if s == "C":
            if number == 0:
                number = 1
            lines[-1].extend([3]*number)
            number = 0
    if len(lines) > 0:
        while len(lines[-1]) < x:
            lines[-1].append(0)
    while len(lines) < y:
        lines.append([])
        while len(lines[-1]) < x:
            lines[-1].append(0)
    #print(lines)
    if tostr:
        return "\n".join(map(lambda a:"".join(map(str,a)), lines))
    else:
        return lines


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
    for y in range(ymax-ymin+1):
        mat.append([])
        for x in range(xmax-xmin+1):
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
