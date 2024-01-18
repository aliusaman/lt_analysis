#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2024-01-18 02:46:00 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import pandas as pd
import root_pandas as rpd
import numpy as np
import ROOT
from ROOT import TCanvas, TGraph, TGraphErrors, TMultiGraph, TLegend
from ROOT import kBlack, kCyan, kRed, kGreen, kMagenta
from functools import reduce
import re
import sys, math, os, subprocess

##################################################################################################################################################
# Check the number of arguments provided to the script

if len(sys.argv)-1!=10:
    print("!!!!! ERROR !!!!!\n Expected 10 arguments\n Usage is with - ParticleType POL Q2 W LOEPS HIEPS NumtBins NumPhiBins KIN OutUnsepxsectsFilename\n!!!!! ERROR !!!!!")
    sys.exit(1)

###############################################################################################################################################

ParticleType = sys.argv[1]
POL = sys.argv[2]

Q2 = sys.argv[3]
W = sys.argv[4]

LOEPS = sys.argv[5]
HIEPS = sys.argv[6]

NumtBins = int(sys.argv[7])
NumPhiBins = int(sys.argv[8])

kinematics = sys.argv[9]
OutFilename = sys.argv[10]

if int(POL) == 1:
    pol_str = "pl"
elif int(POL) == -1:
    pol_str = "mn"
else:
    print("ERROR: Invalid polarity...must be +1 or -1")
    sys.exit(2)
    
###############################################################################################################################################

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

foutname = OUTPATH+"/" + OutFilename + ".root"
fouttxt  = OUTPATH+"/" + OutFilename + ".txt"
outputpdf  = OUTPATH+"/" + OutFilename + ".pdf"

################################################################################################################################################
# Suppressing the terminal splash of Print()
ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = kError;")
################################################################################################################################################

def are_within_tolerance(num1, num2, tolerance=0.1):
    return abs(num1 - num2) <= tolerance

def file_to_df(f_name, columns):
    '''
    Read in file and convert to dataframe with custom column names
    '''

    lineskip=False
    
    # Open the file for reading
    with open(f_name, 'r') as file:
        lines = file.readlines()
        if '1.000000\n' in lines:
            lineskip=True

    if lineskip:
        df = pd.read_csv(f_name, header=None, sep=' ', skiprows=1, skipfooter=1, engine='python')
    else:
        df = pd.read_csv(f_name, header=None, sep=' ')    
    df.columns = columns
    return df

################################################################################################################################################

def fix_spacing(f_name):
    '''
    Fortran created files are bad with spacing. This fixes it.
    '''

    # Open the file for reading
    with open(f_name, 'r') as file:

        # Read the lines of the file and split based on whitespace
        lines = file.readlines()
        lines = [re.split(r'\s+', line.strip()) for line in lines]

        # Join the split lines with a single space
        lines = [' '.join(line) for line in lines]

        # Write the lines back to the file
        with open(f_name, 'w') as output:
            output.write('\n'.join(lines))

# Fix file spacing to work in pandas
fix_spacing(LTANAPATH+"/src/{}/averages/avek.{}.dat".format(ParticleType, Q2.replace("p","")))
fix_spacing(LTANAPATH+"/src/{}/xsects/x_unsep.{}_{}_{:.0f}.dat".format(ParticleType, pol_str, Q2.replace("p",""), float(LOEPS)*100))
fix_spacing(LTANAPATH+"/src/{}/xsects/x_unsep.{}_{}_{:.0f}.dat".format(ParticleType, pol_str, Q2.replace("p",""), float(HIEPS)*100))
fix_spacing(LTANAPATH+"/src/{}/xsects/x_sep.{}_{}.dat".format(ParticleType, pol_str, Q2.replace("p","")))
################################################################################################################################################
# Read in files and convert to dataframes

file_df_dict = {}

setting_file = LTANAPATH+"/src/{}/list.settings".format(ParticleType)
file_df_dict['setting_df'] = file_to_df(setting_file, ['POL', 'Q2', 'EPSVAL', 'thpq', 'TMIN', 'TMAX', 'NumtBins'])

try:
    with open("{}/src/{}/t_bin_interval".format(LTANAPATH, ParticleType), "r") as file:
        # Read all lines from the file into a list
        all_lines = file.readlines()
        # Check if the file has at least two lines
        if len(all_lines) >= 2:
            # Extract the second line and remove leading/trailing whitespace
            t_bins = all_lines[1].split("\t")
            del t_bins[0]
            t_bins = np.array([float(element) for element in t_bins])
except FileNotFoundError:
    print("{} not found...".format("{}/src/{}/t_bin_interval".format(LTANAPATH, ParticleType)))
except IOError:
    print("Error reading {}...".format("{}/src/{}/t_bin_interval".format(LTANAPATH, ParticleType)))    

t_bin_centers = (t_bins[:-1] + t_bins[1:]) / 2

try:
    with open("{}/src/{}/phi_bin_interval".format(LTANAPATH, ParticleType), "r") as file:
        # Read all lines from the file into a list
        all_lines = file.readlines()
        # Check if the file has at least two lines
        if len(all_lines) >= 2:
            # Extract the second line and remove leading/trailing whitespace
            phi_bins = all_lines[1].split("\t")
            del phi_bins[0]
            phi_bins = np.array([float(element) for element in phi_bins])
except FileNotFoundError:
    print("{} not found...".format("{}/src/{}/phi_bin_interval".format(LTANAPATH, ParticleType)))
except IOError:
    print("Error reading {}...".format("{}/src/{}/phi_bin_interval".format(LTANAPATH, ParticleType)))    

#phi_bin_centers = (phi_bins[:-1] + phi_bins[1:]) / 2
phi_bin_centers = phi_bins
    
for i,row in file_df_dict['setting_df'].iterrows():
    if row['Q2'] == float(Q2.replace("p",".")):
        file_df_dict['beam_file'] = file_to_df(LTANAPATH+"/src/{}/beam/Eb_KLT.dat".format(ParticleType), ['ebeam', 'Q2', 'EPSVAL'])
        file_df_dict['avek_file'] = file_to_df(LTANAPATH+"/src/{}/averages/avek.{}.dat".format(ParticleType, Q2.replace("p","")) \
                                               , ['W', 'dW', 'Q2', 'dQ2', 't', 'dt', 'th_pos', "tbin"])        
        
        if row['EPSVAL'] == float(LOEPS):
            file_df_dict['aver_loeps'] = file_to_df( \
                                                     LTANAPATH+"/src/{}/averages/aver.{}_{}_{:.0f}.dat" \
                                                     .format(ParticleType, pol_str, Q2.replace("p",""), float(LOEPS)*100) \
                                                     , ['ratio', 'dratio', 'phibin', 'tbin'])            
            if row['thpq'] < 0.0:
                file_df_dict['kindata_loeps_{}'.format('right')] = file_to_df( \
                                                                               LTANAPATH+"/src/{}/kindata/kindata.{}_{}_{:.0f}_{}.dat" \
                                                                               .format(ParticleType, pol_str, Q2.replace("p",""), float(LOEPS)*100, int(row['thpq']*1000)) \
                                                                               , ['Q2', 'dQ2', 'W', 'dW', 't', 'dt'])
            if row['thpq'] > 0.0:
                file_df_dict['kindata_loeps_{}'.format('left')] = file_to_df( \
                                                                              LTANAPATH+"/src/{}/kindata/kindata.{}_{}_{:.0f}_+{}.dat" \
                                                                              .format(ParticleType, pol_str, Q2.replace("p",""), float(LOEPS)*100, int(row['thpq']*1000)) \
                                                                              , ['Q2', 'dQ2', 'W', 'dW', 't', 'dt'])
            if row['thpq'] == 0.0:
                file_df_dict['kindata_loeps_{}'.format('center')] = file_to_df( \
                                                                                LTANAPATH+"/src/{}/kindata/kindata.{}_{}_{:.0f}_+0000.dat" \
                                                                                .format(ParticleType, pol_str, Q2.replace("p",""), float(LOEPS)*100) \
                                                                                , ['Q2', 'dQ2', 'W', 'dW', 't', 'dt'])
            file_df_dict['unsep_file_loeps'] = file_to_df( \
                                                            LTANAPATH+"/src/{}/xsects/x_unsep.{}_{}_{:.0f}.dat" \
                                                            .format(ParticleType, pol_str, Q2.replace("p",""), float(LOEPS)*100) \
                                                            , ['x_real', 'dx_real', 'x_mod', 'eps', 'th_cm', 'phi', 't', 'tm', 'W', 'Q2'])

        if row['EPSVAL'] == float(HIEPS):
            file_df_dict['aver_hieps'] = file_to_df( \
                                                     LTANAPATH+"/src/{}/averages/aver.{}_{}_{:.0f}.dat" \
                                                     .format(ParticleType, pol_str, Q2.replace("p",""), float(HIEPS)*100) \
                                                     , ['ratio', 'dratio', 'phibin', 'tbin'])            
            if row['thpq'] < 0.0:
                file_df_dict['kindata_hieps_{}'.format('right')] = file_to_df( \
                                                                               LTANAPATH+"/src/{}/kindata/kindata.{}_{}_{:.0f}_{}.dat" \
                                                                               .format(ParticleType, pol_str, Q2.replace("p",""), float(HIEPS)*100, int(row['thpq']*1000)) \
                                                                               , ['Q2', 'dQ2', 'W', 'dW', 't', 'dt'])
            if row['thpq'] > 0.0:
                file_df_dict['kindata_hieps_{}'.format('left')] = file_to_df( \
                                                                              LTANAPATH+"/src/{}/kindata/kindata.{}_{}_{:.0f}_+{}.dat" \
                                                                              .format(ParticleType, pol_str, Q2.replace("p",""), float(HIEPS)*100, int(row['thpq']*1000)) \
                                                                              , ['Q2', 'dQ2', 'W', 'dW', 't', 'dt'])
            if row['thpq'] == 0.0:
                file_df_dict['kindata_hieps_{}'.format('center')] = file_to_df( \
                                                                                LTANAPATH+"/src/{}/kindata/kindata.{}_{}_{:.0f}_+0000.dat" \
                                                                                .format(ParticleType, pol_str, Q2.replace("p",""), float(HIEPS)*100) \
                                                                                , ['Q2', 'dQ2', 'W', 'dW', 't', 'dt'])
            file_df_dict['unsep_file_hieps'] = file_to_df( \
                                                            LTANAPATH+"/src/{}/xsects/x_unsep.{}_{}_{:.0f}.dat" \
                                                            .format(ParticleType, pol_str, Q2.replace("p",""), float(HIEPS)*100) \
                                                            , ['x_real', 'dx_real', 'x_mod', 'eps', 'th_cm', 'phi', 't', 'tm', 'W', 'Q2'])
        file_df_dict['sep_file'] = file_to_df( \
                                               LTANAPATH+"/src/{}/xsects/x_sep.{}_{}.dat" \
                                               .format(ParticleType, pol_str, Q2.replace("p","")) \
                                               , ['sigT', 'dsigT', 'sigL', 'dsigL', 'sigLT', 'dsigLT', 'sigTT', 'dsigTT', 'chisq', 't', 'tm', 'W', 'Q2'])

            
################################################################################################################################################
ROOT.gROOT.SetBatch(ROOT.kTRUE) # Set ROOT to batch mode explicitly, does not splash anything to screen
################################################################################################################################################

C_ratio_phi = TCanvas()
C_ratio_phi.SetGrid()
C_ratio_phi.Divide(1,NumtBins)
l_ratio_phi = TLegend(0.7, 0.6, 0.9, 0.9)

multiDict = {}
for k in range(NumtBins):

    multiDict["G_ratio_phi_{}".format(k+1)] = TMultiGraph()
    
    G_ratio_phi_loeps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_ratio_phi_loeps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_loeps']['phibin'].tolist())[i]], np.array(file_df_dict['aver_loeps']['ratio'].tolist())[i])
            G_ratio_phi_loeps.SetPointError(j, 0, np.array(file_df_dict['aver_loeps']['dratio'].tolist())[i])
            j+=1
    G_ratio_phi_loeps.SetMarkerStyle(21)
    G_ratio_phi_loeps.SetMarkerSize(1)
    G_ratio_phi_loeps.SetMarkerColor(1)
    multiDict["G_ratio_phi_{}".format(k+1)].Add(G_ratio_phi_loeps)

    G_ratio_phi_hieps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_ratio_phi_hieps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_hieps']['phibin'].tolist())[i]], np.array(file_df_dict['aver_hieps']['ratio'].tolist())[i])
            G_ratio_phi_hieps.SetPointError(j, 0, np.array(file_df_dict['aver_hieps']['dratio'].tolist())[i])
            j+=1
    G_ratio_phi_hieps.SetMarkerStyle(23)
    G_ratio_phi_hieps.SetMarkerSize(1)
    G_ratio_phi_hieps.SetMarkerColor(2)
    multiDict["G_ratio_phi_{}".format(k+1)].Add(G_ratio_phi_hieps)    
    
    C_ratio_phi.cd(k+1)
    
    multiDict["G_ratio_phi_{}".format(k+1)].Draw('AP')
    multiDict["G_ratio_phi_{}".format(k+1)].SetTitle("t = {:.2f} ; #phi; Ratio".format(t_bin_centers[k]))
    
    multiDict["G_ratio_phi_{}".format(k+1)].GetYaxis().SetTitleOffset(1.5)
    multiDict["G_ratio_phi_{}".format(k+1)].GetXaxis().SetTitleOffset(1.5)
    multiDict["G_ratio_phi_{}".format(k+1)].GetXaxis().SetLabelSize(0.04)

    # Add a gray line at unity
    line_at_y1 = TLine(multiDict["G_ratio_phi_{}".format(k+1)].GetXaxis().GetXmin(), 1.0, multiDict["G_ratio_phi_{}".format(k+1)].GetXaxis().GetXmax(), 1.0)
    line_at_y1.SetLineColor(17)  # 17 corresponds to gray color
    line_at_y1.SetLineStyle(2)   # Dashed line style
    line_at_y1.Draw("same")
    
l_ratio_phi.AddEntry(G_ratio_phi_loeps,"loeps")
l_ratio_phi.AddEntry(G_ratio_phi_hieps,"hieps")
l_ratio_phi.Draw()
C_ratio_phi.Print(outputpdf + '(')

C_Q2_t = TCanvas()
C_Q2_t.SetGrid()
l_Q2_t = TLegend(0.7, 0.6, 0.9, 0.9)


G_Q2_t = TMultiGraph()
for k in range(NumtBins):

    G_Q2_t_loeps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_Q2_t_loeps.SetPoint(j, t_bins[np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i]], np.array(file_df_dict['unsep_file_loeps']['Q2'].tolist())[i])
            j+=1
    G_Q2_t_loeps.SetMarkerStyle(21)
    G_Q2_t_loeps.SetMarkerSize(1)
    G_Q2_t_loeps.SetMarkerColor(1)
    G_Q2_t.Add(G_Q2_t_loeps)

    G_Q2_t_hieps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_Q2_t_hieps.SetPoint(j, t_bins[np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i]], np.array(file_df_dict['unsep_file_hieps']['Q2'].tolist())[i])
            j+=1
    G_Q2_t_hieps.SetMarkerStyle(23)
    G_Q2_t_hieps.SetMarkerSize(1)
    G_Q2_t_hieps.SetMarkerColor(2)
    G_Q2_t.Add(G_Q2_t_hieps)    
    
    G_Q2_t.Draw('AP')
    G_Q2_t.SetTitle("; t; Q2")
    
    G_Q2_t.GetYaxis().SetTitleOffset(1.5)
    G_Q2_t.GetXaxis().SetTitleOffset(1.5)
    G_Q2_t.GetXaxis().SetLabelSize(0.04)
    
l_Q2_t.AddEntry(G_Q2_t_loeps,"loeps")
l_Q2_t.AddEntry(G_Q2_t_hieps,"hieps")
l_Q2_t.Draw()
C_Q2_t.Print(outputpdf)

C_Q2_phi = TCanvas()
C_Q2_phi.SetGrid()
C_Q2_phi.Divide(1,NumtBins)
l_Q2_phi = TLegend(0.7, 0.6, 0.9, 0.9)

multiDict = {}
for k in range(NumtBins):

    multiDict["G_Q2_phi_{}".format(k+1)] = TMultiGraph()
    
    G_Q2_phi_loeps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_Q2_phi_loeps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_loeps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_loeps']['Q2'].tolist())[i])
            j+=1
    G_Q2_phi_loeps.SetMarkerStyle(21)
    G_Q2_phi_loeps.SetMarkerSize(1)
    G_Q2_phi_loeps.SetMarkerColor(1)
    multiDict["G_Q2_phi_{}".format(k+1)].Add(G_Q2_phi_loeps)

    G_Q2_phi_hieps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_Q2_phi_hieps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_hieps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_hieps']['Q2'].tolist())[i])
            j+=1
    G_Q2_phi_hieps.SetMarkerStyle(23)
    G_Q2_phi_hieps.SetMarkerSize(1)
    G_Q2_phi_hieps.SetMarkerColor(2)
    multiDict["G_Q2_phi_{}".format(k+1)].Add(G_Q2_phi_hieps)    
    
    C_Q2_phi.cd(k+1)
    
    multiDict["G_Q2_phi_{}".format(k+1)].Draw('AP')
    multiDict["G_Q2_phi_{}".format(k+1)].SetTitle("t = {:.2f} ; #phi; Q2".format(t_bin_centers[k]))
    
    multiDict["G_Q2_phi_{}".format(k+1)].GetYaxis().SetTitleOffset(1.5)
    multiDict["G_Q2_phi_{}".format(k+1)].GetXaxis().SetTitleOffset(1.5)
    multiDict["G_Q2_phi_{}".format(k+1)].GetXaxis().SetLabelSize(0.04)
    
l_Q2_phi.AddEntry(G_Q2_phi_loeps,"loeps")
l_Q2_phi.AddEntry(G_Q2_phi_hieps,"hieps")
l_Q2_phi.Draw()
C_Q2_phi.Print(outputpdf)

C_W_phi = TCanvas()
C_W_phi.SetGrid()
C_W_phi.Divide(1,NumtBins)
l_W_phi = TLegend(0.7, 0.6, 0.9, 0.9)

multiDict = {}
for k in range(NumtBins):

    multiDict["G_W_phi_{}".format(k+1)] = TMultiGraph()
    
    G_W_phi_loeps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_W_phi_loeps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_loeps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_loeps']['W'].tolist())[i])
            j+=1
    G_W_phi_loeps.SetMarkerStyle(21)
    G_W_phi_loeps.SetMarkerSize(1)
    G_W_phi_loeps.SetMarkerColor(1)
    multiDict["G_W_phi_{}".format(k+1)].Add(G_W_phi_loeps)

    G_W_phi_hieps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_W_phi_hieps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_hieps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_hieps']['W'].tolist())[i])
            j+=1
    G_W_phi_hieps.SetMarkerStyle(23)
    G_W_phi_hieps.SetMarkerSize(1)
    G_W_phi_hieps.SetMarkerColor(2)
    multiDict["G_W_phi_{}".format(k+1)].Add(G_W_phi_hieps)    
    
    C_W_phi.cd(k+1)
    
    multiDict["G_W_phi_{}".format(k+1)].Draw('AP')
    multiDict["G_W_phi_{}".format(k+1)].SetTitle("t = {:.2f} ; #phi; W".format(t_bin_centers[k]))
    
    multiDict["G_W_phi_{}".format(k+1)].GetYaxis().SetTitleOffset(1.5)
    multiDict["G_W_phi_{}".format(k+1)].GetXaxis().SetTitleOffset(1.5)
    multiDict["G_W_phi_{}".format(k+1)].GetXaxis().SetLabelSize(0.04)
    
l_W_phi.AddEntry(G_W_phi_loeps,"loeps")
l_W_phi.AddEntry(G_W_phi_hieps,"hieps")
l_W_phi.Draw()
C_W_phi.Print(outputpdf)

C_xreal_thcm = TCanvas()
C_xreal_thcm.SetGrid()
C_xreal_thcm.Divide(1,NumtBins)
l_xreal_thcm = TLegend(0.7, 0.6, 0.9, 0.9)

multiDict = {}
for k in range(NumtBins):

    multiDict["G_xreal_thcm_{}".format(k+1)] = TMultiGraph()
    
    G_xreal_thcm_loeps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_xreal_thcm_loeps.SetPoint(j, np.array(file_df_dict['unsep_file_loeps']['th_cm'].tolist())[i], np.array(file_df_dict['unsep_file_loeps']['x_real'].tolist())[i])
            G_xreal_thcm_loeps.SetPointError(j, 0, np.array(file_df_dict['unsep_file_loeps']['dx_real'].tolist())[i])
            j+=1
    G_xreal_thcm_loeps.SetMarkerStyle(21)
    G_xreal_thcm_loeps.SetMarkerSize(1)
    G_xreal_thcm_loeps.SetMarkerColor(1)
    multiDict["G_xreal_thcm_{}".format(k+1)].Add(G_xreal_thcm_loeps)

    G_xreal_thcm_hieps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_xreal_thcm_hieps.SetPoint(j, np.array(file_df_dict['unsep_file_hieps']['th_cm'].tolist())[i], np.array(file_df_dict['unsep_file_hieps']['x_real'].tolist())[i])
            G_xreal_thcm_hieps.SetPointError(j, 0, np.array(file_df_dict['unsep_file_hieps']['dx_real'].tolist())[i])
            j+=1
    G_xreal_thcm_hieps.SetMarkerStyle(23)
    G_xreal_thcm_hieps.SetMarkerSize(1)
    G_xreal_thcm_hieps.SetMarkerColor(2)
    multiDict["G_xreal_thcm_{}".format(k+1)].Add(G_xreal_thcm_hieps)    
    
    C_xreal_thcm.cd(k+1)
    
    multiDict["G_xreal_thcm_{}".format(k+1)].Draw('AP')
    multiDict["G_xreal_thcm_{}".format(k+1)].SetTitle("t = {:.2f} ; #theta_{{cm}}; xmod".format(t_bin_centers[k]))
    
    multiDict["G_xreal_thcm_{}".format(k+1)].GetYaxis().SetTitleOffset(1.5)
    multiDict["G_xreal_thcm_{}".format(k+1)].GetXaxis().SetTitleOffset(1.5)
    multiDict["G_xreal_thcm_{}".format(k+1)].GetXaxis().SetLabelSize(0.04)
    
l_xreal_thcm.AddEntry(G_xreal_thcm_loeps,"loeps")
l_xreal_thcm.AddEntry(G_xreal_thcm_hieps,"hieps")
l_xreal_thcm.Draw()
C_xreal_thcm.Print(outputpdf)

C_xmod_thcm = TCanvas()
C_xmod_thcm.SetGrid()
C_xmod_thcm.Divide(1,NumtBins)
l_xmod_thcm = TLegend(0.7, 0.6, 0.9, 0.9)

multiDict = {}
for k in range(NumtBins):

    multiDict["G_xmod_thcm_{}".format(k+1)] = TMultiGraph()
    
    G_xmod_thcm_loeps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_xmod_thcm_loeps.SetPoint(j, np.array(file_df_dict['unsep_file_loeps']['th_cm'].tolist())[i], np.array(file_df_dict['unsep_file_loeps']['x_mod'].tolist())[i])
            G_xmod_thcm_loeps.SetPointError(j, 0, np.array(file_df_dict['unsep_file_loeps']['dx_real'].tolist())[i])
            j+=1
    G_xmod_thcm_loeps.SetMarkerStyle(21)
    G_xmod_thcm_loeps.SetMarkerSize(1)
    G_xmod_thcm_loeps.SetMarkerColor(1)
    multiDict["G_xmod_thcm_{}".format(k+1)].Add(G_xmod_thcm_loeps)

    G_xmod_thcm_hieps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_xmod_thcm_hieps.SetPoint(j, np.array(file_df_dict['unsep_file_hieps']['th_cm'].tolist())[i], np.array(file_df_dict['unsep_file_hieps']['x_mod'].tolist())[i])
            G_xmod_thcm_hieps.SetPointError(j, 0, np.array(file_df_dict['unsep_file_hieps']['dx_real'].tolist())[i])
            j+=1
    G_xmod_thcm_hieps.SetMarkerStyle(23)
    G_xmod_thcm_hieps.SetMarkerSize(1)
    G_xmod_thcm_hieps.SetMarkerColor(2)
    multiDict["G_xmod_thcm_{}".format(k+1)].Add(G_xmod_thcm_hieps)    
    
    C_xmod_thcm.cd(k+1)
    
    multiDict["G_xmod_thcm_{}".format(k+1)].Draw('AP')
    multiDict["G_xmod_thcm_{}".format(k+1)].SetTitle("t = {:.2f} ; #theta_{{cm}}; xmod".format(t_bin_centers[k]))
    
    multiDict["G_xmod_thcm_{}".format(k+1)].GetYaxis().SetTitleOffset(1.5)
    multiDict["G_xmod_thcm_{}".format(k+1)].GetXaxis().SetTitleOffset(1.5)
    multiDict["G_xmod_thcm_{}".format(k+1)].GetXaxis().SetLabelSize(0.04)
    
l_xmod_thcm.AddEntry(G_xmod_thcm_loeps,"loeps")
l_xmod_thcm.AddEntry(G_xmod_thcm_hieps,"hieps")
l_xmod_thcm.Draw()
C_xmod_thcm.Print(outputpdf)

C_xreal_phi = TCanvas()
C_xreal_phi.SetGrid()
C_xreal_phi.Divide(1,NumtBins)
l_xreal_phi = TLegend(0.7, 0.6, 0.9, 0.9)

C_xreal_phi = TCanvas()
C_xreal_phi.SetGrid()
C_xreal_phi.Divide(1,NumtBins)
l_xreal_phi = TLegend(0.7, 0.6, 0.9, 0.9)

multiDict = {}
for k in range(NumtBins):

    multiDict["G_xreal_phi_{}".format(k+1)] = TMultiGraph()

    G_xreal_phi_loeps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_xreal_phi_loeps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_loeps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_loeps']['x_real'].tolist())[i])
            G_xreal_phi_loeps.SetPointError(j, 0, np.array(file_df_dict['unsep_file_loeps']['dx_real'].tolist())[i])
            j+=1
    G_xreal_phi_loeps.SetMarkerStyle(21)
    G_xreal_phi_loeps.SetMarkerSize(1)
    G_xreal_phi_loeps.SetMarkerColor(1)
    multiDict["G_xreal_phi_{}".format(k+1)].Add(G_xreal_phi_loeps)
    
    G_xreal_phi_hieps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_xreal_phi_hieps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_hieps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_hieps']['x_real'].tolist())[i])
            G_xreal_phi_hieps.SetPointError(j, 0, np.array(file_df_dict['unsep_file_hieps']['dx_real'].tolist())[i])
            j+=1
    G_xreal_phi_hieps.SetMarkerStyle(23)
    G_xreal_phi_hieps.SetMarkerSize(1)
    G_xreal_phi_hieps.SetMarkerColor(2)
    multiDict["G_xreal_phi_{}".format(k+1)].Add(G_xreal_phi_hieps)    
    
    C_xreal_phi.cd(k+1)
    
    multiDict["G_xreal_phi_{}".format(k+1)].Draw('AP')
    multiDict["G_xreal_phi_{}".format(k+1)].SetTitle("t = {:.2f} ; #phi; xreal".format(t_bin_centers[k]))
    
    multiDict["G_xreal_phi_{}".format(k+1)].GetYaxis().SetTitleOffset(1.5)
    multiDict["G_xreal_phi_{}".format(k+1)].GetXaxis().SetTitleOffset(1.5)
    multiDict["G_xreal_phi_{}".format(k+1)].GetXaxis().SetLabelSize(0.04)
    
l_xreal_phi.AddEntry(G_xreal_phi_hieps,"hieps")
l_xreal_phi.Draw()
C_xreal_phi.Print(outputpdf)

C_xmod_phi = TCanvas()
C_xmod_phi.SetGrid()
C_xmod_phi.Divide(1,NumtBins)
l_xmod_phi = TLegend(0.7, 0.6, 0.9, 0.9)

multiDict = {}
for k in range(NumtBins):

    multiDict["G_xmod_phi_{}".format(k+1)] = TMultiGraph()
    
    G_xmod_phi_loeps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_xmod_phi_loeps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_loeps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_loeps']['x_mod'].tolist())[i])
            j+=1
    G_xmod_phi_loeps.SetMarkerStyle(21)
    G_xmod_phi_loeps.SetMarkerSize(1)
    G_xmod_phi_loeps.SetMarkerColor(1)
    multiDict["G_xmod_phi_{}".format(k+1)].Add(G_xmod_phi_loeps)

    G_xmod_phi_hieps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_xmod_phi_hieps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_hieps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_hieps']['x_mod'].tolist())[i])
            j+=1
    G_xmod_phi_hieps.SetMarkerStyle(23)
    G_xmod_phi_hieps.SetMarkerSize(1)
    G_xmod_phi_hieps.SetMarkerColor(2)
    multiDict["G_xmod_phi_{}".format(k+1)].Add(G_xmod_phi_hieps)    
    
    C_xmod_phi.cd(k+1)
    
    multiDict["G_xmod_phi_{}".format(k+1)].Draw('AP')
    multiDict["G_xmod_phi_{}".format(k+1)].SetTitle("t = {:.2f} ; #phi; xmod".format(t_bin_centers[k]))
    
    multiDict["G_xmod_phi_{}".format(k+1)].GetYaxis().SetTitleOffset(1.5)
    multiDict["G_xmod_phi_{}".format(k+1)].GetXaxis().SetTitleOffset(1.5)
    multiDict["G_xmod_phi_{}".format(k+1)].GetXaxis().SetLabelSize(0.04)
    
l_xmod_phi.AddEntry(G_xmod_phi_loeps,"loeps")
l_xmod_phi.AddEntry(G_xmod_phi_hieps,"hieps")
l_xmod_phi.Draw()
C_xmod_phi.Print(outputpdf)

C_xmodreal_phi = TCanvas()
C_xmodreal_phi.SetGrid()
C_xmodreal_phi.Divide(1,NumtBins)
l_xmodreal_phi = TLegend(0.7, 0.6, 0.9, 0.9)

import numpy as np
import math
from ROOT import TGraph, TF1, TCanvas

# Define the function to fit
def fit_function(x, p):
    eps_sim = p[0]
    t_gev = p[1]
    q2_gev = p[2]
    thetacm_sim = p[3]
    q2_set = p[4]
    p1 = p[5]
    p2 = p[6]
    p3 = p[7]
    p4 = p[8]
    p5 = p[9]
    p6 = p[10]
    p7 = p[11]
    p8 = p[12]
    p9 = p[13]
    p10 = p[14]
    p11 = p[15]
    p13 = p[16]

    tav = (0.1112 + 0.0066 * math.log(q2_set)) * q2_set
    ftav = (abs(t_gev) - tav) / tav

    sigl = (p1 + p2 * math.log(q2_gev)) * math.exp((p3 + p4 * math.log(q2_gev)) * (abs(t_gev)))
    sigt = p5 + p6 * math.log(q2_gev) + (p7 + p8 * math.log(q2_gev)) * ftav
    siglt = (p9 * math.exp(p10 * abs(t_gev)) + p11 / abs(t_gev)) * math.sin(thetacm_sim)
    sigtt = (p13 * q2_gev * math.exp(-q2_gev)) * ftav * math.sin(thetacm_sim) ** 2

    return (sigt + eps_sim * sigl + eps_sim * math.cos(2. * thetacm_sim) * sigtt +
            math.sqrt(2.0 * eps_sim * (1. + eps_sim)) * math.cos(thetacm_sim) * siglt) / 1.0

multiDict = {}
for k in range(NumtBins):

    multiDict["G_xmodreal_phi_{}".format(k+1)] = TMultiGraph()

    G_xreal_phi_loeps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_xreal_phi_loeps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_loeps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_loeps']['x_real'].tolist())[i])
            G_xreal_phi_loeps.SetPointError(j, 0, np.array(file_df_dict['unsep_file_loeps']['dx_real'].tolist())[i])
            j+=1
    G_xreal_phi_loeps.SetMarkerStyle(21)
    G_xreal_phi_loeps.SetMarkerSize(1)
    G_xreal_phi_loeps.SetMarkerColor(1)
    multiDict["G_xmodreal_phi_{}".format(k+1)].Add(G_xreal_phi_loeps)
    
    G_xreal_phi_hieps = TGraphErrors()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_xreal_phi_hieps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_hieps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_hieps']['x_real'].tolist())[i])
            G_xreal_phi_hieps.SetPointError(j, 0, np.array(file_df_dict['unsep_file_hieps']['dx_real'].tolist())[i])
            j+=1
    G_xreal_phi_hieps.SetMarkerStyle(23)
    G_xreal_phi_hieps.SetMarkerSize(1)
    G_xreal_phi_hieps.SetMarkerColor(2)
    multiDict["G_xmodreal_phi_{}".format(k+1)].Add(G_xreal_phi_hieps)    
    
    G_xmod_phi_loeps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_loeps']['tbin'].tolist())[i] == (k+1):
            G_xmod_phi_loeps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_loeps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_loeps']['x_mod'].tolist())[i])
            j+=1
    G_xmod_phi_loeps.SetMarkerStyle(30)
    G_xmod_phi_loeps.SetMarkerSize(1)
    G_xmod_phi_loeps.SetMarkerColor(1)
    # Create a TF1 function with the fit_function
    fit_unsep_loeps = TF1("fit_unsep_loeps", fit_function, 0, 360, 17)
    # Set initial parameter values
    fit_unsep_loeps.SetParameters(1.0, 1.0, 1.0, 1.0, 2.115, 0.88669E+03, -0.41000E+03, -0.25327E+02, 0.11100E+02, 0.31423E+02, -0.18000E+02, 0.16685E+02, -0.31000E+02, 0, 0, 0, 0)
    fit_unsep_loeps.SetLineColor(1)
    # Fit the TGraph with the TF1 function
    G_xmod_phi_loeps.Fit(fit_unsep_loeps)
    # Access the fit results
    fit_results_root = [fit_unsep_loeps.Eval(phi_bin_centers[i]) for i in range(NumtBins * NumPhiBins)]
    # Display the fit results or use them for further analysis
    print("Fit results:", fit_results_root)
    multiDict["G_xmodreal_phi_{}".format(k+1)].Add(G_xmod_phi_loeps)
    multiDict["G_xmodreal_phi_{}".format(k+1)].Add(fit_unsep_loeps)

    G_xmod_phi_hieps = TGraph()
    j=0
    for i in range(NumtBins*NumPhiBins):
        if np.array(file_df_dict['aver_hieps']['tbin'].tolist())[i] == (k+1):
            G_xmod_phi_hieps.SetPoint(j, phi_bin_centers[np.array(file_df_dict['aver_hieps']['phibin'].tolist())[i]], np.array(file_df_dict['unsep_file_hieps']['x_mod'].tolist())[i])
            j+=1
    G_xmod_phi_hieps.SetMarkerStyle(27)
    G_xmod_phi_hieps.SetMarkerSize(1)
    G_xmod_phi_hieps.SetMarkerColor(2)
    # Create a TF1 function with the fit_function
    fit_unsep_hieps = TF1("fit_unsep_hieps", fit_function, 0, 360, 17)
    # Set initial parameter values
    fit_unsep_hieps.SetParameters(1.0, 1.0, 1.0, 1.0, 2.115, 0.88669E+03, -0.41000E+03, -0.25327E+02, 0.11100E+02, 0.31423E+02, -0.18000E+02, 0.16685E+02, -0.31000E+02, 0, 0, 0, 0)
    fit_unsep_hieps.SetLineColor(2)
    # Fit the TGraph with the TF1 function
    G_xmod_phi_hieps.Fit(fit_unsep_hieps)
    # Access the fit results
    fit_results_root = [fit_unsep_hieps.Eval(phi_bin_centers[i]) for i in range(NumtBins * NumPhiBins)]
    # Display the fit results or use them for further analysis
    print("Fit results:", fit_results_root)
    multiDict["G_xmodreal_phi_{}".format(k+1)].Add(G_xmod_phi_hieps)
    multiDict["G_xmodreal_phi_{}".format(k+1)].Add(fit_unsep_hieps)
    
    C_xmodreal_phi.cd(k+1)
    
    multiDict["G_xmodreal_phi_{}".format(k+1)].Draw('AP')
    multiDict["G_xmodreal_phi_{}".format(k+1)].SetTitle("t = {:.2f} ; #phi; xmod".format(t_bin_centers[k]))
    
    multiDict["G_xmodreal_phi_{}".format(k+1)].GetYaxis().SetTitleOffset(1.5)
    multiDict["G_xmodreal_phi_{}".format(k+1)].GetXaxis().SetTitleOffset(1.5)
    multiDict["G_xmodreal_phi_{}".format(k+1)].GetXaxis().SetLabelSize(0.04)
    
l_xmodreal_phi.AddEntry(G_xreal_phi_loeps,"loeps")
l_xmodreal_phi.AddEntry(G_xreal_phi_hieps,"hieps")    
l_xmodreal_phi.AddEntry(G_xmod_phi_loeps,"loeps model")
l_xmodreal_phi.AddEntry(G_xmod_phi_hieps,"hieps model")
l_xmodreal_phi.Draw()
C_xmodreal_phi.Print(outputpdf+')')
