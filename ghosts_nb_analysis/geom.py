"""geom module

This module provides functions to access to the camera geometry
and transform coordinates from pixels to DVCS, and from focal plane to CCD.

"""
import numpy as np
from lsst.afw import cameraGeom
from lsst.obs.lsst import LsstCam


def focal_to_pixel(fpx, fpy, det):
    """
    Parameters
    ----------
    fpx, fpy : array
        Focal plane position in millimeters in DVCS
        See https://lse-349.lsst.io/
    det : lsst.afw.cameraGeom.Detector
        Detector of interest.

    Returns
    -------
    x, y : array
        Pixel coordinates.
    """
    tx = det.getTransform(cameraGeom.FOCAL_PLANE, cameraGeom.PIXELS)
    x, y = tx.getMapping().applyForward(np.vstack((fpx, fpy)))
    return x.ravel(), y.ravel()

def pixel_to_focal(x, y, det):
    """
    Parameters
    ----------
    x, y : array
        Pixel coordinates.
    det : lsst.afw.cameraGeom.Detector
        Detector of interest.

    Returns
    -------
    fpx, fpy : array
        Focal plane position in millimeters in DVCS
        See https://lse-349.lsst.io/
    """
    tx = det.getTransform(cameraGeom.PIXELS, cameraGeom.FOCAL_PLANE)
    fpx, fpy = tx.getMapping().applyForward(np.vstack((x, y)))
    return fpx.ravel(), fpy.ravel()
    
def getMosaicCenter(imageF):
    """ Returns the pixels coordinates of the center of the mosaic
    """
    bbox = imageF.getBBox()
    nx0, ny0 = bbox.getCenter()
    return nx0, ny0

def mosaicPixelsToRoughDVCS(mosaic, nx, ny, nbins=8):
    """ Transform pixel coordinates to mm position in the focal plane
    
    Parameters
    ----------
    mosaic : lsst.afw.image.imageF
        A mosaic image of the full focal plane, e.g. created with eoFocalPlaneMosaic task
    nx, ny : floats
        Pixel coordinates.
    nbins : int
        Sampling of the full focal plane mosaic, e.g. 8 by default for the eoFocalPlaneMosaic task

    Returns
    -------
    fpx, fpy : floats
        position in the focal plane in mm 
    
    """
    nx0, ny0 = getMosaicCenter(mosaic)
    fpx = (nx-nx0)*nbins*10e-3
    fpy = (ny-ny0)*nbins*10e-3
    return fpx, fpy

def fpDVCStoCCDpixels(mosaic, nx, ny, nbins=8):
    """ Get the CCD name and position in pixel coordinates from
    a position in full focal plane DVCS coordinates.
    
    Parameters
    ----------
    mosaic : lsst.afw.image.imageF
        A mosaic image of the full focal plane, e.g. created with eoFocalPlaneMosaic task
    nx, ny : floats
        Pixel coordinates.
    nbins : int
        Sampling of the full focal plane mosaic, e.g. 8 by default for the eoFocalPlaneMosaic task

    Returns
    -------
    ccd : lsst.afw.cameraGeom.Detector
        Detector of interest.
        
    x, y : floats
        pixels coordinates in the detector reference frame
    
    """
    # focal plane center to pixels coordinate w.r.t. R22_S11
    # ax0, ay0 = focal_to_pixel([0], [0.], camera['R22_S11'])
    # this is to have an idea of where the center of a CCD is pixels coordinates
    x0 = 2047.5
    y0 = 2001.5
    
    # first transform pixel coordinates to mm position in the focal plane
    fpx, fpy = mosaicPixelsToRoughDVCS(mosaic, nx, ny, nbins=nbins)
    
    # need an LSST camera
    camera = LsstCam.getCamera()
    # initialize output
    det_name = None
    x = 0.
    y = 0.
    # loop on all detectors to find the good one
    for det_num, det in enumerate(camera):
        #print(det_num, det.getName())
        # get pixels coordinate w.r.t current detector
        pos = focal_to_pixel([fpx], [fpy], det)
        xp, yp = pos[0][0], pos[1][0]
        # if pixels coordinate are within the range of one CCD
        # we found the good one !
        if xp>0 and yp>0 and xp<4100 and yp<4100:
            ccd = det
            x = xp
            y = yp
            break
    return ccd, x, y
