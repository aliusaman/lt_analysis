#! /usr/bin/python

#
# Description: Adapted from fortran code wt28_3.f
# ================================================================
# Time-stamp: "2023-09-18 15:42:35 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import ROOT
from ROOT import TCanvas, TH1D, TH2D, gStyle, gPad, TPaveText, TArc, TGraphErrors, TGraphPolar, TFile, TLegend, TMultiGraph, TLine
from array import array
import sys, math, os, subprocess

# Import the dynamic script
import importlib.util

##################################################################################################################################################
# Importing utility functions

sys.path.append("utility")
from utility import run_fortran

##################################################################################################################################################
# Importing param model for weight iteration

sys.path.append("models")
from param_active import iterWeight    

################################################################################################################################################
'''
ltsep package import and pathing definitions
'''

# Import package for cuts
from ltsep import Root
# Import package for progress bar
from ltsep import Misc

lt=Root(os.path.realpath(__file__),"Plot_Prod")

# Add this to all files for more dynamic pathing
USER=lt.USER # Grab user info for file finding
HOST=lt.HOST
REPLAYPATH=lt.REPLAYPATH
UTILPATH=lt.UTILPATH
LTANAPATH=lt.LTANAPATH
ANATYPE=lt.ANATYPE
OUTPATH=lt.OUTPATH

################################################################################################################################################

def iter_weight(param_file, simc_root, inpDict, phi_setting):

    
    formatted_date  = inpDict["formatted_date"]
    ParticleType  = inpDict["ParticleType"]
    Q2 = inpDict["Q2"].replace("p","")
    POL = inpDict["POL"]
    
    if int(POL) == 1:
        pol_str = "pl"
    elif int(POL) == -1:
        pol_str = "mn"
    else:
        print("ERROR: Invalid polarity...must be +1 or -1")
        sys.exit(2)
    
    # Define diamond cut parameters
    a1 = inpDict["a1"]
    b1 = inpDict["b1"]
    a2 = inpDict["a2"]
    b2 = inpDict["b2"]
    a3 = inpDict["a3"]
    b3 = inpDict["b3"]
    a4 = inpDict["a4"]
    b4 = inpDict["b4"]
    
    param_arr = []
    with open(param_file, 'r') as f:
        for i, line in enumerate(f):
            columns = line.split()
            param_arr.append(str(columns[0]))    

    if not os.path.isfile(simc_root):
        print("\n\nERROR: No simc file found called {}\n\n".format(simc_root))

    InFile_SIMC = TFile.Open(simc_root, "OPEN")
    TBRANCH_SIMC  = InFile_SIMC.Get("h10")
    Weight_SIMC  = TBRANCH_SIMC.GetBranch("Weight")

    # Associate a variable with the branch
    iweight = ROOT.Double(0)

    # Create a new TBranch with the same name 'Weight' in a new TTree
    #new_tree = ROOT.TTree("TBRANCH_SIMC", "Modified TTree with Weight")

    # Clone the existing TBranch structure from the original TTree
    new_tree = TBRANCH_SIMC.CloneTree(-1, "newtree=fast")

    #TBRANCH_SIMC.SetBranchAddress("Weight", iweight)
    new_tree.Branch("Weight", iweight, "Weight/D")
    
    ################################################################################################################################################
    # Run over simc root branch to determine new weight

    print("\nRecalculating weight for %s simc..." % phi_setting)
    for i,evt in enumerate(TBRANCH_SIMC):

      # Progress bar
      Misc.progressBar(i, TBRANCH_SIMC.GetEntries(),bar_length=25)

      # Define the acceptance cuts  
      SHMS_Acceptance = (evt.ssdelta>=-10.0) & (evt.ssdelta<=20.0) & (evt.ssxptar>=-0.06) & (evt.ssxptar<=0.06) & (evt.ssyptar>=-0.04) & (evt.ssyptar<=0.04)
      HMS_Acceptance = (evt.hsdelta>=-8.0) & (evt.hsdelta<=8.0) & (evt.hsxptar>=-0.08) & (evt.hsxptar<=0.08) & (evt.hsyptar>=-0.045) & (evt.hsyptar<=0.045)
      if ( a1 == 0.0 and  b1 == 0.0 and  a2 == 0.0 and  b2 == 0.0 and  a3 == 0.0 and  b3 == 0.0 and  a4 == 0.0 and  b4 == 0.0):
          Diamond = True
      else:
          try:
              Diamond = (evt.W/evt.Q2>a1+b1/evt.Q2) & (evt.W/evt.Q2<a2+b2/evt.Q2) & (evt.W/evt.Q2>a3+b3/evt.Q2) & (evt.W/evt.Q2<a4+b4/evt.Q2)
          except ZeroDivisionError:
              Diamond = False

      #........................................

      #Fill SIMC events
      if(HMS_Acceptance & SHMS_Acceptance & Diamond):

          TBRANCH_SIMC.GetEntry()
          
          # thetacm and phicm are correct, the next line is just for testingx
          #inp_param = '{} {} {} {} {} {} {} {} {} '.format(Q2, evt.Q2, evt.W, evt.t, evt.epsilon, evt.thetacm, evt.phicm, evt.sigcm, evt.Weight)+' '.join(param_arr)
          inp_param = '{} {} {} {} {} {} {} {} {} '.format(Q2, evt.Q2, evt.W, evt.t, evt.epsilon, evt.thetapq, evt.phipq, evt.sigcm, evt.Weight)+ \
                           ' '.join(param_arr)
          #print("-"*25,"\n",i,"\n",inp_param)
          
          # Set the value of iweight
          iweight = iterWeight(inp_param)*1e6
    
          new_tree.Fill()
          
    # Write the new TTree to the output file
    new_tree.Write("h10", ROOT.TObject.kOverwrite)
    
    #TBRANCH_SIMC.Write("", ROOT.TObject.kOverwrite)
    InFile_SIMC.Close()
