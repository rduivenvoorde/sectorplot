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
from SectorPlot.sector import Sector, Pie, SectorSet

from SectorPlot.sectorplot_settings import SectorPlotSettings
from SectorPlot.qgissettingmanager.setting import Scope, Setting
from SectorPlot.qgissettingmanager.setting_manager import SettingManager
from SectorPlot.qgissettingmanager.types.string import String

class SectorTest(unittest.TestCase):
    """Test the sector.py module"""

    def setUp(self):

        settings = SectorPlotSettings()
        print('Connecting to database "{}" as user "{}"'.format(settings.value('postgis_database'), settings.value('postgis_user')))
        settings.set_value('postgis_password', 'Eso0JLmaRupT')

    def test_sector_simple(self):
        """Sector can be initiated"""
        s = Sector()
        print(s)
        self.assertEqual(s.lat, 0)
        self.assertEqual(s.lon, 0)
        #self.assertEqual(str(s), 'Sector[None, (0,0), 0, 1, 0, 45, 2015-11-26 14:40:10 +0000, -1]')

    def test_sector(self):
        s = Sector(setName='test', lon=5.0, lat=53.0,
                     minDistance=0,
                     maxDistance=5, direction=0, angle=45, counterMeasureId=1,
                     z_order=1, saveTime=None, counterMeasureTime=None,
                     sectorName='testsector', setId=-1, color='#ffffff',
                     npp_block=None, geometry=None)
        print(s)

    def test_sectorset_to_db(self):
        lon = 5.0
        lat = 53.0
        sector = Sector(setName='test', lon=lon, lat=lat,
                     minDistance=0,
                     maxDistance=5, direction=0, angle=45, counterMeasureId=1,
                     z_order=1, saveTime=None, counterMeasureTime=None,
                     sectorName='testsector', setId=-1, color='#ffffff',
                     npp_block=None, geometry=None)
        sectorset = SectorSet(lon=lon, lat=lat, name='testset', npp_block=None, setId=-1)
        sectorset.sectors.append(sector)
        result = sectorset.exportToDatabase()
        self.assertTrue(result[0])
        print(result[1])

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

    def test_pie_with_sectorset_id(self):
        SECTORSET_ID = 33
        s5 = Pie(lon=10, lat=10, start_angle=10.0, sector_count=4,
                 zone_radii=[5, 10, 20], sectorset_id=SECTORSET_ID)
        self.assertEqual(len(s5.sectors), 12)
        self.assertEqual(s5.sectorset_id, SECTORSET_ID)
        print(s5)
        #print(s5.getInsertQuery())

    def test_pie_to_db(self):
        SECTORSET_ID = 33
        s5 = Pie(lon=10, lat=10, start_angle=10.0, sector_count=4,
                 zone_radii=[5, 10, 20], sectorset_id=SECTORSET_ID)
        self.assertEqual(len(s5.sectors), 12)
        self.assertEqual(s5.sectorset_id, SECTORSET_ID)
        #print(s5)
        #print(s5.getInsertQuery())
        result = s5.exportToDatabase()
        self.assertTrue(result[0])
        self.assertEqual(result[1], SECTORSET_ID)

    def test_pie_from_db(self):
        SECTORSET_ID = 127  # single record
        #SECTORSET_ID = 33   # 2 records...
        s = Pie()
        result = s.importFromDatabase(SECTORSET_ID)
        #print(s)
        self.assertTrue(result[0])

        self.assertTrue(len(s.sectors), 1)

        print('111')
        print(len(s.get_features()))  # should return multiple Features with SimplePolygon as geom

        print('222')
        print(s.get_features(True))  # should return 1 Feature with a MultiPolygon