from geopy import geocoders
from models import CrimeReport
import mapscale



class MvGeocoder(object):

    INVALID_LAT=999
    INVALID_LONG=999

    GOOGLE_MAP_API_KEY='ABQIAAAAkBx_wN2XPPUySvsaWrZmsRQtxdBrUrEVBbmJ9yn4lD0zu_2OpBTZMxcOC1oMEGk4oxZmOtEHsHWKxQ'

    def __init__(self):
        self.geocoder = geocoders.Google(self.GOOGLE_MAP_API_KEY,format_string='%s, Mountain View, CA')

    def geocode(self,address,map_scale):
        """
        given address (string) and map_scale (also string from mapscale.py),
        return string tuplet (latitude, longitude) """

        #
        # normalize
        address=address.lower()

        #
        # reformat address to make it more geocoder friendly
        ################
        if map_scale==mapscale.BLOCK:
            address = address.replace(' block ',' ',1)

        #
        # reformat streetA/streetB as "street A & street B"
        if map_scale==mapscale.INTERSECTION:
            address = address.replace('/',' & ',1)

        #
        # cuernavaca cl. -> circulo
        if address.find('cuernavaca cl.'):
            address = address.replace('cuernavaca cl.','cuernavaca circulo')

        print "final address: " + address

        if map_scale != mapscale.OTHER:
            try:
                place,(lat,long)=self.geocoder.geocode(address)
            except ValueError:
                #
                # geocoder puked
                (lat,long)=(self.INVALID_LAT,self.INVALID_LONG)

        else:
            lat=self.INVALID_LAT
            long=self.INVALID_LONG

        return (str(lat),str(long))




