from sector import Sector, Roos

sec = Sector()
print(sec)


roos = Roos()
print(roos)

for geom in roos.sectors:
    print(geom)


#layer =  QgsVectorLayer('Polygon', 'poly' , "memory")
#pr = layer.dataProvider()
#poly = getSector(26000, 370000, 8000, 45, 20)
#pr.addFeatures([poly])
#layer.updateExtents()
#QgsMapLayerRegistry.instance().addMapLayers([layer]) 


