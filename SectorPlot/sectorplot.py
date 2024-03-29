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
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, \
    QCoreApplication, Qt, QDateTime, QUrl, QSortFilterProxyModel, QLocale
from qgis.PyQt.QtGui import QIcon, \
    QStandardItemModel, QStandardItem, \
    QColor, QDoubleValidator, \
    QCursor, QPixmap, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QToolBar, \
    QAbstractItemView, QColorDialog, QMessageBox, QWidget, QFileDialog
from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsPointXY, \
    QgsRectangle, QgsCoordinateTransform, QgsVectorLayer, QgsProject, QgsPoint, \
    QgsVectorFileWriter, QgsMessageLog, QgsExpression, QgsFeatureRequest, \
    QgsApplication, Qgis
from qgis.gui import QgsMapTool
# Initialize Qt resources from file resources.py
from . import resources  # needed for button images!
# Import the code for the dialogs
from .sectorplot_sectorplotsets_dialog import SectorPlotSetsDialog
from .sectorplot_location_dialog import SectorPlotLocationDialog
from .sectorplot_sector_dialog import SectorPlotSectorDialog
from .sectorplot_sectorplotset_dialog import SectorPlotSectorPlotSetDialog
from .sectorplot_settings_dialog import SectorPlotSettingsDialog
from .sectorplot_settings import SectorPlotSettings

from .countermeasures import CounterMeasures

from .npp import NppSet
from .sector import Sector, SectorSet, SectorSets, Pie
from .connect import Database, RestClient

import os.path
import shutil
import sys

import logging
from . import LOGGER_NAME
log = logging.getLogger(LOGGER_NAME)

# pycharm debugging
# COMMENT OUT BEFORE PACKAGING !!!
#import pydevd
#pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)

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
        locale = QgsApplication.instance().locale()
        if locale and len(locale) >= 2:
            locale_path = os.path.join(
                self.plugin_dir,
                'i18n',
                '{}.qm'.format(locale))

            if os.path.exists(locale_path):
                self.translator = QTranslator()
                self.translator.load(locale_path)
                if qVersion() > '4.3.3':
                    QCoreApplication.installTranslator(self.translator)

        self.MSG_BOX_TITLE = self.tr("SectorPlot Plugin")
        self.TOOLBAR_TITLE = self.tr("RIVM Cal-Net Toolbar")  # TODO get this from commons
        # ALPHA is a fixed number for opacity, used in other sld's (Geoserver etc)
        self.ALPHA = 127
        # name of sector layer (memory layer) to be used to draw sectors in
        self.SECTOR_LAYER_NAME = self.tr("Sector Plugin Layer")
        self.PIE_LAYER_NAME = self.tr("Sector Plugin Layer (Pie)")

        self.DEMO = False

        # inits
        self.settings = SectorPlotSettings()

        self.sectorplotsets = None
        self.sectorplotsets_source_model = None

        self.npps = None
        self.npp_source_model = None
        self.npp_proxy_model = None

        self.xy_tool = GetPointTool(self.iface.mapCanvas(), self.locationdlg_xy_clicked)

        # actions
        #  see in sectorplotsetdlg_open_new_sector_dialog
        # inits
        # the data for the combo_countermeasures
        self.counter_measures = CounterMeasures()

        # available styles
        self.sector_styles = {
            'default': ['default', self.tr('Default (more or less idential in QGIS, Geoserver, JRodos)'), 'sectorplot.qml'],
            'gradient': ['gradient', self.tr('Gradient/Fading style (QGIS only)'), 'sectorplotwithgradient.qml'],
            'nolabels': ['nolabels', self.tr('Default, NO labels (QGIS only)'), 'sectorplotnolabels.qml'],
            'nolabelsgradient': ['nolabelsgradient', self.tr('Gradient/Fading style, NO labels (QGIS only)'), 'sectorplotwithgradientnolabels.qml'],
        }

        # some data input validators
        # set to current locale of QGIS application, else number input troubles
        self.locale = QLocale(QgsApplication.instance().locale())
        # using RejectGroupSeparator makes input of wrong numbers harder !!
        self.locale.setNumberOptions(QLocale.RejectGroupSeparator)
        self.degree_validator = QDoubleValidator(-360.00, 360.00, 6)
        self.degree_validator.setLocale(self.locale)
        self.positive_degree_validator = QDoubleValidator(1, 360.00, 6)
        self.positive_degree_validator.setLocale(self.locale)
        self.distance_validator = QDoubleValidator(0.1, 999.99, 6)
        self.distance_validator.setLocale(self.locale)
        self.min_distance_validator = QDoubleValidator(0.0, 999.99, 6)
        self.min_distance_validator.setLocale(self.locale)

        self.current_sectorset = None
        self.current_pie = None
        self.current_style = self.sector_styles['default']

        # memory Layer
        self.sector_layer = None
        self.pie_layer = None
        self.crs_4326 = QgsCoordinateReferenceSystem()
        self.crs_4326.createFromString('EPSG:4326')

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('RIVM &SectorPlot')
        self.toolbar = self.get_rivm_toolbar()

        self.sector_dlg = None
        self.location_dlg = None
        self.sectorplotset_dlg = None
        self.sectorplotsets_dlg = None
        # TODO connect to new project event, sectorlayer opruimen bij uninstall plugin, evt self.sector_layer -> self.get_sector_layer (mits nog beschikbaar)
        # create self.sector_layer when the user creates a new project (and removes this memory layer)

        # pycharm debugging
        # COMMENT OUT BEFORE PACKAGING !!!
        #import pydevd
        #pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)

        # when the user starts a new project, the plugins should remove the self.sector_layer, as the underlying cpp layer is removed
        self.iface.newProjectCreated.connect(self.stop_sectorplot_session)

    # TODO: move this to a commons class/module
    def get_rivm_toolbar(self):
        TOOLBAR_TITLE = 'RIVM Cal-Net Toolbar'  # TODO get this from commons and make translatable
        toolbars = self.iface.mainWindow().findChildren(QToolBar, TOOLBAR_TITLE)
        if len(toolbars) == 0:
            toolbar = self.iface.addToolBar(TOOLBAR_TITLE)
            toolbar.setObjectName(TOOLBAR_TITLE)
        else:
            toolbar = toolbars[0]
        return toolbar

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
        # main menu/dialog
        icon_path = ':/plugins/SectorPlot/images/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Sector plot'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # settings menu
        icon_path = ':/plugins/SectorPlot/images/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Show Settings'),
            callback=self.settingsdlg_show,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())

        # help menu
        icon_path = ':/plugins/SectorPlot/images/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Documentation'),
            callback=self.show_help,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())

        # The SectorplotSetS dialog, showing recent Sectorplots
        self.sectorplotsets_dlg = SectorPlotSetsDialog()
        # Below does not seem to work? So set modality in ui file
        # self.sectorplotsets_dlg.setModal(True)
        # self.sectorplotsets_dlg.setWindowModality(True)  # or this one?
        self.sectorplotsets_dlg.table_sectorplot_sets.horizontalHeader().setStretchLastSection(True)
        self.sectorplotsets_dlg.table_sectorplot_sets.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sectorplotsets_dlg.table_sectorplot_sets.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sectorplotsets_dlg.table_sectorplot_sets.setSelectionMode(QAbstractItemView.SingleSelection)
        # dlg actions
        self.sectorplotsets_dlg.btn_new_sectorplotset_dialog.clicked.connect(self.locationdlg_open_dialog)
        self.sectorplotsets_dlg.btn_copy_sectorplotset_dialog.clicked.connect(self.sectorplotsetsdlg_new_sectorplotset_dialog)
        self.sectorplotsets_dlg.btn_create_wms.clicked.connect(self.sectorplotsetsdlg_create_wms)
        self.sectorplotsets_dlg.btn_create_shapefile.clicked.connect(self.sectorplotsetsdlg_create_shapefile)
        self.sectorplotsets_dlg.table_sectorplot_sets.doubleClicked.connect(self.sectorplotsetsdlg_new_sectorplotset_dialog)
        cur = 0
        style_idx = cur
        for style_key in self.sector_styles.keys():
            # add styles key + title to the styles dropdown
            self.sectorplotsets_dlg.combo_styles.addItem(self.sector_styles[style_key][1], self.sector_styles[style_key][0])
            # remember index corresponding to settings key
            if style_key == self.settings.value('sector_style'):
                style_idx = cur
            cur = cur+1
        self.sectorplotsets_dlg.combo_styles.setCurrentIndex(style_idx)
        self.sectorplotsets_dlg.combo_styles.currentIndexChanged.connect(self.sectorplotsetsdlg_style_selected)

        # The Location_dialog for setting x/y lat/lon
        self.location_dlg = SectorPlotLocationDialog(parent=self.sectorplotsets_dlg)
        self.location_dlg.table_npps.horizontalHeader().setStretchLastSection(True)
        self.location_dlg.table_npps.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.location_dlg.table_npps.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.location_dlg.table_npps.setSelectionMode(QAbstractItemView.SingleSelection)
        # actions
        self.location_dlg.tabs.currentChanged.connect(self.locationdlg_tab_changed)
        self.location_dlg.le_longitude.textChanged.connect(self.locationdlg_lonlat_changed)
        self.location_dlg.le_latitude.textChanged.connect(self.locationdlg_lonlat_changed)
        self.location_dlg.le_longitude.textEdited.connect(self.locationdlg_lonlat_edited)
        self.location_dlg.le_latitude.textEdited.connect(self.locationdlg_lonlat_edited)
        self.location_dlg.btn_location_from_map.clicked.connect(self.locationdlg_btn_location_clicked)
        self.location_dlg.cmb_pie_sectors.currentIndexChanged.connect(self.locationdlg_lonlat_changed)
        self.location_dlg.cmb_pie_angle.currentIndexChanged.connect(self.locationdlg_lonlat_changed)
        self.lon_validator = QDoubleValidator(-180.0, 180.0, 7, self.location_dlg.le_longitude)
        self.lon_validator.setLocale(self.locale)
        self.location_dlg.le_longitude.setValidator(self.lon_validator)
        # epsg:3857 valid untill about -85/85 ! Not sure if this is ok?
        self.lat_validator = QDoubleValidator(-85.0, 85.0, 7, self.location_dlg.le_latitude)
        self.lat_validator.setLocale(self.locale)
        self.location_dlg.le_latitude.setValidator(self.lat_validator)
        # using currentTextChanged below, because user can edit text in combo's
        self.location_dlg.spin_pie_ring1.valueChanged.connect(self.locationdlg_lonlat_changed)
        self.location_dlg.spin_pie_ring2.valueChanged.connect(self.locationdlg_lonlat_changed)
        self.location_dlg.spin_pie_ring3.valueChanged.connect(self.locationdlg_lonlat_changed)
        # defaults
        self.location_dlg.spin_pie_ring1.setValue(2000)
        self.location_dlg.spin_pie_ring2.setValue(5000)
        self.location_dlg.spin_pie_ring3.setValue(10000)

        # SectorplotSet_dialog showing current sectorplot (list of sectors in this plot)
        self.sectorplotset_dlg = SectorPlotSectorPlotSetDialog(parent=self.sectorplotsets_dlg)
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setStretchLastSection(True)
        self.sectorplotset_dlg.table_sectors.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sectorplotset_dlg.table_sectors.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sectorplotset_dlg.table_sectors.setSelectionMode(QAbstractItemView.SingleSelection)
        # user is able to drag/drop both columns and rows
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setSectionResizeMode(True)
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setDragEnabled(True)
        self.sectorplotset_dlg.table_sectors.horizontalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setSectionsMovable(True)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setDragEnabled(True)
        self.sectorplotset_dlg.table_sectors.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        # actions
        self.sectorplotset_dlg.btn_new_sector.clicked.connect(self.sectorplotsetdlg_open_new_sector_dialog)
        self.sectorplotset_dlg.btn_open_selected_sector.clicked.connect(self.sectorplotsetdlg_open_sector_for_edit_dialog)
        self.sectorplotset_dlg.btn_remove_selected_sector.clicked.connect(self.sectorplotsetdlg_remove_sector_from_table)
        self.sectorplotset_dlg.table_sectors.verticalHeader().sectionMoved.connect(
            self.sectorplotsetdlg_create_sectorset_from_sector_table)
        self.sectorplotset_dlg.table_sectors.clicked.connect(self.sectorplotsetdlg_sector_selected)
        self.sectorplotset_dlg.table_sectors.doubleClicked.connect(self.sectorplotsetdlg_open_sector_for_edit_dialog)

        # inits
        self.sectorplotset_source_model = QStandardItemModel()
        self.sectorplotset_dlg.table_sectors.setModel(self.sectorplotset_source_model)

        # Sector dialog
        self.sector_dlg = SectorPlotSectorDialog(parent=self.sectorplotset_dlg)
        self.sector_dlg.setModal(True)
        self.sector_dlg.cb_min_distance.stateChanged.connect(self.sector_dlg_enable_min_distance)
        self.sector_dlg.combo_countermeasures.currentIndexChanged.connect(self.sector_dlg_countermeasure_selected)
        self.sector_dlg.btn_color.clicked.connect(self.sector_dlg_btn_color_clicked)
        self.sector_dlg.btn_preview.clicked.connect(self.sector_dlg_preview)
        self.sector_dlg.le_color.setReadOnly(True)  # not editing of color in the LineEdit here
        self.sector_dlg.le_direction.setValidator(self.degree_validator)
        self.sector_dlg.le_angle.setValidator(self.positive_degree_validator)
        self.sector_dlg.le_distance.setValidator(self.distance_validator)
        self.sector_dlg.le_min_distance.setValidator(self.min_distance_validator)
        for counter_measure in self.counter_measures.all():
            # addItem sets both the text for the dropdown AND adds a data-item to it
            self.sector_dlg.combo_countermeasures.addItem(counter_measure['text'], counter_measure)
        # tab order, start with the countermeasures
        QWidget.setTabOrder(self.sector_dlg.combo_countermeasures, self.sector_dlg.le_direction)
        QWidget.setTabOrder(self.sector_dlg.le_direction, self.sector_dlg.le_angle)
        QWidget.setTabOrder(self.sector_dlg.le_angle, self.sector_dlg.le_distance)
        QWidget.setTabOrder(self.sector_dlg.le_distance, self.sector_dlg.cb_min_distance)
        QWidget.setTabOrder(self.sector_dlg.cb_min_distance, self.sector_dlg.le_sector_name)

        # Settings dialog
        self.settings_dlg = SectorPlotSettingsDialog(parent=self.iface.mainWindow())
        self.settings_dlg.btn_test_postgis.clicked.connect(self.settingsdlg_test_postgis_clicked)
        self.settings_dlg.btn_test_geoserver.clicked.connect(self.settingsdlg_test_geoserver_clicked)
        self.settings_dlg.btn_test_jrodos.clicked.connect(self.settingsdlg_test_jrodos_clicked)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&SectorPlot'),
                action)
            #self.iface.removeToolBarIcon(action)
            self.toolbar.removeAction(action)
        # NOT (as it is RIVM toolbar) remove the toolbar
        #del self.toolbar
        self.stop_sectorplot_session()
        del self.xy_tool
        self.xy_tool = None

    def msg(self, parent=None, msg=""):
        if parent is None:
            parent = self.iface.mainWindow()
        QMessageBox.warning(parent, self.MSG_BOX_TITLE, "%s" % msg, QMessageBox.Ok, QMessageBox.Ok)

    def show_help(self):
        docs = os.path.join(os.path.dirname(__file__), "help/html", "index.html")
        QDesktopServices.openUrl(QUrl("file:" + docs))

    def run(self):
        """Start the plugin"""

        # hack: because we fiddle around with so many non modal dialogs, it is possible to
        # show the main window WHILE in the middle of the creation of a sectorplot(set)
        # this happens mainly on windows where non-modal dialogs go behind the main dialog..
        # so we check if either the self.location_dlg or self.sectorplotset_dlg or self.sector_dlg is visible
        # if so... do nothing for now..
        if self.location_dlg.isVisible() or self.sectorplotset_dlg.isVisible() or self.sector_dlg.isVisible():
            log.debug('NOT starting main dialog because an other dialog isVisible()')
            if self.location_dlg.isVisible():
                self.location_dlg.activateWindow()
            if self.sectorplotset_dlg.isVisible():
                self.sectorplotset_dlg.activateWindow()
            if self.sector_dlg.isVisible():
                self.sector_dlg.activateWindow()
            return

        # fresh installs do not have passwords, present the settings dialog upon first use
        settings = SectorPlotSettings()
        no_postgis_password = settings.value('postgis_password') == '' or settings.value('postgis_password') == None
        if no_postgis_password:
            self.settingsdlg_show()

        # fill the nuclear power plant list, because we need npp info to show pie's in current sectorsets
        if self.npps is None:
            try:
                url = self.settings.value('jrodos_rest_url')
                self.npps = NppSet(url)
            except:
                self.msg(self.location_dlg, self.tr("Problem retrieving the NPP (Nuclear Power Plant) list.\nPlease check if the the url used in the settings is valid."))
                return

        if self.settings.value('sector_style') in self.sector_styles:
            self.current_style = self.sector_styles[self.settings.value('sector_style')]

        # add a memory layer to show sectors and the pie if not yet available
        self.get_pie_layer()
        self.get_sector_layer()
        # open a the dialog with the sectorplotsets from the database
        self.new_sectorplotset()  # clean all
        self.sectorplotsetsdlg_open_dialog()

    def get_sector_layer(self):
        if len(QgsProject.instance().mapLayersByName(self.SECTOR_LAYER_NAME)) >= 0:
            # check IF there is already a SECTOR_LAYER_NAME in the project with the right fields
            if len(QgsProject.instance().mapLayersByName(self.SECTOR_LAYER_NAME)) > 0:
                # not 100% sure if this layers IS the real SECTOR_LAYER_NAME but no further checks for now
                self.sector_layer = QgsProject.instance().mapLayersByName(self.SECTOR_LAYER_NAME)[0]
            else:
                # give the memory layer the same CRS as the source layer
                # NOTE!!! the order of the attributes is vital, to the order you add the fields in sector.py!!!
                self.current_sectorset = None
                self.sector_layer = QgsVectorLayer(
                    "Polygon?crs=epsg:4326&field=setname:string(250)&field=countermeasureid:integer&field=z_order:integer" +
                    "&field=saveTime:string(50)&field=counterMeasureTime:string(50)&field=sectorname:string(250)" +
                    "&field=setid:integer&field=color:string(9)&field=npp_block:string(250)" +
                    "&index=yes",
                    self.SECTOR_LAYER_NAME,
                    "memory")
                # use a saved style as style
                self.sector_layer.loadNamedStyle(os.path.join(os.path.dirname(__file__), self.current_style[2]))
                # add empty layer to the map
                QgsProject.instance().addMapLayer(self.sector_layer)
                self.sector_layer.editingStopped.connect(self.sector_layer_edited_finished)
                # WHEN the sectorplot layer is deleted from the layer tree, stop the session
                # mmm, trying this results in SegFaults when quiting QGIS
                #self.sector_layer.destroyed.connect(self.stop_sectorplot_session)
        # do NOT ask if we want this layer to be saved!
        self.sector_layer.setCustomProperty("skipMemoryLayersCheck", 1)
        return self.sector_layer

    def get_pie_layer(self):
        if len(QgsProject.instance().mapLayersByName(self.PIE_LAYER_NAME)) >= 0:
            if len(QgsProject.instance().mapLayersByName(self.PIE_LAYER_NAME)) > 0:
                self.pie_layer = QgsProject.instance().mapLayersByName(self.PIE_LAYER_NAME)[0]
            else:
                # give the memory layer the same CRS as the source layer
                # NOTE!!! the order of the attributes is vital, to the order you add the fields in sector.py!!!
                self.current_pie = None
                self.pie_layer = QgsVectorLayer(
                    "Polygon?crs=epsg:4326&field=setname:string(250)&field=countermeasureid:integer&field=z_order:integer" +
                    "&field=saveTime:string(50)&field=counterMeasureTime:string(50)&field=sectorname:string(250)" +
                    "&field=setid:integer&field=color:string(9)&field=npp_block:string(250)" +
                    "&index=yes",
                    self.PIE_LAYER_NAME,
                    "memory")
                # use a saved style as style
                self.pie_layer.loadNamedStyle(os.path.join(os.path.dirname(__file__), 'sectorpie.qml'))
                # add empty layer to the map
                QgsProject.instance().addMapLayer(self.pie_layer)
                # connect selectionChanged to sector_dlg_pie_sector_select
                self.pie_layer.selectionChanged.connect(self.sector_dlg_pie_sector_select)
                # WHEN the pie layer is deleted from the layer tree, stop the session
                # mmm, trying this results in SegFaults when quiting QGIS
                #self.pie_layer.destroyed.connect(self.stop_sectorplot_session)
        # do NOT ask if we want this layer to be saved!
        self.pie_layer.setCustomProperty("skipMemoryLayersCheck", 1)
        return self.pie_layer

    def stop_sectorplot_session(self):
        # close all dialogs
        if self.sector_dlg is not None:
            self.sector_dlg.reject()
        if self.location_dlg is not None:
            self.location_dlg.reject()
        if self.sectorplotset_dlg is not None:
            self.sectorplotset_dlg.reject()
        if self.sectorplotsets_dlg is not None:
            self.sectorplotsets_dlg.reject()
        # remove plugin layers
        pie_lyrs = QgsProject.instance().mapLayersByName(self.PIE_LAYER_NAME)
        if len(pie_lyrs) > 0 and self.pie_layer:
            try:
                QgsProject.instance().removeMapLayer(pie_lyrs[0].id())
            except:
                pass
        sector_lyrs = QgsProject.instance().mapLayersByName(self.SECTOR_LAYER_NAME)
        if len(sector_lyrs) > 0 and self.sector_layer:
            try:
                QgsProject.instance().removeMapLayer(sector_lyrs[0].id())
            except:
                pass

        #  set instances to None
        self.sector_layer = None
        self.pie_layer = None
        self.current_sectorset = None
        self.current_pie = None
        self.iface.mapCanvas().refreshAllLayers()

    def new_sectorplotset(self):
        self.current_sectorset = None
        self.current_pie = None
        self.sectorplotset_source_model.clear()
        # show... nothing
        self.show_current_sectorplotset_on_map()

    def show_current_sectorplotset_on_map(self, zooms=0):
        self.clean_sector_layer(sectorset=True, pie=True)
        if self.current_sectorset is not None and self.sector_layer is not None:
            self.get_sector_layer().dataProvider().addFeatures(self.current_sectorset.get_qgs_features())
            # using "self.get_sector_layer().dataProvider().sourceExtent()" as in QGIS 3.4 "self.get_sector_layer().extent()" is not updated yet !!
            self.zoom_map_to_lonlat(self.current_sectorset.lon, self.current_sectorset.lat, self.get_sector_layer().dataProvider().sourceExtent())
        if self.current_pie is not None and self.pie_layer is not None:
            self.get_pie_layer().dataProvider().addFeatures(self.current_pie.get_features())
            # using "self.get_pie_layer().dataProvider().sourceExtent()" as in QGIS 3.4 "self.get_pie_layer().extent()" is not updated yet !!
            self.zoom_map_to_lonlat(self.current_pie.lon, self.current_pie.lat, self.get_pie_layer().dataProvider().sourceExtent())
        for i in range(0, zooms):
            self.iface.mapCanvas().zoomOut()
        self.repaint_sector_layers()

    def repaint_sector_layers(self):
        self.iface.mapCanvas().refreshAllLayers()

    def zoom_map_to_lonlat(self, lon: float, lat: float, extent=None):
        crs_to = self.iface.mapCanvas().mapSettings().destinationCrs()
        crs_transform = QgsCoordinateTransform(self.crs_4326, crs_to, QgsProject.instance())
        if extent is None or extent.isNull():  # isNull() returns True if a 0,0,0,0 rectangle
            point = QgsPointXY(float(lon), float(lat))
            geom = QgsGeometry.fromPointXY(point)
            geom.transform(crs_transform)
            center = geom.asPoint()
            self.iface.mapCanvas().setCenter(center)
        else:
            rect = crs_transform.transformBoundingBox(extent)
            self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()

    def sectorplotsetsdlg_open_dialog(self, selected_id=-1):
        # show a new dialog with recent sectorplotsets
        self.sectorplotsets = SectorSets()
        db_ok, result = self.sectorplotsets.importFromDatabase()
        if self.DEMO:
            self.msg(None, "DEMO MODE: no wms and saving / retrieving of old sectors / listing of recent plots\nPlease create a new Sectorplot via 'New Sectorplot' button in next dialog.")
        elif not db_ok:
            # if NOT OK importFromDatabase returns the database error
           self.msg(None, self.tr("There is a problem with the Database to retrieve the Sectorplots\nThe Database error is:\n%s") % result)
           return
        # create emtpy model for new list
        self.sectorplotsets_source_model = QStandardItemModel()
        self.sectorplotsets_dlg.table_sectorplot_sets.setModel(self.sectorplotsets_source_model)
        # enable the sorting of columns by clicking on header
        self.sectorplotsets_dlg.table_sectorplot_sets.setSortingEnabled(True)
        # resize columns to fit text in it
        self.sectorplotsets_dlg.table_sectorplot_sets.resizeColumnsToContents()
        # be sure that the copy button is disabled (as nothing is selected?)
        self.sectorplotsets_dlg.btn_copy_sectorplotset_dialog.setEnabled(False)
        for sectorplot_set in self.sectorplotsets:
            name = QStandardItem("%s" % sectorplot_set.name)
            set_id = QStandardItem("%s" % sectorplot_set.setId)
            # TODO: get time right instead of get_***_time_string()
            save_time = QStandardItem(sectorplot_set.get_save_time_string())
            countermeasure_time = QStandardItem(sectorplot_set.get_counter_measure_time_string())
            # attach the sectorplot_set as data to the first row item
            set_id.setData(sectorplot_set, Qt.UserRole)
            self.sectorplotsets_source_model.insertRow(0, [set_id, name, countermeasure_time, save_time])
        # headers
        self.sectorplotsets_source_model.setHeaderData(0, Qt.Horizontal, self.tr("Id"))
        self.sectorplotsets_source_model.setHeaderData(1, Qt.Horizontal, self.tr("Name"))
        self.sectorplotsets_source_model.setHeaderData(2, Qt.Horizontal, self.tr("Countermeasure Time"))
        self.sectorplotsets_source_model.setHeaderData(3, Qt.Horizontal, self.tr("Save Time"))
        self.sectorplotsets_dlg.table_sectorplot_sets.selectionModel().selectionChanged.connect(self.sectorplotsetsdlg_select_sectorplotset)
        # resize columns to fit text contents
        self.sectorplotsets_dlg.table_sectorplot_sets.resizeColumnsToContents()
        # select the row of 'selected_id' if given and >= 0
        selected_row = 0
        if selected_id >= 0:
            for row in range(0, self.sectorplotsets_source_model.rowCount()):
                sectorplot = self.sectorplotsets_source_model.item(row, 0).data(Qt.UserRole)
                if sectorplot.setId == selected_id:
                    selected_row = row
                    break;
        self.sectorplotsets_dlg.table_sectorplot_sets.selectRow(selected_row)
        self.sectorplotsets_dlg.btn_new_sectorplotset_dialog.setFocus()
        # See if OK was pressed
        self.sectorplotsets_dlg.show()

    def sectorplotsetsdlg_select_sectorplotset(self):
        if len(self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()) > 0:
            # needed to scroll To the selected row incase of using the keyboard / arrows
            self.sectorplotsets_dlg.table_sectorplot_sets.scrollTo(
                self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()[0])
            # make this sectorplot(set) current
            self.current_sectorset = self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()[0].data(Qt.UserRole)
            # IF this current_sectorset has a npp_block name, then create a pie for it too
            self.current_pie = None
            if self.current_sectorset.npp_block is not None and self.current_sectorset.npp_block != "":
                npp_block = self.current_sectorset.npp_block
                # find the npp-block in our list of npp's...?
                for npp in self.npps:
                    if npp['block'] == npp_block:
                        self.current_pie = Pie(npp['longitude'], npp['latitude'], npp['angle'], npp['numberofsectors'],
                                               npp['zoneradii'])
                        break
            else:
                # CHECK if the sectorset has a 'pie' in the database and make it self.current_pie
                self.current_pie = Pie()
                db_ok, result = self.current_pie.importFromDatabase(self.current_sectorset.setId)
                if not db_ok:
                    self.current_pie = None
                    #self.msg(self.sectorplotset_dlg, self.tr('Problem retrieving Pie for this SectorSet {}\n{}').format(self.current_sectorset.setId, result))
            # zoom to and show
            #log.debug(f'SELECT self.current_sectorset: {self.current_sectorset}')
            #log.debug(f'SELECT self.current_pie: {self.current_pie}')
            self.show_current_sectorplotset_on_map(1)
            self.sectorplotsets_dlg.btn_copy_sectorplotset_dialog.setEnabled(True)
        else:
            # disable the button
            self.sectorplotsets_dlg.btn_copy_sectorplotset_dialog.setEnabled(False)

    def sectorplotsetsdlg_new_sectorplotset_dialog(self, lon=None, lat=None, name='', npp_block=None):
        self.sectorplotsets_dlg.hide()
        if self.current_sectorset is None:
            # create a SectorSet based on location dialog
            self.current_sectorset = SectorSet(lon, lat)
            self.current_sectorset.setSetName(name)
            if npp_block is not None:
                self.current_sectorset.setNppBlock(npp_block)
        else:
            # deep clone the current one
            self.current_sectorset = self.current_sectorset.clone()
            # clean up the sectorset model
        self.sectorplotset_source_model.clear()
        self.sectorplotset_dlg.lbl_location_name_lon_lat.setText(
            self.tr('Lon: %s') % self.locale.toString(self.current_sectorset.lon, 'f', 4) +
            self.tr(' Lat: %s') % self.locale.toString(self.current_sectorset.lat, 'f', 4)
        )
        self.sectorplotset_dlg.le_sectorplot_name.setText('%s' % self.current_sectorset.name)
        if self.current_sectorset.npp_block is not None:
            self.sectorplotset_dlg.lbl_npp_block.setText('%s' % self.current_sectorset.npp_block)
        else:
            self.sectorplotset_dlg.lbl_npp_block.setText('')
        date_format = "yyyy-MM-dd HH:mm:ss +0000"
        #self.msg(None, ("%s" % self.current_sectorset.sectors[0].counterMeasureTime) + " *** " + self.current_sectorset.get_counter_measure_time_string())
        #self.msg(None, date_format + " *** " + self.current_sectorset.get_counter_measure_time_string())
        datetime = QDateTime.fromString(self.current_sectorset.get_counter_measure_time_string(), date_format)

        if datetime.isValid():
            # self.msg(None, datetime)
            self.sectorplotset_dlg.time_edit_countermeasure.setTime(datetime.time())
            self.sectorplotset_dlg.date_edit_countermeasure.setDate(datetime.date())
        else:
            self.msg(self.sectorplotset_dlg, self.tr("Date Time conversion problem"))  # should not come here
            return

        # IF SectorplotSet has sectors: show them
        if len(self.current_sectorset.sectors) > 0:
            for sector in self.current_sectorset.sectors:
                sector.calcGeometry()
                self.sectorplotsetdlg_add_sector_to_table(sector)
        self.sectorplotsetdlg_show()

    def sectorplotsetsdlg_create_wms(self):
        name = self.current_sectorset.getUniqueName()
        result = self.current_sectorset.publish(name)
        # TODO: show more verbose messages
        # till now only True or False is returned!
        if result is True:
            self.msg(self.sectorplotsets_dlg, self.tr(u"WMS layer created successfully as layer\n%s." % name))
        else:
            self.msg(self.sectorplotsets_dlg, self.tr(u"Problem creating WMS layer\n(Maybe already published? A SectorPlot cannot be republished...)"))

    def sectorplotsetsdlg_create_shapefile(self):
        # open file dialog with unique name preselected
        # TODO: onthoud de laatste directory
        default_name = str('/tmp/' + self.current_sectorset.getUniqueName())
        filename, filter = QFileDialog.getSaveFileName(self.sectorplotsets_dlg, self.tr("Save shapefile as"), default_name, filter="*.shp")
        if self.sector_layer is not None:
            # save shapefile
            # check if it is already there??
            QgsVectorFileWriter.writeAsVectorFormat(self.sector_layer, filename, 'utf-8',  QgsCoordinateReferenceSystem(), 'ESRI Shapefile')
            # AND corresponding sld with same name
            sld_name = os.path.join(self.plugin_dir, 'sectorplot.sld')
            # on windows .shp is added to filename already, so remove it here IF it is there
            filename = filename.replace('.shp', '')
            new_sld_name = filename + '.sld'
            shutil.copy2(sld_name, new_sld_name)
            qml_name = os.path.join(self.plugin_dir, self.current_style[2])
            new_qml_name = filename + '.qml'
            shutil.copy2(qml_name, new_qml_name)
            self.msg(self.sectorplotsets_dlg, self.tr(u"Shapefile created successfully:\n ") + filename + ".shp")
        else:
            # should not come here!!
            self.msg(self.sectorplotsets_dlg, self.tr("Problem saving shapefile"))

    def sectorplotsetsdlg_style_selected(self):
        idx = self.sectorplotsets_dlg.combo_styles.currentIndex()
        style_name = self.sectorplotsets_dlg.combo_styles.itemData(idx)
        self.settings.setValue('sector_style', style_name)
        self.current_style = self.sector_styles[style_name]
        if self.sector_layer is not None:
            self.sector_layer.loadNamedStyle(os.path.join(os.path.dirname(__file__), self.current_style[2]))
            self.repaint_sector_layers()

    def locationdlg_open_dialog(self):
        # hide the start/sets dialog
        self.sectorplotsets_dlg.hide()
        self.new_sectorplotset()
        self.location_dlg.le_longitude.clear()
        self.location_dlg.le_latitude.clear()
        self.sectorplotsets_dlg.table_sectorplot_sets.clearSelection()
        self.location_dlg.selected_npp_name = ''
        self.npp_proxy_model = QSortFilterProxyModel()
        self.npp_source_model = QStandardItemModel()
        self.npp_proxy_model.setSourceModel(self.npp_source_model)
        # setFilterKeyColumn = search in the data in column
        self.npp_proxy_model.setFilterKeyColumn(0)
        self.location_dlg.table_npps.setModel(self.npp_proxy_model)
        # enable the sorting of columns by clicking on header
        self.location_dlg.table_npps.setSortingEnabled(True)
        self.location_dlg.table_npps.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # using textEdited here to be sure, that we only filter when a user types
        self.location_dlg.le_search_npp.textEdited.connect(self.locationdlg_filter_npps)
        self.location_dlg.le_search_npp.setPlaceholderText(self.tr("Search"))
        if len(self.npps):
            # load the npps in the table in dialog
            for npp in self.npps:
                # prepare a commaseparated string to search in from the values of the npp dict
                vals = ""
                for val in npp.values():
                    vals += ", %s" % val
                # you can attache different "data's" to to an QStandarditem
                # default one is the visible one:
                country_code = QStandardItem("%s" % (npp["countrycode"].upper()))
                # userrole is a free form one:
                # attach the data/npp to the first visible(!) column
                # when clicked you can get the npp from the data of that column
                data = QStandardItem(vals)
                country_code.setData(npp, Qt.UserRole)
                site = QStandardItem("%s" % (npp["site"].upper()))
                npp_block = QStandardItem("%s" % (npp["block"].upper()))
                self.npp_source_model.appendRow([data, country_code, site, npp_block])
            # headers
            self.npp_source_model.setHeaderData(1, Qt.Horizontal, self.tr("Countrycode"))
            self.npp_source_model.setHeaderData(2, Qt.Horizontal, self.tr("Site"))
            self.npp_source_model.setHeaderData(3, Qt.Horizontal, self.tr("Block"))
            # hide the data / search string column:
            self.location_dlg.table_npps.hideColumn(0)
            # handle the selection of a NPP
            self.location_dlg.table_npps.selectionModel().selectionChanged.connect(self.locationdlg_select_npp)
        # show the location dialog
        self.locationdlg_show()

    def locationdlg_lonlat_changed(self):
        # called via several routes: when user clicks in npp list
        # or when user sets location via 'click in map'
        #log.debug('locationdlg_lonlat_changed')
        lon_txt = self.location_dlg.le_longitude.text()
        lat_txt = self.location_dlg.le_latitude.text()

        if self.locationdlg_lonlat_checked(lon_txt, lat_txt):
            self.zoom_map_to_lonlat(self.locale.toFloat(lon_txt)[0],
                                    self.locale.toFloat(lat_txt)[0])
            self.clean_sector_layer()
            sector_count = int(self.location_dlg.cmb_pie_sectors.currentText())
            start_angle = float(self.location_dlg.cmb_pie_angle.currentText())
            ring1 = int(self.location_dlg.spin_pie_ring1.value())
            ring2 = int(self.location_dlg.spin_pie_ring2.value())
            ring3 = int(self.location_dlg.spin_pie_ring3.value())
            self.current_pie = Pie(self.locale.toFloat(lon_txt)[0],
                                   self.locale.toFloat(lat_txt)[0],
                                   start_angle=start_angle,
                                   sector_count=sector_count,
                                   zone_radii=[ring1, ring2, ring3])
            self.get_pie_layer().dataProvider().addFeatures(self.current_pie.get_features())
            self.repaint_sector_layers()

    def locationdlg_lonlat_edited(self):
        # ONLY if the user edits coords by hand, override npp selection
        # by cleaning the npp name
        # remembering the lat lon
        log.debug('locationdlg_lonlat_edited')
        self.location_dlg.table_npps.clearSelection()
        lon_txt = self.location_dlg.le_longitude.text()
        lat_txt = self.location_dlg.le_latitude.text()
        if self.locationdlg_lonlat_checked(lon_txt, lat_txt):
            self.zoom_map_to_lonlat(self.locale.toFloat(lon_txt)[0], self.locale.toFloat(lat_txt)[0])
        self.unset_npp()
        #self.debug('setting last_location to: %s' % [lon_txt, lat_txt])
        QSettings().setValue("plugins/SectorPlot/last_location", [lon_txt, lat_txt])

    def unset_npp(self):
        # clear npp search input
        #self.location_dlg.le_search_npp.setText('')
        # deselect row in npp list
        self.location_dlg.table_npps.clearSelection()
        # clear selected_npp_name
        self.location_dlg.selected_npp_name = ''
        # remove npp pie
        self.current_pie = None
        self.clean_sector_layer(sectorset=False, pie=True)

    def clean_sector_layer(self, sectorset=True, pie=True):
        # sector_layer = self.sector_layer
        # if sectorset and pie:
        #     #sector_layer.dataProvider().deleteFeatures(sector_layer.allFeatureIds())
        #     expr = QgsExpression('"setname"!=\'XxXxX\'')  # hopefully all
        # elif sectorset:
        #     expr = QgsExpression('"setname"!=\'rose\'')
        # elif pie:
        #     expr = QgsExpression('"setname"=\'rose\'')
        # ids = [f.id() for f in sector_layer.getFeatures(QgsFeatureRequest(expr))]
        # sector_layer.dataProvider().deleteFeatures(ids)
        # self.repaint_sector_layer()
        if sectorset and self.sector_layer is not None:
            self.get_sector_layer().dataProvider().deleteFeatures(self.get_sector_layer().allFeatureIds())
        if pie and self.pie_layer is not None:
            self.get_pie_layer().dataProvider().deleteFeatures(self.get_pie_layer().allFeatureIds())
        self.repaint_sector_layers()

    def locationdlg_lonlat_checked(self, lon_txt, lat_txt):
        lat_state, lon, pos = self.lat_validator.validate(lat_txt, 6)
        lon_state, lat, pos = self.lon_validator.validate(lon_txt, 6)
        # only return True for full accaptence, not for intermediate ok's
        return lat_state == QDoubleValidator.Acceptable and lon_state == QDoubleValidator.Acceptable

    def locationdlg_filter_npps(self, string):
        self.location_dlg.table_npps.clearSelection()
        self.location_dlg.le_longitude.setText('')
        self.location_dlg.le_latitude.setText('')
        self.npp_proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.npp_proxy_model.setFilterFixedString(string)
        # always select top one IF we are filtering by hand (that is, editing the search line)
        if self.npp_proxy_model.rowCount() > 0:
            self.location_dlg.table_npps.selectRow(0)

    def locationdlg_select_npp(self):
        # needed to scroll To the selected row incase of using the keyboard / arrows
        # self.location_dlg.table_npps.scrollTo(self.location_dlg.table_npps.selectedIndexes()[0])
        # itemType holds the data (== column 1)
        if len(self.location_dlg.table_npps.selectedIndexes()) > 0:
            npp = self.location_dlg.table_npps.selectedIndexes()[0].data(Qt.UserRole)
            self.location_dlg.le_longitude.setText(self.locale.toString(npp['longitude']))
            self.location_dlg.le_latitude.setText(self.locale.toString(npp['latitude']))
            self.location_dlg.selected_npp_name = npp['block']
            self.zoom_map_to_lonlat(npp['longitude'], npp['latitude'])
            self.clean_sector_layer(True, True)
            # lon=0, lat=0, start_angle=0.0, sector_count=8, zone_radii=[5]
            self.current_pie = Pie(npp['longitude'], npp['latitude'], npp['angle'], npp['numberofsectors'], npp['zoneradii'])
            self.get_pie_layer().dataProvider().addFeatures(self.current_pie.get_features())
            self.show_current_sectorplotset_on_map()
            self.repaint_sector_layers()
            #self.debug('setting last_location to: %s' % npp['block'])
            QSettings().setValue("plugins/SectorPlot/last_location", npp['block'])
        else:
            self.unset_npp()

    def locationdlg_btn_location_clicked(self):
        self.iface.mapCanvas().setMapTool(self.xy_tool)

    def locationdlg_xy_clicked(self, xy):
        # we retrieve an x,y from the mapcanvas in the project crs
        # set it to epsg:4326 if different
        log.debug('locationdlg_xy_clicked')
        crs_from = self.iface.mapCanvas().mapSettings().destinationCrs()
        crs_transform = QgsCoordinateTransform(crs_from, self.crs_4326, QgsProject.instance())
        xy4326 = crs_transform.transform(xy)
        lon_txt = self.locale.toString(xy4326.x())
        lat_txt = self.locale.toString(xy4326.y())
        self.location_dlg.le_longitude.setText(lon_txt)
        self.location_dlg.le_latitude.setText(lat_txt)
        QSettings().setValue("plugins/SectorPlot/last_location", [lon_txt, lat_txt])
        self.iface.mapCanvas().unsetMapTool(self.xy_tool)
        self.location_dlg.activateWindow()

    def locationdlg_tab_changed(self, tab):
        log.debug('locationdlg_tab_changed: {}'.format(tab))
        if tab == 1:  # via map
            self.clean_sector_layer()
            self.location_dlg.le_longitude.setText('')
            self.location_dlg.le_latitude.setText('')
        elif tab == 0:  # via npp's list
            self.locationdlg_select_npp()

    def locationdlg_show(self):
        last_location = QSettings().value("plugins/SectorPlot/last_location")
        log.debug('last_location: {}'.format(last_location))
        if isinstance(last_location, list):  # should be a list of two floats as string
            # last try was one via setting lat lon, enable tab 1
            #self.location_dlg.tabs.setCurrentIndex(1)
            # try to retrieve lat location lon and lat, BUT can have locale
            # problems, then pass
            try:
                self.location_dlg.le_longitude.setText(
                    self.locale.toString(last_location[0]))
                self.location_dlg.le_latitude.setText(
                    self.locale.toString(last_location[1]))
            except Exception as e:
                #log.debug('Locale number issue with lon {} lat {}'.format(last_location[0], last_location[1]))
                #log.debug(e)
                self.location_dlg.le_longitude.setText(last_location[0])
                self.location_dlg.le_latitude.setText(last_location[1])
            self.location_dlg.tabs.setCurrentIndex(1)
        elif isinstance(last_location, str):
            self.location_dlg.le_search_npp.setText(last_location)
            self.locationdlg_filter_npps(last_location)
            self.location_dlg.tabs.setCurrentIndex(0)

        # See if OK was pressed
        if self.location_dlg.exec_():
            # the le's (LineEdit's) should contain a locale aware TEXT number
            # we CHECK the float numbers
            lon_txt = self.location_dlg.le_longitude.text()
            lat_txt = self.location_dlg.le_latitude.text()
            if self.locationdlg_lonlat_checked(lon_txt, lat_txt):
                # location coordinates are OK: create floats from them
                lon = self.locale.toFloat(lon_txt)[0]
                lat = self.locale.toFloat(lat_txt)[0]
                npp_block = None
                set_name = ''
                # IF and only IF a NPP is selected in the table, pass it to the sectorplotset dialog
                if self.location_dlg.tabs.currentIndex() == 0 and len(self.location_dlg.table_npps.selectedIndexes()) > 0:
                    npp = self.location_dlg.table_npps.selectedIndexes()[0].data(Qt.UserRole)
                    npp_block = npp['block']
                    set_name = self.location_dlg.selected_npp_name
                self.sectorplotsetsdlg_new_sectorplotset_dialog(lon, lat, set_name, npp_block)
            else:
                # problem validating the lat lon coordinates
                self.msg(self.sectorplotsets_dlg,
                         self.tr('At least one of the coordinates is not valid.\nPlease check and correct.\nNote: number notation: {}'
                                 .format(self.locale.toString(52.123456, 'f', 5))))
                self.location_dlg.show()
        else:
            self.clean_sector_layer(True, True)

    def sectorplotsetdlg_create_backup(self):
        # create a copy of current sectors, to be able to go back to current status
        sectors = []
        for i in range(0, self.sectorplotset_source_model.rowCount()):
            idx = self.sectorplotset_dlg.table_sectors.model().index(i, 0)
            sectors.append(self.sectorplotset_dlg.table_sectors.model().data(idx, Qt.UserRole))
        self.sector_dlg.old_sectors = sectors

    # note: when new sector button is clicked, this method is called with 'bool checked = false'
    # that is why the signature is self, bool, old_sector
    def sectorplotsetdlg_open_new_sector_dialog(self, bool=False, edited_sector=None):
        if edited_sector is None:
            self.sectorplotsetdlg_create_backup()
            # ok creating a fresh new sector from scratch
            # we do two setCurrentIndex's to be sure we fire the currentIndexChanged
            self.sector_dlg.combo_countermeasures.setCurrentIndex(1)
            self.sector_dlg.combo_countermeasures.setCurrentIndex(0)
            # self.sector_dlg.le_sector_name.setText('') #  already reset by countermeasure rest
            self.sector_dlg.le_direction.setText('')
            self.sector_dlg.le_angle.setText('')
            self.sector_dlg.le_distance.setText('')
            # be sure to deselect sectors in the sector table!
            self.sectorplotset_dlg.table_sectors.clearSelection()
            self.sector_dlg.lbl_min_distance.setEnabled(False)
            self.sector_dlg.le_min_distance.setText('0')
        else:
            # prefill the dialog with the values of the original sector
            # select the right countermeasure in the combo (but note that the sectorName can be changed too)
            for i in range(0, self.sector_dlg.combo_countermeasures.count()):
                if edited_sector.counterMeasureId == self.sector_dlg.combo_countermeasures.itemData(i)['id']:
                    self.sector_dlg.combo_countermeasures.setCurrentIndex(i)
                    break
            self.sector_dlg.le_sector_name.setText(edited_sector.sectorName)
            self.sector_dlg.le_direction.setText('{}'.format(self.locale.toString(edited_sector.direction, 'f', 2)))
            self.sector_dlg.le_angle.setText('{}'.format(self.locale.toString(edited_sector.angle, 'f', 2)))
            self.sector_dlg.le_distance.setText('%s' % (self.locale.toString(edited_sector.maxDistance / 1000, 'f', 3)))
            # use can have overridden the color
            self.sector_dlg_set_color(edited_sector.color)
            if edited_sector.minDistance != 0:
                self.sector_dlg.le_min_distance.setText('{}'.format(self.locale.toString(edited_sector.minDistance / 1000, 'f', 3)))
                self.sector_dlg.le_min_distance.setEnabled(True)
                self.sector_dlg.lbl_min_distance.setEnabled(True)
                self.sector_dlg.cb_min_distance.setChecked(True)
            else:
                self.sector_dlg.lbl_min_distance.setEnabled(False)
        self.sector_dlg.combo_countermeasures.setFocus()
        self.sector_dlg_show(edited_sector)

    def sectorplotsetdlg_open_sector_for_edit_dialog(self):
        if len(self.sectorplotset_dlg.table_sectors.selectedIndexes()) > 0:
            sector = self.sectorplotset_dlg.table_sectors.selectedIndexes()[0].data(Qt.UserRole)
            self.sectorplotsetdlg_create_backup()
            self.sectorplotsetdlg_open_new_sector_dialog(True, sector.clone())

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
        self.sectorplotsetdlg_create_sectorset_from_sector_table()

    def sectorplotsetdlg_add_sector_to_table(self, sector, row=-1):
        #self.debug('Adding sector to sector table with row= %s' % row)
        sector_name_item = QStandardItem(sector.sectorName)

        #direction_item = QStandardItem('{:.2f}'.format(sector.direction))
        #angle_item = QStandardItem('{:.2f}'.format(sector.angle))
        #min_distance_item = QStandardItem('{:.3f}'.format(sector.minDistance/1000))
        #distance_item = QStandardItem('{:.3f}'.format(sector.maxDistance/1000))

        direction_item = QStandardItem(self.locale.toString(sector.direction, 'f', 2))
        angle_item = QStandardItem(self.locale.toString(sector.angle, 'f', 2))
        min_distance_item = QStandardItem(self.locale.toString(sector.minDistance/1000, 'f', 3))
        distance_item = QStandardItem(self.locale.toString(sector.maxDistance/1000, 'f', 3))

        countermeasure_item = QStandardItem(self.counter_measures.get(sector.counterMeasureId))
        # attach the sector(data) as data to column 0
        sector_name_item.setData(sector, Qt.UserRole)
        if row < 0:
            # default, just append a fresh sector to the end
            self.sectorplotset_source_model.appendRow([sector_name_item, countermeasure_item, min_distance_item,
                                                       distance_item, direction_item, angle_item])
            # select the last appended row (rowcount -1)
            self.sectorplotset_dlg.table_sectors.selectRow(self.sectorplotset_source_model.rowCount()-1)
        else:
            # update a row from a sector which just has been editted
            self.sectorplotset_source_model.removeRow(row)
            self.sectorplotset_source_model.insertRow(row, [sector_name_item, countermeasure_item, min_distance_item,
                                                       distance_item, direction_item, angle_item])
            # and select it again
            self.sectorplotset_dlg.table_sectors.selectRow(row)
        self.sectorplotsetdlg_create_sectorset_from_sector_table()
        self.sectorplotsetdlg_set_headers()

    def sectorplotsetdlg_remove_sector_from_table(self):
        if len(self.sectorplotset_dlg.table_sectors.selectedIndexes()) > 0:
            self.sectorplotset_source_model.removeRow(self.sectorplotset_dlg.table_sectors.selectedIndexes()[0].row())
            self.sectorplotsetdlg_create_sectorset_from_sector_table()
            self.show_current_sectorplotset_on_map()

    def sector_layer_edited_finished(self):
        '''
        To make it possible that a user edits the geometry (sector) after defining it,
        we listen to the 'layer_edited' signal.

        If received, we define all geometries based on the geometries of the layer!

        Passing a handle of a geometry does not work so we export the geometry from the
        edit buffer as WKT to the sector, where a geometry is created from the wkt
        '''
        for feat in self.sector_layer.getFeatures():
            # actually the z_order is the 'id' of a sector in the sectorset, so use that
            sector = self.current_sectorset.get_sector_by_z_order(feat['z_order'])
            # passing a wkt string to the sector so sector will be responsible for/owner of QgsGeometry creation
            sector.setGeometryFromWkt4326(feat.geometry().asWkt())

    def sectorplotsetdlg_create_sectorset_from_sector_table(self):
        # NOW get the sectors from the model/dialog, put them in a sectorset in the order they are seen in the table.
        # First: create an array with 'None's so we can place the sectors on the right spot in the right order
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
        if self.sectorplotset_dlg.lbl_npp_block.text() is not None or self.sectorplotset_dlg.lbl_npp_block.text() != "":
            self.current_sectorset.setNppBlock(self.sectorplotset_dlg.lbl_npp_block.text())
        # set save time (for the SectorplotSet == for all sectors in it)
        self.current_sectorset.setSaveTime()
        # show the sectorset!
        self.show_current_sectorplotset_on_map()
        try:
            self.pie_layer.selectionChanged.disconnect(self.sector_dlg_pie_sector_select)
        except Exception as e:
            pass
            #log.debug(f'Info: failing to disconnect Pie selection signal (for angle values) {e}')

    def sectorplotsetdlg_show(self):
        self.sectorplotset_dlg.btn_new_sector.setFocus()
        # OK will save to db
        if self.sectorplotset_dlg.exec_():
            self.sectorplotsetdlg_create_sectorset_from_sector_table()
            if self.current_sectorset.name is None or len(self.current_sectorset.name) == 0:
                # no name set, please provide one
                msg = self.tr("You did not provide a name for this Sectorplot. \nPlease provide one.")
                self.msg(self.sectorplotset_dlg, msg)
                self.sectorplotsetdlg_show()
            elif len(self.current_sectorset.sectors) == 0:
                # no name set, please provide one
                msg = self.tr("You did not provide a sector for this Sectorplot. \nPlease provide at least one.")
                self.msg(self.sectorplotset_dlg, msg)
                self.sectorplotsetdlg_show()
            else:
                # NOW we cannot change modification time anymore, so let's get it from the dialog and set it
                # format: "%Y-%m-%d %H:%M:%S"
                time = self.sectorplotset_dlg.time_edit_countermeasure.time()  # QTime
                date = self.sectorplotset_dlg.date_edit_countermeasure.date()  # QDate
                datetime = QDateTime(date, time)
                #self.msg(None, datetime.toString("yyyy-MM-dd HH:mm:00"))
                self.current_sectorset.setCounterMeasureTime(datetime.toString("yyyy-MM-dd HH:mm:00"))
                # save the sectors to DB and retrieve id of sectorplotset
                db_ok, result = self.current_sectorset.exportToDatabase()
                # save the pie to DB
                if db_ok:
                    self.current_pie.set_sectorset_id(self.current_sectorset.setId)
                db_ok2, result2 = self.current_pie.exportToDatabase()
                if (db_ok and db_ok2):
                    # (re)open sectorplotlist_dialog on row with just saved id BUT without pie
                    self.current_pie = None
                    # if OK exportToDatabase returns the inserted id
                    self.sectorplotsetsdlg_open_dialog(result)
                elif self.DEMO:
                    self.msg(self.sectorplotset_dlg, self.tr("Demo mode\nSectorplot is not saved to WMS or Database"))
                else:
                    # if NOT OK exportToDatabase returns the database error
                    # self.msg(self.sectorplotset_dlg, self.tr("Database error:\n %s") % result)
                    self.msg(self.sectorplotset_dlg, self.tr("Database error:\n %s") % result)
        else:
            self.current_sectorset = None
            self.current_pie = None
            # go back to (old) selected one, IF there was one selected
            # NOPE: not doing that anymore, just start over please...
            #if len(self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()) > 0:
            #    self.current_sectorset = self.sectorplotsets_dlg.table_sectorplot_sets.selectedIndexes()[0].data(Qt.UserRole)
            self.show_current_sectorplotset_on_map()

    def sector_dlg_enable_min_distance(self):
        self.sector_dlg.le_min_distance.setEnabled(self.sector_dlg.cb_min_distance.isChecked())
        # set to zero back if set back
        if self.sector_dlg.cb_min_distance.isChecked() is False:
            self.sector_dlg.le_min_distance.setText("0")
            self.sector_dlg.le_sector_name.setFocus()
            self.sector_dlg.lbl_min_distance.setEnabled(False)
        else:
            self.sector_dlg.lbl_min_distance.setEnabled(True)
            self.sector_dlg.le_min_distance.setFocus()

    def sector_dlg_btn_color_clicked(self):
        color = QColorDialog.getColor()
        # name() returns a html/hex color without alpha: #ff0000
        self.sector_dlg_set_color(color.name())

    def sector_dlg_set_color(self, html_color="#ff0000"):
        color = QColor(html_color)
        # colors in Qt styles are in 0-255 notation if you want to use opacity, we have to add it
        color.setAlpha(self.ALPHA)
        style = "QLineEdit { background: rgba(%s, %s, %s, %s); }" % (color.red(), color.green(), color.blue(), color.alpha())
        self.sector_dlg.le_color.setStyleSheet(style)
        # to have #rrggbbaa notation:  color.name()+hex(color.alpha())[2:]
        self.sector_dlg.le_color.setText(color.name())

    def sector_dlg_countermeasure_selected(self):
        countermeasure = self.sector_dlg.combo_countermeasures.itemData(self.sector_dlg.combo_countermeasures.currentIndex())
        # default: put countermeasure text in sector name. Category 'overig' is to be set by the user!!
        self.sector_dlg.le_sector_name.setText(countermeasure['text'])
        self.sector_dlg_set_color(countermeasure['color'])

    def sector_dlg_pie_sector_select(self):
        # find all selectied PIE-sectors
        selected_features = self.get_pie_layer().selectedFeatures()
        #log.debug("Pie select, # of selectedFeatures: {}".format(len(selected_features)))
        min_distance = 0
        smallest_distance = sys.maxsize
        for feature in selected_features:
            # self.debug("selectedfeature attributes: %s" % feature.attributes())
            # really do not know, but clicking a second feature by using the CTRL-button
            # one of the returned selected features will have zero attributes....
            # not sure where this comes from, but with this if we are sure to handle this...
            if len(feature.attributes()) > 0:
                arr = feature['sectorname'].split('|')
                if len(arr) == 4:
                    # trying to find the feature with smallest distance
                    # because we sometimes select several features
                    d = int(float(arr[3]) / 1000)
                    if d < smallest_distance:
                        smallest_distance = d
                        direction = self.locale.toString(float(arr[0]))
                        angle = self.locale.toString(float(arr[1]))
                        #min_distance = float(arr[2])/1000)
                        max_distance = self.locale.toString(float(arr[3])/1000)

                        self.sector_dlg.le_direction.setText('%s' % direction)
                        self.sector_dlg.le_angle.setText('%s' % angle)
                        if min_distance > 0:
                            self.sector_dlg.le_min_distance.setEnabled(True)
                            self.sector_dlg.le_min_distance.setText('%s' % min_distance)
                        self.sector_dlg.le_distance.setText('%s' % max_distance)
                        self.sector_dlg_preview()
            #break
        # setHidden does NOT work because it silently OK/Cancels the Dialog
        #self.sector_dlg.setHidden(True)
        #self.sector_dlg.setHidden(False)
        self.sector_dlg.activateWindow()  # YES this works, also on Windows

    def sector_dlg_sector_is_ok(self):
        acceptable = QDoubleValidator.Acceptable  #  0=invalid, 1=intermediate, 2=acceptable
        problem = None

        # check if at least all fields are filled, else silently return False
        if self.sector_dlg.le_direction.text() == '' or self.sector_dlg.le_angle.text() == '' \
                or self.sector_dlg.le_distance.text() == '':
            # ok all are at least filled...
            problem = self.tr("Empty field(s) found, please fill them all.")
            log.debug(problem)
        # check direction
        elif self.degree_validator.validate(self.sector_dlg.le_direction.text(), 0)[0] != acceptable:
            problem = self.tr('The Direction value is not valid: {} \nValid between: [{} - {}].\nPlease check and correct.\nExample number format: {}') \
                .format(
                  self.sector_dlg.le_direction.text(),
                  self.locale.toString(self.degree_validator.bottom(), 'f', 2),
                  self.locale.toString(self.degree_validator.top(), 'f', 2),
                  self.locale.toString(75.505, 'f', 2))
            log.debug(problem)
        # check angle
        elif self.positive_degree_validator.validate(self.sector_dlg.le_angle.text(), 0)[0] != acceptable:
            problem = self.tr('The Angle value is not valid: {} \nValid between: [{} - {}].\nPlease check and correct.\nExample number format: {}') \
                .format(
                  self.sector_dlg.le_angle.text(),
                  self.locale.toString(self.positive_degree_validator.bottom(), 'f', 2),
                  self.locale.toString(self.positive_degree_validator.top(), 'f', 2),
                  self.locale.toString(52.522, 'f', 2))
            log.debug(problem)
        # check max distance
        elif self.distance_validator.validate(self.sector_dlg.le_distance.text(), 0)[0] != acceptable:
            problem = self.tr('The Distance value is not valid: {} \nValid between: [{} - {}].\nPlease check and correct.\nExample number format: {}') \
                .format(
                  self.sector_dlg.le_distance.text(),
                  self.locale.toString(self.distance_validator.bottom(), 'f', 3),
                  self.locale.toString(self.distance_validator.top(), 'f', 3),
                  self.locale.toString(7.553, 'f', 3)
                )
            log.debug(problem)
        # check min distance
        elif self.min_distance_validator.validate(self.sector_dlg.le_min_distance.text(), 0)[0] != acceptable:
            problem = self.tr('The Min Distance value is not valid {} \nValid between: [{} - {}].\nPlease check and correct.\nExample number format: {}') \
                .format(
                  self.sector_dlg.le_min_distance.text(),
                  self.locale.toString(self.min_distance_validator.bottom(), 'f', 3),
                  self.locale.toString(self.min_distance_validator.top(), 'f', 3),
                self.locale.toString(2.123, 'f', 3),
                )
            log.debug(problem)
        # check if min_distance < then distance
        elif self.locale.toFloat(self.sector_dlg.le_min_distance.text())[0] >= self.locale.toFloat(self.sector_dlg.le_distance.text())[0]:
            problem = self.tr(
                'The Min Distance value is not valid. \nMin Distance value is bigger then Distance value:\n{} >= {}\n' +
                ' Please check and correct.\nExample number format: {}').format(
                     self.locale.toFloat(self.sector_dlg.le_min_distance.text())[0],
                     self.locale.toFloat(self.sector_dlg.le_distance.text())[0],
                     self.locale.toString(2.755, 'f', 3)
                )
            log.debug(problem)
        if problem is not None:
            self.msg(None, problem)
            return False
        else:
            return True

    def sector_dlg_sector_create(self):
        # OK, all seems fine. let's create a sector and add it to the sector table
        countermeasure = \
            self.sector_dlg.combo_countermeasures.itemData(self.sector_dlg.combo_countermeasures.currentIndex())
        # countermeasureid and (default) color from dropdown
        countermeasure_id = countermeasure['id']
        color = self.sector_dlg.le_color.text()

        lon = self.current_sectorset.lon # self.locale.toFloat(self.current_sectorset.lon)[0]
        lat = self.current_sectorset.lat # self.locale.toFloat(self.current_sectorset.lat)[0]

        direction = self.locale.toFloat(self.sector_dlg.le_direction.text())[0]  # toFloat returns tuple like (60,0 True)
        #log.debug('direction {}'.format(direction))
        angle = self.locale.toFloat(self.sector_dlg.le_angle.text())[0]
        distance = self.locale.toFloat(self.sector_dlg.le_distance.text())[0]
        min_distance = self.locale.toFloat(self.sector_dlg.le_min_distance.text())[0]
        sector_name = self.sector_dlg.le_sector_name.text()
        new_sector = Sector(lon=lon,
                            lat=lat,
                            minDistance=1000 * float(min_distance),
                            maxDistance=1000 * float(distance),
                            direction=direction,
                            angle=angle,
                            counterMeasureId=countermeasure_id,
                            sectorName=sector_name,
                            color=color)
        # new sector or editing an excisting one?
        # if we have an old_sector in the set dialog (== we had a selected one), select it again
        row = -1  # -1 means append it as last sector in the table
        if len(self.sectorplotset_dlg.table_sectors.selectedIndexes()) > 0:
            row = self.sectorplotset_dlg.table_sectors.selectedIndexes()[0].row()
        self.sectorplotsetdlg_add_sector_to_table(new_sector, row)

    def sector_dlg_preview(self):
        if self.sector_dlg_sector_is_ok():
            self.sector_dlg_sector_create()

    def sector_dlg_show(self, old_sector=None):
        #self.debug('sector_dlg_show with old sector = %s' % old_sector)
        self.iface.layerTreeView().setCurrentLayer(self.get_pie_layer())  # make pie_layer current for selections
        self.iface.actionSelect().trigger()  # activate the selecttool

        if self.sector_dlg.exec_():   # exec_ also SHOWS the dialog!
            # OK pressed in Sector dialog(!)
            # do some checking...
            if not self.sector_dlg_sector_is_ok():
                # mmm, one of the validators failed: reopen the sector_dlg after the msg was OK'ed
                # self.sector_dlg_show(old_sector) # nope: recursive calls HELL!
                self.iface.layerTreeView().setCurrentLayer(self.get_pie_layer())  # make pie_layer current for selections
                self.iface.actionSelect().trigger()  # activate the selecttool
                self.sector_dlg.show()
                return
            else:
                self.sector_dlg_sector_create()  # if all ok ALSO shows preview
        else:
            # user canceled dialog
            # set the data of the selected row BACK to the old_sector (original sector)
            self.sectorplotset_dlg.table_sectors.model().clear()
            row = 0
            for sector in self.sector_dlg.old_sectors:
                self.sectorplotsetdlg_add_sector_to_table(sector, row)
                row = row + 1
            # repaint restored state
            self.sectorplotsetdlg_create_sectorset_from_sector_table()
        self.sectorplotset_dlg.table_sectors.clearSelection()
        self.iface.actionPan().trigger()  # just want to disable selection tool... by activating Panning tool...

    def settingsdlg_test_postgis_clicked(self):
        db = Database('sectorplot')
        test_ok = db.test_connection(self.settings_dlg.postgis_host.text(),
                                     self.settings_dlg.postgis_database.text(),
                                     self.settings_dlg.postgis_user.text(),
                                     self.settings_dlg.postgis_password.text())
        if test_ok:
            self.msg(self.settings_dlg, self.tr('Connection successful'))
        else:
            self.msg(self.settings_dlg, self.tr('Connection problem, please check inputs'))

    def settingsdlg_test_geoserver_clicked(self):
        rc = RestClient('sectorplot')
        test_ok = rc.test_connection(self.settings_dlg.geoserver_url.text(),
                                     self.settings_dlg.geoserver_user.text(),
                                     self.settings_dlg.geoserver_password.text())
        if test_ok:
            self.msg(self.settings_dlg, self.tr('Connection successful'))
        else:
            self.msg(self.settings_dlg, self.tr('Connection problem, please check inputs'))

    def settingsdlg_test_jrodos_clicked(self):
        try:
            url = self.settings_dlg.jrodos_rest_url.text()
            NppSet(url)
            self.msg(self.settings_dlg, self.tr('Connection successful'))
        except:
            self.msg(self.settings_dlg, self.tr('Connection problem, please check inputs'))

    def settingsdlg_show(self):
        self.settings_dlg.exec_()

    #def debug(self, s):
    #    QgsMessageLog.logMessage('%s' % s, tag="SectorPlot Debug", level=Qgis.Info)


class GetPointTool(QgsMapTool):

    def __init__(self, canvas, callback):
        QgsMapTool.__init__(self, canvas)
        self.callback = callback
        self.pos = None
        # self.canvas = canvas
        self.cursor = QCursor(QPixmap(["16 16 4 1", "  c None", ". c #000000", "+ c #FFFFFF", "- c #FF0000",
                                    "                ",
                                    "       +.+      ",
                                    "      ++.++     ",
                                    "     +.....+    ",
                                    "    +.     .+   ",
                                    "   +.   .   .+  ",
                                    "  +.    .    .+ ",
                                    " ++.    -    .++",
                                    " ... ..---.. ...",
                                    " ++.    -    .++",
                                    "  +.    .    .+ ",
                                    "   +.   .   .+  ",
                                    "   ++.     .+   ",
                                    "    ++.....+    ",
                                    "      ++.++     ",
                                    "       +.+      "]))

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.pos = self.toMapCoordinates(e.pos())

    def canvasReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.callback(self.pos)

    def activate(self):
        self.canvas().setCursor(self.cursor)

    def deactivate(self):
        self.pos = None
