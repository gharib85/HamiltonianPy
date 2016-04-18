'''
Geometry, including
1) functions: azimuthd, azimuth, polard, polar, volume, is_parallel, reciprocals, tiling, bonds
2) classes: Point, Bond, Lattice
'''

__all__=['azimuthd','azimuth','polard','polar','volume','is_parallel','reciprocals','tiling','bonds','ID','Point','Bond','Lattice']

from numpy import *
from numpy.linalg import norm,inv
from ConstantPy import RZERO
from IDPy import ID
from scipy.spatial import cKDTree
from copy import deepcopy
import matplotlib.pyplot as plt
import itertools 

def azimuthd(self):
    '''
    Azimuth in degrees of an array-like vector.
    '''
    if self[1]>=0:
        return degrees(arccos(self[0]/norm(self)))
    else:
        return 360-degrees(arccos(self[0]/norm(self)))

def azimuth(self):
    '''
    Azimuth in radians of an array-like vector.
    '''
    if self[1]>=0:
        return arccos(self[0]/norm(self))
    else:
        return 2*pi-arccos(self[0]/norm(self))

def polard(self):
    '''
    Polar angle in degrees of an array-like vector.
    '''
    if self.shape[0]==3:
        return degrees(arccos(self[2]/norm(self)))
    else:
        raise ValueError("PolarD error: the array-like vector must contain three elements.")

def polar(self):
    '''
    Polar angle in radians of an array-like vector.
    '''
    if self.shape[0]==3:
        return arccos(self[2]/norm(self))
    else:
        raise ValueError("Polar error: the array-like vector must contain three elements.")

def volume(O1,O2,O3):
    '''
    Volume spanned by three array-like vectors.
    '''
    if O1.shape[0] in [1,2] or O2.shape[0] in [1,2] or O3.shape[0] in [1,2]:
        return 0
    elif O1.shape[0] ==3 and O2.shape[0]==3 and O3.shape[0]==3:
        return inner(O1,cross(O2,O3))
    else:
        raise ValueError("Volume error: the shape of the array-like vectors is not supported.")

def is_parallel(O1,O2):
    '''
    Judge whether two array-like vectors are parallel to each other.
    Parameters:
        O1,O2: 1D array-like
    Returns: int
         0: not parallel,
         1: parallel, and 
        -1: anti-parallel.
    '''
    norm1=norm(O1)
    norm2=norm(O2)
    if norm1<RZERO or norm2<RZERO:
        return 1
    elif O1.shape[0]==O2.shape[0]:
        buff=inner(O1,O2)/(norm1*norm2)
        if abs(buff-1)<RZERO:
            return 1
        elif abs(buff+1)<RZERO:
            return -1
        else:
            return 0
    else:
        raise ValueError("Is_parallel error: the shape of the array-like vectors does not match.") 

def reciprocals(vectors):
    '''
    Return the corresponding reciprocals dual to the input vectors.
    Parameters:
        vectors: 2D array-like
    Returns:
        The reciprocals.
    '''
    result=[]
    nvectors=len(vectors)
    if nvectors==0:
        return
    if nvectors==1:
        result.append(array(vectors[0]/(norm(vectors[0]))**2*2*pi))
    elif nvectors in (2,3):
        ndim=vectors[0].shape[0]
        buff=zeros((3,3))
        buff[0:ndim,0]=vectors[0]
        buff[0:ndim,1]=vectors[1]
        if nvectors==2:
            buff[(2 if ndim==2 else 0):3,2]=cross(vectors[0],vectors[1])
        else:
            buff[0:ndim,2]=vectors[2]
        buff=inv(buff)
        result.append(array(buff[0,0:ndim]*2*pi))
        result.append(array(buff[1,0:ndim]*2*pi))
        if nvectors==3:
            result.append(array(buff[2,0:ndim]*2*pi))
    else:
        raise ValueError('Reciprocals error: the number of translation vectors should not be greater than 3.')
    return result

def tiling(cluster,vectors,indices,translate_icoord=False,return_map=False):
    '''
    Tile a supercluster by translations of the input cluster.
    Parameters:
        cluster: list of Point
            The original cluster.
        #translations: list of 3-tuple
        #    For each tuple:
        #        tuple[0]: 1D ndarray
        #            The translation vector for the original cluster.
        #        tuple[1],tuple[2]: integer
        #            The start number and end number of slices along the corresponding vector.
        vectors: list of 1D ndarray
            The translation vectors.
        indices: any iterable object of tuple
            It iterates over the indices of the translated clusters in the tiled superlattice.
        translate_icoord: logical, optional
            If it is set to be False, the icoord of the translated points will not be changed.
            Otherwise, the icoord of the translated points will be set to be equal to the vectors connecting the original points and the translated points.
        return_map: logical, optional
            If it is set to be False, the tiling map will not be returned.
            Otherwise, the tiling map will be returned.
    Returns:
        supercluster: list of Point
            The supercluster tiled from the translations of the input cluster.
        map: dict,optional
            The tiling map, whose key is the translated point's id and value the original point's id.
            Only when return_map is set to be True, will it be returned.
        
    '''
    supercluster,map=[],{}
    for point in cluster:
        if not hasattr(point.id,'site'):
            raise ValueError("Function tiling error: to use this function, the id of every input point must have the attribute 'site'.")

    inc=max([point.id.site for point in cluster])+1

    for index in indices:
        index=array(index)
        for point in cluster:
            id=deepcopy(point.id.__dict__)
            id['site']=point.id.site+(product([i+1 for i in index])-1)*inc
            new=ID(**id)
            map[new]=map[point.id] if point.id in map else point.id
            disp=inner(index,vectors)
            if translate_icoord:
                supercluster.append(Point(id=new,rcoord=point.rcoord+disp,icoord=point.icoord+disp))
            else:
                supercluster.append(Point(id=new,rcoord=point.rcoord+disp,icoord=point.icoord))
    if return_map:
        return supercluster,map
    else:
        return supercluster

def bonds(cluster,vectors=[],nneighbour=1,max_coordinate_number=6):
    '''
    This function returns all the bonds up to the nneighbour-th order.
    Parameters:
        cluster: list of Point
            The cluster within which the bonds are looked for. 
            If the parameter vectors is not None, the inter cluster bonds will also be searched.
        vectors: list of 1D ndarray, optional
            The translation vectors for the cluster.
        nneighbour: integer, optional
            The highest order of neighbour to be searched.
        max_coordinate_number: int, optional
            The max coordinate number for every neighbour.
    Returns:
        result: list of Bond
            All the bonds up to the nneighbour-th order.
            Note that the input points will be used to form the zero-th neighbour bonds, i.e. the start point and the end point is the same point.
    '''
    result=[]
    supercluster,map=tiling(cluster=cluster,translations=[(vector,nneighbour+1) for vector in vectors],translate_icoord=True,return_map=True)
    tree=cKDTree([point.rcoord for point in supercluster])
    distances,indices=tree.query([point.rcoord for point in cluster],k=nneighbour*max_coordinate_number)
    mdists=[inf for i in xrange(nneighbour+1)]
    for dist in concatenate(distances):
        for i,mdist in enumerate(mdists):
            if abs(dist-mdist)<RZERO:
                break
            elif dist<mdist:
                mdists[i+1:nneighbour+1]=mdists[i:nneighbour]
                mdists[i]=dist
                break
    max_mdists=mdists[nneighbour]
    for i,(dists,inds) in enumerate(zip(distances,indices)):
        max_dists=dists[nneighbour*max_coordinate_number-1]
        if max_dists<max_mdists or abs(max_dists-max_mdists)<RZERO:
            raise ValueError("Function bonds error: the max_coordinate_number(%s) should be larger."%max_coordinate_number)
        for dist,index in zip(dists,inds):
            for neighbour,mdist in enumerate(mdists):
                if abs(dist-mdist)<RZERO:
                    buff=supercluster[index]
                    result.append(Bond(neighbour,spoint=cluster[i],epoint=Point(id=map[buff.id],rcoord=buff.rcoord,icoord=buff.icoord)))
    return result    

class Point:
    '''
    Point.
    Attributes:
        id: ID
            The specific id of a point.
        rcoord: 1D ndarray
            The coordinate in real space.
        icoord: 1D ndarray
            The coordinate in lattice space.
    '''

    def __init__(self,id,rcoord=None,icoord=None):
        '''
        Constructor.
        Parameters:
            id: ID
                The specific id of a point
            rcoord: 1D array-like
                The coordinate in real space.
            icoord: 1D array-like,optional
                The coordinate in lattice space.
        '''
        if not isinstance(id,ID):
            raise ValueError("Point constructor error: the 'id' parameter must be an instance of ID.")
        self.id=id
        self.rcoord=array([]) if rcoord is None else array(rcoord)
        self.icoord=array([]) if icoord is None else array(icoord)

    def __str__(self):
        '''
        Convert an instance to string.
        '''
        return 'id,rcoord,icoord: %s, %s, %s'%(self.id,self.rcoord,self.icoord)

    def __repr__(self):
        '''
        Convert an instance to string.
        '''
        return '<Point>id,rcoord,icoord: %s, %s, %s'%(self.id,self.rcoord,self.icoord)

    def __eq__(self,other):
        '''
        Overloaded operator(==).
        '''
        return self.id==other.id and norm(self.rcoord-other.rcoord)<RZERO and norm(self.icoord-other.icoord)<RZERO
    
    def __ne__(self,other):
        '''
        Overloaded operator(!=).
        '''
        return not self==other

class Bond:
    '''
    This class describes the bond in a lattice.
    Attributes:
        neighbour: integer
            The rank of the neighbour of the bond.
        spoint: Point
            The start point of the bond.
        epoint: Point
            The end point of the bond.
    '''
    
    def __init__(self,neighbour,spoint,epoint):
        '''
        Constructor.
        '''
        self.neighbour=neighbour
        self.spoint=spoint
        self.epoint=epoint

    def __str__(self):
        '''
        Convert an instance to string.
        '''
        return 'Neighbour: %s\nSpoint -:- %s\nEpoint -:- %s'%(self.neighbour,self.spoint,self.epoint)
    
    @property
    def rcoord(self):
        '''
        The real coordinate of a bond.
        '''
        return self.epoint.rcoord-self.spoint.rcoord
    
    @property
    def icoord(self):
        '''
        The lattice coordinate of a bond.
        '''
        return self.epoint.icoord-self.spoint.icoord
    
    def is_intra_cell(self):
        '''
        Judge whether a bond is intra the unit cell or not. 
        '''
        if norm(self.icoord)< RZERO:
            return True
        else:
            return False

    @property
    def reversed(self):
        '''
        Return the reversed bond.
        '''
        return Bond(self.neighbour,self.epoint,self.spoint)

class Lattice(object):
    '''
    This class provides a unified description of 1D, quasi 1D, 2D, quasi 2D and 3D lattice systems.
    Attributes:
        name: string
            The lattice's name.
        points: dict of Point
            The lattice points in a unit cell.
        vectors: list of 1D ndarray
            The translation vectors.
        reciprocals: list of 1D ndarray
            The dual translation vectors.
        nneighbour: integer
            The highest order of neighbours;
        bonds: list of Bond
            The bonds of the lattice system.
        max_coordinate_number: int
            The max coordinate number for every neighbour.
    '''

    def __init__(self,name,points,vectors=[],nneighbour=1,max_coordinate_number=6):
        '''
        Constructor.
        Parameters:
            name: string
                The name of the lattice.
            points: list of Point
                The lattice points in a unit cell.
            vectors: list of 1D ndarray, optional
                The translation vectors of the lattice.
            nneighbour: integer, optional
                The highest order of neighbours.
            max_coordinate_number: int, optional
                The max coordinate number for every neighbour.
                This variable is used in the search for bonds.
        '''
        self.name=name
        self.points={p.id:p for p in points}
        self.vectors=vectors
        self.reciprocals=reciprocals(self.vectors)
        self.nneighbour=nneighbour
        self.max_coordinate_number=max_coordinate_number
        self.bonds=bonds(points,vectors,nneighbour,max_coordinate_number)

    def __str__(self):
        '''
        Convert an instance to string.
        '''
        result=''
        for bond in self.bonds:
            result+='%s\n'%bond
        return result

    def plot(self,show=True):
        '''
        Plot the lattice points and bonds. Only 2D or quasi 1D systems are supported.
        '''
        plt.axes(frameon=0)
        plt.axis('equal')
        plt.title(self.name)
        for bond in self.bonds:
            nb=bond.neighbour
            if nb==1: color='k'
            elif nb==2: color='r'
            elif nb==3: color='b'
            else: color=str(nb*1.0/self.nneighbour)
            if nb==0:
                plt.scatter(bond.spoint.rcoord[0],bond.spoint.rcoord[1])
            else:
                if bond.is_intra_cell():
                    plt.plot([bond.spoint.rcoord[0],bond.epoint.rcoord[0]],[bond.spoint.rcoord[1],bond.epoint.rcoord[1]],color=color)
                else:
                    plt.plot([bond.spoint.rcoord[0],bond.epoint.rcoord[0]],[bond.spoint.rcoord[1],bond.epoint.rcoord[1]],color=color,ls='--')
        frame=plt.gca()
        frame.axes.get_xaxis().set_visible(False)
        frame.axes.get_yaxis().set_visible(False)
        if show:
            plt.show()
        else:
            plt.savefig(self.name+'.png')
        plt.close()
