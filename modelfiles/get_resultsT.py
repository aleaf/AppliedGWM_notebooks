'''
get head and river flux results
'''

from flopy.utils import binaryfile as bf
import pandas as pd
import numpy as np

#Create the binary output objects
headobj = bf.HeadFile('P9Tcal.hds')
cbobj = bf.CellBudgetFile('P9Tcal.cbc')


# bring in observations 
# (using numpy instead of pandas because the windows version of python used by PEST batch file doesn't have it)
obs = pd.read_csv('../observations.csv')
obs[['Row', 'Column']] = obs[['Row', 'Column']] -1 # convert to zero-based

# get simulated values at observation locations
head1 = headobj.get_data(totim=1)
simulated1 = head1[0, obs.Row.values, obs.Column.values]

head2 = headobj.get_data(totim=4)
simulated2 = head2[0, obs.Row.values, obs.Column.values]

# steady state river leakage
riv_leakage = cbobj.get_data(totim=1, text='   RIVER LEAKAGE')
r_out1 = np.sum([l for l in riv_leakage[0].q if l <0])
r_in1 = np.sum([l for l in riv_leakage[0].q if l >0])

# sum river leakage for stress period 2 (transient)
r_out2, r_in2 = 0, 0
for ts in np.arange(1, 11):
    delta_t = cbobj.times[ts] - cbobj.times[ts-1]
    
    riv_leakage = cbobj.get_data(kstpkper=(ts-1, 1), text='   RIVER LEAKAGE')
    r_out2 += np.sum([l for l in riv_leakage[0].q if l <0]) * delta_t
    r_in2 += np.sum([l for l in riv_leakage[0].q if l >0]) * delta_t


ofp = open('resultsT.txt', 'w')
[ofp.write('{}\n'.format(s)) for s in simulated1]
[ofp.write('{}\n'.format(s)) for s in simulated2]
ofp.write('{}\n'.format(r_out1))
ofp.write('{}\n'.format(r_in1))
ofp.write('{}\n'.format(r_out2))
ofp.write('{}\n'.format(r_in2))

ofp.close()