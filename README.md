# gol-agars
Generation and analysis of agars for Game of Life and other Life-like (two-state, two-dimensional, Moore neighborhood of radius 1, outer totalistic) cellular automata.

The file `gol_agars.py` contains a search script for self-forcing agars of given spatial and temporal periods. It can also be set to find self-forcing patches inside the agars it finds.

Command line arguments:
* The required arguments `width`, `height` and `temp` are the spatial and temporal periods of the agars we search for.
* `--instance` is the method used for encoding the local rule of the CA as a SAT instance. It must be either `totalizer`, `sort_network` or `bisector`.
* `--rule` is a Life-like CA, given as live neighbor counts for birth and survival. The default is Life, or B3/S23. Only `totalizer` and `sort_network` support all Life-like rules; `bisector` is limited to Life.
* `--pad_rows` is the number of additional rows per round used in the self-forcingness check, and `--pad_columns` is the same for columns. The fundamental domain of the agar has size `width × height`, and on round `i`, we check a patch of size `(width + 2*i*padcol) × (height + 2*i*padrow)`.
* `--shift` is the displacement vector of the agar: after applying the CA `temp` times, it should return to its original state but shifted. Defaults to `0,0`.
* If `--finite_pattern_size=w,h` is given, for every self-forcing agar we find, we also check whether a `w × h` patch contains a nonempty self-forcing patch (that solves the Unique father problem).
* `--golly` specifies that output will be in Golly's "Extended RLE" format with human-readable comments. Otherwise, each row will be a space-separated string of the search parameters followed by a Python dict.
* `--jump` indicates that forcing is checked for the entire temporal period, as opposed to a separate check for each time step. In principle, some agars may force themselves in this way but not for each step separately, but the search becomes much slower. For `temp=1` this is useless.
* `--quiet` suppresses console output.

The file `verify_agars.py` verifies three results: the common forced part in the preimages of köynnös-rectangles, the self-forcing patch of kynnös, and the common forced part in the preimages of marching band-rectangles. Flip the Booleans in the file and run it.

The file `rle_forced.py` allows one to check whether a pattern in rle format contains a self-forcing patch.

The folder `agars` contains lists of self-forcing agars of Life for some small parameter values:
* Still life agars of period at most 6x6. The list of 6x6 agars is possibly incomplete, smaller periods are complete.
* All period-2 agars of period at most 7x7.