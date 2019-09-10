from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox

import os

from .providers.npp_provider import NPPConfig, NPPProvider

class Npp(dict):
    def __init__(self, rec=None):
        self.ok = False
        if rec is not None:
            self.setByRec(rec)

    def setByRec(self, rec):
        if len(rec) < 18:
            return
        self['block'] = rec[0].strip()
        self['site'] = rec[1].strip()
        self['longitude'] = float(rec[2].strip())
        self['latitude'] = float(rec[3].strip())
        self['inventory'] = rec[4].strip()
        self['stackheight'] = float(rec[5].strip())
        self['thermalpower'] = float(rec[6].strip())
        self['operationtime'] = int(rec[7].strip())
        self['blocktype'] = rec[8].strip()
        self['buildingwidth'] = float(rec[9].strip())
        self['buildingheight'] = float(rec[10].strip())
        self['volumeflux'] = float(rec[11].strip())
        self['ventopening'] = float(rec[12].strip())
        self['countrycode'] = rec[13].strip()
        self['numberofzones'] = int(rec[14].strip())
        self['zoneradii'] = [2.5, 5.0, 10.0]  # get array(rec[15]) ??? TODO
        self['numberofsectors'] = int(rec[16].strip())
        self['starangle'] = float(rec[17].strip())
        #self['closetoborder'] = rec[18] == 'True'  # ???
        self.ok = True

    def __str__(self):
        result = ''
        for key in self:
            result += '[%s]: %s\n' % (key, self[key])
        return result


class NppSet(list):
    def __init__(self, url):

        # fill the nuclear power plant list
        conf = NPPConfig()

        # try remote version first
        conf.url = url
        prov = NPPProvider(conf)
        prov.finished.connect(self.prov_finished)
        prov.get_data()
        while not prov.is_finished():
            QCoreApplication.processEvents()

        if len(self) == 0:
            # fetch the local copy if available
            QMessageBox.warning(None, "", "Error retrieving Remote NPP's via REST, trying to find local file with NPP's", QMessageBox.Ok, QMessageBox.Ok)
            conf.url = 'file://' + os.path.dirname(__file__) + os.path.sep + os.path.join('providers', 'npp-rest.json')
            prov = NPPProvider(conf)
            prov.finished.connect(self.prov_finished)
            prov.get_data()
            while not prov.is_finished():
                QCoreApplication.processEvents()

    def prov_finished(self, result):
        if result.error():
            # TODO ? log the error message?

            return
        for npp_data in result.data['content']:
            npp = Npp()
            npp['block'] = npp_data['block']
            npp['site'] = npp_data['site']
            npp['longitude'] = float(npp_data['longitude'])
            npp['latitude'] = float(npp_data['latitude'])
            npp['inventory'] = npp_data['inventory']
            npp['stackheight'] = float(npp_data['stackheight'])
            npp['thermalpower'] = float(npp_data['thermalpower'])
            npp['operationtime'] = int(npp_data['operationtime'])
            npp['blocktype'] = npp_data['blocktype']
            npp['buildingwidth'] = float(npp_data['buildingwidth'])
            npp['buildingheight'] = float(npp_data['buildingheight'])
            npp['volumeflux'] = float(npp_data['volumeflux'])
            npp['ventopening'] = float(npp_data['ventopening'])
            npp['countrycode'] = npp_data['countrycode']
            npp['numberofzones'] = int(npp_data['numberofzones'])
            npp['zoneradii'] = npp_data['zoneradii']
            npp['numberofsectors'] = int(npp_data['numberofsectors'])
            npp['angle'] = float(npp_data['angle'])
            npp['closetoborder'] = npp_data['closetoborder']
            #print(npp)
            self.append(npp)

    def __str__(self):
        result = '[%s] NPPs' % (str(len(self)))
        return result

