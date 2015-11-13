from math import ceil, floor, cos, sin, pi
from qgis.core import QgsFeature, QgsPoint, QgsGeometry
from time import strftime, gmtime
import psycopg2
import psycopg2.extras

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


class Sector():
    def __init__(self, x=0, y=0, distance=1.0, direction=0.0, angle=45.0, type="jodium", z_order=0):
        self.x = x
        self.y = y
        self.distance = distance
        self.direction = direction
        self.angle = angle
        self.type = type
        self.z_order = z_order
        self.savetime = gmtime()
        self.geometry = self.getGeometry(self.x, self.y, self.distance, self.direction, self.angle)

    def __str__(self):
        result = 'Sector[(%d,%d), %d, %d]' % (self.x, self.y, self.distance, self.direction)
        return result

    def getQgsFeature(self):
        result = QgsFeature()
        result.setGeometry(self.geometry)
        return result
        

    def getArcPoint(self, x, y, r, direction):
        newdir = direction/180.0*pi
        newx = x + r * sin(newdir)
        newy = y + r * cos(newdir)
        return QgsPoint(newx, newy)

    def getGeometry(self, x, y, distance, direction, angle):

        # TODO: adjust radius to distance in projection
        r = distance
        arc = []

        # make: 0 <= direction < 360
        direction %= 360

        #check if sector is circle
        if angle >= 360:
            for d in range(0,360):
                arc.append(getArcPoint(x, y, r, d))
        else:
            arcStart = direction
            if isinstance(arcStart,( int, long )):
                loopStart = arcStart + 1
            else:
                loopStart = int(ceil(arcStart))

            arcEnd = direction + (angle % 360)
            if isinstance(arcEnd,( int, long )):
                loopEnd = arcEnd - 1
            else:
                loopEnd = int(floor(arcEnd))

            arc.append(QgsPoint(x,y))
            arc.append(self.getArcPoint(x, y, r, arcStart))
            if loopStart <= loopEnd:
                arc.append(self.getArcPoint(x, y, r, loopStart))
                if loopStart < loopEnd:
                    for d in range(loopStart+1, loopEnd+1):
                        arc.append(self.getArcPoint(x, y, r, d))
            arc.append(self.getArcPoint(x, y, r, arcEnd))

        return QgsGeometry.fromPolygon([arc])

    def getInsertQuery(self):
        query = {}
        query['text'] = 'INSERT INTO sectors (geom, x, y, distance, direction, angle, type, z_order, savetime)'
        query['text'] += ' VALUES (ST_GeomFromText(%s, 4326), %s, %s, %s, %s, %s, %s, %s, %s::timestamp)'
        vals = []
        vals.append(self.geometry.exportToWkt())
        vals.append(self.x)
        vals.append(self.y)
        vals.append(self.distance)
        vals.append(self.direction)
        vals.append(self.angle)
        vals.append(self.type)
        vals.append(self.z_order)
        vals.append(strftime("%Y-%m-%d %H:%M:%S +0000", self.savetime))
        query['vals'] = tuple(vals)
        return query



class Roos():
    def __init__(self, x=0, y=0, distances=[1], count=8):
        self.distances = distances
        self.count = count
        self.sectors = []
        if count > 0:
            angle = 360 / count
            for dist in distances:
                direction = 0                
                for i in range(self.count):
                    sec = Sector(x, y, dist, direction, angle)
                    self.sectors.append(sec)
                    direction += angle

    def __str__(self):
        result = 'Roos[%s, %d, %d]' % (str(self.distances), self.count, len(self.sectors))
        return result
        


class SectorPlaat():
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.roos = Roos()
        self.sectors = []

    def __str__(self):
        result = 'SectorPlaat[ %s sectors]' % len(self.sectors)
        return result

    def exportToDatabase(self):
        queries = []
        for sector in self.sectors:
            queries.append(sector.getInsertQuery())
        result = doQueries(queries)




