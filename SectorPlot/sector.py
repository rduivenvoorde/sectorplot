from math import ceil, floor, cos, sin, pi
from qgis.core import QgsFeature, QgsPoint, QgsGeometry


class Sector():
    def __init__(self, x=0, y=0, distance=1.0, direction=0.0, angle=45.0):
        self.x = x
        self.y = y
        self.distance = distance
        self.direction = direction
        self.angle = angle
        self.geometry = self.getGeometry(self.x, self.y, self.distance, self.direction, self.angle)

    def __str__(self):
        result = 'Sector[(%d,%d), %d, %d]' % (self.x, self.y, self.distance, self.direction)
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

        poly = QgsFeature()
        poly.setGeometry(QgsGeometry.fromPolygon([arc]))
        return poly




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
    

    def __str__():
        result = 'SectorPlaat[]'
        return result






