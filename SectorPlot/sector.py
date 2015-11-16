from math import ceil, floor, cos, sin, pi
from qgis.core import QgsFeature, QgsPoint, QgsGeometry, QgsField, QgsFields
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from PyQt4.QtCore import QVariant
from time import strftime, gmtime
import psycopg2
import psycopg2.extras
import math

# for running standalone:
from qgis.core import QgsApplication
QgsApplication.setPrefixPath("/usr", True)

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

#def 

class Sector():
    def __init__(self, name='', lon=0, lat=0, minDistance=0, maxDistance=1.0, direction=0.0, angle=45.0, counterMeasure="jodium", z_order=0, counterMeasureTime=None):
        self.name = name
        self.lon = lon # longitude in decimal degrees
        self.lat = lat # latitude in decimal degrees
        self.minDistance = minDistance
        self.maxDistance = maxDistance
        self.direction = direction
        self.angle = angle
        self.counterMeasure = counterMeasure
        self.z_order = z_order
        self.saveTime = gmtime()
        if counterMeasureTime is None:
            self.counterMeasureTime = gmtime()
        else:
            self.counterMeasureTime = counterMeasureTime
        self.geometry = self.calcGeometry()

    def __str__(self):
        result = 'Sector[%s, (%d,%d), %d, %d, %d, %d, %s]' % (self.name, self.lon, self.lat, self.minDistance, self.maxDistance, self.direction, self.angle, strftime("%Y-%m-%d %H:%M:%S +0000", self.saveTime))
        return result

    def getQgsFeature(self):
        feat = QgsFeature()
        fields = QgsFields()
        fields.append(QgsField('name', QVariant.String))
        fields.append(QgsField('counterMeasure', QVariant.String))
        fields.append(QgsField('z_order', QVariant.Int))
        fields.append(QgsField('saveTime', QVariant.String))
        fields.append(QgsField('counterMeasureTime', QVariant.String))
        feat.setFields(fields)
        feat['name'] = self.name
        feat['counterMeasure'] = self.counterMeasure
        feat['z_order'] = self.z_order
        feat['saveTime'] = strftime("%Y-%m-%d %H:%M:%S +0000", self.saveTime)
        feat['counterMeasureTime'] = strftime("%Y-%m-%d %H:%M:%S +0000", self.counterMeasureTime)
        feat.setGeometry(self.geometry)
        return feat


    def _getArcPoint(self, x, y, r, direction):
        newdir = direction/180.0*pi
        newx = x + r * sin(newdir)
        newy = y + r * cos(newdir)
        return QgsPoint(newx, newy)

    def calcGeometry(self):

        # scale distance for Merkator
        scale = 1.0 / (math.cos(float(self.lat) * math.pi / 180.0))
        minR = self.maxDistance * scale
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

        #check if sector is circle
        if self.angle >= 360:
            for d in range(0,360):
                arc.append(self._getArcPoint(x, y, maxR, d))
        else:
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

            arc.append(QgsPoint(x, y))
            arc.append(self._getArcPoint(x, y, maxR, arcStart))
            if loopStart <= loopEnd:
                arc.append(self._getArcPoint(x, y, maxR, loopStart))
                if loopStart < loopEnd:
                    for d in range(loopStart+1, loopEnd+1):
                        arc.append(self._getArcPoint(x, y, maxR, d))
            arc.append(self._getArcPoint(x, y, maxR, arcEnd))

        xformTo4326 = QgsCoordinateTransform(crs3857, crs4326)
        geom = QgsGeometry.fromPolygon([arc])
        geom.transform(xformTo4326)
        return geom


    def getInsertQuery(self):
        query = {}
        query['text'] = 'INSERT INTO sectors (name, lon, lat, minDistance, maxDistance, direction, angle, countermeasure, z_order, savetime, countermeasuretime, geom)'
        query['text'] += ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::timestamp, %s::timestamp, ST_GeomFromText(%s, 4326))'
        vals = []
        vals.append(self.name)
        vals.append(self.lon)
        vals.append(self.lat)
        vals.append(self.minDistance)
        vals.append(self.maxDistance)
        vals.append(self.direction)
        vals.append(self.angle)
        vals.append(self.counterMeasure)
        vals.append(self.z_order)
        vals.append(strftime("%Y-%m-%d %H:%M:%S +0000", self.saveTime))
        vals.append(strftime("%Y-%m-%d %H:%M:%S +0000", self.counterMeasureTime))
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

    def setSavetime(self, saveTime=None):
        if saveTime is None:
            saveTime = gmtime()
        for sector in self.sectors:
            sector.saveTime = saveTime


