import os
import re
import yaml
import glob
import math

import osr
import gdal
import pyproj

from shapely.geometry import box
from shapely.ops import transform

from pystac.extensions.eo import Band
from utility.parser import getDateTime


class Base:

    def __init__( self, path ):

        """
        constructor
        """

        self._configs = []

        # load config parameters from file
        names = glob.glob( os.path.join( path, '*.yml' ) )
        for name in names:
            with open( name, 'r' ) as f:
                self._configs.append( yaml.safe_load( f ) )

        return


    def getConfig( self, uri ):

        """
        get config
        """

        # locate collection
        match = None
        for config in self._configs:

            if self.getMatch ( uri, config[ 'collection' ][ 'match'] ) is not None:
                match = config
                break

        return match


    @staticmethod
    def getClassName( scene ):

        """
        get identity of dataset
        """

        # ids mapped to class names
        class_map = {   'PHR' : 'Pleiades',
                        'SPOT' : 'Spot'
         }

        _name = None
        for key, value in class_map.items():

            # spot or pleiades dataset
            if key in os.path.basename( scene ):
                _name = value
                break

        return _name


    def getBoundingBox( self, uri, epsg ):

        bbox = None

        # open existing image
        ds = gdal.Open( uri, gdal.GA_ReadOnly )
        if ds is not None:

            # get bbox
            ulx, xres, xskew, uly, yskew, yres  = ds.GetGeoTransform()
            lrx = ulx + ( ds.RasterXSize * xres )
            lry = uly + ( ds.RasterYSize * yres )

            bbox = box( lrx, lry, ulx, uly )            

            # create source to destination transform
            prj = pyproj.Transformer.from_proj( pyproj.Proj(init='epsg:{}'.format( epsg ) ),
                                                pyproj.Proj(init='epsg:4326' ), skip_equivalent=True ) 

            bbox = transform( prj.transform, bbox )   


        return None if math.inf in bbox.bounds else bbox


    def getEpsg( self, uri ):


        epsg = None

        # open existing image
        ds = gdal.Open( uri, gdal.GA_ReadOnly )
        if ds is not None:

            # get geotransform
            prj = osr.SpatialReference( wkt=ds.GetProjection() )
            epsg = prj.GetAttrValue('AUTHORITY', 1 )

        return epsg

    
    def getTimestamp( self, uri ):

        """
        retrieve satellite name and tle from pathname
        """

        return getDateTime( uri )


    def getMatch( self, z, exp ):

        """
        retrieve satellite name and tle from pathname
        """

        match = None

        # identify platform name
        m = re.search( exp, z )
        if m:
            match = str(m.group(0) )

        return match


    def getBands( self, config ):

        """
        get bands
        """

        bands = []
        for band in config[ 'bands' ]:
            bands.append( Band.create(name=band['name'], description=band[ 'description' ], common_name=band[ 'common_name' ] ) )

        return bands
