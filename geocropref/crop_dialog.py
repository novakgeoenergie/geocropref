import os
import time
import tempfile
from osgeo import gdal

from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                 QPushButton, QFileDialog, QMessageBox, 
                                 QCheckBox, QAction, QApplication)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsRasterLayer, QgsWkbTypes, QgsPointXY)
from qgis.gui import QgsMapCanvas, QgsMapToolEmitPoint, QgsRubberBand

# --- Rectangle Drawing Tool ---
class CropTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setColor(QColor(255, 0, 0, 80)) # Semi-transparent red
        self.rubberBand.setStrokeColor(QColor(255, 0, 0, 255))
        self.rubberBand.setWidth(2)
        
        self.startPoint = None
        self.isDrawing = False
        self.extent = None

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.startPoint = self.toMapCoordinates(e.pos())
            self.isDrawing = True
            self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)

    def canvasMoveEvent(self, e):
        if not self.isDrawing:
            return
        
        endPoint = self.toMapCoordinates(e.pos())
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        
        point1 = QgsPointXY(self.startPoint.x(), self.startPoint.y())
        point2 = QgsPointXY(endPoint.x(), self.startPoint.y())
        point3 = QgsPointXY(endPoint.x(), endPoint.y())
        point4 = QgsPointXY(self.startPoint.x(), endPoint.y())
        
        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, True)

    def canvasReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.isDrawing = False
            if self.rubberBand.asGeometry().boundingBox().isEmpty():
                self.extent = None
            else:
                self.extent = self.rubberBand.asGeometry().boundingBox()

# --- Main Plugin Dialog ---
class CropDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("GeoCropRef - Pre-Georeferencing Crop")
        self.resize(800, 600)
        
        self.layer = None
        self.filepath = None
        
        self.setup_ui()
        
        self.crop_tool = CropTool(self.canvas)
        self.canvas.setMapTool(self.crop_tool)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("1. Load Image")
        self.btn_load.clicked.connect(self.load_image)
        
        # Checkbox for Temporary saving
        self.chk_temp = QCheckBox("Save as Temporary File")
        self.chk_temp.setChecked(True)
        self.chk_temp.setToolTip("Saves to your OS Temp folder so it doesn't clutter your hard drive.")
        
        self.btn_crop = QPushButton("2. Crop and Open Georeferencer")
        self.btn_crop.clicked.connect(self.execute_crop)
        self.btn_crop.setEnabled(False)
        
        controls_layout.addWidget(self.btn_load)
        controls_layout.addWidget(self.chk_temp)
        controls_layout.addWidget(self.btn_crop)
        layout.addLayout(controls_layout)
        
        # Map Canvas
        self.canvas = QgsMapCanvas(self)
        self.canvas.setCanvasColor(QColor(240, 240, 240))
        layout.addWidget(self.canvas)

    def load_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Rasters (*.tif *.jpg *.png *.jpeg)")
        if not filepath:
            return
            
        self.filepath = filepath
        self.layer = QgsRasterLayer(filepath, "Preview")
        
        if not self.layer.isValid():
            QMessageBox.critical(self, "Error", "Failed to load image.")
            return

        self.canvas.setExtent(self.layer.extent())
        self.canvas.setLayers([self.layer])
        self.canvas.refresh()
        
        self.btn_crop.setEnabled(True)

    def execute_crop(self):
        if not self.crop_tool.extent:
            QMessageBox.warning(self, "Warning", "Please draw a crop rectangle first!")
            return
            
        ext = self.crop_tool.extent
        layer_ext = self.layer.extent()
        
        # Calculate pixel window (srcWin) to avoid coordinate bugs
        layer_width_px = self.layer.width()
        layer_height_px = self.layer.height()
        
        scale_x = layer_width_px / layer_ext.width()
        scale_y = layer_height_px / layer_ext.height()
        
        xoff = int((ext.xMinimum() - layer_ext.xMinimum()) * scale_x)
        yoff = int((layer_ext.yMaximum() - ext.yMaximum()) * scale_y)
        xsize = int(ext.width() * scale_x)
        ysize = int(ext.height() * scale_y)
        
        # Safety limits
        xoff = max(0, xoff)
        yoff = max(0, yoff)
        xsize = min(xsize, layer_width_px - xoff)
        ysize = min(ysize, layer_height_px - yoff)
        
        src_win = [xoff, yoff, xsize, ysize]
        
        # Decide output path
        if self.chk_temp.isChecked():
            temp_dir = tempfile.gettempdir()
            unique_id = int(time.time())
            output_path = os.path.join(temp_dir, f"geocrop_temp_{unique_id}.tif")
            output_path = os.path.normpath(output_path)
        else:
            output_path, _ = QFileDialog.getSaveFileName(self, "Save Cropped Image", "", "GeoTIFF (*.tif)")
            if not output_path:
                return # User cancelled save dialog
        
        try:
            # Crop via GDAL
            options = gdal.TranslateOptions(format="GTiff", srcWin=src_win)
            gdal.Translate(output_path, self.filepath, options=options)
            
            # Copy path to clipboard as a backup
            QApplication.clipboard().setText(output_path)
            
            # Close this crop dialog window
            self.close()
            
            # Magic: Open Georeferencer and push the file into it
            success = self.open_georeferencer_with_file(output_path)
            
            if not success:
                # Fallback message if the auto-load trick fails
                QMessageBox.information(
                    self.iface.mainWindow(), 
                    "Partial Success", 
                    "Image cropped! The file path has been COPIED TO YOUR CLIPBOARD.\n\n"
                    "In the Georeferencer, click 'Open Raster', click in the File Name box, and press Ctrl+V (Paste)."
                )
                    
        except Exception as e:
            QMessageBox.critical(self, "GDAL Error", str(e))

    def open_georeferencer_with_file(self, file_path):
        """ Finds the Georeferencer window and pushes the file path directly into it """
        try:
            # 1. Trigger the menu action to open Georeferencer
            geo_action = self.iface.mainWindow().findChild(QAction, 'mActionShowGeoreferencer')
            if geo_action:
                geo_action.trigger()
            
            # 2. Give QGIS a moment to actually build and show the window
            QApplication.processEvents()
            time.sleep(0.1) 
            QApplication.processEvents()
            
            # 3. Search through all open top-level windows
            for widget in QApplication.topLevelWidgets():
                if widget.objectName() == "QgsGeoreferencerMainWindow":
                    # 4. We found it! Call the internal C++ method to load the raster
                    if hasattr(widget, 'loadRaster'):
                        widget.loadRaster(file_path)
                        return True
                        
            return False
        except Exception as e:
            return False