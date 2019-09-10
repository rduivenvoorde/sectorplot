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

import unittest
from SectorPlot.sector import Sector, Pie

class SectorTest(unittest.TestCase):
    """Test the sector.py module"""

    def test_sector(self):
        """Sector can be initiated"""
        s = Sector()
        print(s)
        self.assertEqual(s.lat, 0)
        self.assertEqual(s.lon, 0)
        #self.assertEqual(str(s), 'Sector[None, (0,0), 0, 1, 0, 45, 2015-11-26 14:40:10 +0000, -1]')

    def test_pie(self):
        """Sector can be initiated"""

        # Borssele
        # "longitude":3.7174,
        # "latitude":51.4312,
        # "numberofzones":3,
        # "zoneradii":[5.0, 10.0, 20.0],
        # "numberofsectors":16,
        # "angle":0.0,

        s1 = Pie()
        self.assertEqual(s1.lat, 0)
        self.assertEqual(s1.lon, 0)

        # lon=0, lat=0, start_angle=0.0, sector_count=8, zone_radii=[5]
        s2 = Pie(lon=10, lat=10, start_angle=10.0, sector_count=8, zone_radii=[5])
        self.assertEqual(s2.lat, 10)
        self.assertEqual(s2.lon, 10)
        self.assertEqual(len(s2.sectors), 8)

        s2 = Pie(lon=10, lat=10, start_angle=10.0, sector_count=16, zone_radii=[5])
        self.assertEqual(s2.lat, 10)
        self.assertEqual(s2.lon, 10)
        self.assertEqual(len(s2.sectors), 16)

        s3 = Pie(lon=10, lat=10, start_angle=10.0, sector_count=4, zone_radii=[5, 10])
        self.assertEqual(s3.lat, 10)
        self.assertEqual(s3.lon, 10)
        self.assertEqual(len(s3.sectors), 8)

        s4 = Pie(lon=10, lat=10, start_angle=10.0, sector_count=1, zone_radii=[0.1])
        self.assertEqual(len(s4.sectors), 1)

        s5 = Pie(lon=10, lat=10, start_angle=10.0, sector_count=0, zone_radii=[5, 10, 20])
        self.assertEqual(len(s5.sectors), 0)

