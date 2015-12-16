# for running standalone:
from qgis.core import QgsApplication
QgsApplication.setPrefixPath("/usr", True)


from sector import Sector, Roos, SectorSet, SectorSets
import time


doGenerateData = False
doExport = True


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



if doGenerateData:
    # fill full circle (roos 15km)
    ss = SectorSet()
    for i in range(16):
      s = Sector('rose', 5, 53, 0, 15000, (22.5*i), 22.5, sectorName='q'+str(i+1), color='#ff0000')
      ss.sectors.append(s)
    ss.setSaveTime("2015-11-17 12:00:00")
    if doExport:
        ss.exportToDatabase()

    # fill full circle (roos 20km met gat 10km)
    ss = SectorSet()
    for i in range(12):
      s = Sector('rose', 5, 52.7, 10000, 20000, (30*i), 30, sectorName='q'+str(i+1), color='#ff00ff')
      ss.sectors.append(s)
    ss.setSaveTime("2015-11-17 14:00:00")
    if doExport:
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
    ss.sectors.append(Sector('donut', 4.5, 53, 5000, 10000, 0, 360, sectorName='schuilen', color='#00ffff'))
    ss.sectors.append(Sector('circle', 4.5, 52.7, 0, 10000, 0, 360, color='#ffff00'))
    ss.setSaveTime()
    if doExport:
        ss.exportToDatabase()



# test SectorSets

sss = SectorSets()
#print sss
sss.importFromDatabase()
#print sss
#for ss in sss:
#    ss.display()

ss = sss[0]

#ss.sectors[0].display()

#print ss.get_save_time_string()
#print ss.get_counter_measure_time_string()

ss.display()
#ss2 = ss.clone()
#ss2.display

#ss2.name = 'borsele'
#print ss2.getUniqueName()
#ss2.setSetId(1000)
#ss2.createView()

if True:
    # fill full circle (roos 20km met gat 10km)
    ss = SectorSet()
    for i in range(1):
      s = Sector('rose2', 5.3, 52.7, 5000, 15000, (30*i), 30, sectorName='q'+str(i+1), color='#ff00ff')
      ss.sectors.append(s)
    ss.setCounterMeasureTime("2015-12-04 18:00:00")
    ss.name = 'test'
    name = ss.getUniqueName()
    print name
    if doExport:
        ss.exportToDatabase()
    if True:
        name = ss.getUniqueName()
        print name
        ss.publish(name)


#ss.publish(name)


# generate insert query
#s = Sector('Name', 5.5, 52.5, 10000, 20000, 50, 30, sectorName='SectorName', color='#ff00ff')
#print s.getInsertQuery()




#layer =  QgsVectorLayer('Polygon', 'poly' , "memory")
#pr = layer.dataProvider()
#poly = getSector(26000, 370000, 8000, 45, 20)
#pr.addFeatures([poly])
#layer.updateExtents()
#QgsMapLayerRegistry.instance().addMapLayers([layer]) 


