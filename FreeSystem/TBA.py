'''
===========
TBA and BdG
===========

Tight Binding Approximation for fermionic systems, including:
    * classes: TBA
    * functions: TBAEB, TBADOS, TBABC
'''

__all__=['TBA','TBAEB','TBADOS','TBABC']

from ..Basics import *
from numpy import *
from scipy.linalg import eigh
import matplotlib.pyplot as plt 

class TBA(Engine):
    '''
    Tight-binding approximation for fermionic systems. Also support BdG systems (phenomenological superconducting systems at the mean-field level).

    Attributes
    ----------
    lattice : Lattice
        The lattice of the system.
    config : IDFConfig
        The configuration of the internal degrees of freedom.
    terms : list of Term
        The terms of the system.
    mask : ['nambu'] or []
        ['nambu'] for not using the nambu space and [] for using the nambu space.
    generator : Generator
        The operator generator for the Hamiltonian.


    Supported methods:
        ========    ==============================================
        METHODS     DESCRIPTION
        ========    ==============================================
        `TBAEB`     calculate the energy bands
        `TBADOS`    calculate the density of states
        `TBABC`     calculate the Berry curvature and Chern number
        ========    ==============================================
    '''

    def __init__(self,lattice=None,config=None,terms=None,mask=['nambu'],**karg):
        '''
        Constructor.

        Parameters
        ----------
        lattice : Lattice, optional
            The lattice of the system.
        config : IDFConfig, optional
            The configuration of the internal degrees of freedom.
        terms : list of Term, optional
            The terms of the system.
        mask : ['nambu'] or [], optional
            ['nambu'] for not using the nambu space and [] for using the nambu space.
        '''
        self.lattice=lattice
        self.config=config
        self.terms=terms
        self.mask=mask
        self.generator=Generator(bonds=lattice.bonds,config=config,table=config.table(mask=mask),terms=terms)
        self.status.update(const=self.generator.parameters['const'],alter=self.generator.parameters['alter'])

    def update(self,**karg):
        '''
        This method update the engine.
        '''
        self.generator.update(**karg)
        self.status.update(alter=karg)

    @property
    def nmatrix(self):
        '''
        The dimension of the matrix representation of the Hamiltonian.
        '''
        return len(self.generator.table)

    def matrix(self,k=[],**karg):
        '''
        This method returns the matrix representation of the Hamiltonian.

        Parameters
        ----------
        k : 1D array-like, optional
            The coords of a point in K-space.
        karg : dict, optional
            Other parameters.

        Returns
        -------
        2d ndarray
            The matrix representation of the Hamiltonian.
        '''
        self.update(**karg)
        nmatrix=self.nmatrix
        result=zeros((nmatrix,nmatrix),dtype=complex128)
        for opt in self.generator.operators.values():
            phase=1 if len(k)==0 else exp(-1j*inner(k,opt.rcoords[0]))
            result[opt.seqs]+=opt.value*phase
            if len(self.mask)==0:
                i,j=opt.seqs
                if i<nmatrix/2 and j<nmatrix/2: result[j+nmatrix/2,i+nmatrix/2]+=-opt.value*conjugate(phase)
        result+=conjugate(result.T)
        return result

    def matrices(self,basespace=None,mode='*'):
        '''
        This method returns a generator iterating over the matrix representations of the Hamiltonian defined on the input basespace.

        Parameters
        ----------
        basespace : BaseSpace, optional
            The base space on which the Hamiltonian is defined.
        mode : string, optional
            The mode to iterate over the base space.

        Yields
        ------
        2d ndarray
        '''
        if basespace is None:
            yield self.matrix()
        else:
            for paras in basespace(mode):
                yield self.matrix(**paras)

    def eigvals(self,basespace=None,mode='*'):
        '''
        This method returns all the eigenvalues of the Hamiltonian.

        Parameters
        ----------
        basespace : BaseSpace, optional
            The base space on which the Hamiltonian is defined.
        mode : string,optional
            The mode to iterate over the base space.

        Returns
        -------
        1d ndarray
            All the eigenvalues.
        '''
        nmatrix=self.nmatrix
        result=zeros(nmatrix*(1 if basespace==None else product(basespace.rank.values())))
        if basespace is None:
            result[...]=eigh(self.matrix(),eigvals_only=True)
        else:
            for i,paras in enumerate(basespace(mode)):
                result[i*nmatrix:(i+1)*nmatrix]=eigh(self.matrix(**paras),eigvals_only=True)
        return result

    def mu(self,filling,kspace=None):
        '''
        Return the chemical potential of the system.

        Parameters
        ----------
        filling : float64
            The filling factor of the system.
        kspace : BaseSpace, optional
            The first Brillouin zone.

        Returns
        -------
        float64
            The chemical potential of the system.
        '''
        nelectron,eigvals=int(round(filling*(1 if kspace is None else kspace.rank['k'])*self.nmatrix)),sort(self.eigvals(kspace))
        return (eigvals[nelectron]+eigvals[nelectron-2])/2

    def gse(self,filling,kspace=None):
        '''
        Return the ground state energy of the system.

        Parameters
        ----------
        filling : float64
            The filling factor of the system.
        kspace : BaseSpace, optional
            The first Brillouin zone.

        Returns
        -------
        float64
            The ground state energy of the system.
        '''
        return sort(self.eigvals(kspace))[0:int(round(filling*(1 if kspace is None else kspace.rank['k'])*self.nmatrix))].sum()

def TBAEB(engine,app):
    '''
    This method calculates the energy bands of the Hamiltonian.
    '''
    nmatrix=engine.nmatrix
    if app.path!=None:
        key=app.path.mesh.keys()[0]
        result=zeros((app.path.rank[key],nmatrix+1))
        if len(app.path.mesh[key].shape)==1:
            result[:,0]=app.path.mesh[key]
        else:
            result[:,0]=array(xrange(app.path.rank[key]))
        for i,parameter in enumerate(list(app.path.mesh[key])):
            result[i,1:]=eigh(engine.matrix(**{key:parameter}),eigvals_only=True)
    else:
        result=zeros((2,nmatrix+1))
        result[:,0]=array(xrange(2))
        result[0,1:]=eigh(engine.matrix(),eigvals_only=True)
        result[1,1:]=result[0,1:]
    if app.save_data:
        savetxt('%s/%s_EB.dat'%(engine.dout,engine.status),result)
    if app.plot:
        plt.title('%s_EB'%(engine.status))
        plt.plot(result[:,0],result[:,1:])
        if app.show and app.suspend: plt.show()
        if app.show and not app.suspend: plt.pause(app.SUSPEND_TIME)
        if app.save_fig: plt.savefig('%s/%s_EB.png'%(engine.dout,engine.status))
        plt.close()

def TBADOS(engine,app):
    '''
    This method calculates the density of states of the Hamiltonian.
    '''
    result=zeros((app.ne,2))
    eigvals=engine.eigvals(app.BZ)
    emin=eigvals.min() if app.emin is None else app.emin
    emax=eigvals.max() if app.emax is None else app.emax
    for i,v in enumerate(linspace(emin,emax,num=app.ne)):
       result[i,0]=v
       result[i,1]=sum(app.eta/((v-eigvals)**2+app.eta**2))
    if app.save_data:
        savetxt('%s/%s_DOS.dat'%(engine.dout,engine.status),result)
    if app.plot:
        plt.title('%s_DOS'%(engine.status))
        plt.plot(result[:,0],result[:,1])
        if app.show and app.suspend: plt.show()
        if app.show and not app.suspend: plt.pause(app.SUSPEND_TIME)
        if app.save_fig: plt.savefig('%s/%s_DOS.png'%(engine.dout,engine.status))
        plt.close()

def TBABC(engine,app):
    '''
    This method calculates the total Berry curvature and Chern number of the filled bands of the Hamiltonian.
    '''
    app.set(lambda kx,ky: engine.matrix(k=[kx,ky]))
    engine.log<<'Chern number(mu): %s(%s)'%(app.cn,app.mu)<<'\n'
    if app.save_data or app.plot:
        buff=zeros((app.BZ.rank['k'],3))
        buff[:,0:2]=app.BZ.mesh['k']
        buff[:,2]=app.bc
    if app.save_data:
        savetxt('%s/%s_BC.dat'%(engine.dout,engine.status),buff)
    if app.plot:
        nk=int(round(sqrt(app.BZ.rank['k'])))
        plt.title('%s_BC'%(engine.status))
        plt.axis('equal')
        plt.colorbar(plt.pcolormesh(buff[:,0].reshape((nk,nk)),buff[:,1].reshape((nk,nk)),buff[:,2].reshape((nk,nk))))
        if app.show and app.suspend: plt.show()
        if app.show and not app.suspend: plt.pause(app.SUSPEND_TIME)
        if app.save_fig: plt.savefig('%s/%s_BC.png'%(engine.dout,engine.status))
        plt.close()

def TBAGF(engine,app):
    pass
