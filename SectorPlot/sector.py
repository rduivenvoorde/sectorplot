from math import ceil, floor, cos, sin, pi
from qgis.core import QgsFeature, QgsPoint, QgsGeometry, QgsField, QgsFields
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from PyQt4.QtCore import QVariant
from time import strftime, strptime, gmtime, struct_time
import time
import math
from connect import Database, RestClient


crs4326 = QgsCoordinateReferenceSystem(4326)
crs3857 = QgsCoordinateReferenceSystem(3857)
xformTo3857 = QgsCoordinateTransform(crs4326, crs3857)
xformTo4326 = QgsCoordinateTransform(crs3857, crs4326)


def getTime(t):
    result = gmtime()
    if type(t) is unicode or type(t) is str:
        result = strptime(t, "%Y-%m-%d %H:%M:%S")
    elif isinstance(t, time.struct_time):
        result = t
    return result


def timeToString(t_struct):
    return strftime("%Y-%m-%d %H:%M:%S +0000", t_struct)


class Sector():
    def __init__(self, setName=None, lon=0, lat=0, minDistance=0,
                 maxDistance=1, direction=0, angle=45, counterMeasureId=-1,
                 z_order=-1, saveTime=None, counterMeasureTime=None,
                 sectorName=None, setId=-1, color='#ffffff'):
        self.setName = setName
        self.lon = float(lon)
        self.lat = float(lat)
        self.minDistance = float(minDistance)
        self.maxDistance = float(maxDistance)
        self.direction = float(direction)
        self.angle = float(angle)
        self.counterMeasureId = int(counterMeasureId)
        self.z_order = int(z_order)
        self.saveTime = getTime(saveTime)
        self.counterMeasureTime = getTime(counterMeasureTime)
        self.sectorName = sectorName
        self.setId = int(setId)
        self.color = color
        self.calcGeometry()

    def __str__(self):
        result = 'Sector[%s, (%d,%d), %d, %d, %d, %d, %d, ,%s]' % (self.setName, self.lon, self.lat, self.minDistance, self.maxDistance, self.direction, self.angle, self.setId, self.sectorName)
        return result

    def display(self, doGeometry=False):
        print('--- Sector ---')
        print('  setName: ' + str(self.setName))
        print('  lon: ' + str(self.lon))
        print('  lat: ' + str(self.lat))
        print('  minDistance: ' + str(self.minDistance))
        print('  maxDistance: ' + str(self.maxDistance))
        print('  direction: ' + str(self.direction))
        print('  angle: ' + str(self.angle))
        print('  counterMeasureId: ' + str(self.counterMeasureId))
        print('  z_order: ' + str(self.z_order))
        print('  saveTime: ' + str(self.saveTime))
        print('  counterMeasureTime: ' + str(self.counterMeasureTime))
        print('  sectorName: ' + str(self.sectorName))
        print('  setId: ' + str(self.setId))
        print('  color: ' + str(self.color))
        if doGeometry:
            print('  geometry: ' + str(self.geometry))
        print('--------------')

    def clone(self):
        return Sector(
            setName=self.setName,
            lon=self.lon,
            lat=self.lat,
            minDistance=self.minDistance,
            maxDistance=self.maxDistance,
            direction=self.direction,
            angle=self.angle,
            counterMeasureId=self.counterMeasureId,
            z_order=self.z_order,
            saveTime=self.saveTime,
            counterMeasureTime=self.counterMeasureTime,
            sectorName=self.sectorName,
            setId=self.setId,
            color=self.color)

    def setByDbRecord(self, rec):
        self.setName = rec.setname
        self.lon = rec.lon
        self.lat = rec.lat
        self.minDistance = rec.mindistance
        self.maxDistance = rec.maxdistance
        self.direction = rec.direction
        self.angle = rec.angle
        self.counterMeasureId = rec.countermeasureid
        self.z_order = rec.z_order
        self.saveTime = rec.savetime.timetuple()
        self.counterMeasureTime = rec.countermeasuretime.timetuple()
        #print self.counterMeasureTime
        self.sectorName = rec.sectorname
        self.setId = rec.setid
        self.color = rec.color
        self.calcGeometry()

    def getQgsFeature(self):
        feat = QgsFeature()
        fields = QgsFields()
        fields.append(QgsField('setName', QVariant.String))
        fields.append(QgsField('counterMeasureId', QVariant.Int))
        fields.append(QgsField('z_order', QVariant.Int))
        fields.append(QgsField('saveTime', QVariant.String))
        fields.append(QgsField('counterMeasureTime', QVariant.String))
        fields.append(QgsField('sectorName', QVariant.String))
        fields.append(QgsField('setId', QVariant.Int))
        fields.append(QgsField('color', QVariant.String))
        feat.setFields(fields)
        feat['setName'] = self.setName
        feat['counterMeasureId'] = self.counterMeasureId
        feat['z_order'] = self.z_order
        feat['saveTime'] = timeToString(self.saveTime)
        feat['counterMeasureTime'] = timeToString(self.counterMeasureTime)
        feat['sectorName'] = self.sectorName
        feat['setId'] = self.setId
        feat['color'] = self.color
        feat.setGeometry(self.geometry)
        return feat

    def _getArcPoint(self, x, y, r, direction):
        newdir = direction/180.0*pi
        newx = x + r * sin(newdir)
        newy = y + r * cos(newdir)
        return QgsPoint(newx, newy)

    def _getArc(self, x, y, dist):
        arc = []
        arcStart = self.direction
        if isinstance(arcStart, (int, long)):
            loopStart = arcStart + 1
        else:
            loopStart = int(ceil(arcStart))

        arcEnd = self.direction + (self.angle % 360)
        if isinstance(arcEnd, (int, long)):
            loopEnd = arcEnd - 1
        else:
            loopEnd = int(floor(arcEnd))

        arc.append(self._getArcPoint(x, y, dist, arcStart))
        if loopStart <= loopEnd:
            arc.append(self._getArcPoint(x, y, dist, loopStart))
            if loopStart < loopEnd:
                for d in range(loopStart+1, loopEnd+1):
                    arc.append(self._getArcPoint(x, y, dist, d))
        arc.append(self._getArcPoint(x, y, dist, arcEnd))
        return arc
    def calcGeometry(self):

        # scale distance for Mercator
        scale = 1.0 / (math.cos(float(self.lat) * math.pi / 180.0))
        minR = self.minDistance * scale
        maxR = self.maxDistance * scale

        # get x/y in Mercator from lon/lat
        pnt = QgsPoint(self.lon, self.lat)
        pnt = xformTo3857.transform(pnt)
        x = pnt.x()
        y = pnt.y()

        arc = []

        # make: 0 <= direction < 360
        self.direction %= 360
        outer = []
        inner = []

        #check if sector is circle
        if self.angle >= 360:
            for d in range(0, 360):
                outer.append(self._getArcPoint(x, y, maxR, d))
            if minR > 0:
                for d in range(0, 360):
                    inner.append(self._getArcPoint(x, y, minR, d))
                #inner.reverse()
                geom = QgsGeometry.fromPolygon([outer, inner])
            else:
                geom = QgsGeometry.fromPolygon([outer])
        else:
            outer = self._getArc(x, y, maxR)
            if minR > 0:
                inner = self._getArc(x, y, minR)
                inner.reverse()
            else:
                inner = [QgsPoint(x, y)]
            geom = QgsGeometry.fromPolygon([outer+inner])

        geom.transform(xformTo4326)
        self.geometry = geom

    def getInsertQuery(self):
        query = {}
        query['text'] = 'INSERT INTO sectors'
        query['text'] += ' (setname, lon, lat, minDistance, maxDistance, direction, angle, countermeasureid, z_order, savetime, countermeasuretime, sectorname, setid, color, geom)'
        query['text'] += ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::timestamp, %s::timestamp, %s, %s, %s, ST_GeomFromText(%s, 4326))'
        query['text'] += ';'
        vals = []
        vals.append(self.setName)
        vals.append(self.lon)
        vals.append(self.lat)
        vals.append(self.minDistance)
        vals.append(self.maxDistance)
        vals.append(self.direction)
        vals.append(self.angle)
        vals.append(self.counterMeasureId)
        vals.append(self.z_order)
        vals.append(timeToString(self.saveTime))
        vals.append(timeToString(self.counterMeasureTime))
        vals.append(self.sectorName)
        vals.append(self.setId)
        vals.append(self.color)
        vals.append(self.geometry.exportToWkt())
        query['vals'] = tuple(vals)
        return query


class Roos():
    def __init__(self, lon=0, lat=0, distances=[1], count=8):
        self.distances = distances
        self.count = count
        self.sectors = []
        if count > 0:
            angle = 360 / count
            for dist in distances:
                direction = 0
                for i in range(self.count):
                    sec = Sector('q'+str(i+1), lon, lat, 0, dist, direction, angle)
                    self.sectors.append(sec)
                    direction += angle

    def __str__(self):
        result = 'Roos[%s, %d, %d]' % (str(self.distances), self.count, len(self.sectors))
        return result


class SectorSet():
    def __init__(self, lon=0, lat=0, name=None, setId=-1):
        self.lon = lon
        self.lat = lat
        self.name = name
        self.setId = setId
        #self.roos = Roos()
        self.sectors = []

    def __str__(self):
        result = 'SectorSet[ %s sectors]' % len(self.sectors)
        return result

    def display(self, doGeometry=False):
        print('--- SectorSet ---')
        print('  lon: ' + str(self.lon))
        print('  lat: ' + str(self.lat))
        print('  name: ' + str(self.name))
        print('  setId: ' + str(self.setId))
        for s in self.sectors:
            print('    ' + str(s))
        print('-----------------')

    def clone(self, clearSetId=True):
        result = SectorSet(
            lon=self.lon,
            lat=self.lat,
            name=self.name,
            setId=self.setId)
        for s in self.sectors:
            result.sectors.append(s.clone())
        if clearSetId:
            result.setSetId(-1)
        return result

    def exportToDatabase(self, newSetId=True):
        db = Database('sectorplot')
        if newSetId:
            queries = [{'text': "SELECT nextval(pg_get_serial_sequence('sectors', 'id')) as newsetid", 'vals': ()}]
            result = db.execute(queries)
            if not result['db_ok']:
                return (False, result['error'])
            setId = result['data'][0].newsetid
            self.setSetId(setId)
        queries = []
        for sector in self.sectors:
            queries.append(sector.getInsertQuery())
        result = db.execute(queries)
        if not result['db_ok']:
            return (False, result['error'])
        else:
            return (True, self.setId)

    def setSaveTime(self, t=None):
        t = getTime(t)
        for sector in self.sectors:
            sector.saveTime = t

    def get_save_time_string(self):
        if len(self.sectors) == 0:
            return ''
        else:
            # all sectors should have the same saveTime!
            return timeToString(self.sectors[0].saveTime)

    def getCounterMeasureTime(self):
        if len(self.sectors) == 0:
            return None
        else:
            # all sectors should have the same counterMeasureTime!
            return self.sectors[0].counterMeasureTime
    
    def get_counter_measure_time_string(self):
        if self.getCounterMeasureTime() is None:
            return timeToString(gmtime())
        else:
            return timeToString(self.getCounterMeasureTime())

    def setCounterMeasureTime(self, t=None):
        t = getTime(t)
        for sector in self.sectors:
            sector.counterMeasureTime = t

    def setSetName(self, setName):
        self.name = setName
        for sector in self.sectors:
            sector.setName = setName

    def setSetId(self, setId):
        self.setId = setId
        for sector in self.sectors:
            sector.setId = setId

    def get_qgs_features(self):
        result = []
        for sector in self.sectors:
            result.append(sector.getQgsFeature())
        return result

    def validate_name(self, name):
        forbidden = ' -=+\/";:' + "'"
        result = ''
        for c in name:
            if c in forbidden:
                result += '_'
            else:
                result += c
        return result

    def getUniqueName(self):
        result = ''
        if self.name is not None:
            result += self.name.lower().replace(' ','_')
        if self.getCounterMeasureTime() is not None:
            result += u'_' + strftime("%Y%m%d_%Hh%M", self.getCounterMeasureTime())
        if self.setId > -1:
            result += '_' + str(self.setId)
        result = self.validate_name(result)
        return result 

    def createView(self, name):
        db = Database('sectorplot')
        q = {}
        q['text'] = 'CREATE OR REPLACE VIEW ' + name + ' AS'
        q['text'] +=  ' SELECT * FROM sectors WHERE setid = %s ORDER BY z_order;'
        q['vals'] = (self.setId,)
        result = db.execute([q])
        return result['db_ok']

    def createWms(self, name):
        # config
        style = 'sectorplot'
        workspace = 'rivm'
        store = 'sectorplot'

        rest = RestClient('sectorplot')
        headers={'Content-Type': 'text/xml'}

        try:
            # create layer
            url = rest.top_level_url + '/geoserver/rest/workspaces/' + workspace + '/datastores/' + store + '/featuretypes'
            data = '<featureType><name>' + name + '</name></featureType>'
            result = rest.doRequest(url=url, data=data, headers=headers)

            # set default style
            url = rest.top_level_url + '/geoserver/rest/layers/' + workspace + ':' + name
            #data = '<layer><defaultStyle><name>' + workspace + ':' + style + '</name></defaultStyle></layer>'
            # currently namespace:style is NOT working
            data = '<layer><defaultStyle><name>' + style + '</name></defaultStyle></layer>'
            result = rest.doRequest(url=url, data=data, headers=headers, method='PUT')

            return True
        except:
            return False

    def publish(self, name):
        result = self.createView(name)
        if result:
            result = self.createWms(name)
            return result
        else:
            return False



class SectorSets(list):

    def __init__(self):
        pass

    def __str__(self):
        result = 'SectorSets[' + str(len(self)) + ']'
        return result

    def _clear(self):
        del self[:]

    def findSectorSet(self, setId):
        for sectorSet in self:
            if sectorSet.setId == setId:
                return sectorSet
        return None

    def addToSectorSet(self, sector):
        sectorSet = self.findSectorSet(sector.setId)
        if sectorSet is not None:
            sectorSet.sectors.append(sector)
        else:
            sectorSet = SectorSet(sector.lon, sector.lat, sector.setName, sector.setId)
            self.append(sectorSet)
            sectorSet.sectors.append(sector)

    def _getImportQuery(self):
        query = {}
        query['text'] = 'SELECT * FROM sectors ORDER BY savetime, z_order'
        #query['text'] = 'SELECT * FROM sectors limit 1'
        query['text'] += ';'
        vals = []
        query['vals'] = tuple(vals)
        return query

    def importFromDatabase(self):
        self._clear()
        q = self._getImportQuery()
        db = Database('sectorplot')
        result = db.execute([q])
        if not result['db_ok']:
            return (False, result['error'])
        db_sectors = result['data']
        for dbs in db_sectors:
            s = Sector()
            s.setByDbRecord(dbs)
            self.addToSectorSet(s)
        return (True, None)
