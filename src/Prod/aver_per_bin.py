#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2023-08-11 14:57:44 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#

##################################################################################################################################################

# Import relevant packages
import uproot as up
import numpy as np
import root_numpy as rnp
import ROOT
import scipy
import scipy.integrate as integrate
from scipy.integrate import quad
import matplotlib.pyplot as plt
from collections import defaultdict
import sys, math, os, subprocess
from array import array
from ROOT import TCanvas, TColor, TGaxis, TH1F, TH2F, TPad, TStyle, gStyle, gPad, TGaxis, TLine, TMath, TPaveText, TArc, TGraphPolar, TLatex, TH2Poly
from ROOT import kBlack, kCyan, kRed, kGreen, kMagenta
from functools import reduce

################################################################################################################################################
'''
ltsep package import and pathing definitions
'''

# Import package for cuts
from ltsep import Root

lt=Root(os.path.realpath(__file__),"Plot_Prod")

# Add this to all files for more dynamic pathing
USER=lt.USER # Grab user info for file finding
HOST=lt.HOST
REPLAYPATH=lt.REPLAYPATH
UTILPATH=lt.UTILPATH
LTANAPATH=lt.LTANAPATH
ANATYPE=lt.ANATYPE
OUTPATH=lt.OUTPATH

##################################################################################################################################################
# Importing utility functions

from utility import calculate_aver_simc, convert_TH1F_to_numpy

##################################################################################################################################################

def calculate_aver_data2(hist_data, hist_dummy, t_data, t_dummy, t_bins):

    # Ensure that the input histograms are properly initialized
    if not hist_data or not hist_dummy or not t_data or not t_dummy:
        print("Error: Input histograms are not properly initialized.")
        return []

    # Bin t_data and t_dummy in t_bins
    binned_t_data = t_data.Rebin(len(t_bins)-1, "binned_t_data", array('d', t_bins))
    binned_t_dummy = t_dummy.Rebin(len(t_bins)-1, "binned_t_dummy", array('d', t_bins))

    print("Binned t data contents:", [binned_t_data.GetBinContent(i) for i in range(1, binned_t_data.GetNbinsX()+1)])
    print("Binned t dummy contents:", [binned_t_dummy.GetBinContent(i) for i in range(1, binned_t_dummy.GetNbinsX()+1)])
    
    # Get the bin numbers of t_data and t_dummy
    bin_numbers_t_data = []
    bin_numbers_t_dummy = []
    for bin_idx in range(1, len(t_bins)):
        bin_center_data = binned_t_data.GetBinCenter(bin_idx)
        bin_number_data = hist_data.GetXaxis().FindBin(bin_center_data)  # Corrected line
        bin_numbers_t_data.append(bin_number_data)

        bin_center_dummy = binned_t_dummy.GetBinCenter(bin_idx)
        bin_number_dummy = hist_dummy.GetXaxis().FindBin(bin_center_dummy)  # Corrected line
        bin_numbers_t_dummy.append(bin_number_dummy)

        print("@@@@@@@@@@@@@@@@@@",bin_center_data,bin_number_data)
        
    # Bin hist_data and hist_dummy using the calculated bin numbers
    binned_hist_data = hist_data.Rebin(len(bin_numbers_t_data) - 1, "binned_hist_data", array('d', bin_numbers_t_data))
    binned_hist_dummy = hist_dummy.Rebin(len(bin_numbers_t_dummy) - 1, "binned_hist_dummy", array('d', bin_numbers_t_dummy))

    # Debugging step: Print histogram contents and properties
    print("Binned hist data contents:", [binned_hist_data.GetBinContent(i) for i in range(1, binned_hist_data.GetNbinsX()+1)])
    print("Binned hist dummy contents:", [binned_hist_dummy.GetBinContent(i) for i in range(1, binned_hist_dummy.GetNbinsX()+1)])
    
    # Create subtracted_hist by cloning binned_hist_data
    subtracted_hist = binned_hist_data.Clone("subtracted_hist")
    subtracted_hist.Add(binned_hist_dummy, -1)
    
    # Calculate the average per bin of the subtracted bins
    num_bins = subtracted_hist.GetNbinsX()
    averaged_values = []
    for bin_idx in range(1, num_bins+1):
        bin_content = subtracted_hist.GetBinContent(bin_idx)
        bin_width = subtracted_hist.GetBinWidth(bin_idx)
        average_value = bin_content / bin_width
        averaged_values.append(average_value)
    
    return averaged_values

def calculate_aver_data(hist_data, hist_dummy, t_data, t_bins):
    # Convert ROOT TH1F objects to NumPy arrays
    hist_data_array = np.array(hist_data, dtype=np.float64)
    t_data_array = np.array(t_data, dtype=np.float64)
    hist_dummy_array = np.array(hist_dummy, dtype=np.float64)

    # Calculate the bin centers for t_data
    t_bin_centers = (t_bins[:-1] + t_bins[1:]) / 2
    print("t_bin_centers:", t_bin_centers)

    # Bin the t_data using t_bins
    digitized = np.digitize(t_data_array, t_bins)
    print("digitized:", digitized)

    # Initialize arrays to store binned data
    hist_data_binned = np.zeros(len(t_bins) - 1)
    hist_dummy_binned = np.zeros(len(t_bins) - 1)

    # Loop through the bins, rebin hist_data and hist_dummy, then subtract and calculate averages
    for i in range(1, len(t_bins)):
        mask = (digitized == i)
        print("Processing bin {}:".format(i))
        print("mask:", mask)
        
        hist_data_bin = hist_data_array[mask].sum()  # Rebin hist_data
        hist_dummy_bin = hist_dummy_array[mask].sum()  # Rebin hist_dummy
        
        print("hist_data_bin:", hist_data_bin)
        print("hist_dummy_bin:", hist_dummy_bin)
        
        hist_data_binned[i - 1] = hist_data_bin
        hist_dummy_binned[i - 1] = hist_dummy_bin
        
    # Subtract hist_dummy from hist_data
    subtracted_data = hist_data_binned - hist_dummy_binned
    
    # Calculate bin averages of subtracted data
    bin_averages = subtracted_data / len(t_data_array)
    print("bin_averages:", bin_averages)

    return bin_averages

import numpy as np

def calculate_aver_data(hist_data, hist_dummy, t_data, t_bins):
    # Initialize lists for binned_t_data, iter_bins, binned_hist_data, binned_hist_dummy
    binned_t_data = []
    iter_bins = []
    binned_hist_data = []
    binned_hist_dummy = []

    # Loop through bins in t_data and identify events in specified bins
    for bin_index in range(1, t_data.GetNbinsX() + 1):
        bin_center = t_data.GetBinCenter(bin_index)
        if bin_center >= t_bins[0] and bin_center < t_bins[-1]:
            binned_t_data.append(bin_center)
            iter_bins.append(bin_index)

    # Loop through hist_data and hist_dummy using iter_bins
    for i in iter_bins:
        binned_hist_data.append(hist_data.GetBinContent(i))
        binned_hist_dummy.append(hist_dummy.GetBinContent(i))

    # Convert the lists to numpy arrays for subtraction
    binned_hist_data = np.array(binned_hist_data)
    binned_hist_dummy = np.array(binned_hist_dummy)

    # Subtract binned_hist_dummy from binned_hist_data element-wise
    subtract_hist = binned_hist_data - binned_hist_dummy

    # Calculate the average per bin value of subtract_hist
    aver_hist = np.mean(subtract_hist, axis=0)
    
    # Print statements to check sizes and values
    print("Size of binned_t_data:", len(binned_t_data))
    print("Size of binned_hist_data:", len(binned_hist_data))
    print("Size of binned_hist_dummy:", len(binned_hist_dummy))
    print("Size of t_bins:", len(t_bins))
    print("Values in binned_t_data:", binned_t_data)
    print("Values in binned_hist_data:", binned_hist_data)
    print("Values in binned_hist_dummy:", binned_hist_dummy)
    print("Values in t_bins:", t_bins)
    
    return aver_hist
    

##################################################################################################################################################

def aver_per_bin(histlist, inpDict):

    # Create empty histograms
    empty_hist = ROOT.TH1F()
    
    for hist in histlist:
        t_bins = hist["t_bins"]
        phi_bins = hist["phi_bins"]

        # Assign histograms for Q2
        if hist["phi_setting"] == "Center":
            Q2_Center_DATA = hist["H_Q2_DATA"]
        if hist["phi_setting"] == "Left":
            Q2_Left_DATA = hist["H_Q2_DATA"]
        if hist["phi_setting"] == "Right":
            Q2_Right_DATA = hist["H_Q2_DATA"]

        # Assign histograms for W
        if hist["phi_setting"] == "Center":
            W_Center_DATA = hist["H_W_DATA"]
        if hist["phi_setting"] == "Left":
            W_Left_DATA = hist["H_W_DATA"]
        if hist["phi_setting"] == "Right":
            W_Right_DATA = hist["H_W_DATA"]

        # Assign histograms for t
        if hist["phi_setting"] == "Center":
            t_Center_DATA = hist["H_t_DATA"]
        if hist["phi_setting"] == "Left":
            t_Left_DATA = hist["H_t_DATA"]
        if hist["phi_setting"] == "Right":
            t_Right_DATA = hist["H_t_DATA"]

        # Assign histograms for Q2
        if hist["phi_setting"] == "Center":
            Q2_Center_DUMMY = hist["H_Q2_DUMMY"]
        if hist["phi_setting"] == "Left":
            Q2_Left_DUMMY = hist["H_Q2_DUMMY"]
        if hist["phi_setting"] == "Right":
            Q2_Right_DUMMY = hist["H_Q2_DUMMY"]

        # Assign histograms for W
        if hist["phi_setting"] == "Center":
            W_Center_DUMMY = hist["H_W_DUMMY"]
        if hist["phi_setting"] == "Left":
            W_Left_DUMMY = hist["H_W_DUMMY"]
        if hist["phi_setting"] == "Right":
            W_Right_DUMMY = hist["H_W_DUMMY"]

        # Assign histograms for t
        if hist["phi_setting"] == "Center":
            t_Center_DUMMY = hist["H_t_DUMMY"]
        if hist["phi_setting"] == "Left":
            t_Left_DUMMY = hist["H_t_DUMMY"]
        if hist["phi_setting"] == "Right":
            t_Right_DUMMY = hist["H_t_DUMMY"]

        # Assign histograms for Q2
        if hist["phi_setting"] == "Center":
            Q2_Center_SIMC = hist["H_Q2_SIMC"]
        if hist["phi_setting"] == "Left":
            Q2_Left_SIMC = hist["H_Q2_SIMC"]
        if hist["phi_setting"] == "Right":
            Q2_Right_SIMC = hist["H_Q2_SIMC"]

        # Assign histograms for W
        if hist["phi_setting"] == "Center":
            W_Center_SIMC = hist["H_W_SIMC"]
        if hist["phi_setting"] == "Left":
            W_Left_SIMC = hist["H_W_SIMC"]
        if hist["phi_setting"] == "Right":
            W_Right_SIMC = hist["H_W_SIMC"]

        # Assign histograms for t
        if hist["phi_setting"] == "Center":
            t_Center_SIMC = hist["H_t_SIMC"]
        if hist["phi_setting"] == "Left":
            t_Left_SIMC = hist["H_t_SIMC"]
        if hist["phi_setting"] == "Right":
            t_Right_SIMC = hist["H_t_SIMC"]
            
    # Combine histograms for Q2_data
    Q2_data = ROOT.TH1F("Q2_data", "Combined Q2_data Histogram", Q2_Center_DATA.GetNbinsX(), Q2_Center_DATA.GetXaxis().GetXmin(), Q2_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_DATA.GetBinContent(bin) + Q2_Left_DATA.GetBinContent(bin) + Q2_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_DATA.GetBinContent(bin) + Q2_Left_DATA.GetBinContent(bin)
        Q2_data.SetBinContent(bin, combined_content)

    # Combine histograms for W_data
    W_data = ROOT.TH1F("W_data", "Combined W_data Histogram", W_Center_DATA.GetNbinsX(), W_Center_DATA.GetXaxis().GetXmin(), W_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, W_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = W_Center_DATA.GetBinContent(bin) + W_Left_DATA.GetBinContent(bin) + W_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_DATA.GetBinContent(bin) + W_Left_DATA.GetBinContent(bin)
        W_data.SetBinContent(bin, combined_content)

    # Combine histograms for t_data
    t_data = ROOT.TH1F("t_data", "Combined t_data Histogram", t_Center_DATA.GetNbinsX(), t_Center_DATA.GetXaxis().GetXmin(), t_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, t_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = t_Center_DATA.GetBinContent(bin) + t_Left_DATA.GetBinContent(bin) + t_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = t_Center_DATA.GetBinContent(bin) + t_Left_DATA.GetBinContent(bin)
        t_data.SetBinContent(bin, combined_content)

    # Combine histograms for Q2_dummy
    Q2_dummy = ROOT.TH1F("Q2_dummy", "Combined Q2_dummy Histogram", Q2_Center_DUMMY.GetNbinsX(), Q2_Center_DUMMY.GetXaxis().GetXmin(), Q2_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_DUMMY.GetBinContent(bin) + Q2_Left_DUMMY.GetBinContent(bin) + Q2_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_DUMMY.GetBinContent(bin) + Q2_Left_DUMMY.GetBinContent(bin)
        Q2_dummy.SetBinContent(bin, combined_content)

    # Combine histograms for W_dummy
    W_dummy = ROOT.TH1F("W_dummy", "Combined W_dummy Histogram", W_Center_DUMMY.GetNbinsX(), W_Center_DUMMY.GetXaxis().GetXmin(), W_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, W_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = W_Center_DUMMY.GetBinContent(bin) + W_Left_DUMMY.GetBinContent(bin) + W_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_DUMMY.GetBinContent(bin) + W_Left_DUMMY.GetBinContent(bin)
        W_dummy.SetBinContent(bin, combined_content)

    # Combine histograms for t_dummy
    t_dummy = ROOT.TH1F("t_dummy", "Combined t_dummy Histogram", t_Center_DUMMY.GetNbinsX(), t_Center_DUMMY.GetXaxis().GetXmin(), t_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, t_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = t_Center_DUMMY.GetBinContent(bin) + t_Left_DUMMY.GetBinContent(bin) + t_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = t_Center_DUMMY.GetBinContent(bin) + t_Left_DUMMY.GetBinContent(bin)
        t_dummy.SetBinContent(bin, combined_content)

    Q2_aver_data = calculate_aver_data(Q2_data, Q2_dummy, t_data, t_bins)
    W_aver_data = calculate_aver_data(W_data, W_dummy, t_data, t_bins)
    t_aver_data = calculate_aver_data(t_data, t_dummy, t_data, t_bins)
        
    # Combine histograms for Q2_simc
    Q2_simc = ROOT.TH1F("Q2_simc", "Combined Q2_simc Histogram", Q2_Center_SIMC.GetNbinsX(), Q2_Center_SIMC.GetXaxis().GetXmin(), Q2_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_SIMC.GetBinContent(bin) + Q2_Left_SIMC.GetBinContent(bin) + Q2_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_SIMC.GetBinContent(bin) + Q2_Left_SIMC.GetBinContent(bin)
        Q2_simc.SetBinContent(bin, combined_content)

    # Combine histograms for W_simc
    W_simc = ROOT.TH1F("W_simc", "Combined W_simc Histogram", W_Center_SIMC.GetNbinsX(), W_Center_SIMC.GetXaxis().GetXmin(), W_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, W_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = W_Center_SIMC.GetBinContent(bin) + W_Left_SIMC.GetBinContent(bin) + W_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_SIMC.GetBinContent(bin) + W_Left_SIMC.GetBinContent(bin)
        W_simc.SetBinContent(bin, combined_content)

    # Combine histograms for t_simc
    t_simc = ROOT.TH1F("t_simc", "Combined t_simc Histogram", t_Center_SIMC.GetNbinsX(), t_Center_SIMC.GetXaxis().GetXmin(), t_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, t_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = t_Center_SIMC.GetBinContent(bin) + t_Left_SIMC.GetBinContent(bin) + t_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = t_Center_SIMC.GetBinContent(bin) + t_Left_SIMC.GetBinContent(bin)
        t_simc.SetBinContent(bin, combined_content)
    
    Q2_aver_simc = calculate_aver_simc(Q2_simc, t_bins)
    W_aver_simc = calculate_aver_simc(W_simc, t_bins)
    t_aver_simc = calculate_aver_simc(t_simc, t_bins)
    
    averDict = {
        "t_bins" : t_bins,
        "phi_bins" : phi_bins,                       
        "Q2_aver_data" : Q2_aver_data,
        "W_aver_data" : W_aver_data,
        "t_aver_data" : t_aver_data,
        "Q2_aver_simc" : Q2_aver_simc,
        "W_aver_simc" : W_aver_simc,
        "t_aver_simc" : t_aver_simc,        
    }

    return averDict
