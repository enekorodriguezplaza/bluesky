""" BlueSky SURPLUS plugin
This plugin reads a list containing information on the surplus fuel needed for each aircraft to take, based on the plannability concept
The csv is chosen out of the ones created in the file plan.ipynb, and is read as a pandas DataFrame
Once an aircraft is created, this list is checked and the corresponding surplus fuel added.
Note: every flight adds some surplus fuel. If the surplus weight == 0: this is because the flight did not take a surplus fuel
Once the surplus fuel is added, it remains for the rest of the simulation (core timed function)

This script is also used for the validation part. For that, set val == True in the 2 corresponding IF statements
Author: Eneko Rodriguez
"""
from random import randint
import numpy as np
import pandas as pd
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import core, stack, traf, sim  #, settings, navdb, traf, sim, scr, tools
from bluesky.tools import datalog, areafilter
from bluesky.core import Entity, timed_function
from bluesky.tools.aero import ft,kts,nm,fpm
import sys


### Initialization function of the plugin.
def init_plugin():
    # Instantiate our ''surplus'' entity
    surplus = Surplus()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'surplus',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim'
        }
    stackfunctions = {
        'PLAN': [
            'PLAN FUA,CX,var1,[var2]',
            '[string,string,float,float]',
            surplus.choose_plannability_csv,
            'Choose the concept of plannability'
        ]
    }
    return config, stackfunctions

### Entity Surplus
class Surplus(core.Entity):

    def __init__(self):
        super().__init__()

    def choose_plannability_csv(self, *args):

        global surplus_fuel_table

        val = False    # True: do validation. False: do Experiment 2
        if val == True:
            print('Doing validation, not Experiment 2')
            surplus_fuel_table = pd.read_csv(
                r"C:\Users\rodri\Documents\GitHub\bluesky\plugins\surplus_fuels\val_mass.csv")
            # This csv contains the masses needed to be added so that BADA's m_ref matches the flight's weight from the ACMS data
            print('surplus table found')

        else:
            # the plan command must be input as PLAN FUA,CX,var1[,var2] without spaces.
            info = args[0].split(',')

            # Get data to determine the concept.
            FUA     = info[0]
            concept = info[1]

            # For the Concept Sets
            if 'C' in concept:
                var1        = info[2]

                if concept != 'C1': # For concept Sets 2, 3 and 4 -> must get the second independent variable
                    var2    = info[3]
                    # read the table containing all surplus fuel weights per ac. Those which had no surplus fuel taken, surplus_weight = 0.
                    # So the surplus of all concept sets in the same folder.
                    filename = '\surplus_fuels_'+FUA+'_'+concept+'_'+var1+'_'+var2+'.csv'
                else:
                    filename = '\surplus_fuels_'+FUA+'_'+concept+'_'+var1+'.csv' # concept 1

            # For the baselines
            elif concept == 'B':
                filename = '\surplus_fuels_' + fua + '_' + concept + '.csv'

            else:
                sys.exit('A wrong plannability command has been input')

            # Read the corresponding table of surplus fuel
            surplus_fuel_table = pd.read_csv(
                r"C:\Users\rodri\Documents\GitHub\bluesky\plugins\surplus_fuels" + filename)
            print('surplus table found')


    def create(self, n=1):
        ''' This function gets called automatically when new aircraft are created. '''
        # Don't forget to call the base class create when you reimplement this function!
        super().create(n)

        # This only shows the last one, so will only work if flights are created one by one (as done in the scns)
        # Get the acid (ECTRL ID, unique identifier) and find this in the table
        acid = traf.id[-n:][0]

        val = False

        if val == False:
            row = surplus_fuel_table[surplus_fuel_table['ECTRL ID'] == int(acid)] #acid is read as str, table is in int.
        else:
            row = surplus_fuel_table[surplus_fuel_table['ECTRL ID'] == acid]

        # Get the current mass
        current_mass = traf.perf.mass[-n:][0]

        # look for the surplus fuel in the surplus_fuel_table.
        if len(row) == 0:
            sys.exit('Flight NOT found in surplus_fuels_table')
            # This should not occur, so use it only as flag

        elif len(row) == 1:
            print('Flight found in surplus_fuels_table')
            surplus_weight   = row['Surplus Weight'].item()

            # To simplify things: for all flights w/o surplus fuel -> the table should have them written as 0.
            traf.perf.mass[-n:][0] = current_mass + surplus_weight

        else:
            sys.exit('Flight found in surplus_fuels_table multiple times')
            # This should not occur, so use it only as flag


        #print(acid, current_mass, traf.perf.mass[-n:][0]) # verification



    ## THIS IS ALSO NOT NEEDED. Just for verification to show that the increased fuel indeed stays
    # Functions that need to be called periodically can be indicated to BlueSky
    # with the timed_function decorator
    @core.timed_function(name='surplus', dt=5)
    def update(self): ## Function to do smth periodically
        ''' Periodic update function for our example entity. '''

        #print(traf.perf.mass)


