import os
import json
import yaml
import pystac
import geojson
import argparse
from itertools import chain

from shapely.ops import cascaded_union
from shapely.geometry import mapping, shape

from item.base import Base
from item.spot import Spot 
from item.pleiades import Pleiades
from utility.gsclient import GsClient


def getTemporalExtent( items ):

    """
    get temporal extent
    """

    # compile spatial polygons into list
    dts = []
    for item in items:
        dts.append( item.datetime )

    # sort into descending order
    collection_interval = sorted(dts)
    return pystac.TemporalExtent(intervals=[collection_interval])


def getSpatialExtent( items ):

    """
    get spatial extent
    """

    # compile spatial polygons into list
    polygons = []
    for item in items:

        s = json.dumps( item.geometry )
        polygons.append( shape( geojson.loads( s ) ) )


    # aggregate polygons and compute bbox
    union_footprint = cascaded_union( polygons )
    aggregated_bbox = list( union_footprint.bounds )

    return pystac.SpatialExtent(bboxes=[aggregated_bbox])


def getSpatioTemporalExtent( items ):

    """
    get spatiotemporal extent
    """

    # get spatial and temporal extents
    spatial_extent = getSpatialExtent( items )
    temporal_extent = getTemporalExtent( items )

    return pystac.Extent(spatial=spatial_extent, temporal=temporal_extent)


def getClient( config ):

    """
    get client
    """

    client = None 

    # create gcs client
    if GsClient.isUri( config[ 'bucket' ] ):

        GsClient.updateCredentials( config[ 'key' ] )
        client = GsClient( config[ 'bucket' ] )

    return client


def getItems( config ):

    """
    get items
    """

    items = []

    # select client based on bucket uri
    client = getClient( config )
    if client is None:
        raise ValueError( 'Unable to identify client for bucket: {bucket}'.format( config[ 'bucket' ] ) )

    # get image uri list
    uris = client.getImageUriList( config[ 'prefix' ], config[ 'pattern'] )
    for uri in uris:

        # get class
        _name = Base.getClassName( uri )
        if _name is not None:

            try:                

                # create object
                _class = globals()[ _name ]            
                obj = _class ( '/home/sac/stac-config' )
                
                # add valid items to list
                items.append( obj.getItem( uri ) )
            
            except Exception as e:
                print ( str( e ) )


    return items


def getCatalog( root, items ):

    """
    get catalog
    """

    # create catalog
    obj = pystac.Catalog(  id=root.pop( 'id', 'test_id' ), 
                        description=root.pop( 'description', 'test_description' ) )

    # add optional items and return
    if len( items ) > 0:
        obj.add_items( items )

    return obj


def getCollection( root, items ):

    """
    get collection
    """

    # get spatial and temporal extent
    extent = getSpatioTemporalExtent( items )

    # create collection
    obj = pystac.Collection(id=root[ 'id' ],
                            description=root[ 'description'],
                            extent=extent,
                            license=root[ 'license' ] )

    # add optional items and return
    if len( items ) > 0:
        obj.add_items( items )

    return obj


def getStacObject( config ):
    
    """
    create stac object from configuration - recursively create children
    """

    # config key / function lut
    functions = { 'catalog' : getCatalog, 'collection' : getCollection }
    obj = None

    # match config key with function
    for name in functions.keys():

        if name in config.keys():

            # get object config
            root = config[ name ]

            # create optional items
            items = []
            if 'items' in root.keys():
                items = list ( chain.from_iterable( getItems( c ) for c in root[ 'items' ] ) )

            # create stac object
            obj = functions[ name ]( root, items )

            # add optional child stac objects
            if 'children' in root.keys():
                for child in root[ 'children' ]:
                    obj.add_child( getStacObject( child ) ) 

    return obj


def parseArguments(args=None):

    """
    parse command line arguments
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description='collection creator')
    parser.add_argument( 'config_file', action="store" )
    parser.add_argument( 'out_path', action="store" )

    return parser.parse_args(args)


def main():

    """
    main path of execution
    """

    # parse arguments
    args = parseArguments()

    # read stac specification 
    with open( args.config_file, 'r' ) as f:
        root = yaml.safe_load( f )

    # generate nested stac hierarchy
    obj = getStacObject( root )

    # create out path if required
    if not os.path.exists ( args.out_path ):
        os.makedirs( args.out_path )

    # generate nested stac hierarchy
    obj.normalize_and_save( root_href=args.out_path, 
                            catalog_type=pystac.CatalogType.SELF_CONTAINED)

    return

# execute main
if __name__ == '__main__':
    main()
