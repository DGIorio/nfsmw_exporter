# Need for Speed Most Wanted 2012 exporter
The NFSMW12 exporter is a Blender add-on to enable exporting objects as a Need for Speed Most Wanted 2012 (PC) file, currently supporting vehicles, tracks, collisions and characters.

## Requirements
- [Blender](https://www.blender.org/download/) (v3.1 or up to v3.4)  
- [NVIDIA textute tools 2.1.1 - NVTT](https://github.com/castano/nvidia-texture-tools)  
- [Bundle Packer Unpacker](https://github.com/DGIorio/bundle_packer_unpacker)  
- [Additional Blender panels](https://github.com/DGIorio/additional_blender_panels)  
- [Game library](https://drive.google.com/file/d/10zKBiuUgS96G6tKT2AQGnIUovaH7Pg_c/view?usp=sharing)
- [PS3 Game library](https://drive.google.com/file/d/1i27u9Gqc3lXKMYoA7BbieXC79-jLu4qg/view?usp=sharing)

### Recommended Blender add-ons
- [Vertex Oven](https://github.com/ForestKatsch/VertexOven) for baking ao map on vertex color
- [Criterion modding helpers](https://github.com/DGIorio/criterion_modding_helpers) for some tools and help with preparing the Blender scene

## Installation
Go to `Edit > Preferences > Addons > Install` and either select .zip file or the unzipped `export_nfsmw_models.py` file.

## Location
`File > Export > Need for Speed Most Wanted (2012)`

## Features
- Able to export vehicles, track units and characters
- Support to exporting wheels on vehicles
- Support to all shader types, with their custom parameters and textures
- Predefined shader types for easy usage: `Metal or BodyLivery (livery), BodyPaint (paintable), BodyColor (non-paintable, uses Blender color), Interior, Chrome, CarbonFiber, DullPlastic, Badge, Chassis, Glass, Mirror, LicensePlate, LicensePlate_Number, Tyre, Rim, Caliper, BrakeDisc`

## Samples
Samples are available on [samples repository](https://github.com/DGIorio/exporter_samples)
