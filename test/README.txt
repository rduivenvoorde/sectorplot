
https://docs.python.org/3/library/unittest.html#test-discovery

Om de tests te runnen:

In PyCharm:
- rechtermuisknop op mapje 'test' en dan 'Run unittests in test'
- zal falen
- nu in de testconfigurate (rechtsboven dropdown)
"/home/richard/git/sectorplot/test"
aanpassen naar
"/home/richard/git/sectorplot"
Dan werken de relatieve imports in de plugin modules

LET OP: in de tests dus GEEN relatieve imports gebruiken!!
Maar: from SectorPlot.npp import NppSet

EERST LD en paden zetten:
cat `which qgis'

bv:
export LD_LIBRARY_PATH=/home/richard/bin/qgis/master/debug/lib/:/usr/lib/grass76/lib/
export PYTHONPATH=/home/richard/bin/qgis/master/debug/share/qgis/python

python3 -m unittest discover -s /home/richard/git/sectorplot/test -t /home/richard/git/sectorplot

Wat OOK werkt om individuele tests aan te roepen:

python3 -m unittest /home/richard/git/sectorplot/test/test_sectors.py

# of 1 test (-k = testnamepatterns)
python3 -m unittest /home/richard/git/sectorplot/test/test_sectors.py -k test_pie_with_sectorset_id
