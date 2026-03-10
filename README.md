GeoCropRef: Plugin Documentation


1. Introduction and Purpose of the Plugin

GeoCropRef is a QGIS tool designed to solve a common problem when georeferencing scanned maps and historical plans: unnecessary borders (white frames, legends, empty margins).
If you don’t crop these borders before georeferencing, transformation algorithms (such as Thin Plate Spline) unnecessarily distort the empty areas, resulting in ugly “black corners” and warped edges in the final GeoTIFF.
This plugin enables fast visual cropping using the mouse and automatically passes the cropped image to QGIS’s native Georeferencer.


2. Main Features

Visual Cropping: A tool for drawing a cropping rectangle directly on the plugin canvas.
Lossless Processing (GDAL): Cropping is performed via gdal.Translate at the pixel level—no compression, no quality loss of the original scan.
Clean Disk (Temp Files): Option to save the cropped image only as a temporary OS file so your drive isn’t cluttered with intermediate data.
Auto‑Load into Georeferencer: The plugin can automatically launch the Georeferencer window and insert the cropped file directly.
Clipboard Backup: The path to the cropped file is always copied to your clipboard for manual insertion if needed.

3. Installation

Since this is a custom local plugin:

Open the plugin directory for your QGIS installation:
Windows: C:\Users\YourName\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
Linux/Mac: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

Copy the entire geocropref folder into this directory.
Start (or restart) QGIS.
Go to Plugins → Manage and Install Plugins…
Under Installed, find GeoCropRef and enable it.

4. User Guide (Step by Step)

In the main QGIS menu, click Raster → Crop Image for Georeferencing.
A plugin window opens. Click “1. Load Image”.
Select your scanned file (supported: TIF, JPG, PNG). The raster will display in the canvas.
Draw the crop area:
Click inside the image with the left mouse button.
Drag to create a red rectangle around the map area you want to keep (exclude borders and legend).

Choose how to save:
“Save as Temporary File” checked: Creates a hidden temporary file that disappears after a PC restart. (Recommended)
Unchecked: The plugin will ask where to save the cropped TIF permanently.

Click “2. Crop and Open Georeferencer”.

What happens then?
The plugin window closes, QGIS Georeferencer opens instantly, and your cleanly cropped map is already loaded.
You can now start adding Ground Control Points (GCPs) as usual.

5. Troubleshooting

Problem: The Georeferencer opens, but the image is not loaded.
Cause: In some very specific QGIS versions, window rendering is delayed, causing the Auto‑Load command to fail.
Solution: The plugin anticipates this. The file path was automatically copied to your clipboard.
In the Georeferencer:
Click Open Raster,
Click into the filename box,
Press Ctrl+V,
Hit Enter.

Problem: The raster appears distorted when loaded into the plugin.
Cause: QGIS attempts to apply a coordinate system to an image that doesn’t have one yet.
Solution: This is only a visual preview issue in the plugin window.
Cropping uses actual pixel coordinates (srcWin), so the resulting image will NOT be distorted.
