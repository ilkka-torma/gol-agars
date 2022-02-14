# Check whether an rle pattern contains a self-forcing patch

from pattern_basics import degollify, mat_to_pattern, print_pattern
from gol_agars import find_self_forcing

# Glider; replace by another pattern to check it
rle = """
x = 3, y = 3, rule = B3/S23
3o$o$bo!
"""

# We find and print the largest subpattern that forces itself in all nth preimages, shifted by -shift.
# "No pattern" means the input is an (nth generation) orphan.
# "Empty pattern" means the pattern contains no self-forcing patch with these parameters.
# Note: even though there is no self-forcing patch with n and shift,
# there might be one with k*n and k*shift for some k >= 2.

# Number of iterations n
temp = 1
# Spatial shift
shift = (0,0)
# SAT instance construction method
instance = "sort_network"
#instance = "bisector"

pat = mat_to_pattern(degollify(rle))
print("Input pattern")
print_pattern(pat)
print("Finding maximal self-forcing patch")
print_pattern(find_self_forcing(pat, temp, shift, instance=instance))
