# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SectorPlot
                                 A QGIS plugin
 Plots sector areas s on risk management map
                              -------------------
        begin                : 2015-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2015 by RIVM
        email                : marnix.de.ridder@rivm.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QSortFilterProxyModel, QStandardItemModel, \
    QAbstractItemView, QStandardItem, QAbstractItemView
from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint, \
    QgsRectangle, QgsCoordinateTransform, QgsVectorLayer, QgsMapLayerRegistry, QgsFeature
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialogs
from sectorplot_dialog import SectorPlotDialog
from sectorplot_location_dialog import SectorPlotLocationDialog
from sectorplot_sector_dialog import SectorPlotSectorDialog
from sectorplot_sectorplotset_dialog import SectorPlotSectorPlotSetDialog

from countermeasures import CounterMeasures

from npp import NppSet
from sector import Sector, SectorSet, SectorSets

import os.path


class SectorPlot:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SectorPlot_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.sectorplotlist_dlg = SectorPlotDialog()
        self.sectorplotlist_dlg.table_sectorplot_sets.horizontalHeader().setStretchLastSection(True)
        self.sectorplotlist_dlg.table_sectorplot_sets.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sectorplot_list = None
        self.sectorplotlist_source_model = None
        # dlg actions
        self.sectorplotlist_dlg.btn_new_sectorplot_dialog.clicked.connect(self.open_location_dialog)

        # Create location_dialog
        self.location_dlg = SectorPlotLocationDialog()
        self.npp_source_model = None
        self.npp_proxy_model = None
        # actions
        #self.location_dlg.le_longitude.textChanged.connect(self.zoom_to)
        #self.location_dlg.le_latitude.textChanged.connect(self.zoom_to)

        # Create sector_dialog
        self.sector_dlg = SectorPlotSectorDialog()
        # the data for the combo_countermeasures
        self.counter_measures = CounterMeasures()
        # actions

        # Create sectorplotset_dialog
        self.sectorplotset_dlg = SectorPlotSectorPlotSetDialog()
        self.sectorplotset_source_model = QStandardItemModel()
        self.sectorplotset_dlg.table_sectors.setModel(self.sectorplotset_source_model)
        # actions
        self.sectorplotset_dlg.btn_new_sector.clicked.connect(self.open_new_sector_dialog)
        self.sectorplotset_dlg.btn_remove_selected_sectors.clicked.connect(self.remove_selected_sectors)

        # add memory Layer
        self.sector_layer = None
        self.crs_4326 = QgsCoordinateReferenceSystem()
        self.crs_4326.createFromId(4326)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SectorPlot')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SectorPlot')
        self.toolbar.setObjectName(u'SectorPlot')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SectorPlot', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SectorPlot/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Sector plot'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SectorPlot'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Start the plugin"""
        # add a memory layer to show sectors if not yet available
        if self.sector_layer is None:
            # give the memory layer the same CRS as the source layer
            #self.sector_layer = QgsVectorLayer("Polygon?crs=epsg:4326&field=cm:string(200)&field=cmid:integer&index=yes", self.tr("Sector Layer"), "memory")
            self.sector_layer = QgsVectorLayer("Polygon?crs=epsg:4326&index=yes", self.tr("Sector Layer"), "memory")
            # use a saved style as style
            # TODO new qml based on color column
            # self.sector_layer.loadNamedStyle(os.path.join(os.path.dirname(__file__), 'sectors.qml'))
            # add empty layer to the map
            QgsMapLayerRegistry.instance().addMapLayer(self.sector_layer)
        # open a new dialog
        self.open_sectorplotlist_dialog()

    def open_sectorplotlist_dialog(self):
        # show the dialog with recent sectorplotsets
        self.sectorplot_list = SectorSets()
        self.sectorplot_list.importFromDatabase()
        # create emtpy model for new list
        self.sectorplotlist_source_model = QStandardItemModel()
        self.sectorplotlist_dlg.table_sectorplot_sets.setModel(self.sectorplotlist_source_model)
        for sectorplot_set in self.sectorplot_list:
            lon = sectorplot_set.lon
            lat = sectorplot_set.lat
            name = QStandardItem("%s" % sectorplot_set.name )
            set_id = QStandardItem("%s" % sectorplot_set.setId )
            time = QStandardItem(sectorplot_set.getSaveTimeString())
            # attach the sectorplot_set as data to the first row item
            set_id.setData(sectorplot_set, Qt.UserRole)
            self.sectorplotlist_source_model.appendRow([set_id, name, time])
        # headers
        self.sectorplotlist_source_model.setHeaderData(0, Qt.Horizontal, self.tr("Id"))
        self.sectorplotlist_source_model.setHeaderData(1, Qt.Horizontal, self.tr("Name"))
        self.sectorplotlist_source_model.setHeaderData(2, Qt.Horizontal, self.tr("Time"))
        self.sectorplotlist_dlg.table_sectorplot_sets.selectionModel().selectionChanged.connect(self.select_sectorplot_set)

        self.sectorplotlist_dlg.show()
        # See if OK was pressed
        if self.sectorplotlist_dlg.exec_():
            print "Cleaning up with OK"
            self.sectorplotlist_source_model = None
            self.sectorplot_list = None
        else:
            print "Cleaning up with Cancel"
            self.sectorplotlist_source_model = None
            self.sectorplot_list = None

    def select_sectorplot_set(self):
        if len(self.sectorplotlist_dlg.table_sectorplot_sets.selectedIndexes())>0:
            sectorplot_set = self.sectorplotlist_dlg.table_sectorplot_sets.selectedIndexes()[0].data(Qt.UserRole)
            # zoom to and show
            self.zoom_to(sectorplot_set.lon, sectorplot_set.lat)
            print sectorplot_set.getSectorFeatures()
            self.add_sector_features(sectorplot_set.getSectorFeatures())

    def open_location_dialog(self):
        # fill the nuclear power plant list
        npp_source = os.path.join(os.path.dirname(__file__), r'data/tabel-npp-export.txt')
        npps = NppSet(npp_source)
        self.npp_proxy_model = QSortFilterProxyModel()
        self.npp_source_model = QStandardItemModel()
        self.npp_proxy_model.setSourceModel(self.npp_source_model)
        # setFilterKeyColumn = search in the data in column
        self.npp_proxy_model.setFilterKeyColumn(0)
        self.location_dlg.table_npps.setModel(self.npp_proxy_model)
        self.location_dlg.table_npps.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.location_dlg.le_search_npp.textChanged.connect(self.filter_npps)
        self.location_dlg.le_search_npp.setPlaceholderText(self.tr("Search"))
        if (len(npps)):
            # load the npps in the table in dialog
            for npp in npps:
                # prepare a commaseparated string to search in from the values of the npp dict
                vals = ""
                for val in npp.values():
                    vals += ", %s" % unicode(val)
                # you can attache different "data's" to to an QStandarditem
                # default one is the visible one:
                data = QStandardItem(vals)
                # userrole is a free form one:
                # attach the data/npp to the first visible(!) column
                # when clicked you can get the npp from the data of that column
                country_code = QStandardItem("%s" % (npp["countrycode"].upper()) )
                country_code.setData(npp, Qt.UserRole)
                site = QStandardItem("%s" % (npp["site"].upper()) )
                block = QStandardItem("%s" % (npp["block"].upper()) )
                self.npp_source_model.appendRow ( [data, country_code, site, block] )
        # headers
        self.npp_source_model.setHeaderData(1, Qt.Horizontal, self.tr("Countrycode"))
        self.npp_source_model.setHeaderData(2, Qt.Horizontal, self.tr("Site"))
        self.npp_source_model.setHeaderData(3, Qt.Horizontal, self.tr("Block"))
        self.location_dlg.table_npps.horizontalHeader().setStretchLastSection(True)
        self.location_dlg.table_npps.setSelectionBehavior(QAbstractItemView.SelectRows)
        # hide the data / search string column:
        self.location_dlg.table_npps.hideColumn(0)
        # handle the selection of a NPP
        self.location_dlg.table_npps.selectionModel().selectionChanged.connect(self.select_npp)
        # show the dialog
        self.location_dlg.show()
        # See if OK was pressed
        if self.location_dlg.exec_():
            # show the sectorplotset dialog
            lon = self.location_dlg.le_longitude.text()
            lat = self.location_dlg.le_latitude.text()
            self.current_sectorset = SectorSet(lon, lat)
            self.open_sectorplotset_dialog(lon, lat)

    def open_sectorplotset_dialog(self, lon, lat):
        self.sectorplotset_dlg.lbl_location_name_lon_lat.setText(self.tr('Lon: ') + lon + self.tr(' Lat: ') + lat)
        self.sectorplotset_dlg.show()
        # OK will save to db
        if self.sectorplotset_dlg.exec_():
            # NOW get the sectors from the model/dialog, put them in a sectorset
            # data=sector is attached to column 0
            for row in range(0, self.sectorplotset_source_model.rowCount()):
                sector = self.sectorplotset_source_model.item(row, 0).data(Qt.UserRole)
                print sector
                self.current_sectorset.sectors.append(sector)
            # save to DB
            self.current_sectorset.exportToDatabase()

    def filter_npps(self, string):
        # remove selection if we start filtering AND empty lon lat fields
        self.location_dlg.table_npps.clearSelection()
        self.location_dlg.le_longitude.setText('')
        self.location_dlg.le_latitude.setText('')
        self.npp_proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.npp_proxy_model.setFilterFixedString(string)

    def select_npp(self):
        # needed to scroll To the selected row incase of using the keyboard / arrows
        #self.location_dlg.table_npps.scrollTo(self.location_dlg.table_npps.selectedIndexes()[0])
        # itemType holds the data (== column 1)
        if len(self.location_dlg.table_npps.selectedIndexes())>0:
            npp = self.location_dlg.table_npps.selectedIndexes()[0].data(Qt.UserRole)
            self.location_dlg.le_longitude.setText(unicode(npp['longitude']))
            self.location_dlg.le_latitude.setText(unicode(npp['latitude']))
            self.zoom_to(npp['longitude'], npp['latitude'])

    def zoom_to(self, lon, lat):
#        if lon is None or lat is None:
#            # we get them from the inputs of the dialog
#           lon = self.location_dlg.le_longitude.text()
#            lat = self.latitude_dlg.le_longitude.text()
        crs_to = self.iface.mapCanvas().mapRenderer().destinationCrs()
        crs_transform = QgsCoordinateTransform(self.crs_4326, crs_to)
        point = QgsPoint(float(lon), float(lat))
        geom = QgsGeometry.fromPoint(point)
        geom.transform(crs_transform)
        # zoom to with center is actually setting a point rectangle and then zoom
        center = geom.asPoint()
        rect = QgsRectangle(center, center)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().zoomScale(300000)
        self.iface.mapCanvas().refresh()

    def open_new_sector_dialog(self):
        # TODO !!! nu even alleen om te tonen, maar de id/key moet hier ook bij komen!!
        self.sector_dlg.combo_countermeasures.addItems(self.counter_measures.values())
        self.sector_dlg.show()
        # OK pressed
        if self.sector_dlg.exec_():

            self.add_sector(100, '0', '45', '10', '0', 'test1')
            self.add_sector(120, '45', '45', '12', '0', 'test2')
            self.add_sector(130, '90', '45', '13', '0', 'test3')
            self.add_sector(140, '135', '45', '15', '0', 'test4')
            self.add_sector(220, '180', '45', '10', '3', 'test5')
            self.add_sector(400, '245', '65', '16', '5', 'test6')
            #self.add_sector()
        else:
            # user canceled
            # TODO clean up generated sectors
            pass

    # def add_sector(self):
    def add_sector(self, countermeasure=-1, direction='0', angle='10', distance='10', min_distance='0', sector_name=''):
        # get values from dialog
        # TODO: only for testing
        if (countermeasure<0):
            # TODO countermeasure should be number from dropdown
            countermeasure = 100
            direction = self.sector_dlg.le_direction.text()
            angle = self.sector_dlg.le_angle.text()
            distance = self.sector_dlg.le_distance.text()
            min_distance = self.sector_dlg.le_min_distance.text()
            sector_name = self.sector_dlg.le_sector_name.text()

        # new sector

        sector = Sector(lon=self.current_sectorset.lon,
                        lat=self.current_sectorset.lat,
                        minDistance=1000*float(min_distance), 
                        maxDistance=1000*float(distance), 
                        direction=direction,
                        angle=angle,
                        counterMeasureId=countermeasure,
                        sectorName=sector_name)

        # self.current_sectorset.sectors.append(sector)

        sector_name_item = QStandardItem(sector_name)
        direction_item = QStandardItem(direction)
        min_distance_item = QStandardItem(min_distance)
        distance_item = QStandardItem(distance)
        angle_item = QStandardItem(angle)
        countermeasure_item = QStandardItem(self.counter_measures.get(countermeasure))
        # attach the sector(data) as data to column 0
        sector_name_item.setData(sector, Qt.UserRole)

        self.sectorplotset_source_model.appendRow([sector_name_item, countermeasure_item, min_distance_item,
                                                   distance_item, direction_item, angle_item])

        # TODO: use the sector.getQgsFeature()
        # http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/vector.html#add-features
        #feat = QgsFeature(self.sector_layer.pendingFields())
        #feat.setAttributes([0, 'hello'])
        # Or set a single attribute by key or by index:
        #feat.setAttribute('cm', self.counter_measures.get(countermeasure))
        #feat.setAttribute('cmid', int(countermeasure))
        feat = QgsFeature()
        feat.setAttributes([self.counter_measures.get(countermeasure), int(countermeasure)])
        feat.setGeometry(sector.geometry)

        self.add_sector_features([feat])

        # TODO only once?
        self.sectorplotset_source_model.setHeaderData(0, Qt.Horizontal, self.tr("Sector name"))
        self.sectorplotset_source_model.setHeaderData(1, Qt.Horizontal, self.tr("Countermeasure"))
        self.sectorplotset_source_model.setHeaderData(2, Qt.Horizontal, self.tr("MinDist"))
        self.sectorplotset_source_model.setHeaderData(3, Qt.Horizontal, self.tr("Distance"))
        self.sectorplotset_source_model.setHeaderData(4, Qt.Horizontal, self.tr("Direction"))
        self.sectorplotset_source_model.setHeaderData(5, Qt.Horizontal, self.tr("Angle"))
        # some size for sectorname and countermeasure
        self.sectorplotset_dlg.table_sectors.setColumnWidth(0, 150)
        self.sectorplotset_dlg.table_sectors.setColumnWidth(1, 250)
        # make sure we select a full row when clicked on a cell
        self.sectorplotset_dlg.table_sectors.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setStretchLastSection(True)
        # user is able to drag/drop both columns and rows
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setMovable(True)
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setDragEnabled(True)
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setMovable(True)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setDragEnabled(True)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)

    def add_sector_features(self, features_list=[], remove_all=False):
        #if remove_all:
        #    self.sector_layer.dataProvider().deleteFeatures(self.sector_layer.allFeatureIds())
        #(result, out_feats) = self.sector_layer.dataProvider().addFeatures([feat])
        self.sector_layer.dataProvider().addFeatures(features_list)
        self.sector_layer.updateFields()
        self.sector_layer.updateExtents()
        if self.iface.mapCanvas().isCachingEnabled():
            self.sector_layer.setCacheImage(None)
        else:
            self.iface.mapCanvas().refresh()

    def remove_selected_sectors(self):
        if len(self.sectorplotset_dlg.table_sectors.selectedIndexes()) > 0:
            # TODO make then we can only select one row at a time
            self.sectorplotset_source_model.removeRow(self.sectorplotset_dlg.table_sectors.selectedIndexes()[0].row())
