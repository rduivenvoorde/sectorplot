from sector import Sector, Roos, SectorPlaat

sec = Sector()
print(sec)
print(sec.getInsertQuery())
print(sec.getQgsFeature())

'''
roos = Roos()
print(roos)
for geom in roos.sectors:
    print(geom)
'''

sp = SectorPlaat()
print(sp)
sp.sectors.append(Sector(0,0,3,195,65))
sp.sectors.append(Sector(0,0,3,195,65))

print(sp)
sp.exportToDatabase()
sp.setSavetime()
print sp.sectors[0]


#layer =  QgsVectorLayer('Polygon', 'poly' , "memory")
#pr = layer.dataProvider()
#poly = getSector(26000, 370000, 8000, 45, 20)
#pr.addFeatures([poly])
#layer.updateExtents()
#QgsMapLayerRegistry.instance().addMapLayers([layer]) 


