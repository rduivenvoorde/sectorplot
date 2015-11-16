from sector import Sector, Roos, SectorSet

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

'''
# add 3 sectors
ss.sectors.append(Sector('', 4, 54, 0, 0.3, 20, 60))
ss.sectors.append(Sector('', 4, 54, 0, 0.5, 40, 25))
ss.sectors.append(Sector('', 4, 54, 0, 0.1, 0, 360))
'''

'''
# fill full circle (roos)
for i in range(12):
  s = Sector('q'+str(i), 5, 52, 0, 20000, (30*i), 30)
  print(s)
  ss.sectors.append(s)
'''


# north/south circles
for i in range(-80, 90, 10):
  s = Sector('lat'+str(i), 35, (i), 0, 500000, (30*i), 360)
  print(s)
  ss.sectors.append(s)




print(ss)
ss.setSavetime()
ss.exportToDatabase()
#print ss.sectors[0]




#layer =  QgsVectorLayer('Polygon', 'poly' , "memory")
#pr = layer.dataProvider()
#poly = getSector(26000, 370000, 8000, 45, 20)
#pr.addFeatures([poly])
#layer.updateExtents()
#QgsMapLayerRegistry.instance().addMapLayers([layer]) 


