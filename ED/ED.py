'''
====================
Exat diagonalization
====================

Base class for exact diagonalization, including:
    * classes: ED, EL, GF
    * functions: EDEL, EDGFP, EDGF, EDDOS
'''

__all__=['ED','EL','EDEL','GF','EDGFP','EDGF','EDDOS']

from ..Misc import Lanczos,derivatives
from scipy.linalg import eigh,norm,solve_banded,solveh_banded
from scipy.sparse.linalg import eigsh
from copy import deepcopy
import numpy as np
import pickle as pk
import HamiltonianPy as HP
import matplotlib.pyplot as plt
import os.path,sys,time

class ED(HP.Engine):
    '''
    Base class for exact diagonalization.

    Attributes
    ----------
    lattice : Lattice
        The lattice of the system.
    config : IDFConfig
        The configuration of the internal degrees of freedom on the lattice.
    terms : list of Term
        The terms of the system.
    dtype : np.float32, np.float64, np.complex64, np.complex128
        The data type of the matrix representation of the Hamiltonian.
    generator : Generator
        The generator of the Hamiltonian.
    operators : Operators
        The operators of the Hamiltonian.
    matrix : csr_matrix
        The sparse matrix representation of the Hamiltonian.

    Supported methods:
        =======     ================================
        METHODS     DESCRIPTION
        =======     ================================
        `EDEL`      calculates the energy spectrum
        `EDGF`      calculates the Green's function
        `EDDOS`     calculates the density of states
        =======     ================================
    '''

    def update(self,**karg):
        '''
        Update the engine.
        '''
        self.generator.update(**karg)
        self.operators=self.generator.operators
        self.status.update(alter=self.generator.parameters['alter'])

    def set_matrix(self):
        '''
        Set the csr_matrix representation of the Hamiltonian.
        '''
        raise NotImplementedError("%s set_matrix err: not implemented."%(self.__class__.__name__))

    def eig(self,k=1,return_eigenvectors=False):
        '''
        Lowest k eigenvalues and optionally, the corresponding eigenvectors.

        Parameters
        ----------
        k : integer, optional
            The number of eigenvalues to be computed.
        return_eigenvectors : logical, optional
            True for returning the eigenvectors and False for not.
        '''
        self.set_matrix()
        return eigsh(self.matrix,k=k,which='SA',return_eigenvectors=return_eigenvectors)

    def Hmats_Omats(self,operators):
        '''
        The matrix representations of the system's Hamiltonian and the input operators.

        Parameters
        ----------
        operators : list of Operator
            The input Operators.

        Returns
        -------
        Hmats : list of csr_matrix
            The matrix representations of the system's Hamiltonian.
        Omats : list of csr_matrix
            The matrix representations of the input operators.
        '''
        raise NotImplementedError("%s Hmat_Omat err: not implemented."%(self.__class__.__name__))

class EL(HP.EB):
    '''
    Energy level.

    Attributes
    ----------
    nder : integer
        The order of derivatives to be computed.
    ns : integer
        The number of energy levels.
    '''
    
    def __init__(self,nder=0,ns=6,**karg):
        '''
        Constructor.

        Parameters
        ----------
        nder : integer, optional
            The order of derivatives to be computed.
        ns : integer, optional
            The number of energy levels.
        '''
        super(EL,self).__init__(**karg)
        self.nder=nder
        self.ns=ns

def EDEL(engine,app):
    '''
    This method calculates the energy levels of the Hamiltonian.
    '''
    result=np.zeros((app.path.rank(0),app.ns*(app.nder+1)+1))
    if len(app.path.tags)==1 and app.path.mesh(0).ndim==1:
        result[:,0]=app.path.mesh(0)
    else:
        result[:,0]=array(xrange(app.path.rank(0)))
    for i,paras in enumerate(app.path('+')):
        engine.update(**paras)
        engine.set_matrix()
        result[i,1:app.ns+1]=eigsh(engine.matrix,k=app.ns,which='SA',return_eigenvectors=False)
    suffix='_%s'%(app.status.name)
    if app.nder>0:
        for i in xrange(app.ns):
            result.T[[j*app.ns+i+1 for j in xrange(1,app.nder+1)]]=derivatives(result[:,0],result[:,i+1],ders=range(1,app.nder+1))
    if app.save_data:
        np.savetxt('%s/%s_%s.dat'%(engine.dout,engine.status.const,app.status.name),result)
    if app.plot:
        plt.title('%s_%s'%(engine.status.const,app.status.name))
        prefixs={i:'1st' if i==1 else ('2nd' if i==2 else ('3rd' if i==3 else '%sth'%i)) for i in xrange(app.nder+1)}
        for k in xrange(1,result.shape[1]):
            i,j=divmod(k-1,app.ns)
            plt.plot(result[:,0],result[:,k],label=('%s der of '%prefixs[i] if i>0 else '')+'$E_{%s}$'%(j))
        plt.legend(shadow=True,fancybox=True,loc='lower right')
        if app.show and app.suspend: plt.show()
        if app.show and not app.suspend: plt.pause(app.SUSPEND_TIME)
        if app.save_fig: plt.savefig('%s/%s_%s.png'%(engine.dout,engine.status.const,app.status.name))
        plt.close()

class GF(HP.GF):
    '''
    Zero-temperature Green's function.

    Attributes
    ----------
    filter : callable
        A function to filter out the entries of the GF to be computed.
    v0 : 1D ndarray
        The initial guess of the groundstate.
    nstep : integer
        The max number of steps for the Lanczos iteration.
    tol : float
        The tolerance used to terminate the iteration.
    gse : float64
        The ground state energy of the system.
    coeff,hs : 4d ndarray
        The auxiliary data for the computing of GF.
    '''

    def __init__(self,filter=None,v0=None,nstep=200,tol=0.0,**karg):
        '''
        Constructor.

        Parameters
        ----------
        filter : callable, optional
            A function to filter out the entries of the GF to be computed.
        v0 : 1D ndarray, optional
            The initial guess of the groundstate.
        nstep : integer, optional
            The max number of steps for the Lanczos iteration.
        tol : float, optional
            The tol used to terminate the iteration.
        '''
        super(GF,self).__init__(**karg)
        self.filter=filter
        self.v0=v0
        self.nstep=nstep
        self.tol=tol

def EDGFP(engine,app):
    '''
    This method prepares the GF.
    '''
    engine.log<<'::<Parameters>:: %s\n'%(', '.join('%s=%s'%(name,value) for name,value in engine.status.data.iteritems()))
    if os.path.isfile('%s/%s_coeff.dat'%(engine.din,engine.status)):
        with open('%s/%s_coeff.dat'%(engine.din,engine.status),'rb') as fin:
            app.gse=pk.load(fin)
            app.coeff=pk.load(fin)
            app.hs=pk.load(fin)
        return
    timers=HP.Timers('Matrix','GSE','GF')
    timers.add(parent='GF',name='Preparation')
    timers.add(parent='GF',name='Iteration')
    with timers.get('Matrix'):
        engine.set_matrix()
        engine.log<<'::<Information>:: %s=%s, %s=%s, %s=%s, '%('nopts',len(engine.operators),'shape',engine.matrix.shape,'nnz',engine.matrix.nnz)
    with timers.get('GSE'):
        es,vs=eigsh(engine.matrix,k=1,which='SA',v0=app.v0,tol=app.tol)
        app.gse,app.v0=es[0],vs[:,0]
        engine.log<<'%s=%.6f\n'%('GSE',app.gse)
    with timers.get('GF'):
        app.coeff=np.zeros((2,app.nopt,app.nopt,app.nstep),dtype=app.dtype)
        app.hs=np.zeros((2,app.nopt,2,app.nstep),dtype=app.dtype)
        engine.log<<'%s\n'%('~'*56)
        engine.log<<'%s|%s|%s|%s\n%s\n'%('Time(seconds)'.center(13),'Preparation'.center(13),'Iteration'.center(13),'Total'.center(13),'-'*56)
        for h in xrange(2):
            t0=time.time()
            with timers.get('Preparation'):
                engine.log<<'%s|'%(':Electron:' if h==0 else ':Hole:').center(13)
                Hmats,Omats=engine.Hmats_Omats([operator.dagger if h==0 else operator for operator in app.operators])
                states,norms,lczs=[],[],[]
                for i,(Hmat,Omat) in enumerate(zip(Hmats,Omats)):
                    states.append(Omat.dot(app.v0))
                    norms.append(norm(states[-1]))
                    lczs.append(Lanczos(Hmat,v0=states[-1]/norms[-1],check_normalization=False))
                    engine.log<<'%s%s'%('\b'*21 if i>0 else '',('%s/%s(%1.5es)'%(i,app.nopt,time.time()-t0)).center(21))
                engine.log<<'%s%s|'%('\b'*21,('%1.5e'%(time.time()-t0)).center(13))
            t1=time.time()
            with timers.get('Iteration'):
                for k in xrange(app.nstep):
                    for i,(nm,lcz) in enumerate(zip(norms,lczs)):
                        if not lcz.cut:
                            for j,state in enumerate(states):
                                if app.filter(engine,app,i,j): app.coeff[h,i,j,k]=np.vdot(state,lcz.new)*nm
                            lcz.iter()
                    engine.log<<'%s%s'%(('\b'*21 if k>0 else ''),('%s/%s(%1.5es)'%(k,app.nstep,time.time()-t1)).center(21))
                engine.log<<'%s%s|'%('\b'*21,('%1.5e'%(time.time()-t1)).center(13))
                for i,lcz in enumerate(lczs):
                    app.hs[h,i,0,0:len(lcz.a)]=np.array(lcz.a)
                    app.hs[h,i,1,0:len(lcz.b)]=np.array(lcz.b)
            engine.log<<('%1.5e'%(time.time()-t0)).center(13)<<'\n'
        tp,ti,tg=('%1.5e'%timers.time('Preparation')).center(13),('%1.5e'%timers.time('Iteration')).center(13),('%1.5e'%timers.time('GF')).center(13)
        engine.log<<'%s|%s|%s|%s\n%s\n'%('Summary'.center(13),tp,ti,tg,'~'*56)
    timers.record()
    engine.log<<'Summary of the gf preparation:\n%s\n'%timers.tostr(None,form='s')
    if app.save_data:
        with open('%s/%s_coeff.dat'%(engine.din,engine.status),'wb') as fout:
            pk.dump(app.gse,fout,2)
            pk.dump(app.coeff,fout,2)
            pk.dump(app.hs,fout,2)

def EDGF(engine,app):
    '''
    This method calculate the GF.
    '''
    if app.omega is not None:
        app.gf[...]=0.0
        buff=np.zeros((3,app.nstep),dtype=app.dtype)
        b=np.zeros(app.nstep,dtype=app.dtype)
        for h in xrange(2):
            for i in xrange(app.nopt):
                b[...]=0
                b[0]=1
                buff[0,1:]=app.hs[h,i,1,0:app.nstep-1]*(-1)**(h+1)
                buff[1,:]=app.omega-(app.hs[h,i,0,:]-app.gse)*(-1)**h
                buff[2,:]=app.hs[h,i,1,:]*(-1)**(h+1)
                if h==0:
                    app.gf[:,i]+=np.dot(app.coeff[h,i,:,:],solve_banded((1,1),buff,b,overwrite_ab=True,overwrite_b=True,check_finite=False))
                else:
                    app.gf[i,:]+=np.dot(app.coeff[h,i,:,:],solve_banded((1,1),buff,b,overwrite_ab=True,overwrite_b=True,check_finite=False))
    return app.gf

def EDDOS(engine,app):
    '''
    This method calculates the DOS.
    '''
    engine.rundependences(app.status.name)
    erange=np.linspace(app.emin,app.emax,num=app.ne)
    gf=app.dependences[0]
    gf_mesh=np.zeros((app.ne,)+gf.gf.shape,dtype=gf.dtype)
    for i,omega in enumerate(erange+app.mu+1j*app.eta):
        gf.omega=omega
        gf_mesh[i,:,:]=gf.run(engine,gf)
    result=np.zeros((app.ne,2))
    result[:,0]=erange
    result[:,1]=-2*np.trace(gf_mesh,axis1=1,axis2=2).imag
    if app.save_data:
        np.savetxt('%s/%s_%s.dat'%(engine.dout,engine.status,app.status.name),result)
    if app.plot:
        plt.title('%s_%s'%(engine.status,app.status.name))
        plt.plot(result[:,0],result[:,1])
        if app.show and app.suspend: plt.show()
        if app.show and not app.suspend: plt.pause(app.SUSPEND_TIME)
        if app.save_fig: plt.savefig('%s/%s_%s.png'%(engine.dout,engine.status,app.status.name))
        plt.close()
