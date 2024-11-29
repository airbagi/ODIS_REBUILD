# Description

The rebuilder script after update by ODIS VAG flasher.
In order to rebuild CPU flash you need three files:

1. ODX file which was updated into;
2. ODX file which was in original firmware;
3. Binary CPU flash

# Rebuilding principles

Script is comparing two ODX files, finds differences, then find the updated sequence in binary and replaces it with data from original ODX file.
Output is logged into console. If there are ambigous replaces, the replace will not be performed (showed in output).

# ODX file

You need VAG ODX file with the right version for your ECU or `FRF` file, which need to be converted to ODX.
In order to convert you can use this utility:

https://github.com/bri3d/VW_Flash/tree/master/frf
