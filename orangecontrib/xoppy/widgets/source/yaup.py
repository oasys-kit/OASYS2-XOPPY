import sys, os
import numpy
from AnyQt.QtWidgets import QSizePolicy

from orangewidget import gui
from orangewidget.settings import Setting

from oasys2.widget import gui as oasysgui
from oasys2.widget.util.exchange import DataExchangeObject
from oasys2.widget.util.widget_util import EmittingStream, TTYGrabber
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from syned.widget.widget_decorator import WidgetDecorator
import syned.beamline.beamline as synedb
from syned.storage_ring.magnetic_structures.insertion_device import InsertionDevice as synedid

from orangecontrib.xoppy.widgets.gui.ow_xoppy_widget import XoppyWidget
from orangecontrib.xoppy.widgets.gui.text_window import TextWindow

from xoppylib.xoppy_util import locations
from xoppylib.xoppy_run_binaries import xoppy_calc_yaup

class OWyaup(XoppyWidget):
    name = "Tapered Undulator YAUP"
    id = "orange.widgets.datayaup"
    description = "xoppy application to compute..."
    icon = "icons/xoppy_undulator_spectrum.png"
    author = "srio@esrf.eu"
    maintainer_email = "srio@esrf.eu"
    priority = 8.5
    category = ""
    keywords = ["xoppy", "undulator spectrum", "tapered undulator", "yaup"]

    #yaup
    TITLE            = Setting("YAUP EXAMPLE (ESRF BL-8)")
    PERIOD           = Setting(4.0)
    NPER             = Setting(42)
    NPTS             = Setting(40)
    EMIN             = Setting(3000.0)
    EMAX             = Setting(30000.0)
    NENERGY          = Setting(100)
    ENERGY           = Setting(6.04)
    CUR              = Setting(0.1)
    SIGX             = Setting(0.426)
    SIGY             = Setting(0.085)
    SIGX1            = Setting(0.017)
    SIGY1            = Setting(0.0085)
    D                = Setting(30.0)
    XPC              = Setting(0.0)
    YPC              = Setting(0.0)
    XPS              = Setting(2.0)
    YPS              = Setting(2.0)
    NXP              = Setting(69)
    NYP              = Setting(69)
    MODE             = Setting(4)
    NSIG             = Setting(2)
    TRAJECTORY       = Setting("new+keep")
    XSYM             = Setting("yes")
    HANNING          = Setting(0)
    BFILE            = Setting("undul.bf")
    TFILE            = Setting("undul.traj")
    # B field
    BFIELD_FLAG      = Setting(1)
    BFIELD_ASCIIFILE = Setting("")
    PERIOD_BFIELD    = Setting(4.0)
    NPER_BFIELD      = Setting(42)
    NPTS_BFIELD      = Setting(40)
    IMAGNET          = Setting(0)
    ITYPE            = Setting(0)
    K                = Setting(1.38)
    GAP              = Setting(2.0)
    GAPTAP           = Setting(10.0)
    FILE             = Setting("undul.bf")
    I2TYPE           = Setting(0)
    A1               = Setting(0.5)
    A2               = Setting(1.0)

    class Inputs:
        syned_data = WidgetDecorator.syned_input_data()

    def __init__(self):
        super().__init__(show_script_tab=True)

    def build_gui(self):
        self.left_side.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.left_side.setMaximumWidth(self.CONTROL_AREA_WIDTH + 20)
        self.left_side.updateGeometry()

        # self.IMAGE_WIDTH = 850

        # box = oasysgui.widgetBox(self.controlArea, "Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        ##########################
        self.controls_tabs = oasysgui.tabWidget(self.controlArea)
        boxB = oasysgui.createTabPage(self.controls_tabs, "B field")
        box = oasysgui.createTabPage(self.controls_tabs, "Undulator+Ring")
        boxS = oasysgui.createTabPage(self.controls_tabs, "Settings")
        ##########################


        idx = -1

        
        #widget index 0 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "TITLE",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 1 
        idx += 1 
        box1 = gui.widgetBox(box) 
        self.id_PERIOD = gui.lineEdit(box1, self, "PERIOD",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 2 
        idx += 1 
        box1 = gui.widgetBox(box) 
        self.id_NPER = gui.lineEdit(box1, self, "NPER",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 3 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "NPTS",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 4 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "EMIN",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 5 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "EMAX",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 6 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "NENERGY",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 7 
        idx += 1 
        box1 = gui.widgetBox(box) 
        self.id_ENERGY = gui.lineEdit(box1, self, "ENERGY",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 8 
        idx += 1 
        box1 = gui.widgetBox(box) 
        self.id_CUR = gui.lineEdit(box1, self, "CUR",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 9 
        idx += 1 
        box1 = gui.widgetBox(box) 
        self.id_SIGX = gui.lineEdit(box1, self, "SIGX",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 10 
        idx += 1 
        box1 = gui.widgetBox(box) 
        self.id_SIGY = gui.lineEdit(box1, self, "SIGY",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 11 
        idx += 1 
        box1 = gui.widgetBox(box) 
        self.id_SIGX1 = gui.lineEdit(box1, self, "SIGX1",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 12 
        idx += 1 
        box1 = gui.widgetBox(box) 
        self.id_SIGY1 = gui.lineEdit(box1, self, "SIGY1",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 13 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "D",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 14 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "XPC",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 15 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "YPC",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 16 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "XPS",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 17 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "YPS",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=float)
        self.show_at(self.unitFlags()[idx], box1) 

        ####################
        ####################
        #################### Setting panel
        ####################
        ####################

        #widget index 18 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "NXP",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 19 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "NYP",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 20 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "MODE",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 21 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "NSIG",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 22 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "TRAJECTORY",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 23 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "XSYM",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 24 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "HANNING",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                    valueType=int)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 25 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "BFILE",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True)
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 26 
        idx += 1 
        box1 = gui.widgetBox(boxS)
        gui.lineEdit(box1, self, "TFILE",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True)
        self.show_at(self.unitFlags()[idx], box1) 


        ##########################
        ##########################
        ##########################  Bfield Panel
        ##########################
        ##########################

        # widget index 27
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.comboBox(box1, self, "BFIELD_FLAG",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=['from ASCII file', 'from BFIELD preprocessor', 'linear B field'],
                      orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1)


        # widget index 28
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.lineEdit(box1, self, "BFIELD_ASCIIFILE",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True)
        self.show_at(self.unitFlags()[idx], box1)


        # widget index 29
        idx += 1
        box1 = gui.widgetBox(boxB)
        self.id_PERIOD_BFIELD = gui.lineEdit(box1, self, "PERIOD_BFIELD",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                     valueType=float)
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 30
        idx += 1
        box1 = gui.widgetBox(boxB)
        self.id_NPER_BFIELD = gui.lineEdit(box1, self, "NPER_BFIELD",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                     valueType=int)
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 31
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.lineEdit(box1, self, "NPTS_BFIELD",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                     valueType=int)
        self.show_at(self.unitFlags()[idx], box1)



        # widget index 32
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.comboBox(box1, self, "IMAGNET",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=['Nd-Fe-B', 'Sm-Co'],
                      orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 33
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.comboBox(box1, self, "ITYPE",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=['planar undulator', 'tapered undulator'],
                      orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 34
        idx += 1
        box1 = gui.widgetBox(boxB)
        self.id_K = gui.lineEdit(box1, self, "K",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                     valueType=float)
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 35
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.lineEdit(box1, self, "GAP",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                     valueType=float)
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 36
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.lineEdit(box1, self, "GAPTAP",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                     valueType=float)
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 37
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.lineEdit(box1, self, "FILE",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True)
        self.show_at(self.unitFlags()[idx], box1)

        # linear B field
        # NPTS: yaupstr.npts, $
        # ITYPE: ['0', 'Magnetic field B [Tesla]', 'Deflection parameter K'], $
        # a1: 0.5, a2: 1.0, FILE: yaupstr.bfile}

        # widget index 38
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.comboBox(box1, self, "I2TYPE",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=['Magnetic field B [Tesla]', 'Deflection parameter K'],
                      orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 39
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.lineEdit(box1, self, "A1",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                     valueType=float)
        self.show_at(self.unitFlags()[idx], box1)

        # widget index 40
        idx += 1
        box1 = gui.widgetBox(boxB)
        gui.lineEdit(box1, self, "A2",
                     label=self.unitLabels()[idx],
                     orientation="horizontal", labelWidth=225, addSpace=True,
                     valueType=float)
        self.show_at(self.unitFlags()[idx], box1)



        gui.rubber(self.controlArea)

    def unitLabels(self):
        return [
            # 'TITLE', 'PERIOD', 'NPER', 'NPTS',
            #     'EMIN', 'EMAX', 'NENERGY',
            #     'ENERGY', 'CUR',
            #     'SIGX', 'SIGY', 'SIGX1', 'SIGY1',
            #     'D', 'XPC', 'YPC', 'XPS', 'YPS', 'NXP', 'NYP',
            #     'MODE', 'NSIG', 'TRAJECTORY', 'XSYM', 'HANNING', 'BFILE', 'TFILE',
            ' Title:  ',
            'PERIOD - magnet period (cm)',
            'NPER - number of periods',
            'NPTS - number of point/period',
            'EMIN - minimum energy (eV)',
            'EMAX - maximum energy (eV)',
            'NE - number of energy points',
            'ENERGY - e energy (GeV)',
            'CUR - e current (A)',
            'SIGX - H rms e beam (mm)',
            'SIGY - V rms e beam (mm)',
            'SIGX1 - rms H e div (mrad)',
            'SIGY1 - rms V e div (mrad)',
            'D - dist und-observator (m)',
            'XPC - H obs position (mm)',
            'YPC - V obs position (mm)',
            'XPS - H acceptance (mm\mrad)',
            'YPS - V acceptance (mm\mrad)',
            'NXP - no acceptance pts (H)',
            'NYP - no acceptance pts (V)',
            'MODE - (see help)',
            'NSIG - (see help)',
            'TRAJECTORY - calculation flag',
            'XSYM - horizontal symmetry',
            'HANNING - (see help)',
            'BFILE - B filename',
            'TFILE - Traj filename',
            'BFIELD_FLAG',
            'BFIELD_ASCIIFILE - Filename: ',
         # 'PERIOD', 'NPER', 'NPTS',
            'PERIOD_BFIELD - magnet period (cm)',
            'N_BFIELD - number of periods'      ,
            'NPTS_BFIELD - nb of point / period',
        # 'IMAGNET', 'ITYPE', 'K', 'GAP', 'GAPTAP', 'FILE',
            'IMAGNET - Undulator Magnet: '         ,
            'ITYPE - Undulator type: '           ,
            'K - K field parameter'      ,
            'GAP - initial gap (cm)'     ,
            'GAPTAP - Gap taper (%)'     ,
            'FILE - Output file name'    ,
         #    aa       =  {PERIOD: yaupstr.period, NPER: yaupstr.nper, $
         # NPTS: yaupstr.npts, $
         # ITYPE: ['0', 'Magnetic field B [Tesla]', 'Deflection parameter K'], $
         # a1: 0.5, a2: 1.0, FILE: yaupstr.bfile}
         #
         # titles = ['PERIOD - magnet period (cm)', 'N - number of periods'  $
         # , 'NPTS - nb of point / period', 'Input parameter: '                 $
         # , 'From:', 'To:', 'FILE - Output (binary) file name'
            'Input parameter: ',
            'From:',
            'To:'
         ]

    def unitFlags(self):
         return ['True','True','True','True',
                 'True','True','True',
                 'True','True',
                 'True','True','True','True',
                 'True','True','True','True','True','True','True',
                 'True','True','True','True','True','True','True',
                 'True',
                 'self.BFIELD_FLAG == 0',
                 'self.BFIELD_FLAG > 0','self.BFIELD_FLAG > 0','self.BFIELD_FLAG > 0',
                 'self.BFIELD_FLAG == 1','self.BFIELD_FLAG == 1','self.BFIELD_FLAG == 1 and self.ITYPE == 0','self.BFIELD_FLAG == 1 and self.ITYPE == 1','self.BFIELD_FLAG == 1 and self.ITYPE == 1','self.BFIELD_FLAG > 0',
                 'self.BFIELD_FLAG == 2','self.BFIELD_FLAG == 2','self.BFIELD_FLAG == 2',]

    def check_fields(self):
        pass # TODO later
        # self.ENERGY = congruence.checkStrictlyPositiveNumber(self.ENERGY, "Electron Energy")
        # self.CURRENT = congruence.checkStrictlyPositiveNumber(self.CURRENT, "Current")
        # self.ENERGY_SPREAD = congruence.checkStrictlyPositiveNumber(self.ENERGY_SPREAD, "Energy Spread")
        # self.SIGX  = congruence.checkPositiveNumber(self.SIGX , "Sigma X")
        # self.SIGY  = congruence.checkPositiveNumber(self.SIGY , "Sigma Y")
        # self.SIGX1 = congruence.checkPositiveNumber(self.SIGX1, "Sigma X'")
        # self.SIGY1 = congruence.checkPositiveNumber(self.SIGY1, "Sigma Y'")
        # self.PERIOD = congruence.checkStrictlyPositiveNumber(self.PERIOD, "Period length")
        # self.NP = congruence.checkStrictlyPositiveNumber(self.NP, "Number of periods")
        # self.EMIN = congruence.checkPositiveNumber(self.EMIN, "E1 minimum energy")
        # self.EMAX = congruence.checkStrictlyPositiveNumber(self.EMAX, "E1 maximum energy")
        # congruence.checkLessThan(self.EMIN, self.EMAX, "E1 minimum energy", "E1 maximum energy")
        # self.N = congruence.checkStrictlyPositiveNumber(self.N, "Number of Energy Points")
        # self.HARMONIC_FROM = congruence.checkStrictlyPositiveNumber(self.HARMONIC_FROM, "Minimum harmonic number")
        # self.HARMONIC_TO = congruence.checkStrictlyPositiveNumber(self.HARMONIC_TO, "Maximum harmonic number")
        # congruence.checkLessThan(self.HARMONIC_FROM, self.HARMONIC_TO, "Minimum harmonic number", "Maximum harmonic number")
        # self.HARMONIC_STEP = congruence.checkStrictlyPositiveNumber(self.HARMONIC_STEP, "Harmonic step size")
        # self.NEKS  = congruence.checkPositiveNumber(self.NEKS , "Neks OR % Helicity")

    def do_xoppy_calculation(self):
        sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        grabber = TTYGrabber()
        grabber.start()

        self.progressBarInit()
        self.progressBarSet(2)

        e,f,spectral_power,cumulated_power =  xoppy_calc_yaup(
            #yaup
            TITLE            = self.TITLE            ,
            PERIOD           = self.PERIOD           ,
            NPER             = self.NPER             ,
            NPTS             = self.NPTS             ,
            EMIN             = self.EMIN             ,
            EMAX             = self.EMAX             ,
            NENERGY          = self.NENERGY          ,
            ENERGY           = self.ENERGY           ,
            CUR              = self.CUR              ,
            SIGX             = self.SIGX             ,
            SIGY             = self.SIGY             ,
            SIGX1            = self.SIGX1            ,
            SIGY1            = self.SIGY1            ,
            D                = self.D                ,
            XPC              = self.XPC              ,
            YPC              = self.YPC              ,
            XPS              = self.XPS              ,
            YPS              = self.YPS              ,
            NXP              = self.NXP              ,
            NYP              = self.NYP              ,
            MODE             = self.MODE             ,
            NSIG             = self.NSIG             ,
            TRAJECTORY       = self.TRAJECTORY       ,
            XSYM             = self.XSYM             ,
            HANNING          = self.HANNING          ,
            BFILE            = self.BFILE            ,
            TFILE            = self.TFILE            ,
            # B field
            BFIELD_FLAG      = self.BFIELD_FLAG      ,
            BFIELD_ASCIIFILE = self.BFIELD_ASCIIFILE ,
            PERIOD_BFIELD    = self.PERIOD_BFIELD    ,
            NPER_BFIELD      = self.NPER_BFIELD      ,
            NPTS_BFIELD      = self.NPTS_BFIELD      ,
            IMAGNET          = self.IMAGNET          ,
            ITYPE            = self.ITYPE            ,
            K                = self.K                ,
            GAP              = self.GAP              ,
            GAPTAP           = self.GAPTAP           ,
            FILE             = self.FILE             ,
            I2TYPE           = self.I2TYPE           ,
            A1               = self.A1               ,
            A2               = self.A2               ,
            )

        grabber.stop()
        for row in grabber.ttyData:
            self.writeStdOut("      %s" % (row))

        dict_parameters = {
            "TITLE"            : self.TITLE            ,
            "PERIOD"           : self.PERIOD           ,
            "NPER"             : self.NPER             ,
            "NPTS"             : self.NPTS             ,
            "EMIN"             : self.EMIN             ,
            "EMAX"             : self.EMAX             ,
            "NENERGY"          : self.NENERGY          ,
            "ENERGY"           : self.ENERGY           ,
            "CUR"              : self.CUR              ,
            "SIGX"             : self.SIGX             ,
            "SIGY"             : self.SIGY             ,
            "SIGX1"            : self.SIGX1            ,
            "SIGY1"            : self.SIGY1            ,
            "D"                : self.D                ,
            "XPC"              : self.XPC              ,
            "YPC"              : self.YPC              ,
            "XPS"              : self.XPS              ,
            "YPS"              : self.YPS              ,
            "NXP"              : self.NXP              ,
            "NYP"              : self.NYP              ,
            "MODE"             : self.MODE             ,
            "NSIG"             : self.NSIG             ,
            "TRAJECTORY"       : self.TRAJECTORY       ,
            "XSYM"             : self.XSYM             ,
            "HANNING"          : self.HANNING          ,
            "BFILE"            : self.BFILE            ,
            "TFILE"            : self.TFILE            ,
            "BFIELD_FLAG"      : self.BFIELD_FLAG      ,
            "BFIELD_ASCIIFILE" : self.BFIELD_ASCIIFILE ,
            "PERIOD_BFIELD"    : self.PERIOD_BFIELD    ,
            "NPER_BFIELD"      : self.NPER_BFIELD      ,
            "NPTS_BFIELD"      : self.NPTS_BFIELD      ,
            "IMAGNET"          : self.IMAGNET          ,
            "ITYPE"            : self.ITYPE            ,
            "K"                : self.K                ,
            "GAP"              : self.GAP              ,
            "GAPTAP"           : self.GAPTAP           ,
            "FILE"             : self.FILE             ,
            "I2TYPE"           : self.I2TYPE           ,
            "A1"               : self.A1               ,
            "A2"               : self.A2               ,
        }

        script = self.script_template().format_map(dict_parameters)

        self.xoppy_script.set_code(script)


        return e,f,spectral_power,cumulated_power,script

    def script_template(self):
        return """
#
# script to make the calculations (created by XOPPY:YAUP)
#
from xoppylib.xoppy_run_binaries import xoppy_calc_yaup

energy, flux, spectral_power, cumulated_power =  xoppy_calc_yaup(
            #yaup
            TITLE            = "{TITLE}",
            PERIOD           = {PERIOD},
            NPER             = {NPER},
            NPTS             = {NPTS},
            EMIN             = {EMIN},
            EMAX             = {EMAX},
            NENERGY          = {NENERGY},
            ENERGY           = {ENERGY},
            CUR              = {CUR},
            SIGX             = {SIGX},
            SIGY             = {SIGY},
            SIGX1            = {SIGX1},
            SIGY1            = {SIGY1},
            D                = {D},
            XPC              = {XPC},
            YPC              = {YPC},
            XPS              = {XPS},
            YPS              = {YPS},
            NXP              = {NXP},
            NYP              = {NYP},
            MODE             = {MODE},
            NSIG             = {NSIG},
            TRAJECTORY       = "{TRAJECTORY}",
            XSYM             = "{XSYM}",
            HANNING          = {HANNING},
            BFILE            = "{BFILE}",
            TFILE            = "{TFILE}",
            # B field
            BFIELD_FLAG      = {BFIELD_FLAG},
            BFIELD_ASCIIFILE = "{BFIELD_ASCIIFILE}",
            PERIOD_BFIELD    = {PERIOD_BFIELD},
            NPER_BFIELD      = {NPER_BFIELD},
            NPTS_BFIELD      = {NPTS_BFIELD},
            IMAGNET          = {IMAGNET},
            ITYPE            = {ITYPE},
            K                = {K},
            GAP              = {GAP},
            GAPTAP           = {GAPTAP},
            FILE             = "{FILE}",
            I2TYPE           = {I2TYPE},
            A1               = {A1},
            A2               = {A2},
        )

#
# example plot
#
if True:
    import numpy
    from srxraylib.plot.gol import plot
    
    bfield = numpy.loadtxt("bfield.dat",skiprows=3)
    traj = numpy.loadtxt("undul_traj.dat",skiprows=2)
    
    plot(bfield[:, 0], bfield[:, -1],
        title="Magnetic Field", xtitle="Z coordinate [cm]", ytitle="Total field intensity [T]",
        show=False)
    plot(traj[:, 0],traj[:, 2],
        title="Electron Trajectory", xtitle="z [cm]", ytitle="x [cm]",
        show=False)
        
    plot(energy,flux,
        xtitle="Photon energy [eV]",ytitle="Flux [photons/s/0.1%bw]",title="WS Flux",
        xlog=False,ylog=False,show=False)
    plot(energy,spectral_power,
        xtitle="Photon energy [eV]",ytitle="Power [W/eV]",title="WS Spectral Power",
        xlog=False,ylog=False,show=False)
    plot(energy,cumulated_power,
        xtitle="Photon energy [eV]",ytitle="Cumulated Spectral Power [W]",title="WS Cumulated Power",
        xlog=False,ylog=False,show=True)

#
# end script
#
"""

    def extract_data_from_xoppy_output(self, calculation_output):
        e, f, spectral_power, cumulated_power,script = calculation_output

        # send exchange
        calculated_data = DataExchangeObject("XOPPY", self.get_data_exchange_widget_name())

        data_to_send = numpy.zeros((e.size, 4))
        data_to_send[:, 0] = e
        data_to_send[:, 1] = f
        data_to_send[:, 2] = spectral_power
        data_to_send[:, 3] = cumulated_power

        calculated_data.add_content("xoppy_data", data_to_send)
        calculated_data.add_content("xoppy_data_bfield", numpy.loadtxt("bfield.dat",skiprows=3))
        calculated_data.add_content("xoppy_data_traj", numpy.loadtxt("undul_traj.dat",skiprows=2))

        return calculated_data

    def plot_results(self, calculated_data, progressBarValue=80):

        if not self.view_type == 0:
            if not calculated_data is None:
                self.view_type_combo.setEnabled(False)

                #
                #
                #
                try:
                    xoppy_data_bfield = calculated_data.get_content("xoppy_data_bfield")

                    self.plot_histo(xoppy_data_bfield[:, 0],
                                    xoppy_data_bfield[:, -1],
                                    progressBarValue + 10,
                                    tabs_canvas_index=0,
                                    plot_canvas_index=0,
                                    title="Magnetic Field",
                                    xtitle="Z coordinate [cm]",
                                    ytitle="Total field intensity [T]",
                                    control=True)
                except:
                    pass
                #
                #
                #
                try:
                    xoppy_data_traj = calculated_data.get_content("xoppy_data_traj")

                    self.plot_histo(xoppy_data_traj[:, 0],
                                    xoppy_data_traj[:, 2],
                                    progressBarValue + 10,
                                    tabs_canvas_index=1,
                                    plot_canvas_index=1,
                                    title="Electron Trajectory",
                                    xtitle="z [cm]",
                                    ytitle="x [cm]",
                                    control=True)
                except:
                    pass

                #
                #
                #
                try:

                    xoppy_data = calculated_data.get_content("xoppy_data")

                    self.plot_histo(xoppy_data[:, 0],
                                    xoppy_data[:, 1],
                                    progressBarValue + 30,
                                    tabs_canvas_index=2,
                                    plot_canvas_index=2,
                                    title="Flux",
                                    xtitle="Photon energy [eV]",
                                    ytitle="Flux [photons/s/0.1%bw]",
                                    control=True)

                    self.plot_histo(xoppy_data[:, 0],
                                    xoppy_data[:, 2],
                                    progressBarValue + 40,
                                    tabs_canvas_index=3,
                                    plot_canvas_index=3,
                                    title="Spectral Power",
                                    xtitle="Photon energy [eV]",
                                    ytitle="Spectral Power [W/eV]",
                                    control=True)


                    self.plot_histo(xoppy_data[:, 0],
                                    xoppy_data[:, 3],
                                    progressBarValue + 50,
                                    tabs_canvas_index=4,
                                    plot_canvas_index=4,
                                    title="Cumulated Spectral Power",
                                    xtitle="Photon energy [eV]",
                                    ytitle="Cumulated Spectral Power [W]",
                                    control=True)
                except:
                    pass

    def get_data_exchange_widget_name(self):
        return "YAUP"

    def getTitles(self):
        return ["B field", "Trajectory", "Flux", "Spectral power","Cumulated spectral power"]

    @Inputs.syned_data
    def receive_syned_data(self, data):
        if isinstance(data, synedb.Beamline):
            if not data._light_source is None and isinstance(data.get_light_source().get_magnetic_structure(), synedid):
                light_source = data.get_light_source()

                self.ENERGY = light_source.get_electron_beam().energy()
                self.ENERGY_SPREAD = light_source.get_electron_beam()._energy_spread
                self.CUR = light_source._electron_beam.current()

                x, xp, y, yp = light_source.get_electron_beam().get_sigmas_all()

                self.SIGX = 1e3 * x
                self.SIGY = 1e3 * y
                self.SIGX1 = 1e3 * xp
                self.SIGY1 = 1e3 * yp
                self.PERIOD = 100.0 * light_source.get_magnetic_structure().period_length()
                self.NPER = light_source.get_magnetic_structure().number_of_periods()

                # self.EMIN = light_source.get_magnetic_structure().resonance_energy(gamma=light_source.get_electron_beam().gamma())
                # self.EMAX = 5 * self.EMIN

                self.NPTS_BFIELD = self.NPTS
                self.NPER_BFIELD = self.NPER
                self.PERIOD_BFIELD = self.PERIOD

                self.BFIELD_FLAG = 1
                self.ITYPE = 0

                self.K = light_source.get_magnetic_structure().K_vertical()
                self.set_enabled(False)

            else:
                self.set_enabled(True)
        else:
            self.set_enabled(True)

    def set_enabled(self,value):

        self.id_ENERGY.setEnabled(value)
        self.id_SIGX.setEnabled(value)
        self.id_SIGX1.setEnabled(value)
        self.id_SIGY.setEnabled(value)
        self.id_SIGY1.setEnabled(value)
        self.id_CUR.setEnabled(value)
        self.id_PERIOD.setEnabled(value)
        self.id_NPER.setEnabled(value)
        self.id_K.setEnabled(value)

        self.id_NPER_BFIELD.setEnabled(value)
        self.id_PERIOD_BFIELD.setEnabled(value)



    def defaults(self):
         self.reset_settings()
         self.compute()
         return

    def get_help_name(self):
        return 'yaup'

    def help1(self):
        home_doc = locations.home_doc()
        filename1 = os.path.join(home_doc, self.get_help_name() + '.txt')
        TextWindow(file=filename1,parent=self)

add_widget_parameters_to_module(__name__)
