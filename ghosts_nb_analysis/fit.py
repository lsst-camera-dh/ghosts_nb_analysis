"""fit module

This module provides functions to fit ghosts spots on the focal plane

"""

import numpy as np
import math

class spot_fitter(object):
    """ 
    """
    def __init__(self, obs_id, mosaic):
        """ Constructor """
        self.obs_id = obs_id
        self.imageF = mosaic
        
    def _gaussian(self, bkg, height, center_x, center_y, width):
        """ Returns a gaussian function with the given parameters
        """
        width = float(width)
        bkg = float(bkg)
        return lambda x,y: bkg + height*np.exp(
                    -(((center_x-x)/width)**2+((center_y-y)/width)**2)/2)
    
    def _moments(self, data):
        """ Returns (height, x, y, width)
        the gaussian parameters of a 2D distribution by calculating its
        moments """
        total = data.sum()
        X, Y = np.indices(data.shape)
        x = (X*data).sum()/total
        y = (Y*data).sum()/total
        col = data[:, int(y)]
        width = np.sqrt(np.abs((np.arange(col.size)-x)**2*col).sum()/col.sum())
        row = data[int(x), :]
        height = data.max()
        bkg = data.mean()
        # x = 100
        # y = 100
        return bkg, height, x, y, width
    
    def _optimize(self, data):
        """ Returns (height, x, y, width)
        the gaussian parameters of a 2D distribution found by a fit"""
        from scipy import optimize
        params = self._moments(data)
        errorfunction = lambda p: np.ravel(self._gaussian(*p)(*np.indices(data.shape)) -
                                     data)
        p, success = optimize.leastsq(errorfunction, params)
        return p

    def make_stamp(self, x_center, y_center, ds=100):
        """ Make a stamp image around a ghost position
        """
        from lsst.geom import Point2I, Box2I
        ghost_box = Box2I(minimum=Point2I(x=x_center-ds, y=y_center-ds), maximum=Point2I(x=x_center+ds, y=y_center+ds))
        ghost_stamp = self.imageF[ghost_box]   # same as no ImageOrigin argument
        return ghost_stamp

    def fit_gaussian(self, ghost_stamp):
        """ Fit a 2D gaussian on a ghost stamp
        """
        # data - transpose for the fit
        stamp_array = np.transpose(ghost_stamp.getArray())
        # Fit centered in (100,100)
        params = self._optimize(stamp_array)
        # verification
        # fit = gaussian(*params)
        # plt.matshow(cutout, cmap='plasma')
        # plt.contour(fit(*np.indices(cutout.shape)), cmap=plt.cm.copper)
        # Move Gaussian to focal plane coordinates
        rc_params = params.copy()
        rc_params[2] = params[2]+ghost_stamp.getX0()
        rc_params[3] = params[3]+ghost_stamp.getY0()
        rc_fit = self._gaussian(*rc_params)
        return rc_params
            
    def run_fit(self, ghost_xy, dsl=[100, 75, 50, 30]):
        """ Iterate on different windows size to get all fits fine
        """
        for ds in dsl:
            ghost_stamp = self.make_stamp(*ghost_xy, ds=ds)
            bkg, height, x, y, width = self.fit_gaussian(ghost_stamp)
            if abs(x-ds)>ds/2. or abs(y-ds)>ds/2.:
                continue
            else:
                break    
        return [bkg, height, x, y, width]

    def display_ghost_fit(self, ghost_stamp, params, display=None):
        """ Display a ghost stamp and parameters of the spot, usually coming from a fit
        """
        # plot ghosts stamp
        afwdisplay = displayImageGhosts(ghost_stamp, title=self.obs_id, frame_size=5, display=display)
        
        # build gaussian function
        gauss2d = self._gaussian(*params)

        # plot gaussian contours 
        bbox = ghost_stamp.getBBox()
        plt.contour(bbox.x.range(), bbox.y.range(), gauss2d(*bbox.grid()),
                    levels=2, cmap="plasma")
        
        # write params on plot
        ax = plt.gca()
        (bkg, height, x, y, width) = params
        plt.text(0.95, 0.05, """
        bkg : %.1f
        height : %.1f
        x : %.3f
        y : %.3f
        width : %.3f""" %(bkg, height, x, y, width),
                fontsize=16, horizontalalignment='right',
                verticalalignment='bottom', transform=ax.transAxes)    
        print(f'Params (bkg, height, x, y, width): {bkg:.1f}, {height:.1f}, {x:.3f}, {y:.3f}, {width:.3f}')
        return afwdisplay

    def fit_and_display(self, ghost_xy, ds=100, display=None):    
        """ Run the fit and display results
        """
        params = self.run_fit(ghost_xy)
        ghost_stamp = self.make_stamp(*ghost_xy, ds=ds)
        self.display_ghost_fit(ghost_stamp, params, display=display)
        return params

