from pystac import STAC_IO
from pystac import Catalog

from urllib.parse import urlparse
import requests

def requests_read_method(uri):
    parsed = urlparse(uri)
    print ( uri )
    if parsed.scheme.startswith('http'):
        return requests.get(uri).text
    else:
        return STAC_IO.default_read_text_method(uri)

STAC_IO.read_text_method = requests_read_method

cat = Catalog.from_file('https://sentinel-stac.s3.amazonaws.com/catalog.json')

while len(cat.get_item_links()) == 0:
    print('Crawling through {}'.format(cat))
    cat = next(cat.get_children())

print(cat.description)
print('Contains {} items.'.format(len(cat.get_item_links())))

item = next(cat.get_items())

for asset_key in item.assets:
    asset = item.assets[asset_key]
    print('{}: {} ({})'.format(asset_key, asset.href, asset.media_type))

