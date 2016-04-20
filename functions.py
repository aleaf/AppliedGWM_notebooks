import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from flopy.utils import binaryfile as bf

obs = pd.read_csv('observations.csv')
levels = np.arange(503, 518, 1)
extent = [0, 1500, 0, 1500]

def one2one(observed, simulated):
    '''
    make a one to one plot
    '''
    # initialize figure and axis
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    # scatter plot of observed vs. simulated
    plt.scatter(observed, simulated)
    
    # plot one to one line
    lims = ax.get_ylim() + ax.get_xlim()
    mn, mx = np.min(lims), np.max(lims)
    
    plt.plot(np.arange(mn, mx+1), np.arange(mn, mx+1), color='k')
    ax.set_xlim(mn, mx)
    ax.set_ylim(mn, mx)
    ax.set_xlabel('Observed')
    ax.set_ylabel('Simulated')
    
    # calculate statistics and plot
    residuals = simulated - observed
    me = np.mean(residuals)
    mea = np.mean(np.abs(residuals))
    rmse = np.sqrt(np.mean(residuals**2))

    ax.text(0.1, 0.9, 'Mean Error: {:.2f}\nMean Absolute Error: {:.2f}\nRMS Error: {:.2f}'.format(me, mea, rmse),
            va='top', ha='left', transform=ax.transAxes)

def plot_residuals(obs, heads):
    '''
    spatial plot of residuals
    '''
    # oversimulated
    size_factor = 100
    over = obs[obs.residuals > 0]
    under = obs[obs.residuals < 0]
    
    # plot the heads
    plot_heads(heads, levels, extent)
    
    # plot the residuals on top
    plt.scatter(over.X, over.Y, s=np.abs(obs.residuals) * size_factor, c='b', zorder=100)
    plt.scatter(under.X, under.Y, s=np.abs(obs.residuals) * size_factor, c='r', zorder=100)
    

def plot_heads(heads, levels, extent, title=''):
    fig = plt.figure()
    plt.subplot(1, 1, 1, aspect='equal')
    plt.title(title)
    
    plt.imshow(heads, extent=extent, cmap='Blues', vmin=503, vmax=518)
    cb = plt.colorbar()
    cb.set_label('Head')
    cextent = [extent[0], extent[1], extent[3], extent[2]] # had problems with upper left vs. lower left origin
    CS = plt.contour(heads, levels=levels, extent=cextent, colors='k')
    plt.clabel(CS, inline=1, fontsize=10, fmt='%1.1f')


def plot_results(modelname, time=1):
    
    #bring in results
    headobj = bf.HeadFile('{}.hds'.format(modelname))
    heads = headobj.get_data(totim=time)
    
    cbobj = bf.CellBudgetFile('{}.cbc'.format(modelname))
    riv_leakage = cbobj.get_data(totim=time, text='   RIVER LEAKAGE')
    rldf = pd.DataFrame(riv_leakage[0])
    rldf['state'] = ['gaining' if q < 0 else 'losing' for q in rldf.q]
    
    # get simulated values at observation locations
    obs['simulated'] = [heads[0, obs.Row[i], obs.Column[i]] for i in range(len(obs))]
    one2one(obs.Head1, obs.simulated)
    
    obs['residuals'] = obs.simulated - obs.Head1
    plot_residuals(obs, heads[0, :, :])
    
    # sum the leakage to the river, and the leakage out of the river
    r_out = rldf.loc[rldf.state == 'gaining', 'q'].sum()
    r_in = rldf.loc[rldf.state == 'losing', 'q'].sum()
    print ('Total River Leakage In: {}\nTotal River Leakage Out: {}'.format(r_in, r_out))