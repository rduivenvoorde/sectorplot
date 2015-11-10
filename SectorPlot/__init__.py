# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SectorPlot
                                 A QGIS plugin
 Plots sector areas s on risk management map
                             -------------------
        begin                : 2015-11-10
        copyright            : (C) 2015 by RIVM
        email                : marnix.de.ridder@rivm.nl
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SectorPlot class from file SectorPlot.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .sectorplot import SectorPlot
    return SectorPlot(iface)
