#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2023-12-27 07:01:39 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import numpy as np
import ROOT
from ROOT import TGraphErrors, TF1, TF2, TGraph2DErrors, TCanvas
from ROOT import TString, TNtuple
from array import array
import os, sys

ParticleType = sys.argv[1]
POL = sys.argv[2]

Q2 = sys.argv[3]
W = sys.argv[4]

LOEPS = sys.argv[5]
HIEPS = sys.argv[6]

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

pt_to_pt_systematic_error = 2.9 # Percent, just matching Bill's for now

# Low epsilon drawing function
def LT_sep_x_lo_fun(x, par):
    eps = LOEPS
    xx = x[0]
    xs = par[0] + eps * par[1] + ROOT.TMath.Sqrt(2 * eps * (1 + eps)) * par[2] * ROOT.TMath.Cos(xx * ROOT.TMath.Pi() / 180) + eps * par[3] * ROOT.TMath.Cos(2 * xx * ROOT.TMath.Pi() / 180)
    return xs

# High epsilon drawing function
def LT_sep_x_hi_fun(x, par):
    eps = HIEPS
    xx = x[0]
    xs = par[0] + eps * par[1] + ROOT.TMath.Sqrt(2 * eps * (1 + eps)) * par[2] * ROOT.TMath.Cos(xx * ROOT.TMath.Pi() / 180) + eps * par[3] * ROOT.TMath.Cos(2 * xx * ROOT.TMath.Pi() / 180)
    return xs

# Low epsilon calculating unseparated cross section
def LT_sep_x_lo_fun_unsep(x, par):
    eps = LOEPS
    xx = x[0]
    xs = par[0] + eps * par[1] + ROOT.TMath.Sqrt(2 * eps * (1 + eps)) * par[2] * ROOT.TMath.Cos(xx) + eps * par[3] * ROOT.TMath.Cos(2 * xx)
    return xs

# High epsilon calculating unseparated cross section
def LT_sep_x_hi_fun_unsep(x, par):
    eps = HIEPS
    xx = x[0]
    xs = par[0] + eps * par[1] + ROOT.TMath.Sqrt(2 * eps * (1 + eps)) * par[2] * ROOT.TMath.Cos(xx) + eps * par[3] * ROOT.TMath.Cos(2 * xx)
    return xs

def single_setting(q2_set, fn_lo, fn_hi):

    sig_L_g  = TGraphErrors()
    sig_T_g  = TGraphErrors()
    sig_LT_g = TGraphErrors()
    sig_TT_g = TGraphErrors()

    sig_lo = TGraphErrors()
    sig_hi = TGraphErrors()
    sig_diff = TGraphErrors()

    nlo = TNtuple("nlo", "nlo", "x/F:dx:x_mod:eps:theta:phi:t:t_min:w:Q2")
    nlo.ReadFile(fn_lo)
    
    nhi = TNtuple("nhi", "nhi", "x/F:dx:x_mod:eps:theta:phi:t:t_min:w:Q2")
    nhi.ReadFile(fn_hi)

    # Print values for nlo
    print("Values for nlo:")
    for entry in nlo:
        print("x: {}, dx: {}, x_mod: {}, eps: {}, theta: {}, phi: {}, t: {}, t_min: {}, w: {}, Q2: {}".format(
            entry.x, entry.dx, entry.x_mod, entry.eps, entry.theta, entry.phi, entry.t, entry.t_min, entry.w, entry.Q2
        ))

    # Print values for nhi
    print("\nValues for nhi:")
    for entry in nhi:
        print("x: {}, dx: {}, x_mod: {}, eps: {}, theta: {}, phi: {}, t: {}, t_min: {}, w: {}, Q2: {}".format(
            entry.x, entry.dx, entry.x_mod, entry.eps, entry.theta, entry.phi, entry.t, entry.t_min, entry.w, entry.Q2
        ))
    
    # Define variables
    qq = array('f', [0.0])
    ww = array('f', [0.0])
    thetacm = array('f', [0.0])
    tt = array('f', [0.0])
    t_min = array('f', [0.0])
    lo_eps_real = array('f', [0.0])
    hi_eps_real = array('f', [0.0])

    # Set branch addresses
    nlo.SetBranchAddress("Q2", qq)
    nlo.SetBranchAddress("w", ww)
    nlo.SetBranchAddress("theta", thetacm)
    nlo.SetBranchAddress("t", tt)
    nlo.SetBranchAddress("t_min", t_min)
    nlo.SetBranchAddress("eps", lo_eps_real)

    nhi.SetBranchAddress("eps", hi_eps_real)

    N = nlo.GetEntries()

    q2_list = []
    w_list = []
    theta_list = []
    t_min_list = []
    lo_eps_list = []
    hi_eps_list = []

    for i in range(0,N):

        nlo.GetEntry(i)
        nhi.GetEntry(i)
        
        q2_list.append(qq)
        w_list.append(ww)
        theta_list.append(thetacm)
        t_list.append(t)
        t_min_list.append(t_min)
        lo_eps_list.append(lo_eps_real)
        hi_eps_list.append(hi_eps_real)

        t_bin_num = len(t_list)

        c1 =  TCanvas("c1", "c1", 600, 600)
        c2 =  TCanvas("c2", "c2", 600, 600)

        lo_cross_sec = np.zeros(u_bin_num_int, dtype=float)
        hi_cross_sec = np.zeros(u_bin_num_int, dtype=float)
        lo_cross_sec_err = np.zeros(u_bin_num_int, dtype=float)
        hi_cross_sec_err = np.zeros(u_bin_num_int, dtype=float)        

        for i in range(0, t_bin_num-1):
            
            c1.cd()
            
            tpp = TString()

            if i == 0:
                tpp.Form("t < %lf && x!=0.0", t_list[i] + 0.01)
            else:
                tpp.Form("(t > %lf && t < %lf) && x!=0.0", t_list[i - 1] + 0.01, t_list[i] + 0.01)

            lo_eps = lo_eps_list[i]
            hi_eps = hi_eps_list[i]

            nlow.Draw("x:phi:dx", tpp, "goff")

            glo_tmp = TGraphErrors(n1.GetSelectedRows(), n1.GetV2(), n1.GetV1(), [0]*n1.GetSelectedRows(), n1.GetV3())
            
            flo = TF1("lo_eps_fit", LT_sep_x_lo_fun, 0, 360, 4)
            flo_unsep = TF1("lo_eps_unsep", LT_sep_x_lo_fun_unsep, 0, 2*pi, 4)

            fhi = TF1("hi_eps_fit", LT_sep_x_hi_fun, 0, 360, 4)
            fhi_unsep = TF1("hi_eps_unsep", LT_sep_x_hi_fun_unsep, 0, 2*pi, 4)
            
            glo = TGraphErrors(glo_tmp.GetN(), glo_tmp.GetY(), glo_tmp.GetX(), [0]*glo_tmp.GetN(), glo_tmp.GetEY())

            ave_sig_lo = glo.GetMean(2)
            err_sig_lo = glo.GetRMS(2)

            sig_lo.SetPoint(sig_lo.GetN(), t_list[i], ave_sig_lo)
            sig_lo.SetPointError(sig_lo.GetN()-1, 0, err_sig_lo)

            nhi.Draw("x:phi:dx", tpp, "goff")

            ghi_tmp = TGraphErrors(nhi.GetSelectedRows(), nhi.GetV2(), nhi.GetV1(), 0, nhi.GetV3())
            
            ghi = ghi_tmp.Clone("ghi")

            ave_sig_hi = ghi.GetMean(2)
            err_sig_hi = ghi.GetRMS(2)

            sig_hi.SetPoint(sig_hi.GetN(), t_list[i], ave_sig_hi)
            sig_hi.SetPointError(sig_hi.GetN()-1, 0, err_sig_hi)

            g_plot_err = TGraph2DErrors()
            g_xx, g_yy, g_yy_err = Double(), Double(), Double()

            for ii in range(glo.GetN()):
                glo.GetPoint(ii, g_xx, g_yy)
                g_yy_err = sqrt((glo.GetErrorY(ii) / g_yy)**2 + (pt_to_pt_systematic_error/100)**2) * g_yy

                lo_cross_sec_err[i] += 1 / (g_yy_err**2)

                g_plot_err.SetPoint(g_plot_err.GetN(), g_xx, lo_eps, g_yy)
                g_plot_err.SetPointError(g_plot_err.GetN()-1, 0.0, 0.0, g_yy_err)

            for ii in range(ghi.GetN()):
                ghi.GetPoint(ii, g_xx, g_yy)
                g_yy_err = sqrt((ghi.GetErrorY(ii) / g_yy)**2 + (pt_to_pt_systematic_error/100)**2) * g_yy

                hi_cross_sec_err[i] += 1 / (g_yy_err**2)

                g_plot_err.SetPoint(g_plot_err.GetN(), g_xx, hi_eps, g_yy)
                g_plot_err.SetPointError(g_plot_err.GetN()-1, 0.0, 0.0, g_yy_err)
            

            g_plot_err.SetFillColor(29)
            g_plot_err.SetMarkerSize(0.8)
            g_plot_err.SetMarkerStyle(20)
            g_plot_err.SetMarkerColor(ROOT.kRed)
            g_plot_err.SetLineColor(ROOT.kBlue-3)
            g_plot_err.SetLineWidth(2)

            fff2 = TF2("fff2", "[0] + y*[1] + sqrt(2*y*(1+y))*[2]*cos(0.017453*x)  + y*[3]*cos(0.034906*x)", 0, 360, 0.1, 0.6)

            sigL_change = TGraphErrors()
            sigT_change = TGraphErrors()
            sigLT_change = TGraphErrors()
            sigTT_change = TGraphErrors()

            #########
            # Fit 1 #
            #########
            
            print("\n/*--------------------------------------------------*/")
            print(" Fitting Step 1")
            print(" Fit L and T, while Fix LT and TT")

            # Set parameter 0 and 1
            fff2.SetParameter(0, 1)
            fff2.SetParLimits(0, 0, 5)

            fff2.SetParameter(1, 0.1)
            fff2.SetParLimits(1, 0, 3)
            
            # Fix parameter 2 and 3
            fff2.FixParameter(2, 0.0)
            fff2.FixParameter(3, 0.0)

            g_plot_err.Fit(fff2, "MR")

            # sigL_change
            sigL_change.SetPoint(sigL_change.GetN(), sigL_change.GetN() + 1, fff2.GetParameter(1))
            sigL_change.SetPointError(sigL_change.GetN() - 1, 0, fff2.GetParError(1))

            # sigT_change
            sigT_change.SetPoint(sigT_change.GetN(), sigT_change.GetN() + 1, fff2.GetParameter(0))
            sigT_change.SetPointError(sigT_change.GetN() - 1, 0, fff2.GetParError(0))

            #########            
            # Fit 2 #
            #########
            
            print("\n/*--------------------------------------------------*/")
            print(" Fitting Step 2")
            print(" Fit LT, while Fix L, T, and TT")

            # Fix parameter 0, 1, and 3
            fff2.FixParameter(0, fff2.GetParameter(0))
            fff2.FixParameter(1, fff2.GetParameter(1))
            fff2.FixParameter(3, fff2.GetParameter(3))

            # Release parameter 2
            fff2.ReleaseParameter(2)

            # Set parameter 2
            fff2.SetParameter(2, 0.0)
            fff2.SetParLimits(2, -0.1, 0.1)

            g_plot_err.Fit(fff2, "MR")

            #########
            # Fit 3 #
            #########
            
            print("\n/*--------------------------------------------------*/")
            print(" Fitting Step 3")
            print(" Fit L and T, while Fix LT and TT")

            # Release parameter 0 and 1
            fff2.ReleaseParameter(0)
            fff2.ReleaseParameter(1)

            # Set parameter 0 and 1
            fff2.SetParameter(0, fff2.GetParameter(0))
            fff2.SetParameter(1, fff2.GetParameter(1))

            # Fix parameter 2 and 3
            fff2.FixParameter(2, fff2.GetParameter(2))
            fff2.FixParameter(3, fff2.GetParameter(3))

            g_plot_err.Fit(fff2, "MR")

            # sigL_change
            sigL_change.SetPoint(sigL_change.GetN(), sigL_change.GetN() + 1, fff2.GetParameter(1))
            sigL_change.SetPointError(sigL_change.GetN() - 1, 0, fff2.GetParError(1))

            # sigT_change
            sigT_change.SetPoint(sigT_change.GetN(), sigT_change.GetN() + 1, fff2.GetParameter(0))
            sigT_change.SetPointError(sigT_change.GetN() - 1, 0, fff2.GetParError(0))

            #########
            # Fit 4 #
            #########
            
            print("\n/*--------------------------------------------------*/")
            print(" Fitting Step 4")
            print(" Fit TT, while Fix T, L, and LT")

            # Fix parameter 0, 1, and 2
            fff2.FixParameter(0, fff2.GetParameter(0))
            fff2.FixParameter(1, fff2.GetParameter(1))
            fff2.FixParameter(2, fff2.GetParameter(2))

            # Release parameter 3
            fff2.ReleaseParameter(3)

            # Set parameter 3
            fff2.SetParameter(3, 0.0)
            fff2.SetParLimits(3, -0.1, 0.1)

            g_plot_err.Fit(fff2, "MR")

            #########
            # Fit 5 #
            #########
            
            print("\n/*--------------------------------------------------*/")
            print(" Fitting Step 5")
            print(" Fit T and L, while Fix LT and TT")

            # Release parameter 0 and 1
            fff2.ReleaseParameter(0)
            fff2.ReleaseParameter(1)

            # Set parameter 0 and 1
            fff2.SetParameter(0, fff2.GetParameter(0))
            fff2.SetParameter(1, fff2.GetParameter(1))

            # Fix parameter 2 and 3
            fff2.FixParameter(2, fff2.GetParameter(2))
            fff2.FixParameter(3, fff2.GetParameter(3))

            g_plot_err.Fit(fff2, "MR")

            #############
            # Last Step #
            #############
            
            print("\n/*--------------------------------------------------*/")
            print(" Last Step")
            print(" Fit All")

            # Release all parameters
            fff2.ReleaseParameter(0)
            fff2.ReleaseParameter(1)
            fff2.ReleaseParameter(2)
            fff2.ReleaseParameter(3)

            g_plot_err.Fit(fff2)

            # Update sigL_change and sigT_change
            sigL_change.SetPoint(sigL_change.GetN(), sigL_change.GetN() + 1, fff2.GetParameter(1))
            sigL_change.SetPointError(sigL_change.GetN() - 1, 0, fff2.GetParError(1))

            sigT_change.SetPoint(sigT_change.GetN(), sigT_change.GetN() + 1, fff2.GetParameter(0))
            sigT_change.SetPointError(sigT_change.GetN() - 1, 0, fff2.GetParError(0))

            # Update c2
            c2.Update()

            # Go to the c2 canvas
            c2.cd()

            # Set properties for glo
            glo.SetMarkerStyle(5)
            glo.GetXaxis().SetLimits(0, 360)

            # Set properties for ghi
            ghi.SetMarkerColor(2)
            ghi.SetLineColor(2)
            ghi.SetMarkerStyle(4)

            # Create TMultiGraph and add glo, ghi
            g = ROOT.TMultiGraph()
            g.Add(glo)
            g.Add(ghi)

            # Draw TMultiGraph
            g.Draw("AP")

            # Set properties for the TMultiGraph
            g.GetHistogram().SetMinimum(0.0)
            g.GetHistogram().SetMaximum(0.8)
            g.GetYaxis().SetTitle("Unseparated Cross Section [#mub/GeV^{2}]")
            g.GetYaxis().CenterTitle()
            g.GetYaxis().SetTitleOffset(1.4)

            g.GetXaxis().SetTitle("#it{#phi} [degree]")
            g.GetXaxis().CenterTitle()
            g.GetXaxis().SetLimits(0, 360)

            # Update canvas c2
            c2.Update()

            # Fix parameters for flo, flo_unsep, fhi, and fhi_unsep
            flo.FixParameter(0, fff2.GetParameter(0))
            flo.FixParameter(1, fff2.GetParameter(1))
            flo.FixParameter(2, fff2.GetParameter(2))
            flo.FixParameter(3, fff2.GetParameter(3))

            flo_unsep.FixParameter(0, fff2.GetParameter(0))
            flo_unsep.FixParameter(1, fff2.GetParameter(1))
            flo_unsep.FixParameter(2, fff2.GetParameter(2))
            flo_unsep.FixParameter(3, fff2.GetParameter(3))

            fhi.FixParameter(0, fff2.GetParameter(0))
            fhi.FixParameter(1, fff2.GetParameter(1))
            fhi.FixParameter(2, fff2.GetParameter(2))
            fhi.FixParameter(3, fff2.GetParameter(3))

            fhi_unsep.FixParameter(0, fff2.GetParameter(0))
            fhi_unsep.FixParameter(1, fff2.GetParameter(1))
            fhi_unsep.FixParameter(2, fff2.GetParameter(2))
            fhi_unsep.FixParameter(3, fff2.GetParameter(3))

            # Set line properties for flo and fhi
            flo.SetLineColor(1)
            fhi.SetLineColor(2)
            flo.SetLineWidth(2)
            fhi.SetLineWidth(2)
            fhi.SetLineStyle(9)

            # Set line color for ghi
            ghi.SetLineColor(2)

            # Draw flo and fhi on the same canvas
            flo.Draw("same")
            fhi.Draw("same")

            # Calculate integrated cross sections
            lo_cross_sec[i] = flo_unsep.Integral(0, 2*pi) / (2*pi)
            hi_cross_sec[i] = fhi_unsep.Integral(0, 2*pi) / (2*pi)

            # Create and draw TLegend
            leg = ROOT.TLegend(0.7, 0.7, 0.97, 0.97)
            leg.SetFillColor(0)
            leg.SetMargin(0.4)
            leg.AddEntry(glo, "Low #it{#font[120]{e}} data", "p")
            leg.AddEntry(ghi, "High #it{#font[120]{e}} data", "p")
            leg.AddEntry(flo, "Low #it{#font[120]{e}} fit", "l")
            leg.AddEntry(fhi, "High #it{#font[120]{e}} fit", "l")
            leg.Draw()

            # Create TText for fit status
            fit_status = ROOT.TText()
            fit_status.SetTextSize(0.04)
            fit_status.DrawTextNDC(0.15, 0.85, "Q2 = " + q2_set)
            fit_status.DrawTextNDC(0.15, 0.80, "Fit Status: " + gMinuit.fCstatu)

            # Adjust the maximum and minimum of glo based on ghi values
            if ghi.GetMaximum() > glo.GetMaximum():
                glo.SetMaximum(ghi.GetMaximum() * 1.1)

            if ghi.GetMinimum() < glo.GetMinimum():
                glo.SetMinimum(ghi.GetMinimum() * 0.9)

            # Define variables for cross sections and errors
            sig_l, sig_t, sig_lt, sig_tt = fff2.GetParameter(1), fff2.GetParameter(0), fff2.GetParameter(2), fff2.GetParameter(3)
            sig_l_err, sig_t_err, sig_lt_err, sig_tt_err = fff2.GetParError(1), fff2.GetParError(0), fff2.GetParError(2), fff2.GetParError(3)

            # Print values to console
            print("Outputting...  ", sig_t, "  ", sig_l, "  ", tt, "  ", ww, "  ", qq, "  ", lo_eps_real, "  ", hi_eps_real)

            fn_sep = "x_sep.{}_{}.dat".format(POL, q2_set)
            try:
                with open(fn_sep, 'w') as fn_sep:
                    # Write values to output file
                    fn_sep.write("{}  {}  {}  {}  {}  {}  {}  {}  {}  {}  {}  {}  {}  {}\n".format(
                        sig_t, sig_t_err, sig_l, sig_l_err, sig_lt, sig_lt_err, sig_tt, sig_tt_err,
                        fff2.GetChisquare(), tt, t_min, ww, qq, thetacm
                    ))

            except IOError:
                print("Error writing to file {}.".format(fn_sep))
            
            # Delete g_plot_err
            del g_plot_err

            # Set points and errors for g_sig_l_total, g_sig_t_total, g_sig_lt_total, and g_sig_tt_total
            g_sig_l_total.SetPoint(g_sig_l_total.GetN(), uu, sig_l)
            g_sig_l_total.SetPointError(g_sig_l_total.GetN() - 1, 0, sig_l_err)

            g_sig_t_total.SetPoint(g_sig_t_total.GetN(), uu, sig_t)
            g_sig_t_total.SetPointError(g_sig_t_total.GetN() - 1, 0, sig_t_err)

            g_sig_lt_total.SetPoint(g_sig_lt_total.GetN(), uu, sig_lt)
            g_sig_lt_total.SetPointError(g_sig_lt_total.GetN() - 1, 0, sig_lt_err)

            g_sig_tt_total.SetPoint(g_sig_tt_total.GetN(), uu, sig_tt)
            g_sig_tt_total.SetPointError(g_sig_tt_total.GetN() - 1, 0, sig_tt_err)

            # Set points and errors for sig_L_g, sig_T_g, sig_LT_g, and sig_TT_g
            sig_L_g.SetPoint(i, uu, sig_l)
            sig_T_g.SetPoint(i, uu, sig_t)
            sig_LT_g.SetPoint(i, uu, sig_lt)
            sig_TT_g.SetPoint(i, uu, sig_tt)

            sig_L_g.SetPointError(i, 0.0, sig_l_err)
            sig_T_g.SetPointError(i, 0.0, sig_t_err)
            sig_LT_g.SetPointError(i, 0.0, sig_lt_err)
            sig_TT_g.SetPointError(i, 0.0, sig_tt_err)

            # Create TCanvas
            cc4 = ROOT.TCanvas()

            # Form file paths using TString
            sig_check_str = "sigL_change_tbin_" + str(i)
            sig_check_str2 = "sigT_change_tbin_" + str(i)

            # Draw and save plots
            sigL_change.Draw("a*")
            cc4.Print(sig_check_str + "_" + q2_set + ".png")

            sigT_change.Draw("a*")
            cc4.Print(sig_check_str2 + "_" + q2_set + ".png")

            # Clear canvas
            cc4.Clear()

            # Form filename using TString
            filename = "_t_" + str(i)

            # Adjust top and right margins for c2 canvas
            c2.SetTopMargin(0.03)
            c2.SetRightMargin(0.03)

            # Print plots for c1 and c2 canvases
            c1.Print("check_" + q2_set + filename + ".png")
            c2.Print("money" + q2_set + filename + ".png")
            #c2.Print("money" + q2_set + filename + ".root")

            # Clear c1 and c2 canvases
            c1.Clear()
            c2.Clear()

            # Delete cc4 canvas
            del cc4
            
        # Create TCanvas
        c3 = ROOT.TCanvas()

        # Draw and save plots for sig_L_g, sig_T_g, sig_LT_g, and sig_TT_g
        sig_L_g.Draw("a*")
        c3.Print("sigL_" + q2_set + ".png")

        sig_T_g.Draw("a*")
        c3.Print("sigT_" + q2_set + ".png")

        sig_LT_g.Draw("a*")
        c3.Print("sigLT_" + q2_set + ".png")

        sig_TT_g.Draw("a*")
        c3.Print("sigTT_" + q2_set + ".png")

        # Delete c1, c2, and c3 canvases
        del c1
        del c2
        del c3


fn_lo = LTANAPATH + "/{}/src/x_unsep.{}_{}_{:.0f}".format(ParticleType, POL, Q2.replace("p",""), float(LOEPS)*100)
fn_hi = LTANAPATH + "/{}/src/x_unsep.{}_{}_{:.0f}".format(ParticleType, POL, Q2.replace("p",""), float(HIEPS)*100)

g_sig_l_total = TGraphErrors()
g_sig_t_total = TGraphErrors()
g_sig_lt_total = TGraphErrors()
g_sig_tt_total = TGraphErrors()

print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Start")    
single_setting(Q2, fn_lo, fn_hi) # Main function that performs fitting

print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!End")
ROOT.gStyle.SetOptFit(1)

c_total = TCanvas()

g_sig_l_total.Draw("A*")
c_total.Print("sig_L_total.png")
c_total.Clear()

g_sig_t_total.Draw("A*")
c_total.Print("sig_T_total.png")
c_total.Clear()

g_sig_lt_total.Draw("A*")
c_total.Print("sig_LT_total.png")
c_total.Clear()

g_sig_tt_total.Draw("A*")
c_total.Print("sig_TT_total.png")
c_total.Clear()
