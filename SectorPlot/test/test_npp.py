from PyQt4.QtCore import QCoreApplication

from providers.npp_provider import NPPConfig, NPPProvider

from test_provider_base import TestProviderBase

from npp import NppSet

import os
import unittest


# inheriting from TestProviderBase because we need a working QgsApplication for the network related stuff
class TestNPP(TestProviderBase):

    def test_npp_file0(self):
        conf = NPPConfig()
        # find dir of this class
        conf.url = 'file://' + os.path.join(os.path.dirname(__file__), '../providers/npp-rest.json')
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
        url = 'file://' + os.path.join(os.path.dirname(__file__), '../providers/npp-rest.json')
        npps = NppSet(url)
        self.assertGreater(len(npps), 0)

    def test_npp_service(self):
        url = 'http://jrodos.dev.cal-net.nl/rest/jrodos/npps'
        npps = NppSet(url)
        self.assertGreater(len(npps), 0)

