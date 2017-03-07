from qgissettingmanager import *

# Working with: https://github.com/3nids/qgissettingmanager
# learning from: https://github.com/3nids/wincan2qgep
# https://github.com/3nids/quickfinder

# KNMI services:

class SectorPlotSettings(SettingManager):

    def __init__(self):

        plugin_name = 'SectorPlot'

        SettingManager.__init__(self, plugin_name)

        # Postgis connection details
        #
        # to test: "select * from postgis_version()"
        # "1.5 USE_GEOS=1 USE_PROJ=1 USE_STATS=1"
        #
        # conn_string_sectorplot = "host='db02.dev.cal-net.nl' dbname='sectorplot' user='sectorplot' password=''"
        self.add_setting(String('postgis_host', Scope.Global, 'db02.dev.cal-net.nl'))
        self.add_setting(String('postgis_database', Scope.Global, 'sectorplot'))
        self.add_setting(String('postgis_user', Scope.Global, 'sectorplot'))
        self.add_setting(String('postgis_password', Scope.Global, ''))

        # Geoserver REST connection details
        #
        # to test: http://geoserver.dev.cal-net.nl/geoserver/rest/workspaces.json
        #
        # gs_conn_sectorplot = {'user': 'admin', 'password': '', 'top_level_url': 'http://geoserver.dev.cal-net.nl'}
        self.add_setting(String('geoserver_url', Scope.Global, 'http://geoserver.dev.cal-net.nl'))
        self.add_setting(String('geoserver_user', Scope.Global, 'admin'))
        self.add_setting(String('geoserver_password', Scope.Global, ''))

        # JRodos REST server connection details (NPP's)
        #
        # to test: http://jrodos.dev.cal-net.nl:8080/jrodos-rest-service/jrodos
        #          http://jrodos.dev.cal-net.nl/rest-1.0-TEST-1/jrodos/npps
        #
        self.add_setting(
            #String('jrodos_rest_url', Scope.Global,
            #        'http://jrodos.dev.cal-net.nl:8080/jrodos-rest-service/jrodos'))
            # TODO: set this to service url:
            # OLD: http://jrodos.dev.cal-net.nl:8080/jrodos-rest-service/jrodos
            # new: http://jrodos.dev.cal-net.nl/rest/jrodos/npps
            String('jrodos_rest_url', Scope.Global, 'http://jrodos.dev.cal-net.nl/rest-1.0-TEST-1/jrodos/npps'))

