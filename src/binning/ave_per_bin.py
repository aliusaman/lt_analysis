#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2023-09-21 09:59:18 trottar"
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
from ROOT import TCanvas, TH1D, TH2D, gStyle, gPad, TPaveText, TArc, TGraphPolar, TFile, TLegend, TMultiGraph, TLine
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

def calculate_ave_data(kin_type, hist_data, hist_dummy, t_data, t_bins, phi_bins):
    
    # Initialize lists for binned_t_data, binned_hist_data, and binned_hist_dummy
    binned_t_data = []
    binned_hist_data = []
    binned_hist_dummy = []
    
    t_bins = np.append(t_bins, 0.0) # Needed to fully finish loop over bins
    phi_bins = np.append(phi_bins, 0.0) # Needed to fully finish loop over bins
    # Loop through bins in t_data and identify events in specified bins
    for j in range(len(t_bins)-1):
        tmp_t_data = [[],[]]
        tmp_hist_data = [[],[]]
        tmp_hist_dummy = [[],[]]
        for bin_index in range(1, t_data.GetNbinsX() + 1):
            bin_center = t_data.GetBinCenter(bin_index)
            if t_bins[j] <= bin_center <= t_bins[j+1]:
                if hist_data.GetBinContent(bin_index) > 0:
                    print("Checking if {} <= {} <= {}".format(t_bins[j], bin_center, t_bins[j+1]))
                    print("Bin {}, Hist bin {} Passed with content {}".format(j+1, hist_data.GetBinCenter(bin_index), hist_data.GetBinContent(bin_index)))
                    tmp_t_data[0].append(t_data.GetBinCenter(bin_index))
                    tmp_t_data[1].append(t_data.GetBinContent(bin_index))
                    tmp_hist_data[0].append(hist_data.GetBinCenter(bin_index))
                    tmp_hist_data[1].append(hist_data.GetBinContent(bin_index))
                    tmp_hist_dummy[0].append(hist_dummy.GetBinCenter(bin_index))
                    tmp_hist_dummy[1].append(hist_dummy.GetBinContent(bin_index))
        binned_t_data.append(tmp_t_data)
        binned_hist_data.append(tmp_hist_data)
        binned_hist_dummy.append(tmp_hist_dummy)

    ave_hist = []
    binned_sub_data = [[],[]]
    i=0 # iter
    print("-"*25)
    # Subtract binned_hist_dummy from binned_hist_data element-wise
    for data, dummy in zip(binned_hist_data, binned_hist_dummy):
        bin_val_data, hist_val_data = data
        bin_val_dummy, hist_val_dummy = dummy
        sub_val = np.subtract(hist_val_data, hist_val_dummy)
        if sub_val.size != 0:
            # Calculate the weighted sum of frequencies and divide by the total count
            weighted_sum = np.sum(sub_val * bin_val_data)
            total_count = np.sum(sub_val)
            average = weighted_sum / total_count            
            ave_hist.append(average)
            #print("Weighted Sum:",weighted_sum)
            #print("Total Count:",total_count)
            #print("Average for t-bin {}:".format(i),average)
            binned_sub_data[0].append(bin_val_data)
            binned_sub_data[1].append(sub_val)
        else:
            ave_hist.append(0)
            #print("Weighted Sum: N/A")
            #print("Total Count: N/A")
            #print("Average for t-bin {}: 0.0".format(i))
            binned_sub_data[0].append(bin_val_data)
            binned_sub_data[1].append([0]*len(bin_val_data))
        i+=1
    
    # Print statements to check sizes
    #print("Size of binned_t_data:", len(binned_t_data))
    #print("Size of binned_hist_data:", len(binned_hist_data))
    #print("Size of binned_hist_dummy:", len(binned_hist_dummy))
    #print("Size of binned_sub_data:", len(binned_sub_data[1]))
    #print("Size of ave_hist:", len(ave_hist))
    #print("Size of t_bins:", len(t_bins))
    #print("Size of phi_bins:", len(phi_bins), "\n")

    dict_lst = []
    for j in range(len(t_bins) - 1):
        tbin_index = j
        for k in range(len(phi_bins) - 1):
            phibin_index = k
            hist_val = [binned_sub_data[0][j], binned_sub_data[1][j]]
            ave_val = ave_hist[j]
            print("Average {} for t-bin {} phi-bin {}: {:.3f}".format(kin_type, j, k, ave_val))
            dict_lst.append((tbin_index, phibin_index, hist_val, ave_val))

    # Group the tuples by the first two elements using defaultdict
    groups = defaultdict(list)
    for tup in dict_lst:
        key = (tup[0], tup[1])
        groups[key] = {
            "{}_arr".format(kin_type) : tup[2],
            "{}_ave".format(kin_type) : tup[3],
        }            
            
    return groups

def calculate_ave_simc(kin_type, hist_simc, t_simc, t_bins, phi_bins):
    
    # Initialize lists for binned_t_simc, and binned_hist_simc
    binned_t_simc = []
    binned_hist_simc = []
    
    t_bins = np.append(t_bins, 0.0) # Needed to fully finish loop over bins
    phi_bins = np.append(phi_bins, 0.0) # Needed to fully finish loop over bins
    # Loop through bins in t_simc and identify events in specified bins
    for j in range(len(t_bins)-1):
        tmp_t_simc = [[],[]]
        tmp_hist_simc = [[],[]]
        for bin_index in range(1, t_simc.GetNbinsX() + 1):
            bin_center = t_simc.GetBinCenter(bin_index)
            if t_bins[j] <= bin_center <= t_bins[j+1]:
                if hist_simc.GetBinContent(bin_index) > 0:
                    #print("Checking if {} <= {} <= {}".format(t_bins[j], bin_center, t_bins[j+1]))
                    #print("Bin {}, Hist bin {} Passed with content {}".format(j, hist_simc.GetBinCenter(bin_index), hist_simc.GetBinContent(bin_index)))
                    tmp_t_simc[0].append(t_simc.GetBinCenter(bin_index))
                    tmp_t_simc[1].append(t_simc.GetBinContent(bin_index))
                    tmp_hist_simc[0].append(hist_simc.GetBinCenter(bin_index))
                    tmp_hist_simc[1].append(hist_simc.GetBinContent(bin_index))
        binned_t_simc.append(tmp_t_simc)
        binned_hist_simc.append(tmp_hist_simc)

    ave_hist = []
    binned_sub_simc = [[],[]]
    i=0 # iter
    print("-"*25)
    for simc in binned_hist_simc:
        bin_val_simc, hist_val_simc = simc
        sub_val = np.array(hist_val_simc) # No dummy subtraction for simc
        if sub_val.size != 0:
            # Calculate the weighted sum of frequencies and divide by the total count
            weighted_sum = np.sum(sub_val * bin_val_simc)
            total_count = np.sum(sub_val)
            average = weighted_sum / total_count            
            ave_hist.append(average)
            #print("Weighted Sum:",weighted_sum)
            #print("Total Count:",total_count)
            #print("Average for t-bin {}:".format(i),average)
            binned_sub_simc[0].append(bin_val_simc)
            binned_sub_simc[1].append(sub_val)
        else:
            ave_hist.append(0)
            #print("Weighted Sum: N/A")
            #print("Total Count: N/A")
            #print("Average for t-bin {}: 0.0".format(i))
            binned_sub_simc[0].append(bin_val_simc)
            binned_sub_simc[1].append([0]*len(bin_val_simc))
        i+=1
    
    # Print statements to check sizes
    #print("Size of binned_t_simc:", len(binned_t_simc))
    #print("Size of binned_hist_simc:", len(binned_hist_simc))
    #print("Size of binned_sub_simc:", len(binned_sub_simc[1]))
    #print("Size of ave_hist:", len(ave_hist))
    #print("Size of t_bins:", len(t_bins))
    #print("Size of phi_bins:", len(phi_bins), "\n")

    dict_lst = []
    for j in range(len(t_bins) - 1):
        tbin_index = j
        for k in range(len(phi_bins) - 1):
            phibin_index = k
            hist_val = [binned_sub_simc[0][j], binned_sub_simc[1][j]]
            ave_val = ave_hist[j]
            print("Average {} for t-bin {} phi-bin {}: {:.3f}".format(kin_type, j, k, ave_val))            
            dict_lst.append((tbin_index, phibin_index, hist_val, ave_val))

    # Group the tuples by the first two elements using defaultdict
    groups = defaultdict(list)
    for tup in dict_lst:
        key = (tup[0], tup[1])
        groups[key] = {
            "{}_arr".format(kin_type) : tup[2],
            "{}_ave".format(kin_type) : tup[3],
        }                    
    
    return groups

##################################################################################################################################################

def ave_per_bin_data(histlist, inpDict):

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
            
    # Combine histograms for Q2_data
    Q2_data = TH1D("Q2_data", "Combined Q2_data Histogram", Q2_Center_DATA.GetNbinsX(), Q2_Center_DATA.GetXaxis().GetXmin(), Q2_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_DATA.GetBinContent(bin) + Q2_Left_DATA.GetBinContent(bin) + Q2_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_DATA.GetBinContent(bin) + Q2_Left_DATA.GetBinContent(bin)
        Q2_data.SetBinContent(bin, combined_content)

    # Combine histograms for W_data
    W_data = TH1D("W_data", "Combined W_data Histogram", W_Center_DATA.GetNbinsX(), W_Center_DATA.GetXaxis().GetXmin(), W_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, W_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = W_Center_DATA.GetBinContent(bin) + W_Left_DATA.GetBinContent(bin) + W_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_DATA.GetBinContent(bin) + W_Left_DATA.GetBinContent(bin)
        W_data.SetBinContent(bin, combined_content)

    # Combine histograms for t_data
    t_data = TH1D("t_data", "Combined t_data Histogram", t_Center_DATA.GetNbinsX(), t_Center_DATA.GetXaxis().GetXmin(), t_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, t_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = t_Center_DATA.GetBinContent(bin) + t_Left_DATA.GetBinContent(bin) + t_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = t_Center_DATA.GetBinContent(bin) + t_Left_DATA.GetBinContent(bin)
        t_data.SetBinContent(bin, combined_content)

    # Combine histograms for Q2_dummy
    Q2_dummy = TH1D("Q2_dummy", "Combined Q2_dummy Histogram", Q2_Center_DUMMY.GetNbinsX(), Q2_Center_DUMMY.GetXaxis().GetXmin(), Q2_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_DUMMY.GetBinContent(bin) + Q2_Left_DUMMY.GetBinContent(bin) + Q2_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_DUMMY.GetBinContent(bin) + Q2_Left_DUMMY.GetBinContent(bin)
        Q2_dummy.SetBinContent(bin, combined_content)

    # Combine histograms for W_dummy
    W_dummy = TH1D("W_dummy", "Combined W_dummy Histogram", W_Center_DUMMY.GetNbinsX(), W_Center_DUMMY.GetXaxis().GetXmin(), W_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, W_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = W_Center_DUMMY.GetBinContent(bin) + W_Left_DUMMY.GetBinContent(bin) + W_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_DUMMY.GetBinContent(bin) + W_Left_DUMMY.GetBinContent(bin)
        W_dummy.SetBinContent(bin, combined_content)

    # Combine histograms for t_dummy
    t_dummy = TH1D("t_dummy", "Combined t_dummy Histogram", t_Center_DUMMY.GetNbinsX(), t_Center_DUMMY.GetXaxis().GetXmin(), t_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, t_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = t_Center_DUMMY.GetBinContent(bin) + t_Left_DUMMY.GetBinContent(bin) + t_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = t_Center_DUMMY.GetBinContent(bin) + t_Left_DUMMY.GetBinContent(bin)
        t_dummy.SetBinContent(bin, combined_content)

    aveDict = {
        "t_bins" : t_bins,
        "phi_bins" : phi_bins
    }
        
    # List of kinematic types
    kinematic_types = ["Q2", "W", "t"]

    # Loop through histlist and update aveDict
    for hist in histlist:
        print("\n\n")
        print("-"*25)
        print("-"*25)
        print("Finding data averages for {}...".format(hist["phi_setting"]))
        print("-"*25)
        print("-"*25)
        aveDict[hist["phi_setting"]] = {}
        for kin_type in kinematic_types:
            aveDict[hist["phi_setting"]][kin_type] = calculate_ave_data(kin_type, hist["H_{}_DATA".format(kin_type)], hist["H_{}_DUMMY".format(kin_type)], hist["H_t_DATA"], t_bins, phi_bins)
                
    return {"binned_DATA" : aveDict}

def ave_per_bin_simc(histlist, inpDict):

    for hist in histlist:
        t_bins = hist["t_bins"]
        phi_bins = hist["phi_bins"]

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
    
    # Combine histograms for Q2_simc
    Q2_simc = TH1D("Q2_simc", "Combined Q2_simc Histogram", Q2_Center_SIMC.GetNbinsX(), Q2_Center_SIMC.GetXaxis().GetXmin(), Q2_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_SIMC.GetBinContent(bin) + Q2_Left_SIMC.GetBinContent(bin) + Q2_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_SIMC.GetBinContent(bin) + Q2_Left_SIMC.GetBinContent(bin)
        Q2_simc.SetBinContent(bin, combined_content)

    # Combine histograms for W_simc
    W_simc = TH1D("W_simc", "Combined W_simc Histogram", W_Center_SIMC.GetNbinsX(), W_Center_SIMC.GetXaxis().GetXmin(), W_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, W_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = W_Center_SIMC.GetBinContent(bin) + W_Left_SIMC.GetBinContent(bin) + W_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_SIMC.GetBinContent(bin) + W_Left_SIMC.GetBinContent(bin)
        W_simc.SetBinContent(bin, combined_content)

    # Combine histograms for t_simc
    t_simc = TH1D("t_simc", "Combined t_simc Histogram", t_Center_SIMC.GetNbinsX(), t_Center_SIMC.GetXaxis().GetXmin(), t_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, t_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = t_Center_SIMC.GetBinContent(bin) + t_Left_SIMC.GetBinContent(bin) + t_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = t_Center_SIMC.GetBinContent(bin) + t_Left_SIMC.GetBinContent(bin)
        t_simc.SetBinContent(bin, combined_content)

    aveDict = {
        "t_bins" : t_bins,
        "phi_bins" : phi_bins
    }
        
    # List of kinematic types
    kinematic_types = ["Q2", "W", "t"]

    # Loop through histlist and update aveDict
    for hist in histlist:
        print("\n\n")
        print("-"*25)
        print("-"*25)
        print("Finding simc averages for {}...".format(hist["phi_setting"]))
        print("-"*25)
        print("-"*25)
        aveDict[hist["phi_setting"]] = {}
        for kin_type in kinematic_types:
            aveDict[hist["phi_setting"]][kin_type] = calculate_ave_simc(kin_type, hist["H_{}_SIMC".format(kin_type)], hist["H_t_SIMC"], t_bins, phi_bins)

    return {"binned_SIMC" : aveDict}
