#! /usr/bin/python
###########################################################################################################################
# Created - 26/July/22, Author - Jacob Murphy
# Based on script created - 20/July/21, Author - Muhammad Junaid (mjo147@uregina.ca), University of Regina, Canada (Copyright (c) junaid) #
###########################################################################################################################
# Python version of the pion plotting script. Now utilises uproot to select event of each type and writes them to a root file.
# Python should allow for easier reading of databases storing diferent variables.
# This version of script is for shift workers at JLab
# To run this script, execute: python3 scriptname runnumber

###################################################################################################################################################

# Import relevant packages
import ROOT
import numpy as np
import sys, math, os, subprocess
import array
import re # Regexp package - for string manipulation
from ROOT import TCanvas, TH1D, TH2D, gStyle, gPad, TPaveText, TArc, TGraphErrors, TGraphPolar, TFile, TLegend, TMultiGraph, TLine, TCutG
from ROOT import TExec
from ROOT import kBlack, kBlue, kRed
from array import array
import pandas as pd
import glob

###############################################################################################################################################

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
print(OUTPATH)
################################################################################################################################################
# Suppressing the terminal splash of Print()
ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = kError;")
#################################################################################################################################################

print("Running as %s on %s, hallc_replay_lt path assumed as %s" % (USER, HOST, REPLAYPATH))

def DiamondPlot(ParticleType, Q2Val, Q2min, Q2max, WVal, Wmin, Wmax, phi_setting, tmin, tmax, inpDict):

    Qs = str(Q2Val).replace('.','p')
    Ws = str(WVal).replace('.','p')
    
    #FilenameOverride = 'Q'+Qs+'W'+Ws+phi_setting
    FilenameOverride = 'Q'+Qs+'W'+Ws
    target = phi_setting
    
    Analysis_Distributions = OUTPATH+"/{}_{}_diamond_{}.pdf".format(target, ParticleType, FilenameOverride)

    #sys.exit(1)

    lowe_input = False
    mide_input = False
    highe_input = False

    # Arbitrary lengths far longer than any file name
    lenh = 10000
    lenm = 10000
    lenl = 10000
    if(target == '0'): target = ""
    print("\n\nKinematics: ",FilenameOverride,"\nPhi Setting: ",target)
    #    for file in glob.glob(OUTPATH+'/**/'+FilenameOverride+'*'+target+'*Analysed_Data.root',recursive = True):
    for file in glob.glob(OUTPATH+'/*'+ParticleType+'*'+FilenameOverride+'*'+target+'*.root'):
	# Searches through OUTPUT recursively for files matching the wild card format, taking the shortest one
        # Shortest file assumed to be full analyisis as it will not have "part" or "week" or "dummy" labels
        #print(file)
        if "high" in file:
            if (len(file) < lenh):
                highe_input = file
                lenh = len(file)

        
        if "mid" in file:
            if (len(file) < lenm):
                mide_input = file
                lenm = len(file)

        if "low" in file:
            if (len(file) < lenl):
                lowe_input = file
                lenl = len(file)

    if (highe_input == False and mide_input == False and lowe_input == False):
        print("!!!!! ERROR !!!!!\n No valid file found! \n!!!!! ERROR !!!!!")
        sys.exit(1)

    ##############################################################################################################################################
    labelh = ""
    labelm = ""
    labell = ""
    if (highe_input !=False):
        #print("test high")
        labelh = "#splitline{Q2 vs W Dist for Prompt Events (Prompt Cut)}{High (Blue) Epsilon}; Q2; W"
        if (mide_input !=False):
            labelh = "#splitline{Q2 vs W Dist for Prompt Events (Prompt Cut)}{High (Blue) and Mid (Red) Epsilon}; Q2; W"
            #print("test high mid")
            if (lowe_input !=False):
                labelh = "#splitline{Q2 vs W Dist for Prompt Events (Prompt Cut)}{High (Blue), Mid (Red), and Low (Green) Epsilon}; Q2; W"
                #print("test high mid low")
        elif (lowe_input !=False):
            #print("test high low")
            labelh = "#splitline{Q2 vs W Dist for Prompt Events (Prompt Cut)}{High (Blue) and Low (Red) Epsilon}; Q2; W"
    elif (mide_input !=False):
        #print("test mid")
        labelm = "#splitline{Q2 vs W Dist for Prompt Events (Prompt Cut)}{Mid (Blue) Epsilon}; Q2; W"
        if (lowe_input !=False):
            #print("test mid low")
            labelm = "#splitline{Q2 vs W Dist for Prompt Events (Prompt Cut)}{Mid (Blue) and Low (Red) Epsilon}; Q2; W"
    elif (lowe_input !=False):
        #print("test low")
        labell = "#splitline{Q2 vs W Dist for Prompt Events (Prompt Cut)}{Low (Blue) Epsilon}; Q2; W"


    Title = ""
    Q2vsW_cut = TH2D("Q2vsW_cut", labelh, 400, Q2min, Q2max, 400, Wmin, Wmax)
    Q2vsW_mide_cut = TH2D("Q2vsW_mide_cut",labelm, 400, Q2min, Q2max, 400, Wmin, Wmax)
    Q2vsW_lowe_cut = TH2D("Q2vsW_lowe_cut", labell, 400, Q2min, Q2max, 400, Wmin, Wmax)    

    Q2vsW_hi_cut = TH2D("Q2vsW_high_cut", "High Epsilon Q2 vs W Dist for Prompt Events (Prompt Cut); Q2; W", 400, Q2min, Q2max, 400, Wmin, Wmax)
    Q2vsW_mi_cut = TH2D("Q2vsW_middle_cut","Mid Epsilon Q2 vs W Dist for Prompt Events (Prompt Cut); Q2; W", 400, Q2min, Q2max, 400, Wmin, Wmax)
    Q2vsW_lo_cut = TH2D("Q2vsW_low_cut", "Low Epsilon Q2 vs W Dist for Prompt Events (Prompt Cut); Q2; W", 400, Q2min, Q2max, 400, Wmin, Wmax)

    W_cut = TH1D("W_cut", "High Epsilon W Dist for Prompt Events (Prompt Cut); W", 400, Wmin, Wmax)
    Q2_cut = TH1D("Q2_cut", "High Epsilon Q2 Dist for Prompt Events (Prompt  Cut); Q2", 400, Q2min, Q2max)
    t_cut = TH1D("t_cut", "High Epsilon -t Dist for Prompt Events (t-Range  Cut); -t", 400, tmin, tmax)
    t_mi_cut = TH1D("t_mi_cut", "Mid Epsilon -t Dist for Prompt Events (t-Range  Cut); -t", 400, tmin, tmax)

    Q2vsW_lolo_cut = TH2D("Q2vsW_low_lowcut", "Low Epsilon Q2 vs W Dist for Prompt Events (Diamond Cut); Q2; W", 400, Q2min, Q2max, 400, Wmin, Wmax)
    Q2vsW_hilo_cut = TH2D("Q2vsW_high_lowcut", "High Epsilon Q2 vs W Dist for Prompt Events (Diamond and t Cut); Q2; W", 400, Q2min, Q2max, 400, Wmin, Wmax)
    Q2vsW_milo_cut = TH2D("Q2vsW_mid_lowcut","Mid Epsilon Q2 vs W Dist for Prompt Events (Diamond and t Cut); Q2; W", 400, Q2min, Q2max, 400, Wmin, Wmax)
    Q2vsW_himi_cut = TH2D("Q2vsW_high_midcut", "High Epsilon Q2 vs W Dist for Prompt Events (Mid-Diamond and t Cut); Q2; W", 400, Q2min, Q2max, 400, Wmin, Wmax)

    a1 = 0
    b1 = 0
    a2 = 0
    b2 = 0
    a3 = 0
    b3 = 0
    a4 = 0
    b4 = 0
    minQ = 0
    maxQ = 0
    fitl = 0
    fitr = 0
    fitrange = 0
    lol = []
    lor = []
    hil = []
    hir = []
    xvl = []
    xvr = []
    for k in range(0, 3):

	# Construct the name of the rootfile based upon the info we provided
        if (k==2):
            if (highe_input == False): 
                continue
            elif (highe_input != False): # Special condition, with 5th arg, use 5th arg as file name
                rootName = highe_input
                print("\n***** High Epsilon File Found! *****\n")
        if (k==1):
            if (mide_input == False): 
                continue
            elif (mide_input != False): # Special condition, with 5th arg, use 5th arg as file name
                rootName = mide_input
                print("\n*****Mid Epsilon File Found! *****\n")
        if (k==0):
            if (lowe_input == False): 
                continue
            elif (lowe_input != False): # Special condition, with 5th arg, use 5th arg as file name
                rootName = lowe_input
                print("\n***** Low Epsilon File Found! *****\n")
        print ("Attempting to process %s" %(rootName))

	###############################################################################################################################################
        ROOT.gROOT.SetBatch(ROOT.kTRUE) # Set ROOT to batch mode explicitly, does not splash anything to screen

	###############################################################################################################################################

	# Read stuff from the main event tree
        infile = TFile.Open(rootName, "READ")

	# Assumes 2021 trees do not have Prompt MM cut, as some do not right now. *** NEED TO BE REPLAYED AGAIN WITH THIS BRANCH ***
        Cut_Events_all_RF_tree = infile.Get("Cut_{}_Events_prompt_RF".format(ParticleType.capitalize()))

	##############################################################################################################################################
        countB = 0
        countA = 0
        badfit = True
        if (k==2): # High
            # for event in Cut_Events_Prompt_tree:
            for event in Cut_Events_all_RF_tree:
                Q2vsW_cut.Fill(event.Q2, event.W)
                Q2vsW_hi_cut.Fill(event.Q2, event.W)
        elif (k==1): # Mid
            # for event in Cut_Events_Prompt_tree:
            for event in Cut_Events_all_RF_tree:
                Q2vsW_mide_cut.Fill(event.Q2, event.W)
                Q2vsW_mi_cut.Fill(event.Q2, event.W)
        elif (k==0): # Low
            # for event in Cut_Events_Prompt_tree:
            for event in Cut_Events_all_RF_tree:
                Q2vsW_lowe_cut.Fill(event.Q2, event.W)
                Q2vsW_lo_cut.Fill(event.Q2, event.W)
                W_cut.Fill(event.W)
                Q2_cut.Fill(event.Q2)
                countB +=1

            ##############################################################################################################################################
            #Does assume 400 bins for Q2 and W, centered at kinematic values with ranges of +/-2 and +/-0.5 respectively
            minQ = Q2_cut.FindFirstBinAbove(0)
            maxQ = Q2_cut.FindLastBinAbove(0)
            fitrange = int((maxQ-minQ)/8)
            #print("fitrange: ",fitrange)
            minbin = 1
            badfile = False
            #print (minQ, minQ/400*(Q2max-Q2min)+Q2min,maxQ,maxQ/400*(Q2max-Q2min)+Q2min,fitrange)
            print("Q2Val Bin Val: ",Q2vsW_lowe_cut.FindBin(Q2Val))
            fitl = Q2vsW_lowe_cut.FindBin(Q2Val)-fitrange*2
            fitr = Q2vsW_lowe_cut.FindBin(Q2Val)+fitrange
            #fitl = 200-fitrange*2
            #fitr = 200+fitrange
            while (badfit == True):
                lol.clear()
                lor.clear()
                hil.clear()
                hir.clear()
                xvl.clear()
                xvr.clear()
                for b in range (0,fitrange):
        
                    fbl = 1
                    lbl = 400
                    fbr = 1
                    lbr = 400
                    check1 = False
                    check2 = False
                    check3 = False
                    check4 = False
                    # Designed to remove outliers from fit, skips over bins that have empty bins on either side when determining histogram width
                    while (check1 == False or check2 == False or check3 == False or check4 == False):
                        #fbl = Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).FindFirstBinAbove(0,1,fbl,lbl)
                        #lbl = Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).FindLastBinAbove(0,1,fbl,lbl)
                        #fbr = Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1).FindFirstBinAbove(0,1,fbr,lbr)
                        #lbr = Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1).FindLastBinAbove(0,1,fbr,lbr)
                        if (Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1). \
                            GetBinContent(Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).FindFirstBinAbove(0,1,fbl,lbl)+1)==0):
                            fbl = Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).FindFirstBinAbove(1,1,fbl,lbl)+1
                        else: 
                            check1 = True 
                        if (Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1). \
                            GetBinContent(Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).FindLastBinAbove(0,1,fbl,lbl)-1)==0):
                            lbl = Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).FindLastBinAbove(1,1,fbl,lbl)-1
                        else:
                            check2 = True
                        if (Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1). \
                            GetBinContent(Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1).FindFirstBinAbove(0,1,fbr,lbr)+1)==0):
                            fbr = Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1).FindFirstBinAbove(1,1,fbr,lbr)+1
                        else:
                            check3 = True
                        if (Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1). \
                            GetBinContent(Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1).FindLastBinAbove(0,1,fbr,lbr)-1)==0):
                            lbr = Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1).FindLastBinAbove(1,1,fbr,lbr)-1
                        else:
                            check4 = True
                        if (fbl > lbl or fbr > lbr):                     
                            print("WARNING: Bad Fit! Refitting...If script hangs for too long, check lowe file or change Q2min/Q2max range! \n")
                            lowe_input = False
                            badfile = True
                            break
                    if (badfile == True):
                        break
                    #for i in range (fbl,lbl):
                    #print(Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).GetBinContent(i))
                    minYl = Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).FindFirstBinAbove(minbin,1,fbl,lbl)/400*(Wmax-Wmin)+Wmin
                    lol.append(minYl)
                    maxYl = Q2vsW_lowe_cut.ProjectionY("y",b+fitl,b+fitl+1).FindLastBinAbove(minbin,1,fbl,lbl)/400*(Wmax-Wmin)+Wmin
                    hil.append(maxYl)
                    minYr = Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1).FindFirstBinAbove(minbin,1,fbr,lbr)/400*(Wmax-Wmin)+Wmin
                    lor.append(minYr)
                    maxYr = Q2vsW_lowe_cut.ProjectionY("y",b+fitr,b+fitr+1).FindLastBinAbove(minbin,1,fbr,lbr)/400*(Wmax-Wmin)+Wmin
                    hir.append(maxYr)
                    xl = 1.0*(b+fitl)/400*(Q2max-Q2min)+Q2min
                    xr = 1.0*(b+fitr)/400*(Q2max-Q2min)+Q2min
                    xvl.append(xl)
                    xvr.append(xr)
                if (badfile == True):
                    break
        
                lola = np.array(lol)
                hila = np.array(hil)
                lora = np.array(lor)
                hira = np.array(hir)
                xla = np.array(xvl)
                xra = np.array(xvr)

                if target == "Center":
                    a1, b1 = np.polyfit(xla, lola, 1)
                    a2, b2 = np.polyfit(xla, hila, 1)
                    a3, b3 = np.polyfit(xra, lora, 1)
                    a4, b4 = np.polyfit(xra, hira, 1)
                else:
                    a1 = inpDict["a1"]
                    b1 = inpDict["b1"]
                    a2 = inpDict["a2"]
                    b2 = inpDict["b2"]
                    a3 = inpDict["a3"]
                    b3 = inpDict["b3"]
                    a4 = inpDict["a4"]
                    b4 = inpDict["b4"]                    
	            
                for event in Cut_Events_all_RF_tree:
                    if (event.W/event.Q2>a1+b1/event.Q2 and event.W/event.Q2<a2+b2/event.Q2 and event.W/event.Q2>a3+b3/event.Q2 and event.W/event.Q2<a4+b4/event.Q2):
                        Q2vsW_lolo_cut.Fill(event.Q2, event.W)
                        countA +=1
                if (1.0*(countB-countA)/countB<0.1):
                    badfit=False
                    print ("\n !!!!! Diamond Fit Good (w/in 10%)!!!!!\n")
                else:
                    #print ("\n!!!!! Bad Diamond Fit!! Try Reducing fitrange or Increasing minbin and Retrying !!!!!\n")
                    fitrange -= 5
                    #minbin -= 1
                #badfit=False
        
        

        if (lowe_input != False and k>0):
            print("\n\n")
            if (k==2):
                for event in Cut_Events_all_RF_tree:
                    if (event.W/event.Q2>a1+b1/event.Q2 and event.W/event.Q2<a2+b2/event.Q2 and event.W/event.Q2>a3+b3/event.Q2 and event.W/event.Q2<a4+b4/event.Q2):
                        if (tmax != False):
                            if(-event.MandelT<1):
                                Q2vsW_hilo_cut.Fill(event.Q2, event.W)
                                t_cut.Fill(-event.MandelT)
                        else:
                            print("!!!!! Error! tmax not found! Skipping t-range cut !!!!!")
                            Q2vsW_hilo_cut.Fill(event.Q2, event.W)
            elif (k==1):
                for event in Cut_Events_all_RF_tree:
                    if (event.W/event.Q2>a1+b1/event.Q2 and event.W/event.Q2<a2+b2/event.Q2 and event.W/event.Q2>a3+b3/event.Q2 and event.W/event.Q2<a4+b4/event.Q2):
                        if (tmax != False):
                            if(-event.MandelT<tmax):
                                Q2vsW_milo_cut.Fill(event.Q2, event.W)
                                t_mi_cut.Fill(-event.MandelT)
                        else:
                            print("!!!!! Error! tmax not found! Skipping t-range cut !!!!!")
                            Q2vsW_milo_cut.Fill(event.Q2, event.W)        

        print("Histograms filled")

        infile.Close()

    if target == "Center":        
        paramDict = {

            "a1" : a1,
            "b1" : b1,
            "a2" : a2,
            "b2" : b2,
            "a3" : a3,
            "b3" : b3,
            "a4" : a4,
            "b4" : b4
        }

    else:

        paramDict = {}

    ##############################################################################################################################################
    c1_kin = TCanvas("c1_kin", "%s Kinematic Distributions" % ParticleType, 100, 0, 1000, 900)
    gStyle.SetTitleFontSize(0.03)
    gStyle.SetPalette(86)
    ex1 = TExec("ex1","gStyle->SetPalette(86)")
    ex2 = TExec("ex2","gStyle->SetPalette(75)")
    ex3 = TExec("ex3","gStyle->SetPalette(68)")
    gStyle.SetOptStat(0)
    pages = 2
    if (highe_input !=False):
        #print("test high")
        Q2vsW_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
        Q2vsW_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)
        Q2vsW_cut.Draw("col")
        ex1.Draw()
        Q2vsW_cut.Draw("col same")
        if (mide_input !=False):
            #print("test high mid")
            Q2vsW_mide_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
            Q2vsW_mide_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)
            ex2.Draw()
            Q2vsW_mide_cut.Draw("col same")
            pages = 3
            if (lowe_input !=False):
                #print("test high mid low")
                Q2vsW_lowe_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
                Q2vsW_lowe_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)                
                ex3.Draw()
                Q2vsW_lowe_cut.Draw("col same")
                pages = 6
        elif (lowe_input !=False):
            #print("test high low")
            Q2vsW_lowe_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
            Q2vsW_lowe_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)
            ex2.Draw()
            Q2vsW_lowe_cut.Draw("col same")
            pages = 4
    elif (mide_input !=False):
	#print("test mid")
        Q2vsW_mide_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
        Q2vsW_mide_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)        
        Q2vsW_mide_cut.Draw("colz")
        ex1.Draw()
        Q2vsW_mide_cut.Draw("col same")
        if (lowe_input !=False):
            #print("test mid low")
            Q2vsW_lowe_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
            Q2vsW_lowe_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)            
            ex2.Draw()
            Q2vsW_lowe_cut.Draw("col same")
            pages = 4
    elif (lowe_input !=False):
        #print("test low")
        Q2vsW_lowe_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
        Q2vsW_lowe_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)        
        Q2vsW_lowe_cut.Draw("colz")
        ex1.Draw()
        Q2vsW_lowe_cut.Draw("col same")

    c1_kin.Print(Analysis_Distributions + "(")

    #############################################################################################################################

    end = ""
    endm = ""
    endc = ""
    endf = ""
    if (pages==2): end = ")"
    if (pages==3): endm = ")"
    if (pages==4): endc = ")"
    if (pages==6): endf = ")"

    gStyle.SetOptStat(1)
    gStyle.SetPalette(55)

    if (tmax != False):
        c1_kint = TCanvas("c1_kint", "%s Kinematic Distributions" % ParticleType, 100, 0, 1000, 900)
        t_cut.Draw("colz")
        c1_kint.Print(Analysis_Distributions)
    if (highe_input != False):
        c1_kinh = TCanvas("c1_kinh", "%s Kinematic Distributions" % ParticleType, 100, 0, 1000, 900)
        Q2vsW_hi_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
        Q2vsW_hi_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)
        Q2vsW_hi_cut.Draw("colz")
        c1_kinh.Print(Analysis_Distributions+end)
    if (mide_input != False):
        c1_kinm = TCanvas("c1_kinm", "%s Kinematic Distributions" % ParticleType, 100, 0, 1000, 900)
        Q2vsW_mi_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
        Q2vsW_mi_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)        
        Q2vsW_mi_cut.Draw("colz")
        c1_kinm.Print(Analysis_Distributions+end+endm)
    if (lowe_input != False):
        c1_kinl = TCanvas("c1_kinl", "%s Kinematic Distributions" % ParticleType, 100, 0, 1000, 900)
        Q2vsW_lo_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
        Q2vsW_lo_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)        
        Q2vsW_lo_cut.Draw("colz")
        c1_kinl.Print(Analysis_Distributions)
        c1_kinll = TCanvas("c1_kinll", "%s Kinematic Distributions" % ParticleType, 100, 0, 1000, 900)
        Q2vsW_lolo_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
        Q2vsW_lolo_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)        
        Q2vsW_lolo_cut.Draw("colz")
        #    lol.clear()
        #   lor.clear()
        #  hil.clear()
        # hir.clear()
        # xvl.clear()
        # xvr.clear()
        #print (xvl[0], xvl[-1])
        line1 = TLine(xvl[0],a1*xvl[0]+b1,xvl[-1],a1*xvl[-1]+b1)   
        line2 = TLine(xvl[0],a2*xvl[0]+b2,xvl[-1],a2*xvl[-1]+b2) 
        line3 = TLine(xvr[0],a3*xvr[0]+b3,xvr[-1],a3*xvr[-1]+b3) 
        line4 = TLine(xvr[0],a4*xvr[0]+b4,xvr[-1],a4*xvr[-1]+b4)  
        line1.SetLineColor(1)
        line2.SetLineColor(2)
        line3.SetLineColor(3)
        line4.SetLineColor(4)  
        line1.SetLineWidth(5)
        line2.SetLineWidth(5)
        line3.SetLineWidth(5)
        line4.SetLineWidth(5)
        line1.Draw()
        line2.Draw()
        line3.Draw()
        line4.Draw()
        x1 = 100/400*(Q2max-Q2min)+Q2min
        x2 = 300/400*(Q2max-Q2min)+Q2min
        line1f = TLine(x1,a1*x1+b1,x2,a1*x2+b1)   
        line2f = TLine(x1,a2*x1+b2,x2,a2*x2+b2) 
        line3f = TLine(x1,a3*x1+b3,x2,a3*x2+b3) 
        line4f = TLine(x1,a4*x1+b4,x2,a4*x2+b4)  
        line1f.SetLineColor(1)
        line2f.SetLineColor(2)
        line3f.SetLineColor(3)
        line4f.SetLineColor(4)  
        line1f.SetLineWidth(2)
        line2f.SetLineWidth(2)
        line3f.SetLineWidth(2)
        line4f.SetLineWidth(2)
        line1f.Draw()
        line2f.Draw()
        line3f.Draw()
        line4f.Draw()
        c1_kinll.Print(Analysis_Distributions+end)

        if (mide_input != False):
            c1_kinml = TCanvas("c1_kinml", "%s Kinematic Distributions" % ParticleType, 100, 0, 1000, 900)
            Q2vsW_milo_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
            Q2vsW_milo_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)            
            Q2vsW_milo_cut.Draw("colz")
            c1_kinml.Print(Analysis_Distributions+endc)

        if (highe_input != False):
            c1_kinhl = TCanvas("c1_kinhl", "%s Kinematic Distributions" % ParticleType, 100, 0, 1000, 900)
            Q2vsW_hilo_cut.GetXaxis().SetRangeUser(Q2min-Q2min*0.1, Q2max+Q2max*0.1)
            Q2vsW_hilo_cut.GetYaxis().SetRangeUser(Wmin-Wmin*0.1, Wmax+Wmax*0.1)
            Q2vsW_hilo_cut.Draw("colz")
            c1_kinhl.Print(Analysis_Distributions+endc+endf)
	
            
    return paramDict
