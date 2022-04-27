
from gol_agars import *

koynnos = mat_to_pattern([[1,1,1,0,0,0],
                          [0,1,0,1,1,1],
                          [0,0,0,0,1,0]])

kynnos = mat_to_pattern([[0,0,1,1,0,1],
                         [0,0,1,0,1,1],
                         [1,1,0,0,0,0],
                         [0,1,0,1,1,0],
                         [1,0,0,1,1,0],
                         [1,1,0,0,0,0]])

marching_band = mat_to_pattern([[1,0,0,0,0,0,1,0],
                                [1,1,0,0,1,1,0,0],
                                [1,1,0,0,1,1,0,0],
                                [0,0,1,0,1,0,0,0]])

if False:
    print("Koynnos")
    print_pattern(koynnos)
    print("Common forced part of 30x27 patches of koynnos")
    pats = [{(x,y):koynnos[(x+dx)%6,(y+dy)%3] for x in range(30) for y in range(27)}
            for dx in range(6)
            for dy in range(3)]
    print_pattern(common_forced_part(pats, 1, return_pat=True))

if True:
    print("Kynnos")
    print_pattern(kynnos)
    print("Self-forcing patch of kynnos")
    pat = {(x,y) : kynnos[x%6,y%6] for x in range(2,30) for y in range(2,24)}
    print_pattern(find_self_forcing(pat, 1))

if False:
    print("Marching band")
    print_pattern(marching_band)
    print("Common g^2-forced part of 48x44 patches of marching band")
    pats = [{(x,y):marching_band[(x+dx)%8,(y+dy)%4] for x in range(48) for y in range(44)}
            for dx in range(8)
            for dy in range(4)]
    print_pattern(common_forced_part(pats, 2, return_pat=True))
