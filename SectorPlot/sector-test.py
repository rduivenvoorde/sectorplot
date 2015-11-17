from sector import Sector, Roos, SectorSet
import time


'''
sec = Sector()
print(sec)
print(sec.getInsertQuery())
print(sec.getQgsFeature())
'''


'''
roos = Roos()
print(roos)
for geom in roos.sectors:
    print(geom)
'''

ss = SectorSet()
print(ss)
ss.setSaveTime()
ss.setSaveTime("1973-10-14 07:05:03")
#ss.exportToDatabase()
#print ss.sectors[0]



'''
# add 3 sectors
ss.sectors.append(Sector('', 4, 54, 0, 0.3, 20, 60))
ss.sectors.append(Sector('', 4, 54, 0, 0.5, 40, 25))
ss.sectors.append(Sector('', 4, 54, 0, 0.1, 0, 360))
'''

# fill full circle (roos 15km)
ss = SectorSet()
for i in range(12):
  s = Sector('q'+str(i+1), 5, 53, 0, 15000, (30*i), 30)
  ss.sectors.append(s)
ss.setSaveTime("2015-11-17 12:00:00")
ss.exportToDatabase()

# fill full circle (roos 20km met gat 10km)
ss = SectorSet()
for i in range(12):
  s = Sector('q'+str(i+1), 5, 52.7, 10000, 20000, (30*i), 30)
  ss.sectors.append(s)
ss.setSaveTime("2015-11-17 14:00:00")
ss.exportToDatabase()



'''
# north/south circles
for i in range(-80, 90, 10):
  s = Sector('lat'+str(i), 45, (i), 0, 500000, (30*i), 360)
  print(s)
  ss.sectors.append(s)

ss.setSaveTime()

print(ss.sectors[0].saveTime)
'''

ss = SectorSet()
ss.sectors.append(Sector('donut', 4.5, 53, 5000, 10000, 0, 360))
ss.sectors.append(Sector('circle', 4.5, 52.7, 0, 10000, 0, 360))
ss.setSaveTime()
ss.exportToDatabase()








#layer =  QgsVectorLayer('Polygon', 'poly' , "memory")
#pr = layer.dataProvider()
#poly = getSector(26000, 370000, 8000, 45, 20)
#pr.addFeatures([poly])
#layer.updateExtents()
#QgsMapLayerRegistry.instance().addMapLayers([layer]) 


