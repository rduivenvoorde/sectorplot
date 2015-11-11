import csv


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
        self['zoneradii'] = [2.5, 5.0, 10.0]  # get array(rec[15]) ???
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
    def __init__(self, fn=None):
        if fn is not None:
            self.setByFile(fn)

    def setByFile(self, fn):
        try:
            infile = open(fn, 'r')
            records = list(csv.reader(infile, delimiter='|'))
            infile.close()
            print len(records)
        except:
            print('cannot read file')
            return
        self.clear()
        for rec in records:
            npp = Npp(rec)
            if True:
                self.append(npp)

    def clear(self):
        while len(self) > 0:
            self.pop()

    def __str__(self):
        result = 'Npps[%s]' % (str(len(self)))
        return result
