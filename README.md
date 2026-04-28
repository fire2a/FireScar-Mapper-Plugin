# Fire Scar Mapper Plugin for QGIS

The **Fire Scar Mapper** is a QGIS plugin designed to assist in the detection and analysis of wildfire-affected areas. It provides three core functionalities:

---

## 🔥 Functionality Overview

### 1. **Pre- and Post-Fire Image Generator**

This tool allows you to:
- Select a starting and ending date, location of interest and estimated affected area in hectares
- Automatically retrieve satellite imagery before and after the fire from **Google Earth Engine (GEE)**
- Clip the images to a circular area centered on the ignition point — the buffer radius is estimated from the affected area using a non-linear function calibrated from historical fire data
- Add the resulting images to your QGIS project for further analysis

---

### 2. **Image Cropping Tool** *(optional)*

This tool allows you to:
- Select a pre- and post-fire image pair already loaded in your QGIS project
- Draw a rectangular crop zone directly on the map by clicking two opposite corners — a red preview rectangle appears while drawing
- Generate cropped versions of both images, preserving all spectral bands and metadata
- Use the cropped images as input for the fire scar detection model

> 💡 This is useful when the original image is large and the fire scar occupies a small portion of it, or when there are multiple fire events in the same image and you want to isolate one.

---

### 3. **Fire Scar Detection with Deep Learning**

This module enables you to:
- Select **pre- and post-fire images** from your QGIS layers
- Run a trained **U-Net model** to detect burned areas:
  - **AS:** Model trained with images cropped to the affected size of a fire scar. Best used when the fire scar occupies most of the image
  - **128:** Model trained with images of 128×128 pixels centered on the fire scar. Better suited for larger images where the scar is a smaller portion of the scene
- Generate a georeferenced raster representing the fire scar
- Visualize the outputs directly within QGIS with the colormap "Reds" applied

> ⚠️ The models were trained exclusively on wildfire data from the Biobío and Valparaíso regions of Chile (1985–2018), covering mainly forest and shrubland ecosystems. Performance may be significantly lower for fires in other vegetation types, climatic zones, or geographic regions outside of these training conditions.

The fire scar raster is stored in a `/results` folder within the plugin directory.

The repository of the U-Net models is on this [link](https://github.com/fire2a/FireScars)

---

## ⚙️ Plugin Usage Instructions

To use the plugin in QGIS, follow the steps below:

---

### Step 1: Clone the Repository

Clone this repository anywhere and then create a **symbolic link** to the QGIS plugins folder:
- Open a terminal with admin privileges
- Go to the folder where QGIS stores its plugins. On most systems, the folder is located at:
```bash
cd C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins
```
- Create the symbolic link:
```bash
mklink /D FireScar-Mapper-Plugin <path where the repository was cloned>
example: mklink /D FireScar-Mapper-Plugin C:\Users\USER\plugins\FireScar-Mapper-Plugin
```
> Note: The name of the folder must match the repository name (FireScar-Mapper-Plugin)

---

### Step 2: Download the Google Earth Engine Plugin

To use the image generation feature:

1. Install the **Google Earth Engine** plugin via the QGIS Plugin Manager.
2. Follow the instructions that appear.
3. You must link your GEE account and provide an **authorized GEE project ID** (which you can create in [GEE Code Editor](https://code.earthengine.google.com/)).

---

### Step 3: Enable the Plugin in QGIS

1. Restart QGIS (if it was already open).
2. Go to **Plugins > Manage and Install Plugins**.
3. Look for "Fire Scar Mapper" and enable it.
4. A dialog will appear if any dependencies are missing — click **Install** and follow the instructions.
5. After installing the missing dependencies, restart QGIS.

> Note: The `resources.py` file is generated automatically when the plugin loads for the first time. No manual action is required.

---

### Step 4: Use the Plugin

After installation, you can:

- **Tab 1: Generate Images**
  - Select a starting and ending date, ignition point and estimated area in hectares
  - Click **🛰️ Generate Pre and Post Fire Tiff Images** to retrieve and add satellite images to your project

- **Tab 2: Crop Images** *(optional)*
  - Select a pre- and post-fire image pair from the dropdowns
  - Click **📐 Define Crop Zone** and draw a rectangle on the map by clicking two opposite corners
  - A red preview rectangle appears while drawing and remains visible after the second click
  - Use **👁 Show Zone / 🚫 Hide Zone** to toggle the rectangle visibility
  - Use **✖ Clear Zone** to remove the defined zone
  - Right-click at any point to cancel the zone definition
  - Click **✂️ Crop Images** to generate cropped versions of both images
  - Use the 🔄 button to refresh the layer list if new images were recently added

- **Tab 3: Generate Fire Scar**
  - Select pre- and post-fire images from the dropdown
  - Select the model approach: AS or 128
  - Click **🔥 Generate Fire Scar** to run the model
  - Output raster is added to the top of the QGIS Layers Panel with the colormap "Reds" applied
  - If no burned area is detected, a warning message will appear explaining possible causes

🗂️ All outputs are saved in the `/results/` folder within the plugin directory.

---

## 🛰️ Using Custom Satellite Images

If you want to use your own images instead of generating them via GEE, they must meet the following conditions:

**Technical requirements:**
- CRS: `EPSG:4326`
- Pixel resolution: `0.0002695°` (~30m N-S)
- 8 bands in this exact order: `R, G, B, NIR, SWIR1, SWIR2, NDVI, NBR`
- Data type: `Float32`
- Source: Landsat (L5, L7, L8 or L9), Collection 2, Surface Reflectance level
- Reflectance bands (R, G, B, NIR, SWIR1, SWIR2) must be in the **0–10000 range** (not normalized to 0–1)
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