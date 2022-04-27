# gol-agars
Generation and analysis of agars for Game of Life and other Life-like (two-state, two-dimensional, Moore neighborhood of radius 1, outer totalistic) cellular automata.

The file `gol_agars.py` contains a search script for self-forcing agars of given spatial and temporal periods. It can also be set to find self-forcing patches inside still life agars (or arbitrary still lifes). Running it starts an example search; tweak the parameters in the file to search for something else. Results are appended to `output.txt`, by default in "Extended RLE" format with comments.

Search parameters:
* `instance` is the method used for encoding the local rule of the CA as a SAT instance. It must be either `"sort_network"` or `"bisector"`.
* `rule` is a Life-like CA, given as a tuple of lists of integers that specify live neighbor counts for birth and survival. For example, Life is B3/S23, or `([3], [2,3])`. Only `"sort_network"` supports all Life-like rules; `"bisector"` is limited to Life.
* `width` and `height` are the spatial periods of the agars we search for.
* `temp` is the temporal period of the agars.
* `padrow` is the number of additional rows per round used in the self-forcingness check, and `padcol` is the same for columns. The fundamental domain of the agar has size `width × height`, and on round `i`, we check a patch of size `(width + 2*i*padcol) × (height + 2*i*padrow)`.
* `xshift` and `yshift` form the displacement vector of the agar: after applying the CA `temp` times, it should return to its original state shifted by `(xshift, yshift)`.
* If `check_forcing = True`, for every self-forcing agar we find, we also check whether a `tot_width × tot_height` patch contains a nonempty self-forcing patch (that solves the Unique father problem).
* If `rle_output = True`, output will be in Extended RLE format with human-readable comments. Otherwise, each row will be a space-separated string of the search parameters followed by a Python dict.

The file `verify_agars.py` verifies three results: the common forced part in the preimages of köynnös-rectangles, the self-forcing patch of kynnös, and the common forced part in the preimages of marching band-rectangles. Flip the Booleans in the file and run it.

The file `rle_forced.py` allows one to check whether a pattern in rle format contains a self-forcing patch.

The folder `agars` contains lists of self-forcing agars of Life for some small parameter values:
* Still life agars of period at most 6x6. The list of 6x6 agars is possibly incomplete, smaller periods are complete.
* All period-2 agars of period at most 7x7.