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
    QAbstractItemView, QStandardItem, QAbstractItemView, QMessageBox, QColorDialog
from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint, \
    QgsRectangle, QgsCoordinateTransform, QgsVectorLayer, QgsMapLayerRegistry, QgsFeature
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialogs
from sectorplot_sectorplotsets_dialog import SectorPlotSetsDialog
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

        self.MSG_BOX_TITLE = self.tr("SectorPlot Plugin")

        # Create the dialogs (after translation!) and keep references

        #
        self.sectorplotsets_dlg = SectorPlotSetsDialog()
        self.sectorplotsets_dlg.table_sectorplot_sets.horizontalHeader().setStretchLastSection(True)
        self.sectorplotsets_dlg.table_sectorplot_sets.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sectorplotsets_dlg.table_sectorplot_sets.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sectorplotsets_dlg.table_sectorplot_sets.setSelectionMode(QAbstractItemView.SingleSelection)

        self.sectorplotsets = None
        self.sectorplotsets_source_model = None
        # dlg actions
        self.sectorplotsets_dlg.btn_new_sectorplotset_dialog.clicked.connect(self.open_location_dialog)
        self.sectorplotsets_dlg.btn_copy_sectorplotset_dialog.clicked.connect(self.new_sectorplotset_dialog)

        # Create location_dialog
        self.location_dlg = SectorPlotLocationDialog()
        self.location_dlg.table_npps.horizontalHeader().setStretchLastSection(True)
        self.location_dlg.table_npps.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.location_dlg.table_npps.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.location_dlg.table_npps.setSelectionMode(QAbstractItemView.SingleSelection)
        self.npp_source_model = None
        self.npp_proxy_model = None
        # actions
        self.location_dlg.le_longitude.textChanged.connect(self.locationdlg_lonlat_changed)
        self.location_dlg.le_latitude.textChanged.connect(self.locationdlg_lonlat_changed)

        # Create sector_dialog
        self.sector_dlg = SectorPlotSectorDialog()
        self.sector_dlg.cb_min_distance.stateChanged.connect(self.sector_dlg_enable_min_distance)
        self.sector_dlg.combo_countermeasures.currentIndexChanged.connect(self.sector_dlg_countermeasure_selected)

        # the data for the combo_countermeasures
        self.counter_measures = CounterMeasures()
        # actions

        # Create sectorplotset_dialog
        self.sectorplotset_dlg = SectorPlotSectorPlotSetDialog()
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setStretchLastSection(True)
        self.sectorplotset_dlg.table_sectors.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sectorplotset_dlg.table_sectors.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sectorplotset_dlg.table_sectors.setSelectionMode(QAbstractItemView.SingleSelection)
        # user is able to drag/drop both columns and rows
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setMovable(True)
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setDragEnabled(True)
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setMovable(True)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setDragEnabled(True)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)

        self.sectorplotset_source_model = QStandardItemModel()
        self.sectorplotset_dlg.table_sectors.setModel(self.sectorplotset_source_model)
        # actions
        self.sectorplotset_dlg.btn_new_sector.clicked.connect(self.open_new_sector_dialog)
        self.sectorplotset_dlg.btn_open_selected_sector.clicked.connect(self.open_sector_for_edit_dialog)
        self.sectorplotset_dlg.btn_remove_selected_sector.clicked.connect(self.remove_sector_from_table)
        self.sectorplotset_dlg.table_sectors.verticalHeader().sectionMoved.connect(self.create_sectorset_from_sector_table)
        self.sectorplotset_dlg.table_sectors.clicked.connect(self.sectorplotsetdlg_sector_selected)

        self.current_sectorset = None

        # add memory Layer
        self.sector_layer = None
        self.crs_4326 = QgsCoordinateReferenceSystem()
        self.crs_4326.createFromId(4326)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SectorPlot')
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
        # we REALLY need OTF ON
        if self.iface.mapCanvas().hasCrsTransformEnabled() == False:
            QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, self.tr(
                "This Plugin ONLY works when you have OTF (On The Fly Reprojection) enabled for current QGIS Project.\n\n" +
                "Please enable OTF for this project or open a project with OTF enabled."),
                                QMessageBox.Ok, QMessageBox.Ok)
            return
        # add a memory layer to show sectors if not yet available
        if self.sector_layer is None:
            # give the memory layer the same CRS as the source layer
            self.sector_layer = QgsVectorLayer(
                "Polygon?crs=epsg:4326&field=setname:string(50)&field=countermeasureid:integer&field=z_order:integer" +
                "&field=saveTime:string(50)&field=color:counterMeasureTime(9)&field=sectorname:string(50)" +
                "&field=setid:integer&field=color:string(9)" +
                #"&field=setid:integer&field=direction:double&field=angle:double&field=mindistance:double&field=maxdistance:double" +
                "&index=yes",
                self.tr("Sector Layer"), "memory")
            # use a saved style as style
            self.sector_layer.loadNamedStyle(os.path.join(os.path.dirname(__file__), 'sectors.qml'))
            # add empty layer to the map
            QgsMapLayerRegistry.instance().addMapLayer(self.sector_layer)
        # open a the dialog with the sectorplotsets from the database
        self.new_sectorplotset()
        self.open_sectorplotsets_dialog()

    def new_sectorplotset(self):
        self.current_sectorset = None
        self.sectorplotset_source_model.clear()
        # show... nothing
        self.show_current_sectorplot_on_map()

    def open_sectorplotsets_dialog(self):
        # show the dialog with recent sectorplotsets
        self.sectorplotsets = SectorSets()
        self.sectorplotsets.importFromDatabase()
        # create emtpy model for new list
        self.sectorplotsets_source_model = QStandardItemModel()
        self.sectorplotsets_dlg.table_sectorplot_sets.setModel(self.sectorplotsets_source_model)
        # resize columns to fit text in it
        self.sectorplotsets_dlg.table_sectorplot_sets.resizeColumnsToContents()
        # be sure that the copy button is disabled (as nothing is selected?)
        self.sectorplotsets_dlg.btn_copy_sectorplotset_dialog.setEnabled(False)

        for sectorplot_set in self.sectorplotsets:
            lon = sectorplot_set.lon
            lat = sectorplot_set.lat
            name = QStandardItem("%s" % sectorplot_set.name )
            set_id = QStandardItem("%s" % sectorplot_set.setId )
            save_time = QStandardItem(unicode(sectorplot_set.get_save_time_string()))
            countermeasure_time = QStandardItem(unicode(sectorplot_set.get_counter_measure_time_string()))
            # attach the sectorplot_set as data to the first row item
            set_id.setData(sectorplot_set, Qt.UserRole)
            #self.sectorplotlist_source_model.appendRow([set_id, name, save_time, countermeasure_time])
            self.sectorplotsets_source_model.insertRow(0, [set_id, name, save_time, countermeasure_time])
        # headers
        self.sectorplotsets_source_model.setHeaderData(0, Qt.Horizontal, self.tr("Id"))
        self.sectorplotsets_source_model.setHeaderData(1, Qt.Horizontal, self.tr("Name"))
        self.sectorplotsets_source_model.setHeaderData(2, Qt.Horizontal, self.tr("Save Time"))
        self.sectorplotsets_source_model.setHeaderData(3, Qt.Horizontal, self.tr("Countermeasure Time"))
        self.sectorplotsets_dlg.table_sectorplot_sets.selectionModel().selectionChanged.connect(self.select_sectorplotset)
        # resize columns to fit text contents
        self.sectorplotsets_dlg.table_sectorplot_sets.resizeColumnsToContents()
        self.sectorplotsets_dlg.show()
        # See if OK was pressed
        if self.sectorplotsets_dlg.exec_():
            self.new_sectorplotset()
            self.sectorplotsets = None
        else:
            self.new_sectorplotset()
            self.sectorplotsets = None

    def select_sectorplotset(self):
        if len(self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()) > 0:
            # ONLY select the this selected one (multiple selection should not be possible)
            #self.sectorplotlist_dlg.table_sectorplot_sets.selectRow(0)
            # needed to scroll To the selected row incase of using the keyboard / arrows
            self.sectorplotsets_dlg.table_sectorplot_sets.scrollTo(
                self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()[0])
            # make this sectorplot(set) current
            self.current_sectorset = self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()[0].data(Qt.UserRole)
            # zoom to and show
            self.show_current_sectorplot_on_map()
            self.sectorplotsets_dlg.btn_copy_sectorplotset_dialog.setEnabled(True)

    def open_location_dialog(self):
        # starting NEW sectorplot(set), so remove all sectorplots from current sectorlayer, by adding empty array
        self.new_sectorplotset()
        self.location_dlg.selected_npp_name = ''
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
        # hide the data / search string column:
        self.location_dlg.table_npps.hideColumn(0)
        # handle the selection of a NPP
        self.location_dlg.table_npps.selectionModel().selectionChanged.connect(self.select_npp)
        # show the location dialog
        self.location_dlg.show()
        # See if OK was pressed
        if self.location_dlg.exec_():
            lon = self.location_dlg.le_longitude.text()
            lat = self.location_dlg.le_latitude.text()
            set_name = self.location_dlg.selected_npp_name
            self.new_sectorplotset_dialog(lon, lat, set_name)

    def new_sectorplotset_dialog(self, lon=None, lat=None, name=''):
        if self.current_sectorset is None:
            # create a SectorSet based on location dialog
            self.current_sectorset = SectorSet(lon, lat)
            self.current_sectorset.setSetName(name)
            self.sectorplotset_source_model.clear()
        else:
            # deep clone the current one
            self.current_sectorset = self.current_sectorset.clone()
            # clean up the sectorset model
            self.sectorplotset_source_model.clear()
        self.sectorplotset_dlg.lbl_location_name_lon_lat.setText(self.tr('Lon: %s') % self.current_sectorset.lon +
                                                                 self.tr(' Lat: %s') % self.current_sectorset.lat)
        self.sectorplotset_dlg.le_sectorplot_name.setText('%s' % self.current_sectorset.name)
        # IF SectorplotSet has sectors: show them
        if len(self.current_sectorset.sectors) > 0:
            for sector in self.current_sectorset.sectors:
                sector.calcGeometry()
                self.add_sector_to_table(sector)

        self.sectorplotset_dlg.show()
        # OK will save to db
        if self.sectorplotset_dlg.exec_():
            self.create_sectorset_from_sector_table()
            # save to DB
            # TODO: check if this returns an id, OR -1 in case of error
            self.current_sectorset.exportToDatabase()
            # (re)open sectorplotlist_dialog
            self.open_sectorplotsets_dialog()
            # TODO: and select the first last one ?? OR the one with the id we just got returned (safer)
            self.sectorplotsets_dlg.table_sectorplot_sets.selectRow(0)
        else:
            # go back to (old) selected one
            self.current_sectorset = self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()[0].data(Qt.UserRole)
            self.show_current_sectorplot_on_map()

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
            self.location_dlg.selected_npp_name = npp['block']
            self.zoom_map_to_lonlat(npp['longitude'], npp['latitude'])

    def locationdlg_lonlat_changed(self):
        lon = self.location_dlg.le_longitude.text()
        lat = self.location_dlg.le_latitude.text()
        if lon is None or len(lon) == 0:
            lon = 0
        if lat is None or len(lat) == 0:
            lat = 0
        self.zoom_map_to_lonlat(lon, lat)

    # note: when new sector button is clicked, this method is called with 'bool checked = false'
    # that is why the signature is self, bool, old_sector
    def open_new_sector_dialog(self, bool=False, old_sector=None):
        # we create a shiny new dialog to be sure all is initted ok
        self.sector_dlg = SectorPlotSectorDialog()
        self.sector_dlg.cb_min_distance.stateChanged.connect(self.sector_dlg_enable_min_distance)
        self.sector_dlg.combo_countermeasures.currentIndexChanged.connect(self.sector_dlg_countermeasure_selected)
        # TODO: realtime view of sector? So you can see what you are doing ...
        for counter_measure in self.counter_measures.all():
            # addItem sets both the text for the dropdown AND adds a data-item to it
            self.sector_dlg.combo_countermeasures.addItem(counter_measure['text'], counter_measure)
        if old_sector is not None:
            # prefill the dialog with the values of the original sector
            # select the right countermeasure in the combo (but not that the sectorName can be changed too)
            for i in range(0, self.sector_dlg.combo_countermeasures.count()):
                if old_sector.counterMeasureId == self.sector_dlg.combo_countermeasures.itemData(i)['id']:
                    self.sector_dlg.combo_countermeasures.setCurrentIndex(i)
                    break
            self.sector_dlg.le_sector_name.setText(old_sector.sectorName)
            self.sector_dlg.le_direction.setText("%s" % int(old_sector.direction))
            self.sector_dlg.le_angle.setText("%s" % int(old_sector.angle))
            self.sector_dlg.le_distance.setText("%s" % (int(old_sector.maxDistance)/1000))
            if old_sector.minDistance != 0:
                self.sector_dlg.le_min_distance.setText("%s" % (int(old_sector.minDistance)/1000))
                self.sector_dlg.le_min_distance.setEnabled(True)
                self.sector_dlg.lbl_min_distance.setEnabled(True)
                self.sector_dlg.cb_min_distance.setChecked(True)
        self.sector_dlg.show()

        #test = QColorDialog(self.sector_dlg)
        # test.setOption(QColorDialog.ShowAlphaChannel)
        #test.open()

        #QColorDialog.getColor()

        # OK pressed
        if self.sector_dlg.exec_():
            cm = self.sector_dlg.combo_countermeasures.itemData(self.sector_dlg.combo_countermeasures.currentIndex())
            # countermeasureid and (default) color from dropdown
            countermeasure = cm['id']
            color = cm['color']
            direction = self.sector_dlg.le_direction.text()
            angle = self.sector_dlg.le_angle.text()
            distance = self.sector_dlg.le_distance.text()
            min_distance = self.sector_dlg.le_min_distance.text()
            sector_name = self.sector_dlg.le_sector_name.text()
            new_sector = Sector(lon=self.current_sectorset.lon,
                                lat=self.current_sectorset.lat,
                                minDistance=1000*float(min_distance),
                                maxDistance=1000*float(distance),
                                direction=direction,
                                angle=angle,
                                counterMeasureId=countermeasure,
                                sectorName=sector_name,
                                color=color)
            # new sector or editing an excisting one?
            # check this by looking if something was selected in the table
            # -1 if nothing was selected aka we were creating a new one
            row = -1
            if old_sector is not None:
                row = self.sectorplotset_dlg.table_sectors.selectedIndexes()[0].row()
            self.add_sector_to_table(new_sector, row)
        else:
            # user canceled
            # set the data of the selected row BACK to the old_sector (original sector)
            self.sectorplotset_source_model.item(self.sectorplotset_dlg.table_sectors.selectedIndexes()[0].row(), 0) \
                .setData(self.sectorplotset_dlg.old_sector, Qt.UserRole)
            self.sectorplotset_dlg.old_sector = None

    def open_sector_for_edit_dialog(self):
        if len(self.sectorplotset_dlg.table_sectors.selectedIndexes()) > 0:
            sector = self.sectorplotset_dlg.table_sectors.selectedIndexes()[0].data(Qt.UserRole)
            self.sectorplotset_dlg.old_sector = sector
            self.open_new_sector_dialog(True, sector.clone())

    def sectorplotsetdlg_sector_selected(self):
        self.sectorplotset_dlg.btn_remove_selected_sector.setEnabled(True)
        self.sectorplotset_dlg.btn_open_selected_sector.setEnabled(True)

    def sectorplotsetdlg_set_headers(self):
        self.sectorplotset_source_model.setHeaderData(0, Qt.Horizontal, self.tr("Sector name"))
        self.sectorplotset_source_model.setHeaderData(1, Qt.Horizontal, self.tr("Countermeasure"))
        self.sectorplotset_source_model.setHeaderData(2, Qt.Horizontal, self.tr("MinDist (km)"))
        self.sectorplotset_source_model.setHeaderData(3, Qt.Horizontal, self.tr("Distance (km)"))
        self.sectorplotset_source_model.setHeaderData(4, Qt.Horizontal, self.tr("Direction (deg)"))
        self.sectorplotset_source_model.setHeaderData(5, Qt.Horizontal, self.tr("Angle (deg)"))
        # some size for sectorname and countermeasure NOTE: AFTER adding the data
        self.sectorplotset_dlg.table_sectors.setColumnWidth(0, 150)
        self.sectorplotset_dlg.table_sectors.setColumnWidth(1, 250)

    def sectorplotsetdlg_sector_moved(self, a, b, c):
        # user changed the order of the sectors by dragging a row in the table
        self.create_sectorset_from_sector_table()

    def show_current_sectorplot_on_map(self):
        self.sector_layer.dataProvider().deleteFeatures(self.sector_layer.allFeatureIds())
        if self.current_sectorset is not None:
            self.sector_layer.dataProvider().addFeatures(self.current_sectorset.get_qgs_features())
            self.zoom_map_to_lonlat(self.current_sectorset.lon, self.current_sectorset.lat)
        #self.sector_layer.updateFields()
        #self.sector_layer.updateExtents()
        if self.iface.mapCanvas().isCachingEnabled():
            self.sector_layer.setCacheImage(None)
        else:
            self.iface.mapCanvas().refresh()

    def zoom_map_to_lonlat(self, lon, lat, scale=300000):
        crs_to = self.iface.mapCanvas().mapRenderer().destinationCrs()
        crs_transform = QgsCoordinateTransform(self.crs_4326, crs_to)
        point = QgsPoint(float(lon), float(lat))
        geom = QgsGeometry.fromPoint(point)
        geom.transform(crs_transform)
        # zoom to with center is actually setting a point rectangle and then zoom
        center = geom.asPoint()
        rect = QgsRectangle(center, center)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().zoomScale(scale)
        self.iface.mapCanvas().refresh()

    def sector_dlg_enable_min_distance(self):
        self.sector_dlg.le_min_distance.setEnabled(self.sector_dlg.cb_min_distance.isChecked())
        self.sector_dlg.lbl_min_distance.setEnabled(self.sector_dlg.cb_min_distance.isChecked())
        # set to zero back if set back
        if self.sector_dlg.cb_min_distance.isChecked() is False:
            self.sector_dlg.le_min_distance.setText("0")

    def sector_dlg_countermeasure_selected(self):
        countermeasure = self.sector_dlg.combo_countermeasures.itemData(self.sector_dlg.combo_countermeasures.currentIndex())
        # default: put countermeasure text in sector name. Category 'overig' is to be set by the user!!
        self.sector_dlg.le_sector_name.setText(countermeasure['text'])

    def add_sector_to_table(self, sector, row=-1):
        sector_name_item = QStandardItem(sector.sectorName)
        direction_item = QStandardItem("%s" % int(sector.direction))
        angle_item = QStandardItem("%s" % int(sector.angle))
        min_distance_item = QStandardItem("%s" % int(sector.minDistance/1000))
        distance_item = QStandardItem("%s" % int(sector.maxDistance/1000))
        countermeasure_item = QStandardItem(self.counter_measures.get(sector.counterMeasureId))
        # attach the sector(data) as data to column 0
        sector_name_item.setData(sector, Qt.UserRole)
        if row < 0:
            # default, just append a fresh sector to the end
            self.sectorplotset_source_model.appendRow([sector_name_item, countermeasure_item, min_distance_item,
                                                       distance_item, direction_item, angle_item])
        else:
            # update a row from a sector which just has been editted
            self.sectorplotset_source_model.removeRow(row)
            self.sectorplotset_source_model.insertRow(row, [sector_name_item, countermeasure_item, min_distance_item,
                                                       distance_item, direction_item, angle_item])
            # and select it again
            self.sectorplotset_dlg.table_sectors.selectRow(row)
        self.create_sectorset_from_sector_table()
        self.sectorplotsetdlg_set_headers()

    def remove_sector_from_table(self):
        if len(self.sectorplotset_dlg.table_sectors.selectedIndexes()) > 0:
            self.sectorplotset_source_model.removeRow(self.sectorplotset_dlg.table_sectors.selectedIndexes()[0].row())
            self.create_sectorset_from_sector_table()
            self.show_current_sectorplot_on_map()

    def create_sectorset_from_sector_table(self):
        # NOW get the sectors from the model/dialog, put them in a sectorset in the order they are seen in the table
        # create an array with 'None's so we can place the sectors on the right spot
        self.current_sectorset.sectors = [None] * self.sectorplotset_source_model.rowCount()
        for row in range(0, self.sectorplotset_source_model.rowCount()):
            # data=sector is attached to column 0
            sector = self.sectorplotset_source_model.item(row, 0).data(Qt.UserRole)
            z = self.sectorplotset_dlg.table_sectors.verticalHeader().visualIndex(row)
            # set the z-order based on the visual position in the table
            sector.z_order = z
            # and insert the sector in the right position of the sectorset
            self.current_sectorset.sectors[z] = sector
        self.current_sectorset.setSetName(self.sectorplotset_dlg.le_sectorplot_name.text())
        # set save time (for the SectorplotSet == for all sectors in it)
        self.current_sectorset.setSaveTime()
        # show it!
        self.show_current_sectorplot_on_map()

    def msg(self, msg="", context=""):
        QMessageBox.warning(self.iface.mainWindow(), "MESSAGE !!!", "%s [%s]" % (msg, context), QMessageBox.Ok, QMessageBox.Ok)