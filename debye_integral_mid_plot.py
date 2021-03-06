import numpy as np
from matplotlib import pyplot as plt
from numpy import exp,pi,sin,cos,sqrt,arctan2,arcsin     
def getPhaseMask(theta,psi,f,z1,z2,z3,z4):
    """
    The function to calculate the phase mask to reproduce the 4 main aberations for high NA objectives
    ----------
    theta: variable that will be integrated on in the debye integral
    psi: variable that will be integrated on in the debye integral
    f： focal length
    z1: defocus
    z2, z3: lateral and vertical astigmatism
    z4: spherical aberration
    
    Returns
    -------
    mask:
        the phase mask
    
    """
    mask = 0
    mask += z1* np.sqrt(3)*(2*((f*np.sin(theta))**2) - 1)
    mask += z2* np.sqrt(6)*((f*np.sin(theta))**2)*np.cos(2*psi)
    mask += z3* np.sqrt(6)*((f*np.sin(theta))**2)*np.sin(2*psi)
    mask += z4* np.sqrt(5)*(6*((f*np.sin(theta))**4) - 6*((f*np.sin(theta))**2) + 1)
   
    mask = mask % (2 * np.pi) -np.pi
        
    return mask

def addPhaseFeature(mask,theta,psi,f,feature,Z1,Z2):
    """
    Calculates the phase mask to reproduce typical PSF modification
    ----------
    mask: mask to be altered
    theta: variable that will be integrated on in the debye integral
    psi: variable that will be integrated on in the debye integral
    f： focal length
    feature: Phase feature to add
    Z1: variable parameter
    Z2: variable parameter
    
    Returns
    -------
    mask:
        the altered phase mask
    
    """
    
    if feature == 'STED':

        mask = mask+psi*Z1
  
    elif feature == 'bessel':

        mask = mask+np.pi*2*np.cos(Z1*(f*np.sin(theta)))

    elif feature == 'bessel phase':

        mask = mask+Z1*(f*np.sin(theta))

    elif feature == 'bottle':
        
        if Z2<f*np.sin(theta)<Z1:
            mask = mask + pi/2

    mask = mask % (2 * np.pi) -np.pi
        
    return mask

def getPupil(theta,psi,f,beam,Z1,Z2):
    """
    Calculates the beam amplitude at the back of the lens
    ----------
    theta: variable that will be integrated on in the debye integral
    psi: variable that will be integrated on in the debye integral
    f： focal length
    beam: type of beam to use
    Z1: variable parameter
    Z2: variable parameter
    
    Returns
    -------
    mask:
        W x W square array containing the altered phase mask
    
    """

    pupil = 0
    
    if beam == 'Gaussian':

        pupil = np.exp(-(f*np.sin(theta))**2/(2*Z1**2))
    
    elif beam == 'Airy':

        if Z2<f*np.sin(theta)<Z1:
            pupil = 1
        else:
            pupil = 0
                

    # elif beam == 'SIM':

    #     pupil[rho<Z1] = 1
    #     pupil = np.roll(pupil,(int(Z2*w))) + np.roll(pupil,(-int(Z2*w)))

    # elif beam =='SPIM':

    #     pupil[rho<Z1] = 1
    #     pupil = np.roll(pupil,(int(Z2*w)))

    else:
        pupil = 1

    # pupil = pupil/np.amax(pupil)

    return pupil

# def shiftSpot(pupil, beamCentre):

#     w = pupil.shape[0]
#     padLength = int(np.round(w/2))
#     lims = np.linspace(-1,1,w)
#     x, y = np.meshgrid(lims,lims)
#     rho = np.sqrt(x**2 + y**2) 
#     pupil[rho>1]=0
#     pupil = pupil[::2,::2]
#     newPupil = np.pad(pupil, ((padLength, padLength), (padLength, padLength)), 'constant')
#     newPupil = np.roll(newPupil,int(beamCentre*padLength))


#     return newPupil

def addLinearPhase(mask,f,theta,psi,tilt):
    x = f*sin(theta)*cos(psi)   
    linPhase = x*tilt
    linPhase = linPhase % (2 * np.pi) -np.pi
    mask = mask + linPhase
    mask = mask % (2 * np.pi) -np.pi

    return mask

def beam_sphere(theta,psi,f):
    mask = getPhaseMask(theta,psi,f,0,0,0,0)
    mask = addPhaseFeature(mask,theta,psi,f,'STED',1,0)
    mask = addLinearPhase(mask,f,theta,psi,0.5)
    pupil = getPupil(theta,psi,f,'Airy',5,4)
    beam = pupil*np.exp(1j*mask)
    return (beam,mask,pupil)
   
def debyr_integral(alpha,lam,f,E_x,E_y): 
    """
    Calculates the debye integral and get intensity of beams after passing through lens
    ----------
    alpha: NA = sin(alpha), it is also the upper limit of theta
    lam: wavelength(μm)
    f: focal length of lens 
    E_x,E_y: polarisation of the beams E_x = 1 for x-polarised and E_y = 1 for y-polarised
    
    Returns
    -------
    intesity:
        W x W square array containing the intensity
    
    """
    w = 512
    lims = np.linspace(-2,2,w)
    x, y = np.meshgrid(lims,lims)
    z = 0
    k = 2*pi/lam
    r = sqrt(x**2+y**2)
    phi = arctan2(y,x)
    intensity = np.zeros([w,w])
    

    def midpoint_double1(f, a, b, c, d, nx, ny):
        hx = (b - a)/float(nx)
        hy = (d - c)/float(ny)
        I = 0
        for i in range(nx):
            for j in range(ny):
                xi = a + hx/2 + i*hx
                yj = c + hy/2 + j*hy
                I += hx*hy*f(xi, yj)
        return I
        
        
    def e(theta,psi): 
        q1 = cos(theta) + 1
        q2 = cos(theta) - 1
        q3 = 2*sin(theta)
        #q4 = 2*cos(theta)
            
        a_theta = 0.5*sqrt(cos(theta))
            
        ex = a_theta*(E_x*(q1+q2*cos(2*psi))+E_y*q2*sin(2*psi))*(-1j)/lam*f*exp(1j*(k*z*cos(theta)+k*r*sin(theta)*cos(psi-phi)))*sin(theta)*beam_sphere(theta,psi,f)[0]
        ey = a_theta*(E_y*(q1-q2*cos(2*psi))+E_x*q2*sin(2*psi))*(-1j)/lam*f*exp(1j*(k*z*cos(theta)+k*r*sin(theta)*cos(psi-phi)))*sin(theta)*beam_sphere(theta,psi,f)[0]
        ez = a_theta*(-q3)*(E_x*cos(psi)+E_y*sin(psi))*(-1j)/lam*f*exp(1j*(k*z*cos(theta)+k*r*sin(theta)*cos(psi-phi)))*sin(theta)*beam_sphere(theta,psi,f)[0]
        return (ex,ey,ez)
        
        
        
    Ex = np.abs(midpoint_double1(lambda theta, psi: e(theta,psi)[0], 0, alpha, 0, 2*pi, 20, 20))
    Ey = np.abs(midpoint_double1(lambda theta, psi: e(theta,psi)[1], 0, alpha, 0, 2*pi, 20, 20))
    Ez = np.abs(midpoint_double1(lambda theta, psi: e(theta,psi)[2], 0, alpha, 0, 2*pi, 20, 20))
    
    intensity += (Ex**2+Ey**2+Ez**2)
    return intensity


def plotPhaseMask(f,w):
    """
    Generate the plot of phase mask
    
    """
    x = np.linspace(-1,1,w)
    y = np.linspace(-1,1,w)
    mask1 = np.zeros([w,w])
    for i in range(w):
        for j in range(w):
            theta = arctan2(np.sqrt(x[i]**2 + y[j]**2),f) 
            psi = np.arctan2(y[j], x[i])
            mask1[j,i] += beam_sphere(theta,psi,f)[1]
    return mask1
def plotPupil(f,w):
    """
    Generate the plot of pupil
    
    """
    x = np.linspace(-4*f,4*f,w)
    y = np.linspace(-4*f,4*f,w)
    pupil1 = np.zeros([w,w])
    for i in range(w):
        for j in range(w):
            theta = arctan2(np.sqrt(x[i]**2 + y[j]**2),f) 
            psi = np.arctan2(y[j], x[i])
            pupil1[j,i] += beam_sphere(theta,psi,f)[2]
    return pupil1

sample = debyr_integral(0.7,0.68,10,0,8)
mask1 = plotPhaseMask(10,512)
pupil1 = plotPupil(10,512)
plt.figure(figsize=(10, 10))


centre = np.shape(sample)[1]/2
lim_up = int(centre+200)
lim_down = int(centre-200)
plt.subplot(1,3,1)
plt.imshow(sample[lim_down:lim_up,lim_down:lim_up],cmap = 'gray')
plt.subplot(1,3,2)
plt.imshow(pupil1,cmap = 'gray')
plt.subplot(1,3,3)
plt.imshow(mask1,cmap = 'gray')
plt.show()
