# sectorplot

Create a file credentials.py and add the following code with your own connection string. Use the right
connection string in the function def do_queries(queries, conn_string=credentials.conn_strings['example'])
in sector.py.


    conn_strings = {
        'example': "host='localhost' dbname='sectorplot' user='user' password='secret'",
        }
    

