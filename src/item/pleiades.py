import os
import pystac

from pystac.extensions.eo import Band
from shapely.geometry import box, mapping
from item.base import Base


class Pleiades( Base ):
    
    def __init__( self, path ):

        """
        constructor
        """

        # base constructor
        super().__init__( os.path.join( path, 'pleiades' ) )
        return


    def getItem( self, uri, **kwargs ):

        """
        get meta
        """

        item = None

        # get configuration
        config = self.getConfig( os.path.basename( uri ) )
        if config is None:
            raise ValueError ( 'Unable to locate configuration file: {uri}'.format( uri=uri ) )

        # spatial / temporal attributes
        epsg = self.getEpsg( uri )
        bbox = self.getBoundingBox( uri, epsg )
        timestamp = self.getTimestamp( uri )

        # check validity
        if bbox is None or timestamp is None:
            raise ValueError ( 'Invalid spatiotemporal extent: {uri}'.format( uri=uri ) )

        # create item
        item = pystac.Item( id=self.getId( uri ),
                            geometry=mapping(bbox),
                            bbox=list( bbox.bounds ),
                            datetime=timestamp,
                            properties={})

        # set common attributes
        common = config[ 'collection' ][ 'item' ][ 'common' ]

        shortname = self.getMatch( uri, r'_PHR[\d][A|B]_' ).strip( '_' )
        item.common_metadata.platform = common[ 'platform' ] + ' ' + shortname.replace( 'PHR', '' )
        
        item.common_metadata.instrument = common[ 'instruments' ]            
        item.common_metadata.gsd = common[ 'gsd' ]

        # add projection ext
        item.ext.enable('projection')
        item.ext.projection.epsg = epsg

        # add eo ext
        item.ext.enable(pystac.Extensions.EO)
        item.ext.eo.apply( bands=self.getBands( config[ 'collection' ][ 'item' ][ 'eo' ] ) )

        # create asset        
        asset = pystac.Asset(   href=uri.replace( '/vsigs/', 'https://storage.googleapis.com/' ),
                                media_type=pystac.MediaType.GEOTIFF )

        item.add_asset( 'image', asset )
        
        return item


    def getId( self, uri ):

        """
        get id
        """

        # split unique id from filename
        tokens = os.path.basename( uri ).split( '_' )
        if len( tokens ) < 6:
            raise ValueError( 'Unknown naming convention: {uri}'.format( uri=uri ) )

        return tokens[ 5 ]

