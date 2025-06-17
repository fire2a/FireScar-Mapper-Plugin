import os.path
from qgis.core import (QgsProcessingFeedback, QgsProject, QgsRasterLayer, QgsProject)
from qgis.PyQt.QtWidgets import  QVBoxLayout, QPushButton, QFileDialog, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QFileDialog, QLabel, QTextEdit, QHBoxLayout, QMessageBox, QComboBox

from .algorithm_firescarmapper import ProcessingAlgorithm

class LayerSelectionDialog(QWidget):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface

        # Combos to select layer from the project
        self.pre_fire_layer_combo = QComboBox()
        self.post_fire_layer_combo = QComboBox()
        self.populate_layer_combos()  

        # buttons to add a layer from the local system
        self.pre_fire_button = QPushButton("...")
        self.pre_fire_button.setFixedWidth(30)
        self.pre_fire_button.setToolTip("Select from local files")
        self.pre_fire_button.clicked.connect(self.select_pre_fire_files)

        self.post_fire_button = QPushButton("...")
        self.post_fire_button.setFixedWidth(30)
        self.post_fire_button.setToolTip("Select from local files")
        self.post_fire_button.clicked.connect(self.select_post_fire_files)

        # Horizontal layouts that combine combo + button
        self.pre_fire_selector_layout = QHBoxLayout()
        self.pre_fire_label = QLabel("Pre-Fire Image:")
        self.pre_fire_selector_layout.addWidget(self.pre_fire_layer_combo)
        self.pre_fire_selector_layout.addWidget(self.pre_fire_button)

        self.post_fire_selector_layout = QHBoxLayout()
        self.post_fire_label = QLabel("Post-Fire Image:")
        self.post_fire_selector_layout.addWidget(self.post_fire_layer_combo)
        self.post_fire_selector_layout.addWidget(self.post_fire_button)

        # Text field to show selected routes of PreFire Images
        self.pre_fire_display = QTextEdit(self)
        self.pre_fire_display.setReadOnly(True)
        self.pre_fire_display.setPlaceholderText("Pre-fire images will be displayed here...")

         # Text field to show selected routes of PostFire Images
        self.post_fire_display = QTextEdit(self)
        self.post_fire_display.setReadOnly(True)
        self.post_fire_display.setPlaceholderText("Post-fire images will be displayed here...")

        # Model scale selector (AS o 128)
        self.scale_label = QLabel("Model Scale:")
        self.scale_combo = QComboBox(self)
        self.scale_combo.addItems(["AS", "128"])

        # execute process button
        self.run_button = QPushButton("Generate Fire Scar")
        self.run_button.clicked.connect(self.run_fire_scar_mapping)

        # left layout: image selector and text fields
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(self.pre_fire_label)
        left_layout.addLayout(self.pre_fire_selector_layout)
        left_layout.addWidget(self.pre_fire_display)

        left_layout.addWidget(self.post_fire_label)
        left_layout.addLayout(self.post_fire_selector_layout)
        left_layout.addWidget(self.post_fire_display)

        
        left_layout.addWidget(self.scale_label)
        left_layout.addWidget(self.scale_combo)

        left_layout.addWidget(self.run_button)

        # Principal layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)  
        self.setLayout(main_layout)

        # Store routes of selected files
        self.pre_fire_files = []
        self.post_fire_files = []

    def populate_layer_combos(self):
        """Fill combobox with layer fromt the actual project."""
        self.pre_fire_layer_combo.clear()
        self.post_fire_layer_combo.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if isinstance(layer, QgsRasterLayer):
                self.pre_fire_layer_combo.addItem(layer.name(), layer)
                self.post_fire_layer_combo.addItem(layer.name(), layer)


    def get_description(self):
        """Obtener la descripción del plugin en formato HTML."""
        return """
            <h1>Fire Scar Mapper</h1><br>

            <img src=":/plugins/example/images/diagrama plugin.png" alt="Example Image" width="700" height="300"><br>

            <b>Objective:</b> Generate georeferenced fire scar rasters using a pre-trained U-Net model and analyze the impact of fire events by comparing pre- and post-fire satellite images.<br>
            <br>
            <b>Process:</b> 
            Fire scars are identified by comparing the spectral differences between pre-fire and post-fire satellite images.<br>
            <br>
            <b>Model Approaches:</b><br>
            (a) <b>128</b>: Designed for 128 x 128 pixel images centered around the ignition point of the fire event.<br>
            (b) <b>AS</b>: Designed for images cropped to the exact boundaries of the fire scar.<br>
            <br>
            <b>Key Features:</b><br>
            (a) Automated cropping of input images based on the selected model scale when the images are not cropped:<br>
            - <b>128 x 128 approach:</b> Crops the area around the ignition point specified in the shapefile.<br>
            - <b>AS approach:</b> Crops the area based on the predefined boundaries (north, south, west, east) in the shapefile.<br>
            (b) Automatic organization of generated layers in the QGIS interface for easy visualization.<br>
            (c) Integrated download of the pre-trained U-Net model if not found locally.<br>
            <br>
            <b>Constraints:</b><br>
            (a) Pre- and post-fire images must have the same geographical extent.<br>
            <br>
            <b>Inputs:</b><br>
            (i) A <b>pre-fire</b> raster layer containing the necessary spectral bands for analysis.<br>
            (ii) A <b>post-fire</b> raster layer containing the necessary spectral bands for analysis.<br>
            (iii) A <b>shapefile</b> specifying either the ignition point (for 128x128 model) or boundary coordinates (for AS model).<br>
            - All inputs must consist of georeferenced and compatible data with consistent spatial resolution.<br>
            <br>
            <b>File Naming Format:</b><br>
            Pre- and post-fire images files must follow this naming convention:<br>
            <code>&lt;ImgPreF or ImgPosF&gt;_&lt;locality code&gt;_&lt;ID&gt;_&lt;threshold&gt;_&lt;year/month/day&gt;.tif</code><br>
            For example:<br>
            <code>ImgPreF_CL-BI_ID74101_u350_19980330.tif</code><br>
            (If the images are already cropped, "_clip" must be added before ".tif")<br>
            <br>
            <b>Considerations:</b><br>
            - The segmentation model is pre-trained and downloaded from a bucket in AWS if necessary.<br>
            - In the pre- and post-fire image layers, the red and blue bands are swapped. Adjust the symbology in QGIS to correct this.<br>
            - Certain fire scars generated using the 128 approach may be incomplete if the scar is significantly large or distant from the ignition point.<br>
            <br>
            <b>Usage:</b><br>
            1. Select the pre-fire and post-fire images.<br>
            2. Choose the appropriate shapefile containing ignition points or boundaries.<br>
            (It is recommended to use the dataset and shapefile summary provided in "The Landscape Fire Scars DataBase for Chile" for optimal results.)<br>
            3. Specify whether the images are already cropped.<br>
            4. Select the model scale (128x128 or AS).<br>
            5. Run the plugin to generate the fire scar outputs.<br>
            <br>
            <b>Output:</b><br>
            The plugin generates georeferenced fire scar raster layers and organizes them into structured groups for efficient analysis and visualization in QGIS.<br>


        """
    #width="800" height="300"
    def select_pre_fire_files(self):
        """Seleccionar las imágenes pre-incendio y mostrarlas en el campo de texto."""
        self.pre_fire_files, _ = QFileDialog.getOpenFileNames(self, "Select Pre-Fire Images", "", "Images (*.tif *.jpg *.png)")
        if self.pre_fire_files:
            self.pre_fire_display.setText("\n".join(self.pre_fire_files))

    def select_post_fire_files(self):
        """Seleccionar las imágenes post-incendio y mostrarlas en el campo de texto."""
        self.post_fire_files, _ = QFileDialog.getOpenFileNames(self, "Select Post-Fire Images", "", "Images (*.tif *.jpg *.png)")
        if self.post_fire_files:
            self.post_fire_display.setText("\n".join(self.post_fire_files))


    def run_fire_scar_mapping(self):
        """Ejecutar el procesamiento una vez seleccionadas las imágenes."""
        pre_fire_files = self.pre_fire_files
        post_fire_files = self.post_fire_files

        # Si no se usaron archivos manuales, tomar los paths de las capas seleccionadas
        if not pre_fire_files:
            layer = self.pre_fire_layer_combo.currentData()
            if layer:
                pre_fire_files = [layer.source()]
                self.pre_fire_display.setText(layer.source())

        if not post_fire_files:
            layer = self.post_fire_layer_combo.currentData()
            if layer:
                post_fire_files = [layer.source()]
                self.post_fire_display.setText(layer.source())

        model_scale = self.scale_combo.currentText()

        # Verificar que se hayan seleccionado imágenes
        if not pre_fire_files or not post_fire_files :
            QMessageBox.warning(self, "Error", "Please select all required inputs.")
            return

        # Crear un feedback para mostrar el progreso y los mensajes
        feedback = QgsProcessingFeedback()

        # Ejecutar el algoritmo de FireScarMapper
        scar_mapper = ProcessingAlgorithm()

        parameters = {
            'BeforeRasters': pre_fire_files,
            'AfterRasters': post_fire_files,
            'ModelScale': model_scale,
            'OutputScars': os.path.join(os.path.dirname(__file__), f'results/{model_scale}', 'OutputScar.tif')
        }

        scar_mapper.main(parameters, context=None, feedback=feedback)

        feedback.pushInfo("Fire scar mapping process completed successfully.")
        self.close()