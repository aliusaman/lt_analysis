
#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2024-01-22 13:13:05 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import sys, os
import ROOT

root_path = sys.argv[1]
input_file_name = sys.argv[2]
input_tree_names = sys.argv[3]
output_file_name = sys.argv[4]
string_run_nums = sys.argv[5]
particle = sys.argv[6]
err_fout = sys.argv[7]

###############################################################################################################################################
'''
ltsep package import and pathing definitions
'''

# Import progres bar
from ltsep import Misc

###############################################################################################################################################

# Overwrite error file if already exists
with open(err_fout, 'w') as f:
    f.write("Bad runs for {}...\n\n".format(output_file_name))

def log_bad_runs(err_fout, warning):
    print(warning)
    with open(err_fout, 'a') as f:
        f.write(warning+'\n')
    os.remove(filepath)

out_root_file = root_path + output_file_name + ".root"

outfile = ROOT.TFile(out_root_file, "RECREATE")
if not outfile.IsOpen():
    print("ERROR: Output file {} cannot be opened. Exiting the function.".format(outfile.GetName()))
    sys.exit(1)

arr_run_nums = [int(x) for x in string_run_nums.split()]

for tree in input_tree_names.split():

    chain = ROOT.TChain(tree)

    for i,n in enumerate(arr_run_nums):
        # Progress bar
        if len(arr_run_nums) > 1:
            Misc.progressBar(i, len(arr_run_nums)-1,bar_length=25)
        else:
            Misc.progressBar(len(arr_run_nums), len(arr_run_nums),bar_length=25)
        filepath = root_path + particle + "_" + str(n) + input_file_name + ".root"
        if not os.path.isfile(filepath):
            warning = "WARNING: File {} not found. Removing...".format(filepath)
            log_bad_runs(err_fout, warning)
            break
        tempfile = ROOT.TFile.Open(filepath)
        if tempfile == None or not tempfile.IsOpen() or tempfile.TestBit(ROOT.TFile.kRecovered):
            warning = "WARNING: File {} not found or not opened or corrupted. Removing...".format(filepath)
            log_bad_runs(err_fout, warning)
            break
        # Get the tree from the temporary file using the tree_name
        tree_temp = tempfile.Get(tree)
        # Check if the tree exists
        if tree_temp:
            # Get the number of entries in the tree
            num_entries = tree_temp.GetEntries()
            if num_entries == 0:
                warning = "WARNING: Tree {} in file {} is empty. Removing...".format(tree, filepath)
                log_bad_runs(err_fout, warning)
                break
        #print("Adding {}...".format(filepath))
        chain.Add(filepath)

    if os.path.exists(filepath):
        
        if chain.GetEntries() == 0:
            warning = "WARNING: No entries found for tree {}.  Removing...".format(tree)        
            log_bad_runs(err_fout, warning)
            break

        outfile.cd()
        chain.Write(tree, ROOT.TObject.kWriteDelete)
        print("\n\tTree {} added to {}.root".format(tree,output_file_name))
    
outfile.Close()
