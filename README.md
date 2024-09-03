Tools for getting data from code lyoko: quest for infinity(wii).
Has 
 - CLI-ish programs for decompressing
 - converting texture archives to png
 - a somewhat working model importer for blender (that has a skeleton!!!!)
 - a very bad animation importer
   
The Lzss decompressor is adapted from the QuickBMS script example.
http://aluigi.altervista.org/quickbms.htm

File types covered
 - .GCN
 - .pc
 - .TIN
 - .GFX

# how to use
LzssDec and TinGfx2Png need to be run from the command line with python. 
They don't take arguments, you can select the file you want to extract with the file explorer popup

you need to decompress the tin.pc and gfx.pc files with LzssDec before using TinGfx2Png, Also make sure they're in the same folder

The MWLD import script takes decompressed GCN files. Run it in blenders script editor and 
it'll make a pannel in the 3d viewport called Model_Imports with a button to import.

Currently I have no clue how the file gets the skeleton from its default state to its T-Posed state so u need to manually
change the bone chain rotations in the script, Currently that section is commented out at the bottom so idk figure it out lol.
In all honesty I think that might actually be their rest pose. They also use vertex stitching which is an arcane technique
that merges two versions of the same vertex after each has been moved by a different bone. Its weird and i dont know how to do it in blender.
Or if it's even possible.

The animation importer (a_test) is like the MWLD importer. Right now it imports the first 4 animations as actions. It needs the rotation mode set to euler.
Also it gets soo flippy you really need to use the discontinuity filter. Also it doesnt work if the armatures are t-posed so you need to leave them in their
Human-gourd state. Its weird

# Notes
 - Credit me if u use this!
 - the blender importer doesnt do custom normals yet </3
 - It should all work in blender 4.0

