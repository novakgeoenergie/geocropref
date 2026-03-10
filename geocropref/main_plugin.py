from qgis.PyQt.QtWidgets import QAction
from .crop_dialog import CropDialog

class GeoCropRefPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = None
        self.action = None

    def initGui(self):
        # Vytvoření akce v menu (Anglicky)
        self.action = QAction("Crop Image for Georeferencing", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        # Přidání do menu Rastr
        self.iface.addPluginToRasterMenu("Geo Crop Ref", self.action)

    def unload(self):
        # Odstranění z menu
        self.iface.removePluginRasterMenu("Geo Crop Ref", self.action)

    def run(self):
        # Otevření hlavního okna
        self.dialog = CropDialog(self.iface)
        self.dialog.show()