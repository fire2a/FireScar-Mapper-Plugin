import os.path
from qgis.core import (QgsProcessingFeedback)
from qgis.PyQt.QtWidgets import  QVBoxLayout, QPushButton, QFileDialog, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QFileDialog, QLabel, QTextEdit, QHBoxLayout, QMessageBox, QComboBox


class LayerSelectionDialog(QWidget):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        #self.resize(1000, 600) 

        # Descripción del proceso (añadido)
        self.description_label = QTextEdit(self)
        self.description_label.setReadOnly(True)
        self.description_label.setHtml(self.get_description())  # Set HTML content

        # Selector para imágenes pre-incendio
        self.pre_fire_button = QPushButton("Select Pre-Fire Images")
        self.pre_fire_button.clicked.connect(self.select_pre_fire_files)

        # Selector para imágenes post-incendio
        self.post_fire_button = QPushButton("Select Post-Fire Images")
        self.post_fire_button.clicked.connect(self.select_post_fire_files)

        # Campo de texto para mostrar las rutas seleccionadas de imágenes pre-incendio
        self.pre_fire_display = QTextEdit(self)
        self.pre_fire_display.setReadOnly(True)
        self.pre_fire_display.setPlaceholderText("Pre-fire images will be displayed here...")

        # Campo de texto para mostrar las rutas seleccionadas de imágenes post-incendio
        self.post_fire_display = QTextEdit(self)
        self.post_fire_display.setReadOnly(True)
        self.post_fire_display.setPlaceholderText("Post-fire images will be displayed here...")

        # Selector para "Model Scale" (AS o 128)
        self.scale_label = QLabel("Model Scale:")
        self.scale_combo = QComboBox(self)
        self.scale_combo.addItems(["AS", "128"])

        # Botón para ejecutar el procesamiento
        self.run_button = QPushButton("Run Fire Scar Mapping")
        self.run_button.clicked.connect(self.run_fire_scar_mapping)

        # Layout para la izquierda: selectores de imágenes y campo de texto
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.pre_fire_button)
        left_layout.addWidget(self.pre_fire_display)

        left_layout.addWidget(self.post_fire_button)
        left_layout.addWidget(self.post_fire_display)
        
        left_layout.addWidget(self.scale_label)
        left_layout.addWidget(self.scale_combo)

        left_layout.addWidget(self.run_button)

        # Layout principal: distribución en dos columnas (selectores a la izquierda, descripción a la derecha)
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)  # Columna izquierda
        main_layout.addWidget(self.description_label, stretch=1)  # Columna derecha con descripción

        self.setLayout(main_layout)

        # Almacenar las rutas de los archivos seleccionados
        self.pre_fire_files = []
        self.post_fire_files = []

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