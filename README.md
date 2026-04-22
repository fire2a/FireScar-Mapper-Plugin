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

Clone this repository anywhere and then create a **symbolic link** to the QGIS plugins folder
- Open a terminal with admin privileges
- Go to the folder where QGIS store their plugins. On most systems, the folder is located at:
```bash
cd C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins
```
- Create the symbolic link:
```bash
mklink /D FireScar-Mapper-Plugin <path where the repository was cloned>
example: mklink /D FireScar-Mapper-Plugin C:\Users\USER\plugins\FireScar-Mapper-Plugin
```
Note: 
The name of the folder must be the same as the one that it's cloned (FireScar-Mapper-Plugin)

---

### Step 2: Download the Google Earth Engine Plugin

To use the image generation feature:

1. Install the **Google Earth Engine** plugin via the QGIS Plugin Manager.
2. Follow the instructions that appear.
3. You must link your GEE account and provide an **authorized GEE project ID** (which you can create in [GEE Code Editor](https://code.earthengine.google.com/)).

---

### Step 3: Enable the Plugin in QGIS

1. Restart QGIS (if it was opened).
2. Go to **Plugins > Manage and Install Plugins**.
3. Look for "Fire Scar Mapper" and enable it.
4. A dialog will appear if any dependencies are missing — click **Install** and follow the instructions.
5. After downloading the missing dependencies restart QGIS Desktop.

---

### Step 4: Use the Plugin

After installation, you can:

- **Tab 1: Generate Pre- and Post-Fire Images**
  - Select a starting and ending date, ignition point and affected area in hectares.
  - Retrieve and add satellite images directly to your project

- **Tab 2: Generate Fire Scars**
  - Select pre- and post-fire images from the dropdown (all layers in the project are listed)
  - Select the model approach: AS or 128
  - Run the model to generate a burned area mask
  - Output raster is added to the top of the QGIS Layers Panel with the colormap "Reds" applied

🗂️ All outputs are saved in the `/results/` folder within the plugin directory.

---

## 🛰️ Using Custom Satellite Images

If you want to use your own images instead of generating them via GEE, they must meet the following conditions:

**Technical requirements:**
- CRS: `EPSG:4326`
- Pixel resolution: `0.0002695°` (~30m N-S)
- 8 bands in this exact order: `R, G, B, NIR, SWIR1, SWIR2, NDVI, NBR`
- Data type: `Float32`
- Source: Landsat (L5, L7, L8 or L9), Collection 2, Surface Reflectance level, with scale factors applied
- Cloud-free or cloud-masked

**Content requirements:**
- Pre-fire image: most recent available image up to 365 days **before** the fire start date
- Post-fire image: most recent available image up to 180 days **after** the fire control date
- Both images must cover the exact same geographic extent and resolution

> ⚠️ Images that do not meet these conditions may produce inaccurate or empty fire scar predictions, as the models were trained with images generated under these exact specifications.

---

## 📦 Dependencies

The plugin automatically installs required Python packages on first use, including:

- `earthengine-api`
- `torch`
- `torchvision`

A confirmation window will appear before installation. A restart of QGIS may be required afterward.

---
