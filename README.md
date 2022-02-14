# gol-agars
Generation and analysis of Game of Life agars.

The file `gol_agars.py` contains a search script for self-forcing agars of given spatial and temporal periods. It can also be set to find self-forcing patches inside still life agars (or arbitrary still lifes). Running it starts an example search; tweak the parameters in the file to search for something else.

The file `verify_agars.py` verifies three results: the common forced part in the preimages of köynnös-rectangles, the self-forcing patch of kynnös, and the common forced part in the preimages of marching band-rectangles. Flip the Booleans in the file and run it.

The file `rle_forced.py` allows one to check whether a pattern in rle format contains a self-forcing patch.