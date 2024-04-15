# plotting
import pylab as plt
import numpy as np

# butler
from lsst.daf.butler import Butler

# isr and display
import lsst.afw.display as afwDisplay
from lsst.afw.image import Image

# camera stuff
import lsst.afw.math as afwMath
from lsst.afw.cameraGeom import utils as cgu
from lsst.obs.lsst import LsstCam

from matplotlib.backend_bases import MouseButton


def on_click(event):
    if event.button is MouseButton.LEFT:
        print(f'{event.xdata} {event.ydata}')

def displayImageGhosts(image,title=None, frame_size=16):
    afwDisplay.setDefaultBackend('matplotlib') 
    fig = plt.figure(figsize=(frame_size,frame_size))
    afw_display = afwDisplay.Display(1)
    #afw_display.scale('asinh', 'zscale')
    afw_display.scale('linear', min=0, max=20)
    afw_display.setImageColormap(cmap='plasma')
    afw_display.mtv(image)
    plt.title(title)
    #plt.gca().axis('off')
    return afw_display


import lsst.daf.butler as daf_butler
repo = "/sdf/data/rubin/repo/ir2"
butler = daf_butler.Butler(repo)

collections = butler.registry.queryCollections(f"u/bregeon/eo_focal_plane_mosaic*",
                                               collectionTypes=daf_butler.CollectionType.CHAINED)
for item in collections[:5]:
    print(item)

myref=list(set(butler.registry.queryDatasets(datasetType='eoFpMosaic',
                                       instrument='LSSTCam',
                                       collections=collections)))

imageF = butler.get(myref[0])
displayImageGhosts(imageF, frame_size=12)

plt.connect('button_press_event', on_click)
plt.show()

