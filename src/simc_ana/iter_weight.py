#! /usr/bin/python

#
# Description: Adapted from fortran code wt28_3.f
# ================================================================
# Time-stamp: "2023-09-18 12:58:42 trottar"
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

import time
##################################################################################################################################################
# Importing utility functions

sys.path.append("utility")
from utility import run_fortran

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

import math

import math

def iterWeight(q2_set, q2_sim, w_sim, t_sim, eps_sim, thetacm_sim, phicm_sim, sigcm_sim, wt_sim, *params):
    # Define constants
    pi = 3.14159
    mtar_gev = 0.93827231

    # Convert units
    q2_gev = q2_set / 1e6
    t_gev = t_sim
    s = w_sim**2
    s_gev = s / 1e6

    # Calculate tav, ftav, ft
    tav = (0.0735 + 0.028 * math.log(q2_gev)) * q2_gev
    ftav = (abs(t_gev) - tav) / tav
    ft = t_gev / (abs(t_gev) + 0.139570**2)**2

    # Calculate sigl, sigt, siglt, sigtt, sig219, sig
    p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12 = params
    sigl = (p1 + p2 * math.log(q2_gev)) * math.exp((p3 + p4 * math.log(q2_gev)) * (abs(t_gev) - 0.2))
    sigt = p5 + p6 * math.log(q2_gev) + (p7 + p8 * math.log(q2_gev)) * ftav
    siglt = (p9 * math.exp(p10 * abs(t_gev)) + p11 / abs(t_gev)) * math.sin(thetacm_sim)
    sigtt = (p12 * q2_gev * math.exp(-q2_gev)) * ft * math.sin(thetacm_sim)**2

    tav = (-0.178 + 0.315 * math.log(q2_gev)) * q2_gev

    sig219 = (sigt + eps_sim * sigl + eps_sim * math.cos(2. * phicm_sim) * sigtt +
             math.sqrt(2.0 * eps_sim * (1. + eps_sim)) * math.cos(phicm_sim) * siglt) / 1.0

    wfactor = 1.0 / (s_gev - mtar_gev**2)**2
    sig = sig219 * wfactor
    sig = sig / (2.0 * pi * 1e6)  # dsig/dtdphicm in microbarns/MeV**2/rad

    wtn = wt_sim * sig / sigcm_sim

    if wtn > 0.0:
        pass
    else:
        wtn = 0.0

    return wtn


def iter_weight(param_file, fort_param, simc_root, inpDict, phi_setting):

    formatted_date  = inpDict["formatted_date"]
    Q2 = inpDict["Q2"].replace("p","")

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
    iweight = array('f', [0.0])  # Assuming iweight is a float
    Weight_SIMC.SetAddress(iweight)

    ################################################################################################################################################
    # Run over simc root branch to determine new weight

    start_time = time.time()
    print("\nGrabbing %s simc..." % phi_setting)
    #for i,evt in enumerate(TBRANCH_SIMC):
    for i,evt in enumerate(TBRANCH_SIMC):

      if i >=2:
          break

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

          # thetacm and phicm are correct, the next line is just for testingx
          #inp_fort_param = '{} {} {} {} {} {} {} {} {} '.format(Q2, evt.Q2, evt.W, evt.t, evt.epsilon, evt.thetacm, evt.phicm, evt.sigcm, evt.Weight)+' '.join(param_arr)
          inp_fort_param = '{} {} {} {} {} {} {} {} {} '.format(Q2, evt.Q2, evt.W, evt.t, evt.epsilon, evt.thetapq, evt.phipq, evt.sigcm, evt.Weight)+ \
                           ' '.join(param_arr)
          #print("-"*25,"\n",i,"\n",inp_fort_param)
              
          # Get the standard output and standard error
          #stdout, stderr = run_fortran(fort_param, inp_fort_param)
          
          # Print the output
          #print(stdout,"\n",stderr)

          stdout = iterWeight(Q2, evt.Q2, evt.W, evt.t, evt.epsilon, evt.thetapq, evt.phipq, evt.sigcm, evt.Weight,' '.join(param_arr))
          
          # Set the value of iweight
          iweight[0] = float(stdout)
    
          # Fill the branch
          Weight_SIMC.Fill()

    end_time = time.time()

    execution_time = end_time - start_time
    print("Time:", execution_time)

    TBRANCH_SIMC.Write("", ROOT.TObject.kOverwrite)
    InFile_SIMC.Close()
