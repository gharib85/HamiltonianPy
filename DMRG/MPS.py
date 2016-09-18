'''
Matrix product state, including:
1) constants: LLINK, SITE, RLINK
2) classes: MPSBase, MPS, Vidal
'''

__all__=['LLINK','SITE','RLINK','MPSBase','Vidal','MPS']

from numpy import *
from HamiltonianPy.Math.Tensor import *
from copy import deepcopy

LLINK,SITE,RLINK=0,1,2

class MPSBase(object):
    '''
    The base class for matrix product states.
    Attributes:
        order: list of int
            The order of the three axis of each matrix.
        tol: float
            The error tolerance.
    '''
    L,S,R=LLINK,SITE,RLINK
    nmax=200
    tol=10**-14

    @property
    def nsite(self):
        '''
        The number of total sites.
        '''
        raise NotImplementedError()

    @property
    def state(self):
        '''
        Convert to the normal representation.
        '''
        raise NotImplementedError()

    @classmethod
    def from_state(cls,state,*arg,**karg):
        '''
        Convert the normal representation of a state to the matrix product representation.
        Parameters:
            cls: subclass of MPSBase
                The subclass of MPSBase.
            state: 1d ndarray
                The normal representation of a state.
        Returns: MPSBase
            The corresponding matrix product state.
        '''
        raise NotImplementedError()

class MPS(MPSBase,list):
    '''
    The general matrix product state.
    Attributes:
        ms: list of Tensor
            The matrices.
        Lambda: Tensor
            The Lambda matrix (singular values) on the connecting link.
        cut: integer
            The index of the connecting link.
    Note the left-canonical MPS, right-canonical MPS and mixed-canonical MPS are considered as special cases of this form.
    '''

    def __init__(self,ms,labels,Lambda=None,cut=None):
        '''
        Constructor.
        Parameters:
            ms: list of 3d ndarray
                The matrices.
            labels: list of 3 tuples
                The labels of the axis of the matrices, thus its length should be equal to that of ms.
                For each label in labels, 
                    label[0],label[1],label[2]: Label
                        The left link / site / right link label of the matrix.
            Lambda: 1d ndarray, optional
                The Lambda matrix (singular values) on the connecting link.
            cut: integer, optional
                The index of the connecting link.
        '''
        if len(ms)!=len(labels):
            raise ValueError('MPS construction error: the number of matrices(%s) is not equal to that of the labels(%s).'%(len(ms),len(labels)))
        #self=[]
        temp=[None]*3
        for i,(m,label) in enumerate(zip(ms,labels)):
            if m.ndim!=3:
                raise ValueError('MPS construction error: all input matrices should be 3 dimensional.')
            L,S,R=label
            if not (isinstance(L,Label) and isinstance(S,Label) and isinstance(R,Label)):
                raise ValueError("MPS construction error: all labels should be instances of Label.")
            temp[self.L]=L
            temp[self.S]=S
            temp[self.R]=R
            self.append(Tensor(m,labels=deepcopy(temp)))
        if Lambda is None:
            if cut is None:
                self.Lambda=None
                self.cut=None
            else:
                raise ValueError("MPS construction error: cut is %s and Lambda is not assigned."%(cut))
        else:
            if cut is None:
                raise ValueError("MPS construction error: Lambda is not None but cut is not assigned.")
            elif cut>0 and cut<=len(ms):
                self.Lambda=Tensor(Lambda,labels=[deepcopy(labels[cut-1][2])])
                self.cut=cut
            elif cut==0:
                self.Lambda=Tensor(Lambda,labels=[deepcopy(labels[cut][0])])
                self.cut=cut
            else:
                raise ValueError('MPS construction error: the cut(%s) is out of range [0,%s].'%(cut,len(ms)))

    @staticmethod
    def compose(As=[],Bs=[],Lambda=None):
        '''
        Construct an MPS from As, Bs and Lambda.
        Parameters:
            As,Bs: list of 3d Tensor, optional
                The A/B matrices of the MPS.
            Lambda: 1d Tensor, optional
                The Lambda matrix (singular values) on the connecting link.
        Returns: MPS
            The constructed MPS.
        '''
        if all([isinstance(A,Tensor) for A in As]) and all([isinstance(B,Tensor) for B in Bs]):
            result=MPS.__new__(MPS)
            if Lambda is None:
                if len(As)==0 or len(Bs)==0:
                    result.extend(As+Bs)
                    result.cut=None
                    result.Lambda=None
                else:
                    raise ValueError("MPS.compose error: Lambda is None but both As and Bs are not empty.")
            elif isinstance(Lambda,Tensor):
                result.extend(As+Bs)
                result.Lambda=Lambda
                result.cut=len(As)
            else:
                raise ValueError("MPS.compose error: Lambda should be a Tensor.")
            return result
        else:
            raise ValueError("MPS.compose error: both As and Bs should be lists of Tensor.")

    @property
    def As(self):
        '''
        The A matrices.
        '''
        return self[0:self.cut]

    @property
    def Bs(self):
        '''
        The B matrices.
        '''
        return self[self.cut:self.nsite]

    @property
    def decompose(self):
        '''
        Decompose the MPS into A matrices, Lambda matrix and B matrices.
        '''
        return self.As,self.Lambda,self.Bs

    def __str__(self):
        '''
        Convert an instance to string.
        '''
        result=[str(m) for m in self]
        if self.cut is not None:
            result.insert(self.cut,str(self.Lambda))
        return '\n'.join(result)

    @property
    def nsite(self):
        '''
        The number of total sites.
        '''
        return len(self)

    @property
    def state(self):
        '''
        Convert to the normal representation.
        Returns: two cases,
            1) 1d ndarray
                The MPS is a pure state.
                Its norm is omitted.
            2) 2d ndarray 
                The MPS is a mixed state with the columns being the contained pure states.
                The singular value for each pure state is omitted.
        '''
        if self.cut in (0,self.nsite,None):
            result=contract(*self,sequence='sequential')
        else:
            A,B=contract(*self.As,sequence='sequential'),contract(*self.Bs,sequence='sequential')
            result=contract(A,self.Lambda,B)
        legs=set(result.labels)-set(m.labels[self.S] for m in self)
        if len(legs)==0:
            return asarray(result).ravel()
        elif len(legs)==1:
            buff=1
            for label,n in zip(result.labels,result.shape):
                if label in legs:
                    temp=ndim
                else:
                    buff*=ndim
            return asarray(result).reshape((buff,temp))
        else:
            raise ValueError('MPS state error: %s link labels%s are left.'%(len(legs),tuple(legs)))

    @property
    def norm(self):
        '''
        The norm of the matrix product state.
        '''
        temp=deepcopy(self)
        temp._reset_(reset=0)
        temp>>=temp.nsite
        return asarray(temp.Lambda)

    def _reset_(self,merge='A',reset=0):
        '''
        Merge the Lamdbda matrix on the link to its neighbouring A matrix or B matrix and reset the cut to 0 or to self.nsite.
        Parameters:
            merge: 'A' or 'B', optional
                When 'A', self.Lambda will be merged into its neighbouring A matrix;
                When 'B', self.Lambda will be merged into its neighbouring B matrix.
            reset: 0 or self.nsite, optional
                Reset self.cut to this integer.
        '''
        if self[0].shape[MPS.L]!=1 or self[-1].shape[MPS.R]!=1:
            raise ValueError("MPS _reset_ error: method not supported for mixed matrix product states yet.")
        if self.cut is not None:
            if self.cut==self.nsite or (merge=='A' and self.cut!=0):
                self[self.cut-1]=contract(self[self.cut-1],self.Lambda,mask=self.Lambda.labels)
            else:
                self[self.cut]=contract(self.Lambda,self[self.cut],mask=self.Lambda.labels)
        self.cut=0 if reset==0 else self.nsite
        self.Lambda=Tensor(1.0,labels=[])

    def _set_B_and_lmove_(self,M,nmax=MPSBase.nmax,tol=MPSBase.tol,print_truncation_err=True):
        '''
        Set the B matrix at self.cut and move leftward.
        Parameters:
            M: Tensor
                The tensor used to set the B matrix.
            nmax: integer, optional
                The maximum number of singular values to be kept. 
            tol: float64, optional
                The truncation tolerance.
            print_truncation_err: logical, optional
                If it is True, the truncation err will be printed.
        '''
        if self.cut==0:
            raise ValueError('MPS _set_B_and_lmove_ error: the cut is already zero.')
        L,S,R=M.labels[self.L],M.labels[self.S],M.labels[self.R]
        u,s,v=M.svd([L],L.prime,[S,R],nmax=nmax,tol=tol,print_truncation_err=print_truncation_err)
        v.relabel(news=[L],olds=[L.prime])
        self[self.cut-1]=v
        if self.cut==1:
            if len(s)>1:
                raise ValueError('MPS _set_B_and_lmove_ error(not supported operation): the MPS is a mixed state and is to move to the end.')
            self.Lambda=contract(u,s)
        else:
            s.relabel(news=[L],olds=[L.prime])
            self.Lambda=s
            self[self.cut-2]=contract(self[self.cut-2],u)
            self[self.cut-2].relabel(news=[L],olds=[L.prime])
        self.cut=self.cut-1

    def _set_A_and_rmove_(self,M,nmax=MPSBase.nmax,tol=MPSBase.tol,print_truncation_err=True):
        '''
        Set the A matrix at self.cut and move rightward.
        Parameters:
            M: Tensor
                The tensor used to set the B matrix.
            nmax: integer, optional
                The maximum number of singular values to be kept. 
            tol: float64, optional
                The truncation tolerance.
            print_truncation_err: logical, optional
                If it is True, the truncation err will be printed.
        '''
        if self.cut==self.nsite:
            raise ValueError('MPS _set_A_and_rmove_ error: the cut is already maximum.')
        L,S,R=M.labels[self.L],M.labels[self.S],M.labels[self.R]
        u,s,v=M.svd([L,S],R.prime,[R],nmax=nmax,tol=tol,print_truncation_err=print_truncation_err)
        u.relabel(news=[R],olds=[R.prime])
        self[self.cut]=u
        if self.cut==self.nsite-1:
            if len(s)>1:
                raise ValueError('MPS _set_A_and_rmove_ error(not supported operation): the MPS is a mixed state and is to move to the end.')
            self.Lambda=contract(s,v)
        else:
            s.relabel(news=[R],olds=[R.prime])
            self.Lambda=s
            self[self.cut+1]=contract(v,self[self.cut+1])
            self[self.cut+1].relabel(news=[R],olds=[R.prime])
        self.cut=self.cut+1

    def __ilshift__(self,other):
        '''
        Operator "<<=", which shift the connecting link leftward by a non-negative integer.
        Parameters:
            other: two cases,
                1) integer
                    The number of times that self.cut will move leftward.
                2) 3-tuple
                    tuple[0]: integer
                        The number of times that self.cut will move leftward.
                    tuple[1]: integer
                        The maximum number of singular values to be kept.
                    tuple[2]: float64
                        The truncation tolerance.
        '''
        nmax,tol=self.nmax,self.tol
        if isinstance(other,tuple):
            k,nmax,tol=other
        else:
            k=other
        for i in xrange(k):
            M=contract(self[self.cut-1],self.Lambda,mask=self.Lambda.labels)
            self._set_B_and_lmove_(M,nmax,tol)
        return self

    def __lshift__(self,other):
        '''
        Operator "<<".
        Parameters:
            other: integer or 3-tuple.
                Please see MPS.__ilshift__ for details.
        '''
        return deepcopy(self).__ilshift__(other)

    def __irshift__(self,other):
        '''
        Operator ">>=", which shift the connecting link rightward by a non-negative integer.
        Parameters:
            other: two cases,
                1) integer
                    The number of times that self.cut will move rightward.
                2) 3-tuple
                    tuple[0]: integer
                        The number of times that self.cut will move rightward.
                    tuple[1]: integer
                        The maximum number of singular values to be kept.
                    tuple[2]: float64
                        The truncation tolerance.
        '''
        nmax,tol=self.nmax,self.tol
        if isinstance(other,tuple):
            k,nmax,tol=other
        else:
            k=other
        for i in xrange(k):
            M=contract(self.Lambda,self[self.cut],mask=self.Lambda.labels)
            self._set_A_and_rmove_(M,nmax,tol)
        return self

    def __rshift__(self,other):
        '''
        Operator ">>".
        Parameters:
            other: integer or 3-tuple.
                Please see MPS.__irshift__ for details.
        '''
        return deepcopy(self).__irshift__(other)

    def canonicalization(self,cut):
        '''
        Make the MPS in the mixed canonical form.
        Parameters:
            link: integer
                The cut of the A,B part.
        Returns: MPS
            The mixed canonical MPS.
        '''
        if self.cut<=self.nsite/2:
            self._reset_(reset=self.nsite)
            self<<=self.nsite
            self>>=cut
        else:
            self._reset_(reset=0)
            self>>=self.nsite
            self<<=(self.nsite-self.cut)

    def is_canonical(self):
        '''
        Judge whether the MPS is in the canonical form.
        '''
        result=[]
        for i,M in enumerate(self):
            temp=[asarray(M.take(indices=j,axis=self.S)) for j in xrange(M.shape[self.S])]
            buff=None
            for matrix in temp:
                if buff is None:
                    buff=matrix.T.conjugate().dot(matrix) if i<self.cut else matrix.dot(matrix.T.conjugate())
                else:
                    buff+=matrix.T.conjugate().dot(matrix) if i<self.cut else matrix.dot(matrix.T.conjugate())
            result.append(all(abs(buff-identity(M.shape[self.R if i<self.cut else self.L]))<self.tol))
        return result

    def copy(self,copy_data=False):
        '''
        Make a copy of the mps.
        Parameters:
            copy_data: logical, optional
                When True, both the labels and data of each tensor in this mps will be copied;
                When False, only the labels of each tensor in this mps will be copied.
        '''
        As=[A.copy(copy_data=copy_data) for A in self.As]
        Bs=[B.copy(copy_data=copy_data) for B in self.Bs]
        Lambda=None if self.Lambda is None else self.Lambda.copy(copy_data=copy_data)
        return MPS.compose(As,Bs,Lambda)

    def to_vidal(self):
        '''
        Convert to the Vidal MPS representation.
        '''
        Gammas,Lambdas,labels=[],[],[]
        for i,M in enumerate(self):
            L,S,R=M.labels[self.L],M.labels[self.S],M.labels[self.R]
            if i==0:
                temp=M
            else:
                if i==self.cut:
                    temp=contract(v*asarray(s)[:,newaxis],self.Lambda,M)
                else:
                    temp=contract(v*asarray(old)[:,newaxis],M)
                temp.relabel(news=[L],olds=[L.prime])
            labels.append((L,S,R))
            if i==0:
                Gammas.append(asarray(u))
            else:
                Gammas.append(asarray(u)/asarray(old)[:,newaxis])
            old=new
            if i<len(self)-1:
                Lambdas.append(asarray(new))
            else:
                norm=abs((asarray(v)*asarray(new)[:,newaxis])[0,0])
                if abs(norm-1.0)>self.err:
                    raise ValueError('MPS to_vidal error: the norm(%s) of original MPS does not equal to 1.'%norm)
        return Vidal(Gammas,Lambdas,labels)

class Vidal(MPSBase):
    '''
    The Vidal canonical matrix product state.
    Attributes:
        Gammas: list of Tensor
            The Gamma matrices on the site.
        Lambdas: list of Tensor
            The Lambda matrices (singular values) on the link.
    '''

    def __init__(self,Gammas,Lambdas,labels):
        '''
        Constructor.
        Parameters:
            Gammas: list of 3d ndarray
                The Gamma matrices on the site.
            Lamdas: list of 1d ndarray
                The Lambda matrices (singular values) on the link.
            labels: list of 3 tuples
                The labels of the axis of the Gamma matrices.
                Its length should be equal to that of Gammas.
                For each label in labels, 
                    label[0],label[1],label[2]: Label
                        The left link / site / right link label of the matrix.
        '''
        if len(Gammas)!=len(Lambdas)+1:
            raise ValueError('Vidal construction error: there should be one more Gamma matrices(%s) than the Lambda matrices(%s).'%(len(Gammas),len(Lambdas)))
        if len(Gammas)!=len(labels):
            raise ValueError('Vidal construction error: the number of Gamma matrices(%s) is not equal to that of the labels(%s).'%(len(Gammas),len(labels)))
        self.Gammas=[]
        self.Lambdas=[]
        temp,buff=[None]*3,[]
        for i,(Gamma,label) in enumerate(zip(Gammas,labels)):
            if Gamma.ndim!=3:
                raise ValueError('Vidal construction error: all Gamma matrices should be 3 dimensional.')
            L,S,R=label
            if i<len(Gammas)-1:
                buff.append(R)
            temp[self.L]=L
            temp[self.S]=S
            temp[self.R]=R
            if not (isinstance(L,Label) and isinstance(S,Label) and isinstance(R,Label)):
                raise ValueError("MPS construction error: all labels should be instances of Label.")
            self.Gammas.append(Tensor(Gamma,labels=deepcopy(temp)))
        for Lambda,label in zip(Lambdas,buff):
            if Lambda.ndim!=1:
                raise ValueError("Vidal construction error: all Lambda matrices should be 1 dimensional.")
            self.Lambdas.append(Tensor(Lambda,labels=[label]))

    def __str__(self):
        '''
        Convert an instance to string.
        '''
        result=[]
        for i,Gamma in enumerate(self.Gammas):
            result.append(str(Gamma))
            if i<len(self.Gammas)-1:
                result.append(str(self.Lambdas[i]))
        return '\n'.join(result)

    @property
    def nsite(self):
        '''
        The number of total sites.
        '''
        return len(self.Gammas)

    def state(self):
        '''
        Convert to the normal representation.
        '''
        result=None
        for i,Gamma in enumerate(self.Gammas):
            if result is None:
                result=Gamma
            else:
                result=contract(result,self.Lambdas[i-1],Gamma)
        return asarray(result).ravel()

    def to_mixed(self,cut):
        '''
        Convert to the mixed MPS representation.
        '''
        ms,labels,Lambda=[],[],None
        shape=[1]*3
        shape[self.S]=-1
        for i,Gamma in enumerate(self.Gammas):
            L,S,R=Gamma.labels[self.L],Gamma.labels[self.S],Gamma.labels[self.R]
            labels.append((L,S,R))
            if i<cut:
                if i==0:
                    ms.append(asarray(Gamma))
                else:
                    ms.append(asarray(Gamma)*asarray(self.Lambdas[i-1]).reshape(shape))
            else:
                if i>0 and i==cut:
                    Lambda=asarray(self.Lambdas[i-1])
                if i<len(self.Lambdas):
                    ms.append(asarray(Gamma)*asarray(self.Lambdas[i]).reshape(shape))
                else:
                    ms.append(asarray(Gamma))
        return MPS(ms,labels,Lambda,cut)
