#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2024-01-11 18:30:28 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import pandas as pd
import sys, os

################################################################################################################################################
'''
User Inputs
'''
efficiency_table = sys.argv[1]
RUNLIST = sys.argv[2].split(" ")
ParticleType = sys.argv[3]

################################################################################################################################################
'''
ltsep package import and pathing definitions
'''
# Import package for cuts
from ltsep import Root

lt=Root(os.path.realpath(__file__))

# Add this to all files for more dynamic pathing
UTILPATH=lt.UTILPATH
LTANAPATH=lt.LTANAPATH
OUTPATH=lt.OUTPATH

##################################################################################################################################################
# Importing utility functions

sys.path.append("../utility")
from utility import check_runs_in_effcharge

################################################################################################################################################
# Grab and calculate efficiency 

from getEfficiencyValue import getEfficiencyValue

################################################################################################################################################

effective_charge = ""
effective_charge_uncern = ""
tot_efficiency = ""
tot_efficiency_uncern = ""
ebeam_val = ""
pTheta_val = ""

for runNum in RUNLIST:

    # Check if run number exists in analysed root files
    if check_runs_in_effcharge(runNum, ParticleType, "{}/OUTPUT/Analysis/{}LT".format(LTANAPATH, ParticleType)):
    
        efficiency = getEfficiencyValue(runNum,efficiency_table,"efficiency")
        effError = getEfficiencyValue(runNum,efficiency_table,"effError")
        charge  = getEfficiencyValue(runNum,efficiency_table,"bcm")

        # Need to convert to int value for bash to interpret correctly
        effective_charge += " " + str(int(1000*(float(charge)*float(efficiency))))
        effective_charge_uncern += " " + str(int(1000*(float(charge)*float(effError))))

        tot_efficiency += " " + str(efficiency)
        tot_efficiency_uncern += " " + str(effError)

        ebeam_val += " " + str(getEfficiencyValue(runNum,efficiency_table,"ebeam"))
        pTheta_val += " " + str(getEfficiencyValue(runNum,efficiency_table,"pTheta"))        
    print(check_runs_in_effcharge(runNum, ParticleType, OUTPATH))
BashInput=("{}\n{}\n{}\n{}\n{}\n{}".format(effective_charge, effective_charge_uncern, tot_efficiency, tot_efficiency_uncern, pTheta_val, ebeam_val))
print(BashInput)
