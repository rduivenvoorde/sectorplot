import psycopg2
import psycopg2.extras
import urllib
import json

from .sectorplot_settings import SectorPlotSettings


class Database:
    def __init__(self, conn_code):
        self.settings = SectorPlotSettings()
        self.conn_string = self.get_conn_string(conn_code)
        self.db_ok = False
        self.error = ''

    def __str__(self):
        return 'Database[' + self.conn_string + ']'

    def connect(self):
        try:
            self.connection = psycopg2.connect(self.conn_string)
            self.db_ok = True
        except psycopg2.Error as e:
            self.db_ok = False
            self.error = e
            #return self.connection

    def disconnect(self):
        self.connection.close()

    def get_conn_string(self, code):
        if code == 'jrodos':
            # TODO (when actually used, to get the npp data from the database)
            # conn_string_rodoshome = "host='jrodos.dev.cal-net.nl' dbname='RodosHome' user='sectorplot' password='xxx'"
            return "host='jrodos.dev.cal-net.nl' dbname='RodosHome' user='sectorplot' password='xxx'"

        if code == 'sectorplot':
            # conn_string_sectorplot = "host='db02.dev.cal-net.nl' dbname='sectorplot' user='sectorplot' password='xxx'"
            host = self.settings.value('postgis_host')
            database = self.settings.value('postgis_database')
            user = self.settings.value('postgis_user')
            password = self.settings.value('postgis_password')
            return "host='{}' dbname='{}' user='{}' password='{}' connect_timeout=3".format(host, database, user, password)

    def execute(self, queries):
        self.connect()
        if not self.db_ok:
            return {'db_ok':self.db_ok , 'error': self.error}
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        for query in queries:
            cursor.execute(query['text'], query['vals'])
        #print(cursor.statusmessage)
        #print(cursor.rowcount)
        if 'SELECT' in str(cursor.statusmessage):
            memory = cursor.fetchall()
        else:
            memory = None
        self.connection.commit()
        cursor.close()
        self.disconnect()
        if memory is None:
            return {'db_ok': self.db_ok}
        else:
            return {'db_ok': self.db_ok, 'data': memory}

    def test_connection(self, host, database, user, password):
        """
        To test: "select * from postgis_version()"
        Should return something like: "1.5 USE_GEOS=1 USE_PROJ=1 USE_STATS=1"

        :return: Simple True if OK, False if SOME error
        """
        self.conn_string = "host='{}' dbname='{}' user='{}' password='{}'".format(host, database, user, password)
        self.db_ok = False
        self.error = ''
        result = self.execute([{'text': 'select * from postgis_version()', 'vals': ()}])
        #print result
        return result['db_ok']

class RestClient:
    def __init__(self, conn_code):
        self.settings = SectorPlotSettings()
        gs_conn = self.get_conn(conn_code)
        self.user = gs_conn['user']
        self.password = gs_conn['password']
        self.top_level_url = gs_conn['top_level_url']
        self.create_opener()

    def create_opener(self):
        password_mgr = urllib.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.top_level_url, self.user, self.password)
        handler = urllib.HTTPBasicAuthHandler(password_mgr)
        self.opener = urllib.build_opener(handler)

    def __str__(self):
        return 'RestClient[' + self.top_level_url + ']'

    def get_conn(self, code):
        if code == 'sectorplot':
            url = self.settings.value('geoserver_url')
            user = self.settings.value('geoserver_user')
            password = self.settings.value('geoserver_password')
            # gs_conn_sectorplot = {'user': 'admin', 'password': 'xxx', 'top_level_url': 'http://geoserver.dev.cal-net.nl'}
            return {'user': user, 'password': password, 'top_level_url': url}

    def doRequest(self, url, data=None, headers=None, method='POST'):
        #print 'url:    ', url
        #print 'data:   ', data
        #print 'headers:', headers
        req = urllib.Request(url=url, data=data, headers=headers)
        req.get_method = lambda: method
        f = self.opener.open(req)
        #print f.read()
        return f.read()

    def test_connection(self, url, user, password):
        """
        To test: http://geoserver.dev.cal-net.nl/geoserver/rest/workspaces.json
        Should return something like: {"workspaces":{"workspace":[{"name":"radiation.measurements","href":"http:\/\/geoserver.dev.cal-net.nl\/geoserver\/rest\/workspaces\/radiation.measurements.json"},{"name":"rivm","href":"http:\/\/geoserver.dev.cal-net.nl\/geoserver\/rest\/workspaces\/rivm.json"},{"name":"sectorplots","href":"http:\/\/geoserver.dev.cal-net.nl\/geoserver\/rest\/workspaces\/sectorplots.json"}]}}

        :return: True  if OK, False if SOME error
        """
        self.top_level_url = url
        self.user = user
        self.password = password
        self.create_opener()
        try:
            result = json.loads(self.doRequest(self.top_level_url+'/geoserver/rest/workspaces.json', None, {'Content-Type': 'application/json'}, 'GET'))
            if 'workspaces' in result:
                return True
        except:
            # import sys
            # print("Unexpected error:", sys.exc_info()[0])
            pass
        return False


if __name__ == "__main__":
    # db = Database('sectorplot')
    # #db = Database('jrodos')
    # q = {}
    # q['text'] = 'SELECT 0 as "col1"'
    # q['vals'] = ()
    #
    # r = db.execute([q])
    # if r['db_ok']:
    #     print(r['data'][0].col1)
    # else:
    #     print(r['error'])

    db = Database('sectorplot')
    print(db.test_connection('db03.dev.cal-net.nl', 'sectorplot', 'sectorplot', ''))

    rc = RestClient('sectorplot')
    print(rc.test_connection('http://geoserver.dev.cal-net.nl', 'admin', ''))




