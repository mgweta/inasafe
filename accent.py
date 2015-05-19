# coding=utf-8
"""
InaSAFE Disaster risk assessment tool developed by AusAid -
**CLI implementation for inasafe project.**

Contact : jannes@kartoza.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'Jannes Engelbrecht'
__date__ = '16/04/15'

usage = r""
usage_file = file('usage.txt')
for delta in usage_file:
    usage += delta


import docopt

# noinspection PyPackageRequirements
#from PyQt4 import QtGui

from safe.impact_functions.registry import Registry
from safe.impact_functions import register_impact_functions
from safe.test.utilities import test_data_path #get_qgis_app
from safe.impact_functions.impact_function_manager import ImpactFunctionManager
from qgis.core import (
    QgsRasterLayer,
    QgsRaster,
    QgsPoint,
    QgsVectorLayer,
    QgsRectangle)
import os
import sys
#from safe.utilities.analysis import Analysis
import pydevd
import logging
LOGGER = logging.getLogger('InaSAFE')

# arguments/options
output_file = None
hazard = None
exposure = None
version = None
show_list = None
extent = None

# directories
default_dir = os.path.abspath(os.path.join(
    os.path.realpath(os.path.dirname(__file__)), 'cli'))


def get_ifunction_list():
    registry = Registry()
    return registry.impact_functions


def show_names(ifs):
    for impact_function in ifs:
        print impact_function.__name__


def get_qgis_app():
    LOGGER.debug('-- get qgis app --')
    """ Start one QGIS application.

    :returns: Handle to QGIS app, canvas, iface and parent. If there are any
        errors the tuple members will be returned as None.
    :rtype: (QgsApplication, CANVAS, IFACE, PARENT)

    If QGIS is already running the handle to that app will be returned.
    """

    try:
        from qgis.core import QgsApplication
        from qgis.gui import QgsMapCanvas  # pylint: disable=no-name-in-module
        # noinspection PyPackageRequirements
        from PyQt4 import QtGui, QtCore  # pylint: disable=W0621
        # noinspection PyPackageRequirements
        from PyQt4.QtCore import QCoreApplication, QSettings
        from safe.gis.qgis_interface import QgisInterface
    except ImportError:
        return None, None, None, None

    global QGIS_APP  # pylint: disable=W0603

    gui_flag = True  # All test will run qgis in gui mode

    # AG: For testing purposes, we use our own configuration file instead
    # of using the QGIS apps conf of the host
    # noinspection PyCallByClass,PyArgumentList
    QCoreApplication.setOrganizationName('QGIS')
    # noinspection PyCallByClass,PyArgumentList
    QCoreApplication.setOrganizationDomain('qgis.org')
    # noinspection PyCallByClass,PyArgumentList
    QCoreApplication.setApplicationName('CLI')

    # noinspection PyPep8Naming
    QGIS_APP = QgsApplication(sys.argv, gui_flag)

    # Make sure QGIS_PREFIX_PATH is set in your env if needed!
    QGIS_APP.initQgis()
    s = QGIS_APP.showSettings()
    LOGGER.debug(s)

    # Save some settings
    settings = QSettings()
    settings.setValue('locale/overrideFlag', True)
    settings.setValue('locale/userLocale', 'en_US')

    global PARENT  # pylint: disable=W0603
    # noinspection PyPep8Naming
    PARENT = QtGui.QWidget()

    global CANVAS  # pylint: disable=W0603
    # noinspection PyPep8Naming
    CANVAS = QgsMapCanvas(PARENT)
    CANVAS.resize(QtCore.QSize(400, 400))

    global IFACE  # pylint: disable=W0603
    # QgisInterface is a stub implementation of the QGIS plugin interface
    # noinspection PyPep8Naming
    IFACE = QgisInterface(CANVAS)
    register_impact_functions()

    return QGIS_APP, CANVAS, IFACE, PARENT


def run_if():
    QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()
    HAZARD_BASE = test_data_path(default_dir, 'hazard', 'continuous_flood_20_20')
    LOGGER.debug(HAZARD_BASE)
    qhazard = QgsRasterLayer(HAZARD_BASE + '.asc')
    # noinspection PyUnresolvedReferences
    #if not qhazard.isValid():
    #    print message
    hazard_extent = qhazard.extent()
    LOGGER.debug('hazard_extent')
    LOGGER.debug(hazard_extent)
    LOGGER.debug(qhazard.width())
    EXPOSURE_BASE = test_data_path(default_dir, 'exposure', 'buildings')
    LOGGER.debug(EXPOSURE_BASE)
    qexposure = QgsVectorLayer(EXPOSURE_BASE + '.shp')
    # noinspection PyUnresolvedReferences
    exposure_extent = qexposure.extent()
    LOGGER.debug('exposure_extent')
    LOGGER.debug(exposure_extent)
    try:
        from safe.utilities.analysis import Analysis
        LOGGER.debug('imported')
    except ImportError:
        LOGGER.debug('**except** :(')
        return None, None, None, None
    analysis = Analysis()
    # Layers
    analysis.hazard_layer = qhazard
    analysis.exposure_layer = qexposure
    # IF
    impact_function_manager = ImpactFunctionManager()
    impact_function = impact_function_manager.get(
        arguments['--impact-function'])
    LOGGER.debug(arguments['--impact-function'])

    analysis.user_extent(
        106.8054130000000015, -6.1913361000000000,
        106.8380719000000028, -6.1672457999999999)
    analysis.impact_function = impact_function
    LOGGER.debug(analysis)
    analysis.setup_analysis()
    LOGGER.debug('eeee')
    analysis.run_analysis()
    LOGGER.debug("end :)")


if __name__ == '__main__':
    LOGGER.debug("main")
    print "python accent.py"
    print ""

    # setup functions
    register_impact_functions()
    # globals
    output_file = None
    hazard = None
    exposure = None
    version = None
    show_list = None
    extent = None
    pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)
    try:
        # Parse arguments, use file docstring as a parameter definition
        arguments = docopt.docopt(usage)
        output_file = arguments['FILE']
        hazard = arguments['--hazard']
        exposure = arguments['--exposure']
        version = arguments['--version']
        show_list = arguments['--list-functions']
        extent = arguments['--extent']
        LOGGER.debug(arguments)
    # Handle invalid options
    except docopt.DocoptExit as e:
        print e.message

    if show_list:
        show_names(get_ifunction_list())

    elif (extent is not None) and\
            (hazard is not None) and\
            (exposure is not None):
        LOGGER.debug('--do an IF--')
        run_if()
        LOGGER.debug('-- just did an IF--')

