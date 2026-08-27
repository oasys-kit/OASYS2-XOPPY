import sys
import os

import numpy

import scipy.constants as codata

from AnyQt.QtWidgets import QMessageBox, QSizePolicy

from orangewidget import gui
from orangewidget.settings import Setting

from orangewidget.widget import MultiInput, Input
from oasys2.widget import gui as oasysgui
from oasys2.widget.gui import ConfirmDialog
from oasys2.widget.util import congruence
from oasys2.widget.util.exchange import DataExchangeObject
from oasys2.widget.util.widget_objects import OasysSurfaceData
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.xoppy.widgets.gui.ow_xoppy_widget_dabax import XoppyWidgetDabax

from xoppylib.power.power3d import integral_2d, integral_3d, info_total_power
from xoppylib.power.power3d import calculate_component_absorbance_and_transmittance, apply_transmittance_to_incident_beam
from xoppylib.power.power3d import load_radiation_from_h5file, write_radiation_to_h5file, write_txt_file, write_h5_file

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.optical_elements.absorbers.filter import Filter
from syned.beamline.optical_elements.absorbers.slit import Slit
from syned.beamline.optical_elements.mirrors.mirror import Mirror
from syned.beamline.beamline import Beamline
from syned.beamline.shape import Rectangle

try: import xraylib
except: pass

from dabax.dabax_xraylib import DabaxXraylib
from dabax.dabax_files import dabax_f1f2_files, dabax_crosssec_files

class OWpower3Dcomponent(XoppyWidgetDabax, WidgetDecorator):
    name = "Power3Dcomponent"
    id = "orange.widgets.datapower3D"
    description = "Power (vs Energy and spatial coordinates) Absorbed and Transmitted or Reflected by Optical Elements"
    icon = "icons/xoppy_power3d.png"
    priority = 3
    category = ""
    keywords = ["xoppy", "Undulator Radiation", "power3Dcomponent"]

    class Inputs:
        exchange_data      = MultiInput("Exchange Data", DataExchangeObject, default=True, auto_summary=False)
        syned_data         = WidgetDecorator.syned_input_data(multi_input=True)
        surface_data_front = MultiInput("Oasys Surface Data Front", OasysSurfaceData, default=True, auto_summary=False)
        surface_data_back  = MultiInput("Oasys Surface Data Back", OasysSurfaceData, default=True, auto_summary=False)

    INPUT_BEAM_FROM = Setting(0)
    INPUT_BEAM_FILE = Setting("undulator_radiation.h5")

    EL1_FOR = Setting("Be")
    EL1_FLAG = Setting(0)  # 0=Filter 1=Mirror 2=Aperture 3=magnifier, 4=Screen rotation  5=Thin object  6=Multilayer 7=External file
    EL1_THI = Setting(0.5)
    EL1_ANG = Setting(3.0)
    EL1_DEF = Setting(1) # deflection 0=H 1=V
    EL1_ROU = Setting(0.0)
    EL1_DEN = Setting("?")
    EL1_GAPSHAPE = Setting(0)
    EL1_HGAP = Setting(1000.0)
    EL1_VGAP = Setting(1000.0)
    EL1_HGAPCENTER = Setting(0.0)
    EL1_VGAPCENTER = Setting(0.0)
    EL1_HMAG = Setting(1.0)
    EL1_VMAG = Setting(1.0)
    EL1_HROT = Setting(0.0)
    EL1_VROT = Setting(0.0)
    thin_object_file = Setting('<none>')
    thin_object_thickness_outside_file_area = Setting(0.0)
    thin_object_back_profile_flag = Setting(0)
    thin_object_back_profile_file = Setting('<none>')
    multilayer_file = Setting('<none>')
    external_reflectivity_file = Setting('<none>')

    PLOT_SETS = Setting(1)

    FILE_INPUT_FLAG = Setting(0)
    FILE_INPUT_NAME = Setting("power3Dcomponent_in.h5")
    FILE_DUMP = Setting(0)
    FILE_NAME = Setting("power3Dcomponent.h5")
    EL1_SLIT_CROP = Setting(0)
    INTERPOLATION_FLAG = Setting(0)
    INTERPOLATION_FACTOR_H = Setting(1.0)
    INTERPOLATION_FACTOR_V = Setting(1.0)



    def __init__(self):
        super().__init__(show_script_tab=True)

    def dabax_show_f1f2(self):
        return True

    def dabax_show_crosssec(self):
        return True

    def build_gui(self):

        self.left_side.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.left_side.setMaximumWidth(self.CONTROL_AREA_WIDTH + 20)
        self.left_side.updateGeometry()

        ###########
        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)
        tab_1 = oasysgui.createTabPage(tabs_setting, "Input Parameters")
        tab_2 = oasysgui.createTabPage(tabs_setting, "Send Settings")
        self.tab_dabax = oasysgui.createTabPage(tabs_setting, "Materials Library")
        ###########

        box = oasysgui.widgetBox(tab_1, self.name + " Input Parameters", orientation="vertical",width=self.CONTROL_AREA_WIDTH-10)

        idx = -1
        box11 = gui.widgetBox(box, "Input beam")

        #widget index 12
        idx += 1
        box1 = gui.widgetBox(box11)
        gui.comboBox(box1, self, "INPUT_BEAM_FROM",
                    label=self.unitLabels()[idx],
                    items=['Oasys wire','h5 file (from undulator_radiation)'],
                     orientation="horizontal", callback=self.visibility_input_file, labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index 12 ***********   File Browser ******************
        idx += 1
        box1 = gui.widgetBox(box11)
        self.file_box_id = oasysgui.widgetBox(box1, "", addSpace=False, orientation="horizontal")
        self.file_id = oasysgui.lineEdit(self.file_box_id, self, "INPUT_BEAM_FILE", "File hdf5",
                                    labelWidth=100, valueType=str, orientation="horizontal")
        gui.button(self.file_box_id, self, "...", callback=self.select_input_file, width=25)


        #
        box11 = gui.widgetBox(box, "Optical element")
        #widget index 12
        idx += 1
        box1 = gui.widgetBox(box11)
        gui.comboBox(box1, self, "EL1_FLAG",
                    label=self.unitLabels()[idx],
                    items=['Filter', 'Mirror','Aperture','Magnifier','Screen Rotation',"Thin object filter","Multilayer","Reflectivity from file"],
                     orientation="horizontal", callback=self.set_EL_FLAG, labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index 11
        idx += 1
        box1 = gui.widgetBox(box11)
        gui.separator(box1, height=7)
        oasysgui.lineEdit(box1, self, "EL1_FOR",
                     label=self.unitLabels()[idx], addSpace=False, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)


        list_w = ["EL1_THI", "EL1_ANG", "EL1_DEF", "EL1_ROU", "EL1_DEN", "multilayer_file", "external_reflectivity_file",
                  "EL1_GAPSHAPE", "EL1_HGAP", "EL1_VGAP", "EL1_HGAPCENTER", "EL1_VGAPCENTER",
                  "EL1_HMAG", "EL1_VMAG",
                  "EL1_HROT", "EL1_VROT",
                  "thin_object_file", "thin_object_thickness_outside_file_area", "thin_object_back_profile_flag", "thin_object_back_profile_file",
                  ]

        for el in list_w:
            idx += 1
            box1 = gui.widgetBox(box11)
            if el == "EL1_DEF":
                gui.comboBox(box1, self, el,
                             label=self.unitLabels()[idx],
                             items=['Horizontal',
                                    'Vertical'],
                              orientation="horizontal", labelWidth=250)
            elif el == "EL1_GAPSHAPE":
                gui.comboBox(box1, self, el,
                             label=self.unitLabels()[idx],
                             items=['Rectangle',
                                    'Ellipse'],
                              orientation="horizontal", labelWidth=250)
            elif el == "thin_object_back_profile_flag":
                gui.comboBox(box1, self, el,
                             label=self.unitLabels()[idx],
                             items=['zero',
                                    'from h5 file'],
                              orientation="horizontal", labelWidth=250)
            elif el in ["EL1_DEN", "thin_object_file", "thin_object_back_profile_file"]:
                oasysgui.lineEdit(box1, self, el,
                                  label=self.unitLabels()[idx], addSpace=False,
                                  valueType=str, orientation="horizontal", labelWidth=250)
            elif el in ["multilayer_file"]:
                oasysgui.lineEdit(box1, self, el,
                                  label=self.unitLabels()[idx], addSpace=False,
                                  valueType=str, orientation="horizontal", labelWidth=200)
            elif el in ["external_reflectivity_file"]:
                oasysgui.lineEdit(box1, self, el,
                                  label=self.unitLabels()[idx], addSpace=False,
                                  valueType=str, orientation="horizontal", labelWidth=200)
            else:
                oasysgui.lineEdit(box1, self, el,
                                  label=self.unitLabels()[idx], addSpace=False,
                                  valueType=float, orientation="horizontal", labelWidth=250)
            self.show_at(self.unitFlags()[idx], box1)


        box = gui.widgetBox(tab_1, "Presentation")
        #widget index 41
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)

        gui.comboBox(box1, self, "PLOT_SETS",
                    label=self.unitLabels()[idx],
                    items=['Input Beam',
                           'Element transmittance and absorbance',
                           'Absorbed by element',
                           'Transmitted/reflected by element'],
                     orientation="horizontal", labelWidth=100, callback=self.replot_results)
        self.show_at(self.unitFlags()[idx], box1)

        ##
        box = gui.widgetBox(tab_2, "Files")
        #################

        #widget index xx
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)
        gui.comboBox(box1, self, "FILE_INPUT_FLAG",
                     label=self.unitLabels()[idx],
                    items=['No', 'Yes (hdf5)'],
                    orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index xx
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)
        oasysgui.lineEdit(box1, self, "FILE_INPUT_NAME",
                     label=self.unitLabels()[idx], addSpace=False, orientation="horizontal", labelWidth=150)
        self.show_at(self.unitFlags()[idx], box1)
        # self.visibility_input_file()


        #################


        #widget index xx
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)

        gui.comboBox(box1, self, "FILE_DUMP",
                     label=self.unitLabels()[idx],
                    items=['No', 'Yes (hdf5)',
                           'Yes (x,y,absorbed)', 'Yes (absorbed matrix)',
                           'Yes (x,y,transmitted)', 'Yes (transmitted matrix)'],
                    orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index xx
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)
        oasysgui.lineEdit(box1, self, "FILE_NAME",
                     label=self.unitLabels()[idx], addSpace=False, orientation="horizontal", labelWidth=150)
        self.show_at(self.unitFlags()[idx], box1)
        self.visibility_input_file()


        ##
        box = gui.widgetBox(tab_2, "Send beam")
        #widget index 12
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)
        gui.comboBox(box1, self, "EL1_SLIT_CROP",
                     label=self.unitLabels()[idx],
                     items=['No',
                            'Yes'],
                     orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index XX
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)
        gui.comboBox(box1, self, "INTERPOLATION_FLAG",
                     label=self.unitLabels()[idx],
                     items=['No',
                            'Yes'],
                     orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index XX
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)
        oasysgui.lineEdit(box1, self, "INTERPOLATION_FACTOR_H",
                          label=self.unitLabels()[idx], addSpace=False,
                          valueType=float, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index XX
        idx += 1
        box1 = gui.widgetBox(box)
        gui.separator(box1, height=7)
        oasysgui.lineEdit(box1, self, "INTERPOLATION_FACTOR_V",
                          label=self.unitLabels()[idx], addSpace=False,
                          valueType=float, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)


    def set_EL_FLAG(self):
        self.initializeTabs()

    def unitLabels(self):
        labels = []
        labels.append('input beam from:')
        labels.append('input beam file:')
        labels.append('optical element is:')
        labels.append('formula: ')
        labels.append('Filter thick[mm]')
        labels.append('Grazing angle[mrad]')
        labels.append('Component deflection')
        labels.append('Roughness[A]')
        labels.append('Density [g/cm^3]')
        labels.append('File from xoppy/Multilayer')
        labels.append('File with reflectivity vs E')
        labels.append('Aperture shape')
        labels.append('H Size/Gap [mm]')
        labels.append('V Size/Gap [mm]')
        labels.append('H Center/Gap [mm]')
        labels.append('V Center/Gap [mm]')
        labels.append('H Magnification')
        labels.append('V Magnification')
        labels.append('Rotation angle around H axis [deg]')
        labels.append('Rotation angle around V axis [deg]')
        labels.append('File with FRONT profile z(x,y)')
        labels.append('Front profile z outside file definition')
        labels.append('Back profile z(x,y)')
        labels.append('File with BACK profile z(x,y)')



        labels.append("Plot")
        labels.append("Write input beam")
        labels.append("Input beam filename [.h5]")
        labels.append("Write output file")
        labels.append("File name")
        labels.append('Crop beam before being sent')
        labels.append('Interpolate output radiation?')
        labels.append('Interpolate H factor (default=1.0)')
        labels.append('Interpolate V factor (default=1.0)')

        return labels

    def unitFlags(self):
        flags =  []
        flags.append('True')  # input from
        flags.append('self.INPUT_BEAM_FROM  ==  1')  # input file
        flags.append('True')                   # kind
        flags.append('self.EL1_FLAG  in  (0, 1, 5)')   # formula
        flags.append('self.EL1_FLAG  ==  0')   # thickness
        flags.append('self.EL1_FLAG  in  (1, 6)')   # angle
        flags.append('self.EL1_FLAG  in  (1, 6)')   # mirror deflection
        flags.append('self.EL1_FLAG  ==  1')   # roughness
        flags.append('self.EL1_FLAG  in  (0, 1, 5)')   # density
        flags.append('self.EL1_FLAG  == 6')  # multilayer file
        flags.append('self.EL1_FLAG  == 7')   # file with external reflectivity
        flags.append('self.EL1_FLAG  in (0, 1, 2, 6, 7)')  # gap shape
        flags.append('self.EL1_FLAG  in (0, 1, 2, 6, 7)')   # gap
        flags.append('self.EL1_FLAG  in (0, 1, 2, 6, 7)')   # gap
        flags.append('self.EL1_FLAG  in (0, 1, 2, 6, 7)')   # gap center
        flags.append('self.EL1_FLAG  in (0, 1, 2, 6, 7)')   # gap center
        flags.append('self.EL1_FLAG  ==  3')   # magnification
        flags.append('self.EL1_FLAG  ==  3')   # magnification
        flags.append('self.EL1_FLAG  in (0, 4, 7)')   # rotation
        flags.append('self.EL1_FLAG  in (0, 4, 7)')   # rotation
        flags.append('self.EL1_FLAG  == 5')   # thin object thickness
        flags.append('self.EL1_FLAG  == 5')   # thin object thickness
        flags.append('self.EL1_FLAG  == 5')   # thin object back profile flag
        flags.append('self.EL1_FLAG  == 5 and self.thin_object_back_profile_flag == 1')   # thin object back profile file
        flags.append("True")  # plot
        flags.append("True")
        flags.append('self.FILE_INPUT_FLAG >= 1')
        flags.append("True")
        flags.append('self.FILE_DUMP >= 1')
        flags.append('self.EL1_FLAG  ==  2')   # slit crop
        flags.append('True')   # interpolate flag
        flags.append('self.INTERPOLATION_FLAG  ==  1')   # interpolate factor H
        flags.append('self.INTERPOLATION_FLAG  ==  1')   # interpolate factor V
        return flags

    def get_help_name(self):
        return 'power3dcomponent'


    @Inputs.surface_data_front
    def set_surface_data_front(self, index, surface_data_front):
        self.set_input_surface_data_front(surface_data_front)

    @Inputs.surface_data_front.insert
    def insert_surface_data_front(self, index, surface_data_front):
        self.set_input_surface_data_front(surface_data_front)

    @Inputs.surface_data_front.remove
    def remove_surface_data_front(self, index):
        pass

    def set_input_surface_data_front(self, surface_data):
        if isinstance(surface_data, OasysSurfaceData):
            self.EL1_FLAG = 5
            self.thin_object_file = surface_data.surface_data_file
            self.thin_object_thickness_outside_file_area = 0.0
        else:
            raise Exception("Wrong surface_data")

    @Inputs.surface_data_back
    def set_surface_data_back(self, index, surface_data_back):
        self.set_input_surface_data_back(surface_data_back)

    @Inputs.surface_data_back.insert
    def insert_surface_data_back(self, index, surface_data_back):
        self.set_input_surface_data_back(surface_data_back)

    @Inputs.surface_data_back.remove
    def remove_surface_data_back(self, index):
        pass

    def set_input_surface_data_back(self, surface_data):
        if isinstance(surface_data, OasysSurfaceData):
            self.EL1_FLAG = 5
            self.thin_object_back_profile_flag= 1
            self.thin_object_back_profile_file= surface_data.surface_data_file
        else:
            raise Exception("Wrong surface_data")

    @Inputs.exchange_data
    def set_exchange_data(self, index, exchange_data):
        self.acceptExchangeData(exchange_data)

    @Inputs.exchange_data.insert
    def insert_exchange_data(self, index, exchange_data):
        self.acceptExchangeData(exchange_data)

    @Inputs.exchange_data.remove
    def remove_exchange_data(self, index):
        pass
    
    def acceptExchangeData(self, exchangeData):
        try:
            if not exchangeData is None:
                if exchangeData.get_program_name() not in ["XOPPY"]:
                    raise Exception("Exchange data must be XOPPY data")

                name = exchangeData.get_widget_name()
                if name in ["UNDULATOR_RADIATION", "WIGGLER_RADIATION", "POWER3DCOMPONENT", "UNDULATOR_POWER_DENSITY_FROM_HARMONICS"]:
                    try:
                        self.input_beam = exchangeData
                        self.output_beam = None
                        self.process_showers()
                        self.compute()
                    except:
                        raise Exception("Error loading Input data from Xoppy Input widget: %s" % exchangeData.get_widget_name())
                elif name == "MULTILAYER":
                    myscan = -1
                    if exchangeData.has_content_key("myscan"): myscan = exchangeData.get_content("myscan")
                    if myscan == 1: # only energy scan allowed
                        x_index = exchangeData.get_content("plot_x_col")
                        y_index = exchangeData.get_content("plot_y_col")
                        reflectivity = exchangeData.get_content("xoppy_data")
                        reflectivity[numpy.where(numpy.isnan(reflectivity))] = 0

                        external_reflectivity_file = "xoppy_reflectivity_" + str(id(self)) + ".dat"
                        file = open(external_reflectivity_file, "w")
                        for index in range(0, reflectivity.shape[0]):
                            file.write(str(reflectivity[index, x_index]) + " " + str(reflectivity[index, y_index]) + "\n")
                        file.close()

                        self.external_reflectivity_file = external_reflectivity_file
                        self.EL1_FLAG = 7

                        self.EL1_HROT = numpy.round(90.0 - (exchangeData.get_content("THETA")), 4)
                        self.EL1_VROT = 0.0

                    else:
                        raise Exception("Only energy scans allowed.")

                elif name == "XCRYSTAL":
                    if exchangeData.get_content("scan_type") == 3:
                        x_index = 0 # energy
                        y_index = -1 # s-pol

                        reflectivity = exchangeData.get_content("xoppy_data")

                        external_reflectivity_file = "xoppy_reflectivity_" + str(id(self)) + ".dat"
                        file = open(external_reflectivity_file, "w")

                        for index in range(0, reflectivity.shape[0]):
                            file.write(
                                str(reflectivity[index, x_index]) + " " + str(reflectivity[index, y_index]) + "\n")
                        file.close()

                        self.external_reflectivity_file = external_reflectivity_file


                        self.EL1_FLAG = 7

                        self.EL1_HROT = numpy.round(90.0 - \
                                                    (exchangeData.get_content("bragg_angle") + \
                                                     exchangeData.get_content("asymmetry_angle")), 4)
                        self.EL1_VROT = 0.0

                    else:
                        raise Exception("Only Energy Scan are accepted from CRYSTAL")

                else:
                    raise Exception("Cannot recover correct data from widget: %s" % name)

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

    def select_input_file(self):
        self.file_id.setText(oasysgui.selectFileFromDialog(self, self.INPUT_BEAM_FILE,
                                    "Open hdf File from Undulator Radiation",
                                    file_extension_filter="hdf5 Files (*.h5 *.hdf5)"))

    def visibility_input_file(self):
        self.file_box_id.setVisible(self.INPUT_BEAM_FROM == 1)

    def load_input_file(self):

        e, h, v, p, code = load_radiation_from_h5file(self.INPUT_BEAM_FILE, "XOPPY_RADIATION")

        received_data = DataExchangeObject("XOPPY", "POWER3DCOMPONENT")
        received_data.add_content("xoppy_data", [p, e, h, v])
        received_data.add_content("xoppy_code", code)
        received_data.add_content("xoppy_script",
                'from xoppylib.power.power3d import load_radiation_from_h5file\n' +
                'energy, horizontal, vertical, flux3D, code = load_radiation_from_h5file("%s", "XOPPY_RADIATION")\n\n' %
                self.INPUT_BEAM_FILE)
        self.input_beam = received_data

        print("Input beam read from file %s \n\n"%self.INPUT_BEAM_FILE)

    def check_fields(self):

        self.EL1_FOR = congruence.checkEmptyString(self.EL1_FOR, "OE formula")

        if self.EL1_FLAG == 0: # filter
            self.EL1_THI = congruence.checkStrictlyPositiveNumber(self.EL1_THI, "OE filter thickness")
            self.EL1_HROT = congruence.checkNumber(self.EL1_HROT, "OE rotation H")
            self.EL1_VROT = congruence.checkNumber(self.EL1_VROT, "OE rotation V")
        elif self.EL1_FLAG == 1: # mirror
            self.EL1_ANG = congruence.checkStrictlyPositiveNumber(self.EL1_ANG, "OE mirror angle")
            self.EL1_ROU = congruence.checkPositiveNumber(self.EL1_ROU, "OE mirror roughness")
            self.EL1_HROT = congruence.checkNumber(self.EL1_HROT, "OE rotation around H axis")
            self.EL1_VROT = congruence.checkNumber(self.EL1_VROT, "OE rotation around V axis")
            self.EL1_HGAP = congruence.checkStrictlyPositiveNumber(self.EL1_HGAP, "OE H gap")
            self.EL1_VGAP = congruence.checkPositiveNumber(self.EL1_VGAP, "OE V Gap")
            self.EL1_HGAPCENTER = congruence.checkNumber(self.EL1_HGAPCENTER, "OE H gap Center")
            self.EL1_VGAPCENTER = congruence.checkNumber(self.EL1_VGAPCENTER, "OE V Gap Center")
        elif self.EL1_FLAG == 2: # aperture
            self.EL1_HGAP = congruence.checkStrictlyPositiveNumber(self.EL1_HGAP, "OE H gap")
            self.EL1_VGAP = congruence.checkPositiveNumber(self.EL1_VGAP, "OE V Gap")
            self.EL1_HGAPCENTER = congruence.checkNumber(self.EL1_HGAPCENTER, "OE H gap Center")
            self.EL1_VGAPCENTER = congruence.checkNumber(self.EL1_VGAPCENTER, "OE V Gap Center")
        elif self.EL1_FLAG == 3: # magnifier
            self.EL1_HMAG = congruence.checkStrictlyPositiveNumber(self.EL1_HMAG, "OE H magnification")
            self.EL1_VMAG = congruence.checkPositiveNumber(self.EL1_VMAG, "OE V magnification")
        elif self.EL1_FLAG == 4: # rotation
            self.EL1_HROT = congruence.checkNumber(self.EL1_HROT, "OE rotation around H axis")
            self.EL1_VROT = congruence.checkNumber(self.EL1_VROT, "OE rotation around V axis")
        elif self.EL1_FLAG == 4: # thin object filter
            self.thin_object_thickness_outside_file_area = congruence.checkNumber(self.thin_object_thickness_outside_file_area, "Thin object thickness outside file")

        if self.FILE_DUMP == 1:
            if (os.path.splitext(self.FILE_NAME))[-1] not in [".h5",".H5",".hdf5",".HDF5"]:
                filename_alternative = (os.path.splitext(self.FILE_NAME))[0] + ".h5"
                tmp = ConfirmDialog.confirmed(self,
                                          message="Invalid file extension in output file: \n%s\nIt must be: .h5, .H5, .hdf5, .HDF5\nChange to: %s ?"%(self.FILE_NAME,filename_alternative),
                                          title="Invalid file extension")
                if tmp == False: return
                self.FILE_NAME = filename_alternative
        elif self.FILE_DUMP >= 2: # (x,y,power density) or matrix, absorbed or transmitted
            if (os.path.splitext(self.FILE_NAME))[-1] not in [".txt", ".dat", ".TXT", ".DAT"]:
                filename_alternative = (os.path.splitext(self.FILE_NAME))[0] + ".txt"
                tmp = ConfirmDialog.confirmed(self,
                                              message="Invalid file extension in output file: \n%s\nIt must be: .txt, .dat, .TXT, .DAT\nChange to: %s ?" % (
                                              self.FILE_NAME, filename_alternative),
                                              title="Invalid file extension")
                if tmp == False: return
                self.FILE_NAME = filename_alternative



    def do_xoppy_calculation(self):

        if self.INPUT_BEAM_FROM == 1:
            self.load_input_file()

        p0, e0, h0, v0 = self.input_beam.get_content("xoppy_data")
        if self.FILE_INPUT_FLAG:
            write_radiation_to_h5file(e0, h0, v0, p0,
                                   creator="power3Dcomponent.py",
                                   h5_file=self.FILE_INPUT_NAME,
                                   h5_entry_name="XOPPY_RADIATION",
                                   h5_initialize=True,
                                   h5_parameters=None,
                                   )

        # defaults
        gapshape = 0
        hgap = 1000.0
        vgap = 1000.0
        hgapcenter = 0.0
        vgapcenter = 0.0
        hmag = 1.0
        vmag = 1.0
        hrot = 0.0
        vrot = 0.0
        thin_object_file = ''
        thin_object_thickness_outside_file_area = 0.0
        thin_object_back_profile_flag = 0
        thin_object_back_profile_file = ''
        multilayer_file = ''
        external_reflectivity_file = ''

        if self.EL1_FLAG in [0,1,2,5,6,7]: #  using slit
            hgap = self.EL1_HGAP
            vgap = self.EL1_VGAP
            hgapcenter = self.EL1_HGAPCENTER
            vgapcenter = self.EL1_VGAPCENTER
            gapshape = self.EL1_GAPSHAPE

        if self.EL1_FLAG == 3:
            hmag = self.EL1_HMAG
            vmag = self.EL1_VMAG

        if self.EL1_FLAG in [0,4,7]: #  using rotation
            hrot = self.EL1_HROT
            vrot = self.EL1_VROT

        if self.EL1_FLAG == 5:
            thin_object_file = self.thin_object_file
            thin_object_thickness_outside_file_area = self.thin_object_thickness_outside_file_area
            thin_object_back_profile_flag = self.thin_object_back_profile_flag
            thin_object_back_profile_file = self.thin_object_back_profile_file

        if self.EL1_FLAG == 6:
            multilayer_file = self.multilayer_file

        if self.EL1_FLAG == 7:
            external_reflectivity_file = self.external_reflectivity_file

        #
        # dabax stuff
        #
        if self.MATERIAL_CONSTANT_LIBRARY_FLAG == 0:
            material_constants_library = xraylib
            material_constants_library_str = "xraylib"
        else:
            material_constants_library = DabaxXraylib(file_f1f2=dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX],
                                                      file_CrossSec=dabax_crosssec_files()[self.DABAX_CROSSSEC_FILE_INDEX])
            material_constants_library_str = 'DabaxXraylib(file_f1f2="%s",file_CrossSec="%s")' % \
                                             (dabax_f1f2_files()[self.DABAX_F1F2_FILE_INDEX],
                                              dabax_crosssec_files()[self.DABAX_CROSSSEC_FILE_INDEX])
            print(material_constants_library.info())

        #
        # write python script
        #
        if isinstance(self.EL1_DEN, str):
            dens = "'"+self.EL1_DEN+"'"
        else:
            dens = "%g" % self.EL1_DEN

        if len(e0.shape) == 1: # vs energy
            str_bw = "/eV"
            str_transmitted = "p2D_transmitted = numpy.trapezoid(p_transmitted, e0, axis=0)"
            str_absorbed = "p2D_absorbed = numpy.trapezoid(p_absorbed, E, axis=0)"
        else: # vs harmonic
            str_bw = ""
            str_transmitted = "p2D_transmitted = numpy.sum(p_transmitted, axis=0)"
            str_absorbed = "p2D_absorbed = numpy.sum(p_absorbed, axis=0)"


        dict_parameters = {
                "emin"       :    e0.min(), # e0[0],
                "emax"       :    e0.max(), # e0[-1],
                "epoints"    : e0.shape[0], # e0.size,
                "hmin"       :    h0[0],
                "hmax"       :    h0[-1],
                "hpoints"    : h0.size,
                "vmin"       :    v0[0],
                "vmax"       :    v0[-1],
                "vpoints"    : v0.size,
                "EL1_FOR"    : "'"+self.EL1_FOR+"'",
                "EL1_THI"    : self.EL1_THI,
                "EL1_ANG"    : self.EL1_ANG,
                "EL1_DEF"    : self.EL1_DEF,
                "EL1_DEN"    : dens,
                "EL1_ROU"    : self.EL1_ROU,
                "EL1_FLAG"   : self.EL1_FLAG,
                "hgap"       : hgap,
                "vgap"       : vgap,
                "hgapcenter" : hgapcenter,
                "vgapcenter" : vgapcenter,
                "hmag"       : hmag,
                "vmag"       : vmag,
                "hrot"       : hrot,
                "vrot"       : vrot,
                "FILE_INPUT_NAME"        : self.FILE_INPUT_NAME,
                "INTERPOLATION_FLAG"     : self.INTERPOLATION_FLAG,
                "INTERPOLATION_FACTOR_H" : self.INTERPOLATION_FACTOR_H,
                "INTERPOLATION_FACTOR_V" : self.INTERPOLATION_FACTOR_V,
                "EL1_SLIT_CROP"          : self.EL1_SLIT_CROP,
                "thin_object_file"       : thin_object_file,
                "thin_object_thickness_outside_file_area" : thin_object_thickness_outside_file_area,
                "thin_object_back_profile_flag"           : thin_object_back_profile_flag,
                "thin_object_back_profile_file"           : thin_object_back_profile_file,
                "multilayer_file"                         :  multilayer_file,
                "external_reflectivity_file"              : external_reflectivity_file,
                "material_constants_library"              : material_constants_library_str,
                "str_bw"                                  : str_bw,
                "str_transmitted"                         : str_transmitted,
                "str_absorbed"                            : str_absorbed,
            }

        if self.input_beam is not None:
            try:
                script_previous = self.input_beam.get_content("xoppy_script")
            except:
                script_previous = '#\n# >> MISSING SCRIPT TO CREATE (energy, horizontal, vertical, flux3D) <<\n#\n'
        script_element = self.script_template().format_map(dict_parameters)
        script = script_previous + script_element
        self.xoppy_script.set_code(script)


        #
        #calculation
        #
        transmittance, absorbance, E, H, V, txt = calculate_component_absorbance_and_transmittance(
                                  e0, h0, v0,
                                  substance=self.EL1_FOR,
                                  thick=self.EL1_THI,
                                  angle=self.EL1_ANG,
                                  defection=self.EL1_DEF,
                                  dens=self.EL1_DEN,
                                  roughness=self.EL1_ROU,
                                  flags=self.EL1_FLAG,
                                  gapshape=gapshape,
                                  hgap=hgap,
                                  vgap=vgap,
                                  hgapcenter=hgapcenter,
                                  vgapcenter=vgapcenter,
                                  hmag=hmag,
                                  vmag=vmag,
                                  hrot=hrot,
                                  vrot=vrot,
                                  thin_object_file=thin_object_file,
                                  thin_object_thickness_outside_file_area=thin_object_thickness_outside_file_area,
                                  thin_object_back_profile_flag=thin_object_back_profile_flag,
                                  thin_object_back_profile_file=thin_object_back_profile_file,
                                  multilayer_file=multilayer_file,
                                  external_reflectivity_file=external_reflectivity_file,
                                  material_constants_library=material_constants_library,
                                  )


        txt += info_total_power(p0, e0, v0, h0, transmittance, absorbance, EL1_FLAG=self.EL1_FLAG)
        print(txt)

        calculated_data = (transmittance, absorbance, E, H, V)

        if self.FILE_DUMP == 0:
            pass
        elif self.FILE_DUMP == 1:
            write_h5_file(calculated_data, self.input_beam.get_content("xoppy_data"), filename=self.FILE_NAME,
                          EL1_FLAG=self.EL1_FLAG, EL1_HMAG=hmag, EL1_VMAG=vmag)
        elif self.FILE_DUMP == 2:
            write_txt_file(calculated_data, self.input_beam.get_content("xoppy_data"),
                           filename=self.FILE_NAME, method="3columns", quantity="absorbed")
        elif self.FILE_DUMP == 3:
            write_txt_file(calculated_data, self.input_beam.get_content("xoppy_data"),
                           filename=self.FILE_NAME, method="matrix", quantity="absorbed")
        elif self.FILE_DUMP == 4:
            write_txt_file(calculated_data, self.input_beam.get_content("xoppy_data"),
                           filename=self.FILE_NAME, method="3columns", quantity="transmitted")
        elif self.FILE_DUMP == 5:
            write_txt_file(calculated_data, self.input_beam.get_content("xoppy_data"),
                           filename=self.FILE_NAME, method="matrix", quantity="transmitted")


        return transmittance, absorbance, E, H, V, script


    def script_template(self):
        return """

#
# script to make the calculations (created by XOPPY:power3Dcomponent)
#

import numpy
try: import xraylib
except: print("xraylib not available")
from dabax.dabax_xraylib import DabaxXraylib
from xoppylib.power.power3d import calculate_component_absorbance_and_transmittance

# compute local transmittance and absorbance
e0, h0, v0, f0  = energy, horizontal, vertical, flux3D
transmittance, absorbance, E, H, V, txt = calculate_component_absorbance_and_transmittance(
                e0, # energy in eV
                h0, # h in mm
                v0, # v in mm
                substance={EL1_FOR},
                thick={EL1_THI},
                angle={EL1_ANG},
                defection={EL1_DEF},
                dens={EL1_DEN},
                roughness={EL1_ROU},
                flags={EL1_FLAG}, # 0=Filter 1=Mirror 2=Aperture 3=magnifier, 4=Screen rotation  5=Thin object  6=Multilayer 7=External file
                hgap={hgap},
                vgap={vgap},
                hgapcenter={hgapcenter},
                vgapcenter={vgapcenter},
                hmag={hmag},
                vmag={vmag},
                hrot={hrot},
                vrot={vrot},
                thin_object_file='{thin_object_file}',
                thin_object_thickness_outside_file_area={thin_object_thickness_outside_file_area},
                thin_object_back_profile_flag={thin_object_back_profile_flag},
                thin_object_back_profile_file='{thin_object_back_profile_file}',
                multilayer_file='{multilayer_file}',
                external_reflectivity_file='{external_reflectivity_file}',
                material_constants_library = {material_constants_library},
                )



if False:
    # compute data to send 
    from xoppylib.power.power3d import apply_transmittance_to_incident_beam
    # apply transmittance to incident beam 
    f_transmitted, e, h, v = apply_transmittance_to_incident_beam(transmittance, f0, e0, h0, v0,
                    flags = {EL1_FLAG},
                    hgap = {hgap},
                    vgap = {vgap},
                    hgapcenter = {hgapcenter},
                    vgapcenter = {vgapcenter},
                    hmag = {hmag},
                    vmag = {vmag},
                    interpolation_flag     = {INTERPOLATION_FLAG},
                    interpolation_factor_h = {INTERPOLATION_FACTOR_H},
                    interpolation_factor_v = {INTERPOLATION_FACTOR_V},
                    slit_crop = {EL1_SLIT_CROP},
                    )
    
    
    # data to pass
    energy, horizontal, vertical, flux3D = e, h, v, f_transmitted

#                       
# example plots
#
if True:
    from srxraylib.plot.gol import plot_image
    import scipy.constants as codata
    from xoppylib.power.power3d import integral_2d
    
    print(">>>>>>>>>>>>>>>>", h0.max(), H.max(), v0.max(), V.max())

    # transmitted/reflected beam   
    p_transmitted = f0 * transmittance * codata.e * 1e3
    print(">>>>> f0: ", f0.max(), f0.min())
    print(">>>>> p_transmitted: ", p_transmitted.max(), p_transmitted.min(), transmittance.max(), transmittance.min())
    plot_image(p_transmitted[0,:,:],h0,v0,title="Transmitted Spectral Power Density [W{str_bw}/mm2] at lower energy",xtitle="H [mm] (normal to beam)",ytitle="V [mm] (normal to beam)",aspect='auto')
    
    {str_transmitted}
    plot_image(p2D_transmitted, h0, v0,
                     xtitle='H [mm] (normal to beam)',
                     ytitle='V [mm] (normal to beam)',
                     title='Transmitted/Reflected Power Density [W/mm^2].',aspect='auto')
    
    # local absorption
    p_absorbed = f0 * absorbance / (H[0] / h0[0]) / (V[0] / v0[0]) * codata.e * 1e3
    print(">>>>> f0: ", f0.max(), f0.min())
    print(">>>>> p_absorbed: ", p_absorbed.max(), p_absorbed.min(), absorbance.max(), absorbance.min())
    plot_image(p_absorbed[0,:,:],H,V,title="Absorbed Spectral Power Density [W{str_bw}/mm2] at lower energy",xtitle="H [mm] (o.e. coordinates)",ytitle="V [mm] (o.e. coordinates)",aspect='auto')
    
    {str_absorbed}
    plot_image(p2D_absorbed, H, V,
                     xtitle='H [mm] (o.e. coordinates)',
                     ytitle='V [mm] (o.e. coordinates)',
                     title='Absorbed Power Density [W/mm^2].',aspect='auto')
                                               
#
# end script
#
"""

    # TO SEND DATA
    def extract_data_from_xoppy_output(self, calculation_output):

        transmittance, absorbance, E, H, V, script = calculation_output

        p0, e0, h0, v0 = self.input_beam.get_content("xoppy_data")

        p_transmitted, e, h, v = apply_transmittance_to_incident_beam(transmittance, p0, e0, h0, v0,
                                          flags = self.EL1_FLAG,
                                          hgap = self.EL1_HGAP,
                                          vgap = self.EL1_VGAP,
                                          hgapcenter = self.EL1_HGAPCENTER,
                                          vgapcenter = self.EL1_VGAPCENTER,
                                          hmag = self.EL1_HMAG,
                                          vmag = self.EL1_VMAG,
                                          interpolation_flag = self.INTERPOLATION_FLAG,
                                          interpolation_factor_h = self.INTERPOLATION_FACTOR_H,
                                          interpolation_factor_v = self.INTERPOLATION_FACTOR_V,
                                          slit_crop = self.EL1_SLIT_CROP,
                                        )


        data_to_send = DataExchangeObject("XOPPY", self.get_data_exchange_widget_name())
        data_to_send.add_content("xoppy_data", [p_transmitted, e, h, v])
        data_to_send.add_content("xoppy_transmittivity", (transmittance, absorbance, E, H, V) ) # TODO: review this part for crop+interp
        data_to_send.add_content("xoppy_code", "power3Dcomponent")
        data_to_send.add_content("xoppy_script", script)

        self.output_beam = data_to_send

        return data_to_send


    def get_data_exchange_widget_name(self):
        return "POWER3DCOMPONENT"

    def getTitles(self):
        mylist = []
        if self.EL1_FLAG in (1, 6):
            txt1 = "Reflectance "
            txt2 = "Reflected "
        else:
            txt1 = "Transmittance "
            txt2 = "Transmitted  "

        if self.PLOT_SETS == 0: # local
            for ii in ['Input Spectral Power Density vs E,X,Y',
                       'Input Power Density vs X,Y',
                       'Input Spectral Power vs E',
                       'Input Flux vs E',]:
                mylist.append(ii)
        elif self.PLOT_SETS == 1: # input
            for ii in [txt1 + ' vs X,Y,E',
                       txt1 + ' vs E',
                       'Absorbance vs X,Y,E',
                       'Absorbance vs E', ]:
                mylist.append(ii)
        elif self.PLOT_SETS == 2:  # absorption
            for ii in ['Absorbed Spectral Power Density vs E,X,Y',
                       'Absorbed Power Density vs X,Y',
                       'Absorbed Spectral Power vs E',
                       'Absorbed Flux vs E']:
                mylist.append(ii)
        elif self.PLOT_SETS == 3: # transmittance/
            for ii in [
                    txt2 + 'Spectral Power Density vs E,X,Y',
                    txt2 + 'Power Density vs X,Y',
                    txt2 + 'Spectral Power vs E',
                    txt2 + 'Flux vs E']:
                mylist.append(ii)

        return mylist


    def replot_results(self):
        if self.output_beam is None:
            pass
        else:
            self.plot_results(self.output_beam, progressBarValue=80)

    def plot_results(self, calculated_data, progressBarValue=80):
        current_index = self.tabs.currentIndex()
        if not self.view_type == 0:
            if calculated_data is None:
                raise Exception("Empty data")

            p0, e0, h0, v0 = self.input_beam.get_content("xoppy_data")
            if len(e0.shape) == 1:
                self.plot_results_vs_energy(calculated_data, progressBarValue)
            else:
                self.plot_results_vs_harmonics(calculated_data, progressBarValue)


    def plot_results_vs_energy(self, calculated_data, progressBarValue=80):
        current_index = self.tabs.currentIndex()
        if not self.view_type == 0:
            if calculated_data is None:
                raise Exception("Empty data")

            self.initializeTabs() # added by srio to avoid overlapping graphs

            self.view_type_combo.setEnabled(False)

            p0, e0, h0, v0 = self.input_beam.get_content("xoppy_data")
            p = p0.copy()
            e = e0.copy()
            h = h0.copy()
            v = v0.copy()
            p_spectral_power = p * codata.e * 1e3

            transmittance, absorbance, E, H, V = calculated_data.get_content("xoppy_transmittivity")

            print(">>>>>>>>>>>>>>>>>>>>>>", h.max(), v.max(), H.max(), V.max())

            if self.EL1_FLAG == 3:  # magnifier  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                h *= self.EL1_HMAG
                v *= self.EL1_VMAG

            if self.PLOT_SETS == 0:  # source
                # plot result s E,X,Y
                self.plot_data3D(p_spectral_power, e0, h0, v0, 0, 0,
                                 xtitle='H [mm] (normal to beam)',
                                 ytitle='V [mm] (normal to beam)',
                                 title='Input beam Spectral power density[W/eV/mm^2]',
                                 color_limits_uniform=False)
                self.tabs.setCurrentIndex(0)

                # plot result vs X,Y
                power_density = numpy.trapezoid(p_spectral_power, e0, axis=0)
                power_density_integral = integral_2d(power_density, h0, v0)
                self.plot_data2D(power_density, h0, v0, 1, 0,
                                 xtitle='H [mm]',
                                 ytitle='V [mm]',
                                 title='Input beam Power density [W/mm^2]. Integral: %6.3f W'%power_density_integral,)

                # plot result vs E
                spectral_density = numpy.trapezoid(numpy.trapezoid(p_spectral_power, v0, axis=2), h0, axis=1)
                spectral_density_integral = numpy.trapezoid(spectral_density, e0)
                self.plot_data1D(e, spectral_density, 2, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle= 'Spectral power [W/eV]',
                                 title='Input beam Spectral power. Integral: %6.3f W'%spectral_density_integral,)

                # plot flux vs E
                flux = spectral_density / (codata.e * 1e3)
                self.plot_data1D(e, flux, 3, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle= 'Flux [Photons/s/0.1%bw]',
                                 title='Input beam Flux', xlog=True, ylog=True)

            if self.PLOT_SETS == 1:  # transmittance & absorbance
                # plot transmittance stack
                self.plot_data3D(transmittance, e, h, v, 0, 0,
                                 xtitle='H [mm] (normal to beam)',
                                 ytitle='V [mm] (normal to beam)',
                                 color_limits_uniform=True)
                self.tabs.setCurrentIndex(0)

                # plot transmittance spectrum
                if self.EL1_FLAG == 1:
                    ytitle = "Reflectance"
                else:
                    ytitle = "Transmittance"
                self.plot_data1D(e, numpy.trapezoid(numpy.trapezoid(transmittance, v, axis=2), h, axis=1) /
                                 (h[-1] - h[0]) / (v[-1] - v[0]), 1, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle=ytitle,
                                 title='Integrated '+ytitle,)

                # plot absorbance stack
                self.plot_data3D(absorbance, E, H, V, 2, 0,
                                 xtitle='H [mm] (o.e. coordinates)',
                                 ytitle='V [mm] (o.e. coordinates)',
                                 color_limits_uniform=True)

                # plot absorbance spectrum
                self.plot_data1D(E, numpy.trapezoid(numpy.trapezoid(absorbance, V, axis=2), H, axis=1) / (H[-1] - H[0]) / (V[-1] - V[0]), 3, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Absorbance',
                                 title='Integrated Absorbance',)

            if self.PLOT_SETS == 2:  # absorption by element
                p_absorbed = p_spectral_power * absorbance / (H[0] / h0[0]) / (V[0] / v0[0])
                # plot result vs E,X,Y
                self.plot_data3D(p_absorbed, E, H, V, 0, 0,
                                 xtitle='H [mm] (o.e. coordinates)',
                                 ytitle='V [mm] (o.e. coordinates)',
                                 title='Absorbed Spectral Power Density[W/eV/mm^2]',
                                 color_limits_uniform=False)
                self.tabs.setCurrentIndex(0)

                # plot result vs X,Y
                power_density = numpy.trapezoid(p_absorbed, E, axis=0)
                power_density_integral = integral_2d(power_density, H, V)
                self.plot_data2D(power_density, H, V, 1, 0,
                                 xtitle='H [mm] (o.e. coordinates)',
                                 ytitle='V [mm] (o.e. coordinates)',
                                 title='Absorbed Power Density [W/mm^2]. Integral: %6.3f W'%power_density_integral, )

                # plot result vs E
                spectral_density = numpy.trapezoid(numpy.trapezoid(p_absorbed, V, axis=2), H, axis=1)
                spectral_density_integral = numpy.trapezoid(spectral_density, E)
                self.plot_data1D(e, spectral_density, 2, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Spectral power [W/eV]',
                                 title='Absorbed Spectral Power. Integral: %6.3f W'%spectral_density_integral, )

                # plot flux vs E
                flux = spectral_density / (codata.e * 1e3)
                self.plot_data1D(e, flux, 3, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Flux [Photons/s/0.1%bw]',
                                 title='Absorbed Flux', xlog=True, ylog=True)

            if self.PLOT_SETS == 3:  # transmitted/reflected by element
                p_transmitted = p_spectral_power * transmittance / (h[0] / h0[0]) / (v[0] / v0[0])
                if self.EL1_FLAG == 1:
                    tr_ref_txt = "Reflected"
                else:
                    tr_ref_txt = "Transmitted"

                # plot result s E,X,Y
                self.plot_data3D(p_transmitted, e, h, v, 0, 0,
                                 xtitle='H [mm] (normal to beam)',
                                 ytitle='V [mm] (normal to beam)',
                                 title=tr_ref_txt+' Spectral Power Density[W/eV/mm^2]',
                                 color_limits_uniform=False)
                self.tabs.setCurrentIndex(0)

                # self.plot_data2D(p_transmitted.sum(axis=0) * energy_step, H, V, 1, 0,
                power_density = numpy.trapezoid(p_transmitted, E, axis=0)
                power_density_integral = integral_2d(power_density, h, v)
                self.plot_data2D(power_density, h, v, 1, 0,
                                 xtitle='H [mm] (normal to beam)',
                                 ytitle='V [mm] (normal to beam)',
                                 title=tr_ref_txt+' Power Density [W/mm^2]. Integral: %6.3f W'%power_density_integral, )

                # plot result vs E
                spectral_density = numpy.trapezoid(numpy.trapezoid(p_transmitted, v, axis=2), h, axis=1)
                spectral_density_integral = numpy.trapezoid(spectral_density, e)
                self.plot_data1D(e, spectral_density, 2, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Spectral power [W/eV]',
                                 title=tr_ref_txt+' Spectral Power. Integral: %6.3f W'%spectral_density_integral, )

                # plot flux vs E
                # spectral_density = numpy.trapezoid(numpy.trapezoid(p_transmitted, v, axis=2), h, axis=1)
                flux = spectral_density / (codata.e * 1e3)
                self.plot_data1D(e, flux, 3, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Flux [Photons/s/0.1%bw]',
                                 title=tr_ref_txt+' Flux', xlog=True, ylog=True)

            self.view_type_combo.setEnabled(True)

            try:
                self.tabs.setCurrentIndex(current_index)
            except:
                pass

    def plot_results_vs_harmonics(self, calculated_data, progressBarValue=80):
        current_index = self.tabs.currentIndex()
        if not self.view_type == 0:
            if calculated_data is None:
                raise Exception("Empty data")

            self.initializeTabs() # added by srio to avoid overlapping graphs

            self.view_type_combo.setEnabled(False)

            de = 100  # eV
            p0, e0, h0, v0 = self.input_beam.get_content("xoppy_data")
            p = p0.copy()
            p_spectral_power = p * codata.e * 1e3
            h = h0.copy()
            v = v0.copy()
            step_h = h[1] - h[0]
            step_v = v[1] - v[0]
            step_hv = step_h * step_v

            e = (e0[:, e0.shape[1]//2, e0.shape[1]//2]).copy()
            title_callback_light = lambda idx: ("Harmonic %d" % idx)


            transmittance, absorbance, E_in, H, V = calculated_data.get_content("xoppy_transmittivity")
            E = (E_in[:, E_in.shape[1]//2, E_in.shape[1]//2]).copy()

            if self.EL1_FLAG == 3:  # magnifier  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                h *= self.EL1_HMAG
                v *= self.EL1_VMAG

            # plot Input beam  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            if self.PLOT_SETS == 0:  # source
                title_callback = lambda idx: ("Harmonic %d (on-axis energy: %6.3f eV, power: %.1f W)" %
                                              (idx, e[idx], integral_2d(p_spectral_power[idx], h0, v0)))


                # plot result s E,X,Y
                self.plot_data3D(p_spectral_power, e, h0, v0, 0, 0,
                                 xtitle='H [mm]',
                                 ytitle='V [mm]',
                                 title='Input beam Spectral power density[W/eV/mm^2]',
                                 color_limits_uniform=False,
                                 title_callback=title_callback)
                self.tabs.setCurrentIndex(0)

                # plot result vs X,Y
                power_density = numpy.sum(p_spectral_power, axis=0)

                power_density_integral = integral_2d(power_density, h0, v0)

                self.plot_data2D(power_density, h0, v0, 1, 0,
                                 xtitle='H [mm]',
                                 ytitle='V [mm]',
                                 title='Input beam Power density [W/mm^2]. Integral: %6.3f W'%power_density_integral,)

                # plot result vs E
                energies = e0.flatten()  # Flatten all energy values
                powers = p_spectral_power.flatten() * step_hv # Flatten corresponding power contributions

                e_bins = numpy.arange(energies.min(), energies.max() + de, de)
                print("Spectrum calculated from histogramming in photon energy:"
                      "\n min: %g eV, max: %g eV, delta: %g eV, n_bins: %d " %
                      (e0.min(), e0.max(), de, e_bins.size))

                # Bin the powers into energy bins
                spectral_density, bin_edges = numpy.histogram(energies, bins=e_bins, weights=powers)
                bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
                self.plot_data1D(bin_centers, spectral_density / de, 2, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Spectral power [W/eV]',
                                 title='Input beam Spectral power. Bin: %.1f eV. Integral: %6.3f W' % (de, power_density_integral), )

                # plot flux vs E
                flux = (spectral_density / de) / (codata.e * 1e3)
                self.plot_data1D(bin_centers, flux, 3, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle= 'Flux [Photons/s/0.1%bw]',
                                 title='Input beam Flux', xlog=True, ylog=True)

            # plot Element Transmittance and Absorbance <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            if self.PLOT_SETS == 1:  # transmittance & absorbance
                # plot transmittance stack
                self.plot_data3D(transmittance, e, h, v, 0, 0,
                                 xtitle='H [mm] (normal to beam)',
                                 ytitle='V [mm] (normal to beam)',
                                 color_limits_uniform=True,
                                 title_callback=title_callback_light)
                self.tabs.setCurrentIndex(0)

                # plot absorbance stack
                self.plot_data3D(absorbance, E, H, V, 2, 0,
                                 xtitle='H [mm] (o.e. coordinates)',
                                 ytitle='V [mm] (o.e. coordinates)',
                                 color_limits_uniform=True,
                                 title_callback=title_callback_light)

                # plot transmittance spectrum
                if self.EL1_FLAG == 1:
                    ytitle = "Reflectance"
                else:
                    ytitle = "Transmittance"

                f_e0 = e0.flatten()  # Flatten all energy values
                self.plot_data1D(f_e0, transmittance.flatten(), 1, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle=ytitle,
                                 title=ytitle,)
                self.plot_data1D(f_e0, absorbance.flatten(), 3, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Absorbance',
                                 title='Absorbance',)


            # plot Absorbed by element  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            if self.PLOT_SETS == 2:  # absorption by element
                p_absorbed = p_spectral_power * absorbance / (H[0] / h0[0]) / (V[0] / v0[0])
                # plot result vs E,X,Y
                title_callback = lambda idx: ("Harmonic %d (on-axis energy: %6.3f eV, power: %.1f W)" %
                                              (idx, e[idx], integral_2d(p_absorbed[idx], h0, v0)))
                print(">>>>> f0: ", p0.max(), p0.min())
                print(">>>>> p_absorbed: ", p_absorbed.max(), p_absorbed.min(), absorbance.max(), absorbance.min())
                self.plot_data3D(p_absorbed, E, H, V, 0, 0,
                                 xtitle='H [mm] (o.e. coordinates)',
                                 ytitle='V [mm] (o.e. coordinates)',
                                 title='Absorbed Power Density[W/mm^2]',
                                 color_limits_uniform=False,
                                 title_callback=title_callback)
                self.tabs.setCurrentIndex(0)

                # plot result vs X,Y
                power_density = numpy.sum(p_absorbed, axis=0)
                power_density_integral = integral_2d(power_density, H, V)
                self.plot_data2D(power_density, H, V, 1, 0,
                                 xtitle='H [mm] (o.e. coordinates)',
                                 ytitle='V [mm] (o.e. coordinates)',
                                 title='Absorbed Power Density [W/mm^2]. Integral: %6.3f W' % power_density_integral, )

                # plot result vs E
                energies = e0.flatten()  # Flatten all energy values
                weights = (p_spectral_power * absorbance).flatten() * step_hv # Flatten corresponding power contributions

                e_bins = numpy.arange(energies.min(), energies.max() + de, de)
                print("Spectrum calculated from histogramming in photon energy:"
                      "\n min: %g eV, max: %g eV, delta: %g eV, n_bins: %d " %
                      (e0.min(), e0.max(), de, e_bins.size))

                # Bin the powers into energy bins
                spectral_density_histo, bin_edges = numpy.histogram(energies, bins=e_bins, weights=weights)
                bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

                self.plot_data1D(bin_centers, spectral_density_histo / de, 2, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Spectral power [W/eV]',
                                 title='Absorbed Power', )

                # plot flux vs E
                flux = (spectral_density_histo / de) / (codata.e * 1e3)
                self.plot_data1D(bin_centers, flux, 3, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Flux [Photons/s/0.1%bw]',
                                 title='Absorbed Flux', xlog=True, ylog=True)


            # Trsnamitted/reflected by element  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            if self.PLOT_SETS == 3:  # transmitted/reflected by element
                p_transmitted = p_spectral_power * transmittance / (h[0] / h0[0]) / (v[0] / v0[0])
                print(">>>>> p_transmitted: ", p_transmitted.max(), p_transmitted.min(), transmittance.max(), transmittance.min())
                if self.EL1_FLAG == 1:
                    tr_ref_txt = "Reflected"
                else:
                    tr_ref_txt = "Transmitted"

                # plot result s E,X,Y
                title_callback = lambda idx: ("Harmonic %d (on-axis energy: %6.3f eV, power: %.1f W)" %
                                              (idx, e[idx], integral_2d(p_transmitted[idx], h0, v0)))
                self.plot_data3D(p_transmitted, e, h, v, 0, 0,
                                 xtitle='H [mm] (normal to beam)',
                                 ytitle='V [mm] (normal to beam)',
                                 title=tr_ref_txt+' Spectral Power Density[W/eV/mm^2]',
                                 color_limits_uniform=False,
                                 title_callback=title_callback)
                self.tabs.setCurrentIndex(0)

                power_density = numpy.sum(p_transmitted, axis=0)
                power_density_integral = integral_2d(power_density, h, v)
                self.plot_data2D(power_density, h, v, 1, 0,
                                 xtitle='H [mm] (normal to beam)',
                                 ytitle='V [mm] (normal to beam)',
                                 title=tr_ref_txt+' Power Density [W/mm^2]. Integral: %6.3f W'%power_density_integral, )

                # plot result vs E
                energies = e0.flatten()  # Flatten all energy values
                weights = p_transmitted.flatten() * step_hv  # Flatten corresponding power contributions

                e_bins = numpy.arange(energies.min(), energies.max() + de, de)
                print("Spectrum calculated from histogramming in photon energy:"
                      "\n min: %g eV, max: %g eV, delta: %g eV, n_bins: %d " %
                      (e0.min(), e0.max(), de, e_bins.size))

                # Bin the powers into energy bins
                spectral_density_histo, bin_edges = numpy.histogram(energies, bins=e_bins, weights=weights)
                bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])


                self.plot_data1D(bin_centers, spectral_density_histo / de, 2, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Spectral power [W/eV]',
                                 title=tr_ref_txt+' Spectral Power.')

                # plot flux vs E
                flux = (spectral_density_histo / de) / (codata.e * 1e3)
                self.plot_data1D(bin_centers, flux, 3, 0,
                                 xtitle='Photon Energy [eV]',
                                 ytitle='Flux [Photons/s/0.1%bw]',
                                 title=tr_ref_txt+' Flux', xlog=True, ylog=True)

            self.view_type_combo.setEnabled(True)

            try:
                self.tabs.setCurrentIndex(current_index)
            except:
                pass

    @Inputs.syned_data
    def set_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.insert
    def insert_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.remove
    def remove_syned_data(self, index):
        pass

    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, Beamline):
                n = data.get_beamline_elements_number()
                oe = data.get_beamline_element_at(n - 1).get_optical_element()
                coor = data.get_beamline_element_at(n - 1).get_coordinates()

                try:
                    boundary = oe.get_boundary_shape()
                    if isinstance(boundary, Rectangle):
                        x_left, x_right, y_bottom, y_top = boundary.get_boundaries()
                        self.EL1_HGAPCENTER = numpy.round(0.5 * (x_right + x_left) * 1e3, 4)
                        self.EL1_VGAPCENTER = numpy.round(0.5 * (y_top + y_bottom) * 1e3, 4)
                        self.EL1_HGAP = numpy.round((x_right - x_left) * 1e3, 4)
                        self.EL1_VGAP = numpy.round((y_top - y_bottom) * 1e3, 4)
                except:
                    pass

                if isinstance(oe, Filter):
                    self.EL1_FLAG = 0
                    self.EL1_FOR = oe.get_material()
                    self.EL1_THI = oe.get_thickness() * 1e3
                elif isinstance(oe, Mirror):
                    self.EL1_FLAG = 1
                    if oe._coating is not None:
                        self.EL1_FOR = oe._coating
                    self.EL1_ANG = numpy.round( (numpy.pi / 2 - coor.angle_radial()) * 1e3, 4)
                elif isinstance(oe, Slit):
                    self.EL1_FLAG = 2
                else:
                    raise ValueError("Syned optical element not valid")


            else:
                raise ValueError("Syned data not correct")

add_widget_parameters_to_module(__name__)


if __name__ == "__main__":
    from AnyQt.QtWidgets import QMessageBox, QApplication

    if 1:
        # # create unulator_radiation xoppy exchange data
        # from xoppylib.xoppy_undulators import xoppy_calc_undulator_radiation
        # from oasys.widgets.exchange import DataExchangeObject
        #
        # e, h, v, p, code = xoppy_calc_undulator_radiation(ELECTRONENERGY=6.04,ELECTRONENERGYSPREAD=0.001,ELECTRONCURRENT=0.2,\
        #                                    ELECTRONBEAMSIZEH=0.000395,ELECTRONBEAMSIZEV=9.9e-06,\
        #                                    ELECTRONBEAMDIVERGENCEH=1.05e-05,ELECTRONBEAMDIVERGENCEV=3.9e-06,\
        #                                    PERIODID=0.018,NPERIODS=222,KV=1.68,DISTANCE=30.0,
        #                                    SETRESONANCE=0,HARMONICNUMBER=1,
        #                                    GAPH=0.001,GAPV=0.001,\
        #                                    HSLITPOINTS=41,VSLITPOINTS=41,METHOD=2,
        #                                    PHOTONENERGYMIN=7000,PHOTONENERGYMAX=8100,PHOTONENERGYPOINTS=20,
        #                                    USEEMITTANCES=1)
        #
        # received_data = DataExchangeObject("XOPPY", "Power3Dcomponent")
        # received_data.add_content("xoppy_data", [p, e, h, v])
        # received_data.add_content("xoppy_code", code)

        # create wiggler_radiation xoppy exchange data
        from xoppylib.sources.xoppy_bm_wiggler import xoppy_calc_wiggler_radiation

        h5_parameters = dict()
        h5_parameters["ELECTRONENERGY"] = 3.0
        h5_parameters["ELECTRONCURRENT"] = 0.1
        h5_parameters["PERIODID"] = 0.12
        h5_parameters["NPERIODS"] = 37.0
        h5_parameters["KV"] = 22.416
        h5_parameters["FIELD"] = 0  # 0= sinusoidal, 1=from file
        h5_parameters["FILE"] = ''
        h5_parameters["POLARIZATION"] = 0  # 0=total, 1=s, 2=p
        h5_parameters["DISTANCE"] = 30.0
        h5_parameters["HSLITPOINTS"] = 500
        h5_parameters["VSLITPOINTS"] = 500
        h5_parameters["PHOTONENERGYMIN"] = 29000.0 # 100.0
        h5_parameters["PHOTONENERGYMAX"] = 39000.0 # 100100.0
        h5_parameters["PHOTONENERGYPOINTS"] = 2
        h5_parameters["SHIFT_X_FLAG"] = 0
        h5_parameters["SHIFT_X_VALUE"] = 0.0
        h5_parameters["SHIFT_BETAX_FLAG"] = 0
        h5_parameters["SHIFT_BETAX_VALUE"] = 0.0
        h5_parameters["CONVOLUTION"] = 1

        e, h, v, p, traj = xoppy_calc_wiggler_radiation(
            ELECTRONENERGY=h5_parameters["ELECTRONENERGY"],
            ELECTRONCURRENT=h5_parameters["ELECTRONCURRENT"],
            PERIODID=h5_parameters["PERIODID"],
            NPERIODS=h5_parameters["NPERIODS"],
            KV=h5_parameters["KV"],
            FIELD=h5_parameters["FIELD"],
            FILE=h5_parameters["FILE"],
            POLARIZATION=h5_parameters["POLARIZATION"],
            DISTANCE=h5_parameters["DISTANCE"],
            HSLITPOINTS=h5_parameters["HSLITPOINTS"],
            VSLITPOINTS=h5_parameters["VSLITPOINTS"],
            PHOTONENERGYMIN=h5_parameters["PHOTONENERGYMIN"],
            PHOTONENERGYMAX=h5_parameters["PHOTONENERGYMAX"],
            PHOTONENERGYPOINTS=h5_parameters["PHOTONENERGYPOINTS"],
            SHIFT_X_FLAG=h5_parameters["SHIFT_X_FLAG"],
            SHIFT_X_VALUE=h5_parameters["SHIFT_X_VALUE"],
            SHIFT_BETAX_FLAG=h5_parameters["SHIFT_BETAX_FLAG"],
            SHIFT_BETAX_VALUE=h5_parameters["SHIFT_BETAX_VALUE"],
            CONVOLUTION=h5_parameters["CONVOLUTION"],
            h5_file="wiggler_radiation.h5",
            h5_entry_name="XOPPY_RADIATION",
            h5_initialize=True,
            h5_parameters=h5_parameters,
        )
        print(p.shape)
        received_data = DataExchangeObject("XOPPY", "WIGGLER_RADIATION")
        received_data.add_content("xoppy_data", [p, e, h, v])
        # received_data.add_content("xoppy_code", code)
    else:

        #
        # script to make the calculations (created by XOPPY:undulator_spectrum)
        #
        from xoppylib.sources.xoppy_undulators import xoppy_calc_undulator_power_density_from_harmonics

        # define inputs here to be written in h5 file
        h5_parameters = dict()
        h5_parameters["ELECTRONENERGY"] = 6.0
        h5_parameters["ELECTRONENERGYSPREAD"] = 0.001
        h5_parameters["ELECTRONCURRENT"] = 0.2
        h5_parameters["ELECTRONBEAMSIZEH"] = 3.34281e-05
        h5_parameters["ELECTRONBEAMSIZEV"] = 7.28139e-06
        h5_parameters["ELECTRONBEAMDIVERGENCEH"] = 4.51097e-06
        h5_parameters["ELECTRONBEAMDIVERGENCEV"] = 1.94034e-06
        h5_parameters["PERIODID"] = 0.018
        h5_parameters["NPERIODS"] = 111
        h5_parameters["KV"] = 1.6563
        h5_parameters["KH"] = 0.0
        h5_parameters["KPHASE"] = 0.0
        h5_parameters["DISTANCE"] = 23.0
        h5_parameters["GAPH"] = 0.01
        h5_parameters["GAPV"] = 0.01
        h5_parameters["HSLITPOINTS"] = 51
        h5_parameters["VSLITPOINTS"] = 51
        h5_parameters["METHOD"] = 1  # 0=urgent (fortran), 1=urgentpy (python)
        h5_parameters["USEEMITTANCES"] = 1
        h5_parameters["MASK_FLAG"] = 0
        h5_parameters["MASK_ROT_H_DEG"] = 0.0
        h5_parameters["MASK_ROT_V_DEG"] = 0.0
        h5_parameters["MASK_H_MIN"] = -1000.0
        h5_parameters["MASK_H_MAX"] = 1000.0
        h5_parameters["MASK_V_MIN"] = -1000.0
        h5_parameters["MASK_V_MAX"] = 1000.0
        h5_parameters["harmonic_max"] = 5  # maximum harmonic to calculate
        h5_parameters["photon_energy_bin"] = 300.0  # in eV, for calculating Spectral Power

        horizontal, vertical, power_density, code, power_density_harmonics, energy, spectral_power, spectral_power_energy, flux3D = xoppy_calc_undulator_power_density_from_harmonics(
            ELECTRONENERGY=h5_parameters["ELECTRONENERGY"],
            ELECTRONENERGYSPREAD=h5_parameters["ELECTRONENERGYSPREAD"],
            ELECTRONCURRENT=h5_parameters["ELECTRONCURRENT"],
            ELECTRONBEAMSIZEH=h5_parameters["ELECTRONBEAMSIZEH"],
            ELECTRONBEAMSIZEV=h5_parameters["ELECTRONBEAMSIZEV"],
            ELECTRONBEAMDIVERGENCEH=h5_parameters["ELECTRONBEAMDIVERGENCEH"],
            ELECTRONBEAMDIVERGENCEV=h5_parameters["ELECTRONBEAMDIVERGENCEV"],
            PERIODID=h5_parameters["PERIODID"],
            NPERIODS=h5_parameters["NPERIODS"],
            KV=h5_parameters["KV"],
            KH=h5_parameters["KH"],
            KPHASE=h5_parameters["KPHASE"],
            DISTANCE=h5_parameters["DISTANCE"],
            GAPH=h5_parameters["GAPH"],
            GAPV=h5_parameters["GAPV"],
            HSLITPOINTS=h5_parameters["HSLITPOINTS"],
            VSLITPOINTS=h5_parameters["VSLITPOINTS"],
            METHOD=h5_parameters["METHOD"],
            harmonic_max=h5_parameters["harmonic_max"],
            USEEMITTANCES=h5_parameters["USEEMITTANCES"],
            MASK_FLAG=h5_parameters["MASK_FLAG"],
            MASK_ROT_H_DEG=h5_parameters["MASK_ROT_H_DEG"],
            MASK_ROT_V_DEG=h5_parameters["MASK_ROT_V_DEG"],
            MASK_H_MIN=h5_parameters["MASK_H_MIN"],
            MASK_H_MAX=h5_parameters["MASK_H_MAX"],
            MASK_V_MIN=h5_parameters["MASK_V_MIN"],
            MASK_V_MAX=h5_parameters["MASK_V_MAX"],
            h5_file="undulator_power_density_from_harmonics.h5",
            h5_entry_name="XOPPY_POWERDENSITY_FROM_HARMONICS",
            h5_initialize=True,
            h5_parameters=h5_parameters,
            photon_energy_bin=h5_parameters["photon_energy_bin"],
        )

        # example plot
        if 0:
            # Power Density
            from srxraylib.plot.gol import plot, plot_image

            plot_image(power_density_harmonics.sum(axis=0), horizontal, vertical, xtitle="H [mm]", ytitle="V [mm]",
                       title="Power density W/mm2")

            # Spectral Power & Cumulated Power
            plot(spectral_power_energy, spectral_power, xtitle="Photon energy [eV]",
                 ytitle="Spectral Power [W/eV]", grid=1,
                 title="Spectral Power (bin: %.3f eV)" % (h5_parameters['photon_energy_bin']))
            de = spectral_power_energy[1] - spectral_power_energy[0]
            plot(spectral_power_energy, (spectral_power * de).cumsum(), xtitle="Photon energy [eV]",
                 ytitle="Cumulated Power [W]", grid=1,
                 title="Cumulated Power (bin: %.3f eV)" % (h5_parameters['photon_energy_bin']))

            #
        # end script
        #
        received_data = DataExchangeObject("XOPPY", "XOPPY_POWERDENSITY_FROM_HARMONICS")
        # horizontal, vertical, power_density, code, power_density_harmonics, energy, spectral_power, spectral_power_energy, flux3D
        # received_data.add_content("xoppy_data", [flux3D / codata.e / 1e3, energy, horizontal, vertical])
        # received_data.add_content("xoppy_code", code)

        received_data.add_content("xoppy_data", [power_density_harmonics / (codata.e * 1e3), energy, horizontal, vertical])
        received_data.add_content("xoppy_data_plot", [horizontal, vertical, power_density, code, power_density_harmonics, energy, spectral_power, spectral_power_energy, flux3D])

        # received_data.add_content("xoppy_code",  "XOPPY_POWERDENSITY_FROM_HARMONICS")
        # received_data.add_content("xoppy_script", "#error")

    #
    app = QApplication(sys.argv)
    w = OWpower3Dcomponent()
    w.acceptExchangeData(received_data)

    w.EL1_FLAG = 2  # 0=Filter 1=Mirror 2 = Aperture 3 magnifier
    w.EL1_HGAP = 100.0
    w.EL1_VGAP = 3.0
    w.EL1_HGAPCENTER = 0.0
    w.EL1_VGAPCENTER = 0.0
    w.PLOT_SETS = 3

    w.show()
    app.exec()
    w.saveSettings()
