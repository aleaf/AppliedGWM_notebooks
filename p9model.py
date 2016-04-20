import numpy as np
import pandas as pd
import flopy

class problem9model:
    
    MODFLOW_version='mfnwt'
    MODFLOW_exe_name='MODFLOW-NWT.exe', 

    #model domain and grid definition
    Lx = 1500.
    Ly = 1500.
    ztop = 600.
    zbot = 450.
    nlay = 1
    nrow = 15
    ncol = 15
    delr = Lx / ncol
    delc = Ly / nrow
    delv = (ztop - zbot) / nlay
    botm = np.linspace(ztop, zbot, nlay + 1)

    # ibound array
    ibound = np.ones((nlay, nrow, ncol), dtype=int)

    # starting heads
    strt = 515. * np.ones((nlay, nrow, ncol), dtype=float)

    # properties
    Khvalues = {1: 75, 2: 1} # dictionary of K values by zone number (1 = sand, 2 = silt)
    Vani = 1.
    sy = 0.1
    ss = 1.e-4
    laytyp = 1

    # global BC settings
    m_riv = 2 # riverbed thickness
    w_riv = 100 # riverbed width
    R = 0.0001 # recharge rate
    Qleak = 45000 # flow through southern boundary (pos. = inflow)
    Rcond = 150000

    # pumping well for transient simulation
    QA = -20000
    pumping_well_info = [0, 6, 10, QA] # l, r, c, Q zero-based for flopy!

    # Stress Periods
    nper = 2
    perlen = [1, 3]
    nstp = [1, 10]
    tsmult = [1, 2]
    steady = [True, False]
    
    # Kzones
    Kzones = np.ones((15, 15))
    Kzones[4:6, 3:9] = 2 # rows 5 and 6, columns 4-8 have silt
    hk = np.ones((15, 15), dtype=float) # initialize new array for Kvalues
    
    # leaking ditch
    ditch_i = np.ones(15, dtype=int) * 14
    ditch_j = np.arange(0, 15)
    ditch_q = Qleak / len(ditch_i)
    bflux = {0: [[0, ditch_i[j], j, ditch_q] for j in ditch_j]}
    bflux[1] = pumping_well_info
    
    def __init__(self, basename, model_ws):
        self.basename = basename
        self.model_ws = model_ws
        
    def create_input(self):
        m = flopy.modflow.Modflow(self.basename, 
                                       version=self.MODFLOW_version, 
                                       exe_name=self.MODFLOW_exe_name, 
                                       model_ws=self.model_ws)
        dis = flopy.modflow.ModflowDis(m, self.nlay, 
                                       self.nrow, 
                                       self.ncol, 
                                       delr=self.delr, 
                                       delc=self.delc,
                                       top=self.ztop, 
                                       botm=self.botm[1:],
                                       nper=self.nper, 
                                       perlen=self.perlen, 
                                       tsmult=self.tsmult, 
                                       nstp=self.nstp, 
                                       steady=self.steady)
        bas = flopy.modflow.ModflowBas(m, 
                                       ibound=self.ibound, 
                                       strt=self.strt)
        
        words = ['save head','save drawdown','save budget']
        oc = flopy.modflow.ModflowOc(m, stress_period_data={(0,0): words}, compact=True)
        nwt = flopy.modflow.ModflowNwt(m)
        rch = flopy.modflow.mfrch.ModflowRch(m, nrchop=3, rech=self.R, 
                                             irch=1, extension='rch', unitnumber=19)
        
        for zone, value in self.Khvalues.items(): self.hk[self.Kzones == zone] = value
        upw = flopy.modflow.ModflowUpw(m, hk=self.hk, vka=1, 
                                       sy=self.sy, ss=self.ss, laytyp=self.laytyp)

        rivcells = pd.read_csv('rivercells.csv')
        rivcells[['layer', 'row', 'column']] = rivcells[['layer', 'row', 'column']] -1
        rivcells['Rcond'] = self.Rcond
        rivdata = {0: rivcells.values}
        
        riv = flopy.modflow.mfriv.ModflowRiv(m, ipakcb=53, stress_period_data=rivdata, 
                                     extension='riv', unitnumber=18, options=None, naux=0)
        
        wel = flopy.modflow.ModflowWel(m, stress_period_data=self.bflux)
        
        self.m = m
        m.write_input()