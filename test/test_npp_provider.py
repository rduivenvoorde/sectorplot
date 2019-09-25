from qgis.PyQt.QtCore import QCoreApplication

import os
import unittest

from test_provider_base import TestProviderBase
from SectorPlot.providers.npp_provider import NPPConfig, NPPProvider


class TestNPPProvider(TestProviderBase):

    # NOTE: will always run, never fail because of provider threads
    def test_npp_file(self):
        conf = NPPConfig()
        # find dir of this class
        conf.url = 'file://' + os.path.join(os.path.dirname(__file__), '../SectorPlot/providers/npp-rest.json')
        prov = NPPProvider(conf)
        def prov_finished(result):
            self.assertIsNotNone(result.data)
            #print(result.data['content'])
            print('{0: <30} {1: <18} {2: <8} {3}'.format('site', 'numberofsectors', 'angle', 'zoneradii', ))
            print('{0: <30} {1: <18} {2: <8} {3}'.format('SITE', 'NUMBEROFSECTORS', 'ANGLE', 'ZONERADII', ))
            print('{0: <30} {1: <18} {2: <8} {3}'.format('----', '---------------', '-----', '---------', ))
            for npp in result.data['content']:
                print('{0: <30} {1: <18} {2: <8} {3}'.format(npp['site'], npp['numberofsectors'], npp['angle'], npp['zoneradii']))
        prov.finished.connect(prov_finished)
        prov.get_data()
        # while not prov.is_finished():
        #     QCoreApplication.processEvents()


    # NOTE: will always run, never fail because of provider threads
    def test_npp_url(self):
        conf = NPPConfig()
        # find dir of this class
        #conf.url = 'http://jrodos.dev.cal-net.nl/rest/jrodos/npps'
        conf.url = 'http://geoserver.dev.cal-net.nl/rest/jrodos/npps'
        prov = NPPProvider(conf)

        def prov_finished(result):
            self.assertIsNotNone(result.data)
            print(result.data['content'])
            print('{0: <30} {1: <18} {2: <8} {3}'.format('site', 'numberofsectors', 'angle', 'zoneradii', ))
            print('{0: <30} {1: <18} {2: <8} {3}'.format('SITE', 'NUMBEROFSECTORS', 'ANGLE', 'ZONERADII', ))
            print('{0: <30} {1: <18} {2: <8} {3}'.format('----', '---------------', '-----', '---------', ))
            for npp in result.data['content']:
                print('{0: <30} {1: <18} {2: <8} {3}'.format(npp['site'], npp['numberofsectors'], npp['angle'],npp['zoneradii']))

        prov.finished.connect(prov_finished)
        prov.get_data()
        while not prov.is_finished():
            QCoreApplication.processEvents()


