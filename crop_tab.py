import os
from osgeo import gdal

from qgis.core import QgsProject, QgsRasterLayer, QgsRectangle, QgsPointXY, QgsWkbTypes
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

from .tiff_generator_tab import get_unique_filepath, set_band_names

class RectangleMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, rubber_band, on_first_click, on_second_click, on_cancel):
        super().__init__(canvas)
        self.canvas = canvas
        self.rubber_band = rubber_band
        self.on_first_click = on_first_click
        self.on_second_click = on_second_click
        self.on_cancel = on_cancel
        self.first_point = None
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        point = self.toMapCoordinates(event.pos())
        if self.first_point is None:
            self.first_point = point
            self.on_first_click(point)
        else:
            second_point = point
            x_min = min(self.first_point.x(), second_point.x())
            x_max = max(self.first_point.x(), second_point.x())
            y_min = min(self.first_point.y(), second_point.y())
            y_max = max(self.first_point.y(), second_point.y())
            self.first_point = None
            self.on_second_click(QgsRectangle(x_min, y_min, x_max, y_max))
    
    def canvasPressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.first_point = None
            self.on_cancel()

    def canvasMoveEvent(self, event):
        if self.first_point is None:
            return
        current_point = self.toMapCoordinates(event.pos())
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.rubber_band.addPoint(self.first_point)
        self.rubber_band.addPoint(QgsPointXY(current_point.x(), self.first_point.y()))
        self.rubber_band.addPoint(current_point)
        self.rubber_band.addPoint(QgsPointXY(self.first_point.x(), current_point.y()))
        self.rubber_band.addPoint(self.first_point)
        self.rubber_band.show()

    def deactivate(self):
        if self.first_point is not None:
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        super().deactivate()

class CropImagesTab(QWidget):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.crop_rect = None
        self.map_tool = None
        self.previous_map_tool = None
        self.zone_visible = False

        # Single rubber band owned by the tab, not by the map tool
        self.rubber_band = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setFillColor(QColor(255, 0, 0, 30))
        self.rubber_band.setWidth(2)

        # Pre-fire selector
        self.pre_fire_label = QLabel("Pre-Fire Image:")
        self.pre_fire_combo = QComboBox()

        # Post-fire selector
        self.post_fire_label = QLabel("Post-Fire Image:")
        self.post_fire_combo = QComboBox()

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh Layers")
        self.refresh_button.clicked.connect(self.populate_layer_combos)

        # Define zone button
        self.define_zone_button = QPushButton("📐 Define Crop Zone")
        self.define_zone_button.clicked.connect(self.start_define_zone)

        # Clear zone button
        self.clear_zone_button = QPushButton("✖ Clear Zone")
        self.clear_zone_button.setEnabled(False)
        self.clear_zone_button.clicked.connect(self.clear_zone)

        # Show zone button
        self.show_zone_button = QPushButton("👁 Show Zone")
        self.show_zone_button.setEnabled(False)
        self.show_zone_button.clicked.connect(self.show_zone)

        self.zone_actions_layout = QHBoxLayout()
        self.zone_actions_layout.addWidget(self.show_zone_button)
        self.zone_actions_layout.addWidget(self.clear_zone_button)
        
        # Status label
        self.zone_label = QLabel("No zone defined")
        self.zone_label.setStyleSheet("color: gray; font-style: italic;")
        self.zone_label.setWordWrap(True)

        # Crop button
        self.crop_button = QPushButton("✂️ Crop Images")
        self.crop_button.setEnabled(False)
        self.crop_button.clicked.connect(self.crop_images)
        

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.pre_fire_label)
        layout.addWidget(self.pre_fire_combo)
        layout.addWidget(self.post_fire_label)
        layout.addWidget(self.post_fire_combo)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.define_zone_button)
        layout.addLayout(self.zone_actions_layout)
        layout.addWidget(self.zone_label)
        layout.addWidget(self.crop_button)
        
        layout.addStretch()

        self.setLayout(layout)
        self.populate_layer_combos()

    def populate_layer_combos(self):
        self.pre_fire_combo.clear()
        self.post_fire_combo.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsRasterLayer):
                self.pre_fire_combo.addItem(layer.name(), layer)
                self.post_fire_combo.addItem(layer.name(), layer)

    def start_define_zone(self):
        """Activate map tool to capture two corners of the crop rectangle."""
        self.crop_button.setEnabled(False)
        self.crop_rect = None
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)

        # If a previous map tool exists, reset its state before replacing it
        if self.map_tool is not None:
            self.map_tool.first_point = None
            self.iface.mapCanvas().unsetMapTool(self.map_tool)

        self.previous_map_tool = self.iface.mapCanvas().mapTool()
        self.map_tool = RectangleMapTool(
            self.iface.mapCanvas(),
            self.rubber_band,
            on_first_click=self.on_first_click,
            on_second_click=self.on_zone_defined,
            on_cancel=self.on_zone_cancelled
        )
        self.iface.mapCanvas().setMapTool(self.map_tool)
        self.zone_label.setText("Click the first corner on the map..., right-click to cancel.")
        self.zone_label.setStyleSheet("color: blue; font-style: italic;")

    def clear_zone(self):
        """Clear the defined crop zone and reset the rubber band."""
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.crop_rect = None
        self.zone_visible = False
        self.show_zone_button.setText("👁 Show Zone")
        self.crop_button.setEnabled(False)
        self.clear_zone_button.setEnabled(False)
        self.show_zone_button.setEnabled(False)
        self.zone_label.setText("No zone defined")
        self.zone_label.setStyleSheet("color: gray; font-style: italic;")

    def show_zone(self):
        """Toggle rubber band visibility for the currently defined crop zone."""
        if self.crop_rect is None:
            return
        if self.zone_visible:
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.zone_visible = False
            self.show_zone_button.setText("👁 Show Zone")
        else:
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.rubber_band.addPoint(QgsPointXY(self.crop_rect.xMinimum(), self.crop_rect.yMaximum()))
            self.rubber_band.addPoint(QgsPointXY(self.crop_rect.xMaximum(), self.crop_rect.yMaximum()))
            self.rubber_band.addPoint(QgsPointXY(self.crop_rect.xMaximum(), self.crop_rect.yMinimum()))
            self.rubber_band.addPoint(QgsPointXY(self.crop_rect.xMinimum(), self.crop_rect.yMinimum()))
            self.rubber_band.addPoint(QgsPointXY(self.crop_rect.xMinimum(), self.crop_rect.yMaximum()))
            self.rubber_band.show()
            self.zone_visible = True
            self.show_zone_button.setText("🚫 Hide Zone")

    def on_first_click(self, point):
        self.zone_label.setText(
            f"First corner: ({point.x():.4f}, {point.y():.4f})\n"
            "Now click the opposite corner..."
        )

    def on_zone_defined(self, rect):
        """Called after the second click — rectangle is complete."""
        self.crop_rect = rect
        self.zone_label.setText(
            f"Zone defined:\n"
            f"({rect.xMinimum():.4f}, {rect.yMinimum():.4f}) → "
            f"({rect.xMaximum():.4f}, {rect.yMaximum():.4f})"
        )
        self.zone_label.setStyleSheet("color: green; font-style: italic;")
        self.crop_button.setEnabled(True)
        self.clear_zone_button.setEnabled(True)
        self.show_zone_button.setEnabled(True)
        self.zone_visible = True
        self.show_zone_button.setText("🚫 Hide Zone")
        if self.previous_map_tool:
            self.iface.mapCanvas().setMapTool(self.previous_map_tool)
        else:
            self.iface.actionPan().trigger()

    def on_zone_cancelled(self):
        self.zone_label.setText("Zone definition cancelled. Click 'Define Crop Zone' to try again.")
        self.zone_label.setStyleSheet("color: orange; font-style: italic;")
        self.iface.actionPan().trigger()

    def crop_images(self):
        """Crop both images to the defined rectangle."""
        pre_layer = self.pre_fire_combo.currentData()
        post_layer = self.post_fire_combo.currentData()

        if not pre_layer or not post_layer:
            QMessageBox.warning(self, "Missing Input", "Please select both pre-fire and post-fire images.")
            return

        if self.crop_rect is None:
            QMessageBox.warning(self, "Missing Zone", "Please define a crop zone first.")
            return

        if pre_layer.id() == post_layer.id():
            QMessageBox.warning(self, "Invalid Selection", "Pre-fire and post-fire images must be different layers.")
            return

        try:
            pre_output = self._crop_layer(pre_layer)
            post_output = self._crop_layer(post_layer)
            self._add_layer_to_qgis(pre_output)
            self._add_layer_to_qgis(post_output)
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.crop_rect = None
            self.zone_visible = False
            self.show_zone_button.setText("👁 Show Zone")
            self.crop_button.setEnabled(False)
            self.clear_zone_button.setEnabled(False)
            self.show_zone_button.setEnabled(False)
            self.zone_label.setText("No zone defined")
            self.zone_label.setStyleSheet("color: gray; font-style: italic;")
            QMessageBox.information(
                self, "Success",
                "Images cropped successfully.\nGo to Tab 3 to generate the fire scar."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to crop images:\n{str(e)}")

    def _crop_layer(self, layer):
        """Crop a single layer to crop_rect, preserving nodata values exactly."""
        gdal.SetConfigOption('GDAL_TIFF_OVR_BLOCKSIZE', '128')

        source_path = layer.source()
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        output_dir = os.path.dirname(source_path)
        output_path = get_unique_filepath(
            os.path.join(output_dir, f"{base_name}_crop.tif")
        )

        src_ds = None
        dst_ds = None
        try:
            src_ds = gdal.Open(source_path)
            gt = src_ds.GetGeoTransform()
            pixel_w = gt[1]
            pixel_h = abs(gt[5])
            x_origin = gt[0]
            y_origin = gt[3]

            # Convert geographic crop_rect to pixel coordinates
            col_min = int((self.crop_rect.xMinimum() - x_origin) / pixel_w)
            col_max = int((self.crop_rect.xMaximum() - x_origin) / pixel_w)
            row_min = int((y_origin - self.crop_rect.yMaximum()) / pixel_h)
            row_max = int((y_origin - self.crop_rect.yMinimum()) / pixel_h)

            # Clamp to raster bounds
            col_min = max(0, col_min)
            row_min = max(0, row_min)
            col_max = min(src_ds.RasterXSize, col_max)
            row_max = min(src_ds.RasterYSize, row_max)

            n_cols = col_max - col_min
            n_rows = row_max - row_min

            if n_cols <= 0 or n_rows <= 0:
                raise Exception("Crop rectangle does not overlap with the image.")

            new_gt = (
                x_origin + col_min * pixel_w,
                pixel_w,
                0,
                y_origin - row_min * pixel_h,
                0,
                -pixel_h
            )

            driver = gdal.GetDriverByName('GTiff')
            n_bands = src_ds.RasterCount
            src_band = src_ds.GetRasterBand(1)
            dtype = src_band.DataType
            nodata = src_band.GetNoDataValue()

            dst_ds = driver.Create(output_path, n_cols, n_rows, n_bands, dtype, options=['BIGTIFF=IF_NEEDED', 'COMPRESS=NONE'])
            dst_ds.SetGeoTransform(new_gt)
            dst_ds.SetProjection(src_ds.GetProjection())

            for b in range(1, n_bands + 1):
                src_band = src_ds.GetRasterBand(b)
                data = src_band.ReadAsArray(col_min, row_min, n_cols, n_rows)
                dst_band = dst_ds.GetRasterBand(b)
                dst_band.WriteArray(data)
                if nodata is not None:
                    dst_band.SetNoDataValue(nodata)
                dst_band.FlushCache()

        finally:
            dst_ds = None
            src_ds = None

        # Preserve band names from source layer
        band_names = [layer.bandName(b).split(': ')[-1] for b in range(1, layer.bandCount() + 1)]
        set_band_names(output_path, band_names)

        return output_path

    def _add_layer_to_qgis(self, file_path):
        """Add cropped raster to the top of the layer tree."""
        layer_name = os.path.splitext(os.path.basename(file_path))[0]
        for existing in QgsProject.instance().mapLayersByName(layer_name):
            QgsProject.instance().removeMapLayer(existing)
        layer = QgsRasterLayer(file_path, layer_name, "gdal")
        if not layer.isValid():
            raise Exception(f"Could not load cropped layer: {file_path}")
        QgsProject.instance().addMapLayer(layer, False)
        QgsProject.instance().layerTreeRoot().insertLayer(0, layer)