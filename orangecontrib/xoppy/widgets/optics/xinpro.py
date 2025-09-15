import sys

from orangewidget import gui
from orangewidget.settings import Setting
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.util.exchange import DataExchangeObject
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.xoppy.widgets.gui.ow_xoppy_widget import XoppyWidget
from xoppylib.xoppy_run_binaries import xoppy_calc_inpro

class OWxinpro(XoppyWidget):
    name = "INPRO"
    id = "orange.widgets.dataxinpro"
    description = "Crystal Reflectivity (perfect)"
    icon = "icons/xoppy_xinpro.png"
    priority = 7
    category = ""
    keywords = ["xoppy", "xinpro"]

    CRYSTAL_MATERIAL = Setting(0)
    MODE = Setting(0)
    ENERGY = Setting(8000.0)
    MILLER_INDEX_H = Setting(1)
    MILLER_INDEX_K = Setting(1)
    MILLER_INDEX_L = Setting(1)
    ASYMMETRY_ANGLE = Setting(0.0)
    THICKNESS = Setting(500.0)
    TEMPERATURE = Setting(300.0)
    NPOINTS = Setting(100)
    SCALE = Setting(0)
    XFROM = Setting(-50.0)
    XTO = Setting(50.0)

    def __init__(self):
        super().__init__(show_script_tab=True)

    def build_gui(self):
        box = oasysgui.widgetBox(self.controlArea, self.name + " Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)
        
        
        idx = -1 
        
        #widget index 0 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "CRYSTAL_MATERIAL",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['Silicon', 'Germanium', 'Diamond', 'GaAs', 'GaP', 'InAs', 'InP', 'InSb', 'SiC', 'CsF', 'KCl', 'LiF', 'NaCl', 'Graphite', 'Beryllium'],
                     orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 1 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "MODE",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['Reflectivity in Bragg case', 'Transmission in Bragg case', 'Reflectivity in Laue case', 'Transmission in Laue case'],
                     orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 2 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "ENERGY",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=float, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 3 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "MILLER_INDEX_H",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=int, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 4 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "MILLER_INDEX_K",
                     label=self.unitLabels()[idx], addSpace=False,
                     valueType=int, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 5 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "MILLER_INDEX_L",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=int, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 6 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "ASYMMETRY_ANGLE",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=float, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 7 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "THICKNESS",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=float, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 8 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "TEMPERATURE",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=float, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 9 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "NPOINTS",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=int, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 10 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "SCALE",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['Automatic', 'External'],
                     orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 11 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "XFROM",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=float, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 12 
        idx += 1 
        box1 = gui.widgetBox(box) 
        oasysgui.lineEdit(box1, self, "XTO",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=float, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1) 

        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Crystal material: ','Calculation mode:','Energy [eV]:','Miller index H:','Miller index K:','Miller index L:','Asymmetry angle:','Crystal thickness [microns]:','Crystal temperature [K]:','Number of points: ','Angular limits: ','Theta min [arcsec]:','Theta max [arcsec]:']


    def unitFlags(self):
         return ['True','True','True','True','True','True','True','True','True','True','True','self.SCALE  ==  1','self.SCALE  ==  1']


    def get_help_name(self):
        return 'inpro'

    def check_fields(self):
        self.ENERGY = congruence.checkStrictlyPositiveNumber(self.ENERGY, "Energy")
        self.MILLER_INDEX_H = congruence.checkNumber(self.MILLER_INDEX_H, "Miller index H")
        self.MILLER_INDEX_K = congruence.checkNumber(self.MILLER_INDEX_K, "Miller index K")
        self.MILLER_INDEX_L = congruence.checkNumber(self.MILLER_INDEX_L, "Miller index L")
        self.ASYMMETRY_ANGLE = congruence.checkNumber(self.ASYMMETRY_ANGLE, "Asymmetry angle")
        self.THICKNESS = congruence.checkStrictlyPositiveNumber(self.THICKNESS, "Crystal thickness")
        self.TEMPERATURE = congruence.checkNumber(self.TEMPERATURE, "Crystal temperature")
        self.NPOINTS = congruence.checkStrictlyPositiveNumber(self.NPOINTS, "Number of points")
        
        if self.SCALE == 1:
            self.XFROM = congruence.checkNumber(self.XFROM, "Theta min")
            self.XTO = congruence.checkNumber(self.XTO, "Theta max")
            congruence.checkLessThan(self.XFROM, self.XTO, "Theta min", "Theta max")


    def do_xoppy_calculation(self):
        out_file = xoppy_calc_inpro(
            CRYSTAL_MATERIAL = self.CRYSTAL_MATERIAL,
            MODE             = self.MODE,
            ENERGY           = self.ENERGY,
            MILLER_INDEX_H   = self.MILLER_INDEX_H,
            MILLER_INDEX_K   = self.MILLER_INDEX_K,
            MILLER_INDEX_L   = self.MILLER_INDEX_L,
            ASYMMETRY_ANGLE  = self.ASYMMETRY_ANGLE,
            THICKNESS        = self.THICKNESS,
            TEMPERATURE      = self.TEMPERATURE,
            NPOINTS          = self.NPOINTS,
            SCALE            = self.SCALE,
            XFROM            = self.XFROM,
            XTO              = self.XTO,
        )

        dict_parameters = {
            "CRYSTAL_MATERIAL" : self.CRYSTAL_MATERIAL,
            "MODE"             : self.MODE,
            "ENERGY"           : self.ENERGY,
            "MILLER_INDEX_H"   : self.MILLER_INDEX_H,
            "MILLER_INDEX_K"   : self.MILLER_INDEX_K,
            "MILLER_INDEX_L"   : self.MILLER_INDEX_L,
            "ASYMMETRY_ANGLE"  : self.ASYMMETRY_ANGLE,
            "THICKNESS"        : self.THICKNESS,
            "TEMPERATURE"      : self.TEMPERATURE,
            "NPOINTS"          : self.NPOINTS,
            "SCALE"            : self.SCALE,
            "XFROM"            : self.XFROM,
            "XTO"              : self.XTO,
        }

        script = self.script_template().format_map(dict_parameters)

        self.xoppy_script.set_code(script)

        return out_file

    def script_template(self):
        return """
#
# script to make the calculations (created by XOPPY:inpro)
#
from xoppylib.xoppy_run_binaries import xoppy_calc_inpro

out_file =  xoppy_calc_inpro(
            CRYSTAL_MATERIAL = {CRYSTAL_MATERIAL},
            MODE             = {MODE},
            ENERGY           = {ENERGY},
            MILLER_INDEX_H   = {MILLER_INDEX_H},
            MILLER_INDEX_K   = {MILLER_INDEX_K},
            MILLER_INDEX_L   = {MILLER_INDEX_L},
            ASYMMETRY_ANGLE  = {ASYMMETRY_ANGLE},
            THICKNESS        = {THICKNESS},
            TEMPERATURE      = {TEMPERATURE},
            NPOINTS          = {NPOINTS},
            SCALE            = {SCALE},
            XFROM            = {XFROM},
            XTO              = {XTO},
        )

#
# example plot
#
if True:
    import numpy
    from srxraylib.plot.gol import plot
    
    data = numpy.loadtxt(out_file)
    angle = data[:,0]
    reflectivity_s = data[:,1]
    reflectivity_p = data[:,2]
    
    plot(angle,reflectivity_s,angle,reflectivity_p,
        xtitle="Theta-ThetaB [arcsec]",ytitle="Reflectivity",title="inpro crystal reflectivity",
        legend=["s-polarized reflectivity","p-polarized reflectivity"],xlog=False,ylog=False,show=True)

#
# end script
#
"""

    def get_data_exchange_widget_name(self):
        return "XINPRO"

    def add_specific_content_to_calculated_data(self, calculated_data):
        calculated_data.add_content("units_to_degrees",  0.000277777805)

    def getTitles(self):
        return ['s-polarized reflectivity', 'p-polarized reflectivity']

    def getXTitles(self):
        return ["Theta-ThetaB [arcsec]", "Theta-ThetaB [arcsec]"]

    def getYTitles(self):
        return ['s-polarized reflectivity', 'p-polarized reflectivity']

    def getVariablesToPlot(self):
        return [(0, 1), (0, 2)]

    def getLogPlot(self):
        return [(False, False), (False, False)]

add_widget_parameters_to_module(__name__)
