import os

from PyQt4 import QtGui, uic
from sectorplot_settings import SectorPlotSettings
from qgissettingmanager import SettingDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sectorplot_settings_dialog_base.ui'))


class SectorPlotSettingsDialog(QtGui.QDialog, FORM_CLASS, SettingDialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(SectorPlotSettingsDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.settings = SectorPlotSettings()
        SettingDialog.__init__(self, self.settings)
