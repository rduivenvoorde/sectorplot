# coding=utf-8
"""Tests for module sectors.


.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
__author__ = 'r.nijssen@terglobo.nl'
__date__ = '01/12/2015'
__copyright__ = ('Copyright 2015, Terglobo')

import os
import unittest
from qgis.core import (
    QgsProviderRegistry,
    QgsCoordinateReferenceSystem,
    QgsRasterLayer)
from sector import Sector

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()



class SectorTest(unittest.TestCase):
    """Test the sector.py module"""

    def test_sector(self):
        """Sector can be initiated"""
        s = Sector()
        print s
        self.assertEqual(s.lat, 0)
        self.assertEqual(s.lon, 0)
        #self.assertEqual(str(s), 'Sector[None, (0,0), 0, 1, 0, 45, 2015-11-26 14:40:10 +0000, -1]')

if __name__ == '__main__':
    unittest.main()
