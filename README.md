# Need for Speed Most Wanted 2012 exporter
[![Blender](https://img.shields.io/badge/Blender-v3.1_or_up_to_v3.6-blue?logo=blender&logoColor=white)](https://www.blender.org/download/lts/3-6/#versions "Download Blender")
[![GitHub release](https://img.shields.io/github/release/DGIorio/nfsmw_exporter?include_prereleases=&sort=semver&color=blue)](https://github.com/DGIorio/nfsmw_exporter/releases/)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/DGIorio)

The NFSMW12 exporter is a Blender add-on to enable exporting objects as a Need for Speed Most Wanted 2012 (PC) file, currently supporting vehicles, tracks, collisions and characters.

## Requirements
- [Blender](https://www.blender.org/download/lts/3-6/#versions) (v3.1 or up to v3.6)  
- [NVIDIA textute tools 2.1.1 - NVTT](https://github.com/castano/nvidia-texture-tools)  
- [Bundle Packer Unpacker](https://github.com/DGIorio/bundle_packer_unpacker)  
- [Additional Blender panels](https://github.com/DGIorio/additional_blender_panels)  
- [Game library](https://drive.google.com/file/d/10zKBiuUgS96G6tKT2AQGnIUovaH7Pg_c/view?usp=sharing)

### Recommended Blender add-ons
- [Vertex Oven](https://github.com/ForestKatsch/VertexOven) for baking ao map on vertex color
- [Criterion modding helpers](https://github.com/DGIorio/criterion_modding_helpers) for some tools and help with preparing the Blender scene

### Limitations
This Modding Tool only works with Windows! (Tested on Linux and MacOS with no succes)

## Installation
- You need blender v3.1 - 3.6 installed
- nvidia texture tools installed / built and copyd in this path: `USERNAME\AppData\blender\3.x\scripts\addons\nvidia-texture-tools-2.1.1-win64` (x is the subversion of blender. you should have bin and lib folders when you open this path)
- Add the GameLibrary here `USERNAME\AppData\blender\3.6\scripts\addons\NeedForSpeedMostWanted2012` (here you should have the PC libs and PS3 libs)
- Install Additional Blender Panels `Edit > Preferences > Addons > Install` and select the script.py
- Go to `Edit > Preferences > Addons > Install` and either select .zip file or the unzipped `export_nfsmw_models.py` file.

## Location
`File > Export > Need for Speed Most Wanted (2012)`

## Features
- Able to export vehicles, track units and characters
- Support to exporting wheels on vehicles
- Support to all shader types, with their custom parameters and textures
- Predefined shader types for easy usage: `Metal or BodyLivery (livery), BodyPaint (paintable), BodyColor (non-paintable, uses Blender color), Interior, Chrome, CarbonFiber, DullPlastic, Badge, Chassis, Glass, Mirror, LicensePlate, LicensePlate_Number, Tyre, Rim, Caliper, BrakeDisc`

## Documentation
- [How to Setup Blender Addons for MW12 or HPR](https://docs.google.com/document/d/17MgvNmoF_imx64WcghOgUVoji-hd4aQ6_tkreLQcnTk)
- [Using NFS MW 2012/HP Importer Blender addon](https://docs.google.com/document/d/1e23Q_dl1tWWGG5wn7XDRZXqLu6C0A8UihPFyhbTTMvc)
- [Using Blender NFS MW 2012 Exporter addon (for cars)](https://docs.google.com/document/d/1Vz9iIKMCYnIFS7giVAUu0WV8m8zIOoiqTzGKOQsXl_Q)
- [Using Blender NFS MW 2012 Exporter (Advanced - for cars)](https://docs.google.com/document/d/1LZ6DyZFypR9UazhVVC0X6T2y39PaFKFziV8-EV9P-o8)
- [Using Blender NFS MW 2012 Exporter (for driver)](https://docs.google.com/document/d/1B0si343Dlq5t6a986T7UvfWue4les909XTV6-lSv0XM)

## Samples
Samples are available on [samples repository](https://github.com/DGIorio/exporter_samples)
