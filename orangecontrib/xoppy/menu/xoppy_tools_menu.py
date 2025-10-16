from AnyQt.QtWidgets import QMessageBox

from oasys2.canvas.menus.menu import OMenu

class XoppyToolsMenu(OMenu):

    def __init__(self):
        super().__init__(name="Xoppy Tools")

        self.addSubMenu("Xoppy Tool 1")
        self.addSubMenu("Xoppy Tool 2")
        self.addSeparator()
        self.addSubMenu("Xoppy Tool 3")

    def executeAction_1(self, action):
        self.showWarningMessage("Xoppy Tool 1")

    def executeAction_2(self, action):
        self.showWarningMessage("Xoppy Tool 2")

    def executeAction_3(self, action):
        self.showWarningMessage("Xoppy Tool 3")

    def showConfirmMessage(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setText(message)
        msgBox.setInformativeText(
            "Element will be omitted.\nDo you want to continue importing procedure (a broken link will appear)?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_()
        return ret

    def showWarningMessage(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def showCriticalMessage(self, message):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()
