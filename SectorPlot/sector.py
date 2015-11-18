from math import ceil, floor, cos, sin, pi
from qgis.core import QgsFeature, QgsPoint, QgsGeometry, QgsField, QgsFields
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from PyQt4.QtCore import QVariant
from time import strftime, strptime, gmtime
import psycopg2
import psycopg2.extras
import math



def doQueries(queries, conn_string="host='localhost' dbname='gistest' user='postgres' password='postgres'"):
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    for query in queries:
        cursor.execute(query['text'], query['vals'])
    #memory = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    #return memory


def getTime(t):
    result = gmtime()
    if type(t) is unicode or type(t) is str:
        result = strptime(t, "%Y-%m-%d %H:%M:%S") 
    return result


#def 

class Sector():
    def __init__(self, setName=None, lon=0, lat=0, minDistance=0, maxDistance=1.0, direction=0.0, angle=45.0, counterMeasureId=-1, z_order=-1, counterMeasureTime=None, sectorName=None):
        self.setName = setName
        self.lon = lon # longitude in decimal degrees
        self.lat = lat # latitude in decimal degrees
        self.minDistance = minDistance
        self.maxDistance = maxDistance
        self.direction = direction
        self.angle = angle
        self.counterMeasureId = counterMeasureId
        self.z_order = z_order
        self.saveTime = gmtime()
        self.counterMeasureTime = getTime(counterMeasureTime)
        self.sectorName = sectorName
        self.calcGeometry()

    def __str__(self):
        result = 'Sector[%s, (%d,%d), %d, %d, %d, %d, %s]' % (self.setName, self.lon, self.lat, self.minDistance, self.maxDistance, self.direction, self.angle, strftime("%Y-%m-%d %H:%M:%S +0000", self.saveTime))
        return result

    def getQgsFeature(self):
        feat = QgsFeature()
        fields = QgsFields()
        fields.append(QgsField('setName', QVariant.String))
        fields.append(QgsField('counterMeasureId', QVariant.Int))
        fields.append(QgsField('z_order', QVariant.Int))
        fields.append(QgsField('saveTime', QVariant.String))
        fields.append(QgsField('counterMeasureTime', QVariant.String))
        fields.append(QgsField('sectorName', QVariant.String))
        feat.setFields(fields)
        feat['settName'] = self.setName
        feat['counterMeasureId'] = self.counterMeasureId
        feat['z_order'] = self.z_order
        feat['saveTime'] = strftime("%Y-%m-%d %H:%M:%S +0000", self.saveTime)
        feat['counterMeasureTime'] = strftime("%Y-%m-%d %H:%M:%S +0000", self.counterMeasureTime)
        feat['sectorName'] = self.sectorName
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
        if isinstance(arcStart,(int, long)):
            loopStart = arcStart + 1
        else:
            loopStart = int(ceil(arcStart))

        arcEnd = self.direction + (self.angle % 360)
        if isinstance(arcEnd,(int, long)):
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

        # scale distance for Merkator
        scale = 1.0 / (math.cos(float(self.lat) * math.pi / 180.0))
        minR = self.minDistance * scale
        maxR = self.maxDistance * scale
        
        # get x/y in merkator from lon/lat
        crs4326 = QgsCoordinateReferenceSystem(4326)
        crs3857 = QgsCoordinateReferenceSystem(3857)
        xformTo3857 = QgsCoordinateTransform(crs4326, crs3857)
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
            for d in range(0,360):
                outer.append(self._getArcPoint(x, y, maxR, d))
            if minR > 0:
                for d in range(0,360):
                    inner.append(self._getArcPoint(x, y, minR, d))
                #inner.reverse()
                print len(inner)
                geom = QgsGeometry.fromPolygon([outer,inner])
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
            

        xformTo4326 = QgsCoordinateTransform(crs3857, crs4326)
        geom.transform(xformTo4326)
        self.geometry = geom


    def getInsertQuery(self):
        query = {}
        query['text'] = 'INSERT INTO sectors'
        query['text'] += ' (setname, lon, lat, minDistance, maxDistance, direction, angle, countermeasureid, z_order, savetime, countermeasuretime, sectorname, geom)'
        query['text'] += ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::timestamp, %s::timestamp, %s, ST_GeomFromText(%s, 4326))'
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
        vals.append(strftime("%Y-%m-%d %H:%M:%S +0000", self.saveTime))
        vals.append(strftime("%Y-%m-%d %H:%M:%S +0000", self.counterMeasureTime))
        vals.append(self.sectorName)
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
    def __init__(self, lon=0, lat=0):
        self.lon = lon
        self.lat = lat
        #self.roos = Roos()
        self.sectors = []

    def __str__(self):
        result = 'SectorSet[ %s sectors]' % len(self.sectors)
        return result

    def exportToDatabase(self):
        queries = []
        for sector in self.sectors:
            queries.append(sector.getInsertQuery())
        result = doQueries(queries)

    def setSaveTime(self, t=None):
        t = getTime(t)
        for sector in self.sectors:
            sector.saveTime = t

    def setCounterMeasureTime(self, t=None):
        t = getTime(t)
        for sector in self.sectors:
            sector.counterMeasureTime = t

    def setSetName(self, setName=None):
        for sector in self.sectors:
            sector.setName = setName





