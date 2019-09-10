import unittest

from test_provider_base import TestProviderBase

from providers.npp_provider import NPPConfig, NPPProvider

from qgis.PyQt.QtCore import QCoreApplication

from SectorPlot.npp import NppSet

import os
import unittest

class TestNPP(TestProviderBase):

    def test_npp_file0(self):
        conf = NPPConfig()
        # find dir of this class
        conf.url = 'file://' + os.path.join(os.path.dirname(__file__), '../SectorPlot/providers/npp-rest.json')
        prov = NPPProvider(conf)

        def prov_finished(result):
            self.assertIsNotNone(result.data)
            # print(result.data['content'])
            print('{0: <30} {1: <18} {2: <8} {3}'.format('site', 'numberofsectors', 'angle', 'zoneradii', ))
            for npp in result.data['content']:
                print('{0: <30} {1: <18} {2: <8} {3}'.format(npp['site'], npp['numberofsectors'], npp['angle'], npp['zoneradii']))
        prov.finished.connect(prov_finished)
        prov.get_data()
        while not prov.is_finished():
            QCoreApplication.processEvents()

    def test_npp_file(self):
        url = 'file://' + os.path.join(os.path.dirname(__file__), '../SectorPlot/providers/npp-rest.json')
        npps = NppSet(url)
        self.assertGreater(len(npps), 0)

    def test_npp_service(self):
        url = 'http://geoserver.dev.cal-net.nl/rest/jrodos/npps'
        npps = NppSet(url)
        self.assertGreater(len(npps), 0)

if __name__ == '__main__':
    unittest.main()