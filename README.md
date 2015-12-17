# SectorPlot

QGIS plugin for drawing and managing sector plots.

## Credentials

Create a file `credentials.py` in the `SectorPlot` folder and add the following code with your own connection string(s).

```python
#conn_string_sectorplot = "host='localhost' dbname='sectorplot1' user='user1' password='secret1'"
conn_string_sectorplot = "host='db.somewhere.nl' dbname='sectorplot2' user='user2' password='secret2'"
#conn_string_sectorplot = "host='localhost' dbname='sectorplot3' user='user3' password='secret3'"


gs_conn_sectorplot = {'user': 'admin', 'password': 'geoserver', 'top_level_url': 'HTTP://localhost:8080'}
```
