# Fire Scar Mapper Plugin for QGIS

The **Fire Scar Mapper** is a QGIS plugin designed to assist in the detection and analysis of wildfire-affected areas. It provides two core functionalities:

---

## 🔥 Functionality Overview

### 1. **Pre- and Post-Fire Image Generator**

This tool allows you to:
- Select a starting and ending date, location of interest and estimated affected area in hectares (depending on each wildfire)
- Automatically retrieve satellite imagery before and after the fire from **Google Earth Engine (GEE)**
- Clip the images to a circular area centered on the ignition point 
   - This clip is made with a buffer depending on the affected area, this allow to define an estimated length relating the area with the FireScar bigger axis. 
- Add the resulting images to your QGIS project for further analysis


---

### 2. **Fire Scar Detection with Deep Learning**

This module enables you to:
- Select **pre- and post-fire images** from your QGIS layers
- Run a trained **U-Net model** to detect burned areas 
   - AS: Model trained with images cropped to the affected size of a FireScar
   - 128: Model trained with images of 128 x 128 pixels centered on the FireScar
   - (Try with both models to select the best output)  
- Generate a georeferenced raster representing the fire scar
- Visualize the outputs directly within QGIS in a structured and organized way

The fire scar raster is stored in a `/results` folder within the plugin directory.

The repository of the U-Net models is on this [link](https://github.com/fire2a/FireScars)

---

## ⚙️ Plugin Usage Instructions

To use the plugin in QGIS, follow the steps below:

---

### Step 1: Clone the Repository

Clone this repository anywere and then create a **symbolic link** to the QGIS plugins folder
- Open a terminal with admin priviligies
- Go to the folder where QGIS store their plugins. On most systems, the folder is located at:
```bash
cd C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins
```
- Create the symbolik link:
```bash
mklink /D <name of the plugin folder> <path where the repository was cloned>
example: mklink /D FireScarMapper C:\Users\USER\plugins\FireScar-Mapper-Plugin
```

---

### Step 2: Prepare the Plugin Resources

Using the **OSGeo4W Shell**, follow these steps:

```bash
cd <path_to_plugin_folder>
py3_env
qt5_env
pyrcc5 resources.qrc -o resources.py
```
This will generate the necessary `resources.py` file for icons and GUI elements.

Note: 
However, in some cases, the pyrcc5 command works without explicitly activating those environments, especially if you are using a standalone QGIS installation or already have the required tools in your system path.

---

### Step 3: Download the Google Earth Engine Plugin

To use the image generation feature:

1. Install the **Google Earth Engine** plugin via the QGIS Plugin Manager.
2. Follow the instructions that appear.
3. You must link your GEE account and provide an **authorized GEE project ID** (which you can create in [GEE Code Editor](https://code.earthengine.google.com/)).

---

### Step 4: Enable the Plugin in QGIS

1. Restart QGIS (if it was opened).
2. Go to **Plugins > Manage and Install Plugins**.
3. Look for "Fire Scar Mapper" and enable it.
4. A dialog will appear if any dependencies are missing — click **Install** and follow the instructions.

---

### Step 5: Use the Plugin

After installation, you can:

- **Tab 1: Generate Pre- and Post-Fire Images**
  - Select a starting and ending date, ignition point and affected area in hectares.
  - Retrieve and add satellite images directly to your project

- **Tab 2: Generate Fire Scars**
  - Select pre- and post-fire images
  - Indicate whether the images are cropped
  - Run the model to generate a burned area mask
  - Output raster is grouped and displayed in your QGIS Layers Panel

🗂️ All outputs are saved in the `/results/` folder within the plugin directory.

---

## 📦 Dependencies

The plugin automatically installs required Python packages on first use, including:

- `earthengine-api`
- `torch`
- `torchvision`

A confirmation window will appear before installation. A restart of QGIS may be required afterward.

---
