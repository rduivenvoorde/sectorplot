# SectorPlot

QGIS plugin for drawing and managing sector plots.

## Credentials

Create a file `credentials.py` and add the following code with your own connection string(s).

```python
conn_strings = {
    'example': "host='localhost' dbname='sectorplot' user='user' password='secret'",
    }
```
Use the right connection string in `sector.py` in the function: 

```python
    def do_queries(queries, conn_string=credentials.conn_strings['example']):
```
