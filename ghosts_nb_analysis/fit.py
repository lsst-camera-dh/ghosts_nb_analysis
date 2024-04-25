"""fit module

This module provides functions to fit ghosts spots on the focal plane

"""
import pylab as plt
import numpy as np
import math

from ghosts_nb_analysis.utils import displayImageGhosts


class spot_fitter(object):
    """ 
    """
    def __init__(self, obs_id, mosaic):
        """ Constructor """
        self.obs_id = obs_id
        self.imageF = mosaic
        self.fit_box_size_list = [100, 75, 50, 30]
        
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
        npx, npy = self.imageF.getDimensions()
        xmin = max(0, x_center-ds)
        ymin = max(0, y_center-ds)
        xmax = min(npx-1, x_center+ds)
        ymax = min(npy-1, y_center+ds)
        ghost_box = Box2I(minimum=Point2I(x=xmin, y=ymin), maximum=Point2I(x=xmax, y=ymax))
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
            
    def run_fit(self, ghost_xy):
        """ Iterate on different windows size to get all fits fine
        """
        dsl = self.fit_box_size_list
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


###########################
# Deprecated
def show_ghost_fit(obs_id, ghost_stamp, params):
    # plot ghosts stamp
    bbox = ghost_stamp.getBBox()
    plt.imshow(ghost_stamp.getArray(), cmap='plasma', vmin=0, vmax=20,
               extent=[bbox.getMinX(), bbox.getMaxX(), bbox.getMaxY(), bbox.getMinY()])
    plt.title(obs_id)

    # define fit function
    gauss2d = gaussian(*params)
    # plot gaussian contours 
    plt.contour(bbox.x.range(), bbox.y.range(), gauss2d(*bbox.grid()), cmap=plt.cm.copper)
    
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

def fit_and_display_ghosts(obs_id, targets_list):
    n_cols = 5
    n_rows=4
    fig, ax = plt.subplots(n_cols, n_rows, constrained_layout=True, figsize=(32, 32))
    display = afwDisplay.Display(frame=fig)
    plt.title(obs_id)
    axs = ax.ravel()
    spots_list = []
    for i, spot in enumerate(targets_list):
        fig.sca(axs[i])
        params = fit_ghost_iter(spot)
        ghost_stamp = make_stamp(*spot, ds=100)
        display_ghost_fit(obs_id, ghost_stamp, params, display=display)
        spots_list.append(params)
    return spots_list

def plot_ghosts_mosaic(targets_list):
    from lsst.afw.display.utils import Mosaic
    plt.rcParams["figure.figsize"] = [12, 12]
    # image list
    images = []
    for i, spot in enumerate(targets_list):
        images.append(make_stamp(*spot))
    # Mosaic
    m = Mosaic(gutter=30, background=0, mode='square')
    mosaic = m.makeMosaic(images)
    display = afwDisplay.Display(999)
    display.scale('linear', min=0, max=20)
    display.setImageColormap(cmap='plasma')
    display.mtv(mosaic)
    return m, display

def fit_and_map_ghosts(obs_id, targets_list):
    n_cols = 5
    n_rows=4
    fig, ax = plt.subplots(n_cols, n_rows, constrained_layout=True, figsize=(32, 32))
    plt.title(obs_id)
    axs = ax.ravel()
    spots_list = []
    for i, spot in enumerate(targets_list):
        fig.add_subplot(axs[i])
        fig.sca(axs[i])
        params = fit_ghost_iter(spot)
        ghost_stamp = make_stamp(*spot, ds=100)
        show_ghost_fit(obs_id, ghost_stamp, params)
        spots_list.append(params)
    return spots_list

