#-*- coding:utf-8 -*-

# Blender Need for Speed Most Wanted (2012) exporter Add-on
# Add-on developed by DGIorio with contributions and tests by Piotrek


## TO DO
"""
- export probs and other instance types from tracks
- vehicle: modify the coronas file for adding or removing effects
- find a better default color2
- add default tint data
- fix muDebugDataOffset (IDs table) on cars??
"""


bl_info = {
	"name": "Export to Need for Speed Most Wanted (2012) models format (.dat)",
	"description": "Save objects as Need for Speed Most Wanted files",
	"author": "DGIorio",
	"version": (3, 0),
	"blender": (3, 1, 0),
	"location": "File > Export > Need for Speed Most Wanted (2012) (.dat)",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"support": "COMMUNITY",
	"category": "Import-Export"}


import bpy
from bpy.types import Operator
from bpy.props import (
	StringProperty,
	BoolProperty,
	FloatVectorProperty
)
from bpy_extras.io_utils import (
	ExportHelper,
	orientation_helper,
	axis_conversion,
)
import bmesh
import binascii
import math
from mathutils import Euler, Matrix, Quaternion, Vector
import os
import time
import struct
import numpy as np
import shutil
import zlib
from bundle_packer_unpacker import pack_bundle_mw
try:
	from bundle_cleaner import clean_model_data
except:
	print("WARNING: bundle_cleaner.py not found in Blender addons folder. Cleaning original wheel model data will not be possible.")
try:
	from mw_custom_materials import custom_shaders, get_default_sampler_states, get_default_material_parameters, get_default_mRasterId
except:
	print("WARNING: mw_custom_materials.py not found in Blender addons folder. Custom material data will not be available.")


def main(context, export_path, pack_bundle_file, ignore_hidden_meshes, copy_uv_layer, force_rotation, transform_args, global_rotation,
		debug_shared_not_found, debug_use_shader_material_parameters, debug_use_default_samplerstates, debug_redirect_vehicle, new_vehicle_name, m):
	
	os.system('cls')
	start_time = time.time()
	
	if bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode='OBJECT')
	
	
	## INITIALIZING
	print("Initializing variables...")
	
	shared_dir = os.path.join(NFSMWLibraryGet(), "NFSMW_Library_PC")
	shared_model_dir = os.path.join(shared_dir, "Model")
	shared_renderable_dir = os.path.join(shared_dir, "Renderable")
	shared_vertex_descriptor_dir = os.path.join(shared_dir, "VertexDescriptor")
	shared_vertex_descriptor_ported_x360_dir = os.path.join(shared_dir, "VertexDescriptor_port_X360")
	shared_vertex_descriptor_ported_ps3_dir = os.path.join(shared_dir, "VertexDescriptor_port_PS3")
	shared_material_dir = os.path.join(shared_dir, "Material")
	shared_shader_dir = os.path.join(os.path.join(shared_dir, "SHADERS"), "Shader")
	shared_samplerstate_dir = os.path.join(shared_dir, "SamplerState")
	shared_samplerstate_ported_x360_dir = os.path.join(shared_dir, "SamplerState_port_X360")
	shared_samplerstate_ported_ps3_dir = os.path.join(shared_dir, "SamplerState_port_PS3")
	shared_raster_dir = os.path.join(shared_dir, "Texture")
	shared_trafficattribs_dir = os.path.join(shared_dir, "TRAFFICATTRIBS")
	shared_characters_dir = os.path.join(shared_dir, "ALL_CHARS")
	
	for main_collection in bpy.context.scene.collection.children:
		is_hidden = bpy.context.view_layer.layer_collection.children.get(main_collection.name).hide_viewport
		is_excluded = bpy.context.view_layer.layer_collection.children.get(main_collection.name).exclude
		
		if is_hidden or is_excluded:
			print("WARNING: skipping main collection %s since it is hidden or excluded." % (main_collection.name))
			print("")
			continue
		
		main_directory_path = os.path.join(export_path, main_collection.name)
		
		print("Reading scene data for main collection %s..." % (main_collection.name))
		
		if "resource_type" in main_collection:
			resource_type = main_collection["resource_type"]
		else:
			print("WARNING: collection %s is missing parameter %s. Define one of the followings: 'GraphicsSpec', 'InstanceList', 'CharacterSpec'." % (main_collection.name, '"resource_type"'))
			resource_type = "GraphicsSpec"
			#return {"CANCELLED"}
		
		try:
			collections_types = {collection["resource_type"] : collection for collection in main_collection.children}
		except:
			print("WARNING: some collection is missing parameter %s. Define one of the followings: 'GraphicsSpec', 'WheelGraphicsSpec', 'PolygonSoupList', 'Character', 'Effects', 'CharacterSpec'." % '"resource_type"')
			collections_types = {}
			for collection in main_collection.children:
				try:
					collections_types[collection["resource_type"]] = collection
				except:
					collections_types["GraphicsSpec"] = collection
				
			#return {"CANCELLED"}
		
		if resource_type == "InstanceList":
			track_unit_name = main_collection.name
			track_unit_number = track_unit_name.replace("TRK_UNIT", "").replace("TRK", "").replace("UNIT", "")
			track_unit_number = track_unit_number.replace("trk_unit", "").replace("trk", "").replace("unit", "").replace("_", "")
			try:
				track_unit_number = int(track_unit_number)
			except:
				print("ERROR: collection %s name is not in the proper formating. Define it as TRK_UNITXXX where XXX is a number" % track_unit_name)
				return {"CANCELLED"}
			mInstanceListId = calculate_resourceid("trk_unit" + str(track_unit_number) + "_list")
			instancelist_collection = collections_types["InstanceList"]
			collections = [instancelist_collection,]
			
			mCompoundInstanceList = "TRK_UNIT" + str(track_unit_number) + "_cmplist"
			mDynamicInstanceList = "TRK_UNIT" + str(track_unit_number) + "_dynlist"
			mGroundcoverCollection = "TRK_UNIT" + str(track_unit_number) + "_gcvr"
			mLightInstanceList = "TRK_UNIT" + str(track_unit_number) + "_lightlist"
			mPolygonSoupList = "TRK_COL_" + str(track_unit_number)
			mPropInstanceList = "TRK_UNIT" + str(track_unit_number) + "_proplist"
			mZoneHeader = "TRK_UNIT" + str(track_unit_number) + "_hdr"
			mNavigationMesh = "TRK_NAV_" + str(track_unit_number)
			
			mCompoundInstanceListId = calculate_resourceid(mCompoundInstanceList.lower())
			mDynamicInstanceListId = calculate_resourceid(mDynamicInstanceList.lower())
			mGroundcoverCollectionId = calculate_resourceid(mGroundcoverCollection.lower())
			mLightInstanceListId = calculate_resourceid(mLightInstanceList.lower())
			mPolygonSoupListId = calculate_resourceid(mPolygonSoupList.lower())
			mPropInstanceListId = calculate_resourceid(mPropInstanceList.lower())
			mZoneHeaderId = calculate_resourceid(mZoneHeader.lower())
			mNavigationMeshId = calculate_resourceid(mNavigationMesh.lower())
			
			if "PolygonSoupList" in collections_types:
				polygonsouplist_collection = collections_types["PolygonSoupList"]
				collections.append(polygonsouplist_collection)
			elif "Collision" in collections_types:
				polygonsouplist_collection = collections_types["Collision"]
			else:
				print("WARNING: collection %s is missing. An empty one will be created." % '"PolygonSoupList"')
		
		elif resource_type == "GraphicsSpec":
			vehicle_name = main_collection.name
			vehicle_number = vehicle_name.replace("VEH", "").replace("HI", "").replace("LO", "").replace("TR", "").replace("GR", "").replace("MS", "")
			vehicle_number = vehicle_number.replace("veh", "").replace("hi", "").replace("lo", "").replace("tr", "").replace("gr", "").replace("ms", "").replace("_", "")
			try:
				test = int(vehicle_number)
			except:
				print("ERROR: main_collection's name is in the wrong format. Use something like VEH_122672_HI or VEH_122672_LO.")
			mGraphicsSpecId = int_to_id(vehicle_number)
			graphicsspec_collection = collections_types["GraphicsSpec"]
			
			collections = [graphicsspec_collection,]
			
			if "WheelGraphicsSpec" in collections_types:
				wheelgraphicsspec_collection = collections_types["WheelGraphicsSpec"]
				collections.append(wheelgraphicsspec_collection)
			elif "Wheels" in collections_types:
				wheelgraphicsspec_collection = collections_types["Wheels"]
				collections.append(wheelgraphicsspec_collection)
			
			if "PolygonSoupList" in collections_types:
				polygonsouplist_collection = collections_types["PolygonSoupList"]
				collections.append(polygonsouplist_collection)
			elif "Collision" in collections_types:
				polygonsouplist_collection = collections_types["Collision"]
				collections.append(polygonsouplist_collection)
			
			if "Character" in collections_types:
				character_collection = collections_types["Character"]
				collections.append(character_collection)
			elif "Driver" in collections_types:
				character_collection = collections_types["Driver"]
				collections.append(character_collection)
			
			if "Effects" in collections_types:
				effects_collection = collections_types["Effects"]
				collections.append(effects_collection)
			elif "Effect" in collections_types:
				effects_collection = collections_types["Effect"]
				collections.append(effects_collection)
		
		elif resource_type == "CharacterSpec":
			#main_directory_path = os.path.join(export_path, main_collection.name)
			if os.path.isdir(shared_characters_dir):
				main_directory_path = export_path
			else:
				main_directory_path = os.path.join(export_path, main_collection.name)
			character_name = main_collection.name
			character_number = character_name.replace("CHR", "").replace("CHAR", "").replace("GR", "").replace("TR", "").replace("MS", "").replace("_", "")
			
			try:
				test = int(character_number)
			except:
				print("ERROR: main_collection's name is in the wrong format. Use a number in integer format.")
			
			try:
				mSkeletonID = object["SkeletonID"]
			except:
				mSkeletonID = 0x001777E6
			
			try:
				mSkeletonID = int(mSkeletonID)
			except:
				try:
					if is_valid_id(mSkeletonID) == False:
						mSkeletonID = "E6_77_17_00"
					mSkeletonID = id_to_int(mSkeletonID)
				except:
					mSkeletonID = 0x001777E6
			
			try:
				mAnimationListID = object["AnimationListID"]
			except:
				mAnimationListID = 0x001777E8
			
			try:
				mAnimationListID = int(mAnimationListID)
			except:
				try:
					if is_valid_id(mAnimationListID) == False:
						mAnimationListID = "E8_77_17_00"
					mAnimationListID = id_to_int(mAnimationListID)
				except:
					mAnimationListID = 0x001777E8
			
			
			mCharacterSpecId = int_to_id(character_number)
			characterspec_collection = collections_types["CharacterSpec"]
			
			collections = [characterspec_collection,]
		
		else:
			print("ERROR: resource type %s not supported." % resource_type)
			return {"CANCELLED"}
		
		#directory_path = os.path.join(main_directory_path, vehicle_name)
		directory_path = main_directory_path
		
		instancelist_dir = os.path.join(directory_path, "InstanceList")
		compoundinstancelist_dir = os.path.join(directory_path, "CompoundInstanceList")
		dynamicinstancelist_dir = os.path.join(directory_path, "DynamicInstanceList")
		groundcovercollection_dir = os.path.join(directory_path, "GroundcoverCollection")
		lightinstancelist_dir = os.path.join(directory_path, "LightInstanceList")
		polygonsouplist_dir = os.path.join(directory_path, "PolygonSoupList")
		propinstancelist_dir = os.path.join(directory_path, "PropInstanceList")
		zoneheader_dir = os.path.join(directory_path, "ZoneHeader")
		navigationmesh_dir = os.path.join(directory_path, "NavigationMesh")
		graphicsspec_dir = os.path.join(directory_path, "GraphicsSpec")
		genesysobject_dir = os.path.join(directory_path, "GenesysObject")
		characterspec_dir = os.path.join(directory_path, "CharacterSpec")
		model_dir = os.path.join(directory_path, "Model")
		renderable_dir = os.path.join(directory_path, "Renderable")
		vertex_descriptor_dir = os.path.join(directory_path, "VertexDescriptor")
		material_dir = os.path.join(directory_path, "Material")
		samplerstate_dir = os.path.join(directory_path, "SamplerState")
		raster_dir = os.path.join(directory_path, "Texture")
		trafficattribs_dir = os.path.join(export_path, "TRAFFICATTRIBS")
		
		export_effects = True
		
		instances = []
		instances_wheel = []
		instances_wheelGroups = {}
		instances_character = []
		instances_effects = []
		instance_collision = []
		PolygonSoups = []
		models = []
		renderables = []
		materials = []
		shaders = {}
		samplerstates = []
		rasters = []
		
		for collection in collections:
			is_hidden = bpy.context.view_layer.layer_collection.children.get(main_collection.name).children.get(collection.name).hide_viewport
			is_excluded = bpy.context.view_layer.layer_collection.children.get(main_collection.name).children.get(collection.name).exclude
			
			if is_hidden or is_excluded:
				print("WARNING: skipping collection %s since it is hidden or excluded." % (collection.name))
				print("")
				continue
			
			resource_type_child = collection["resource_type"]
			
			objects = collection.objects
			object_index = -1
			
			for object in objects:
				if object.type != "EMPTY":
					continue
				
				is_hidden = object.hide_get()
				if is_hidden == True:
					continue
				
				# Model
				mModelId = object.name
				mModelId = mModelId.split(".")[0]
				
				if resource_type_child in ("InstanceList", "GraphicsSpec", "WheelGraphicsSpec", "Wheels", "CharacterSpec"):
					if is_valid_id(mModelId) == False:
						return {"CANCELLED"}
					
					try:
						is_model_shared_asset = object["is_shared_asset"]
					except:
						is_model_shared_asset = False
					
					if is_model_shared_asset == True:
						model_path = os.path.join(shared_model_dir, mModelId + ".dat")
						if not os.path.isfile(model_path):
							print("WARNING: %s %s is set as a shared asset although it may not exist on NFSMW PC." % ("model", mModelId))
							if debug_shared_not_found == True:
								print("WARNING: setting %s %s is_shared_asset to False." % ("model", mModelId))
								is_model_shared_asset = False
				
				if resource_type_child == "InstanceList":
					try:
						object_index = object["object_index"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"object_index"'))
						object_index = object_index + 1
					
					try:
						is_instance_always_loaded = object["is_always_loaded"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"is_always_loaded"'))
						is_instance_always_loaded = True
					
					try:
						unknown_0x4 = object["unknown_0x4"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"unknown_0x4"'))
						unknown_0x4 = 1.0
					
					try:
						unknown_0x8 = object["unknown_0x8"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"unknown_0x8"'))
						unknown_0x8 = 1104995
					
					TintData = []
					try:
						has_tint_data = object["has_tint_data"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"has_tint_data"'))
						has_tint_data = 0
						#TintData = [[], [], ["AOMapTextureSampler", "LightMapTextureSampler"], ["D5_4F_91_2F", "D5_4F_91_2F"], ["D5_66_04_00", "D5_66_04_00"]]
						TintData = [["diffuseTintColour", "InstanceAdditiveAndAO", "AdditiveIntensities"], [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]], [], [], []]
					
					if has_tint_data == True:
						all_parameters_names = ["diffuseTintColour", "InstanceAdditiveAndAO", "AdditiveIntensities"]
						parameters_names = []
						parameters_data = []
						
						for parameter_name in all_parameters_names:
							try:
								tint_data = object[parameter_name]
								parameters_names.append(parameter_name)
								parameters_data.append(tint_data)
							except:
								pass
						
						try:
							samplers_names = object["samplers_names"]
							sampler_states = object["SamplerStateIds"]
							textures = object["TextureIds"]
						except:
							samplers_names = []
							sampler_states = []
							textures = []
						
						if parameters_data == [] and samplers_names == []:
							has_tint_data = False
							TintData = []
							#TintData = [[], [], ["AOMapTextureSampler", "LightMapTextureSampler"], ["D5_4F_91_2F", "D5_4F_91_2F"], ["D5_66_04_00", "D5_66_04_00"]]
							TintData = [["diffuseTintColour", "InstanceAdditiveAndAO", "AdditiveIntensities"], [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]], [], [], []]
						else:
							TintData = [parameters_names, parameters_data, samplers_names, sampler_states, textures]
							
							# Collecting texture data (same/similar loop is used later)
							if len(textures) != 0:
								for mRasterId, raster_type in zip(textures, samplers_names):
									try:
										raster = bpy.data.images[mRasterId]
									except:
										print("WARNING: No image data for texture %s. Ignoring it." % (mRasterId))
										continue
									
									if raster == None:
										print("WARNING: No image for texture %s. Ignoring it." % (mRasterId))
										continue
									
									if is_valid_id(mRasterId) == False:
										return {"CANCELLED"}
									
									try:
										is_raster_shared_asset = raster.is_shared_asset
									except:
										print("WARNING: image %s is missing parameter %s. Assuming as False." % (raster.name, '"is_shared_asset"'))
										is_raster_shared_asset = False
									
									if is_raster_shared_asset == True:
										raster_path = os.path.join(shared_raster_dir, mRasterId + ".dat")
										raster_dds_path = os.path.join(shared_raster_dir, mRasterId + ".dds")
										if os.path.isfile(raster_path) or os.path.isfile(raster_dds_path):
											mRasterId = mRasterId
										else:
											print("WARNING: %s %s is set as a shared asset although it may not exist on NFSMW PC." % ("texture", mRasterId))
											if debug_shared_not_found == True:
												print("WARNING: setting %s %s is_shared_asset to False." % ("texture", mRasterId))
												is_raster_shared_asset = False
									
									if mRasterId in (rows[0] for rows in rasters):
										continue
									
									if is_raster_shared_asset == True:
										rasters.append([mRasterId, [], is_raster_shared_asset, ""])
										continue
									
									width, height = raster.size
									if width < 4 or height < 4:
										print("ERROR: image %s resolution smaller than the supported by the game. It must be bigger than or equal to 4x4." % raster.name)
										return {"CANCELLED"}
									
									is_packed = False
									if len(raster.packed_files) > 0:
										is_packed = True
										raster.unpack(method='WRITE_LOCAL')	# Default method, it unpacks to the current .blend directory
									
									#raster_path = bpy.path.abspath(raster.filepath)
									raster_path = os.path.realpath(bpy.path.abspath(raster.filepath))
									raster.filepath = raster_path
									
									raster_source_extension = os.path.splitext(os.path.basename(raster_path))[-1].lower()
									if raster_source_extension != ".dds":
										if raster_source_extension in (".tga", ".png", ".psd", ".jpg", ".bmp"):
											if nvidiaGet() == None:
												print("ERROR: NVIDIA Texture Tools not found. Unable to convert %s to .dds" % raster_source_extension)
												return {"CANCELLED"}
											print("WARNING: converting texture %s format from %s to .dds." % (os.path.splitext(os.path.basename(raster_path))[0], raster_source_extension))
											raster_path = convert_texture_to_dxt5(raster_path, False)
										else:
											print("ERROR: texture format %s not supported. Please use .dds format." % raster_source_extension)
											return {"CANCELLED"}
									
									try:
										unknown_0x20 = raster.flags
										if unknown_0x20 == -1:
											raise Exception
									except:
										try:
											unknown_0x20 = raster.unknown_0x20
											if unknown_0x20 == -1:
												raise Exception
										except:
											try:
												unknown_0x20 = raster["unknown_0x20"]
												if unknown_0x20 == -1:
													raise Exception
											except:
												if raster_type == "NormalTextureSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (NormalTextureSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif raster_type == "EffectsTextureSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (EffectsTextureSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif raster_type == "BlurEffectsTextureSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (BlurEffectsTextureSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif raster_type == "CrumpleTextureSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (CrumpleTextureSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif raster_type == "LightmapLightsTextureSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (LightmapLightsTextureSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif raster_type == "EmissiveTextureSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (EmissiveTextureSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif raster_type == "DisplacementSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (DisplacementSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif raster_type == "AmbientOcclusionTextureSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (AmbientOcclusionTextureSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif raster_type == "AOMapTextureSampler":
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (AOMapTextureSampler)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												elif "Normal" in raster_type:
													print("WARNING: image %s is missing parameter %s. Setting as 0x20 (normal texture)" % (raster.name, '"flags"'))
													unknown_0x20 = 0x20
												else:
													print("WARNING: image %s is missing parameter %s. Setting as 0x30" % (raster.name, '"flags"'))
													unknown_0x20 = 0x30
									
									raster_properties = [unknown_0x20]
									
									rasters.append([mRasterId, [raster_properties], is_raster_shared_asset, raster_path])
									
									if is_packed == True:
										raster.pack()
					
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
					instances.append([object_index, [mModelId, [mTransform], is_instance_always_loaded, unknown_0x4, unknown_0x8, TintData[:]]])
				
				elif resource_type_child == "GraphicsSpec":
					try:
						object_index = object["object_index"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"object_index"'))
						object_index = object_index + 1
					
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
					instances.append([object_index, [mModelId, [mTransform]]])
				
				elif resource_type_child == "CharacterSpec":
					try:
						object_index = object["object_index"]
					except:
						object_index = object_index + 1
					
					instances.append([object_index, [mModelId]])
				
				elif resource_type_child == "WheelGraphicsSpec" or resource_type_child == "Wheels":
					try:
						object_index = object["object_index"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"object_index"'))
						object_index = object_index + 1
					
					try:
						is_spinnable = object["spinnable"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as True." % (object.name, '"spinnable"'))
						is_spinnable = True
					
					try:
						object_placement = object["placement"].lower()
					except:
						try:
							object_placement = object["location"].lower()
						except:
							print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"placement"'))
							object_placement = "frontleft"
					
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
					
					instances_wheel.append([object_index, [mModelId, [mTransform], is_spinnable, object_placement]])
				
				elif resource_type_child == "PolygonSoupList" or resource_type_child == "Collision":
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world)
					
					try:
						object_index = int(object.name.replace("PolygonSoup", "").replace("_", "").split(".")[0])
					except:
						try:
							object_index = int(object["object_index"])
						except:
							print("WARNING: object %s is missing parameter %s. With it is possible to set an specific order in the exported file. Assuming some value." % (object.name, '"object_index"'))
							object_index = object_index + 1
					
					try:
						child = object.children[0]
					except:
						# No meshes in the object
						continue
					
					#bbox = [list(point[:]) for point in child.bound_box]
					#bboxX, bboxY, bboxZ = zip(*bbox)
					
					mValidMasks = -1
					#PolySoupBox = [[min(bboxX), min(bboxY), min(bboxZ)], [max(bboxX), max(bboxY), max(bboxZ)], mValidMasks]
					maiVertexOffsets = mTransform.translation
					mfComprGranularity = mTransform.to_scale()[0]
					
					status, PolygonSoupVertices, PolygonSoupPolygons, mu8NumQuads = read_polygonsoup_object(child, maiVertexOffsets, mfComprGranularity)
					if status == 1:
						return {"CANCELLED"}
					
					if len(PolygonSoupVertices) == 0 or len(PolygonSoupPolygons) == 0:
						print("WARNING: collision mesh %s does not have vertices or faces. Skipping it." % child.data.name)
						continue
					
					bboxX, bboxY, bboxZ = zip(*PolygonSoupVertices)
					PolySoupBox = [[min(bboxX)*mfComprGranularity + maiVertexOffsets[0], min(bboxY)*mfComprGranularity + maiVertexOffsets[1], min(bboxZ)*mfComprGranularity + maiVertexOffsets[2]],
								   [max(bboxX)*mfComprGranularity + maiVertexOffsets[0], max(bboxY)*mfComprGranularity + maiVertexOffsets[1], max(bboxZ)*mfComprGranularity + maiVertexOffsets[2]], mValidMasks]
					
					#maiVertexOffsets /= mfComprGranularity
					#maiVertexOffsets = [int(vertex_offset) for vertex_offset in maiVertexOffsets]
					
					PolygonSoup = [object_index, PolySoupBox, maiVertexOffsets, mfComprGranularity, PolygonSoupVertices, PolygonSoupPolygons, mu8NumQuads]
					
					PolygonSoups.append(PolygonSoup)
					
					continue
				
				elif resource_type_child == "Character" or resource_type_child == "Driver":
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world)
					characterOffset = mTransform.translation
					
					try:
						mCharacterSpecID = object["CharacterSpecID"]
					except:
						try:
							mCharacterSpecID = object["CharacterID"]
						except:
							mCharacterSpecID = 0x00003D8E
					
					try:
						mCharacterSpecID = int(mCharacterSpecID)
					except:
						try:
							if is_valid_id(mCharacterSpecID) == False:
								mCharacterSpecID = "8E_3D_00_00"
							mCharacterSpecID = id_to_int(mCharacterSpecID)
						except:
							mCharacterSpecID = 0x00003D8E
					
					instances_character = [mCharacterSpecID, characterOffset]
					
					continue
				
				elif resource_type_child == "Effects" or resource_type_child == "Effect":
					if object.parent != None:
						continue
					
					try:
						effect_index = int(object.name.split("_")[1].split(".")[0])
					except:
						try:
							effect_index = int(object["effect_index"])
						except:
							print("ERROR: effect object %s is missing parameter %s. Effects will not be exported." % (object.name, '"effect_index"'))
							export_effects = False
							continue
					
					try:
						EffectId = object["EffectId"]
					except:
						print("ERROR: effect object %s is missing parameters %s. Effects will not be exported." % (object.name, '"EffectId"'))
						export_effects = False
						continue
					
					try:
						EffectId = int(EffectId)
					except:
						try:
							EffectId = id_to_int(EffectId)
						except:
							print("ERROR: effect object %s parameter %s is not an integer or an Id. Effects will not be exported." % (object.name, '"EffectId"'))
							export_effects = False
							continue
					
					effect_copy_instance = []
					for child in object.children:
						if child.type != "EMPTY":
							continue
						
						if force_rotation == True:
							transform_args[1] = True
							apply_transfrom(child, global_rotation, *transform_args)
						
						mTransform = Matrix(np.linalg.inv(m) @ child.matrix_world)
						effectLocation = mTransform.translation
						child.rotation_mode = 'QUATERNION'
						effectRotation = [0.0, 0.0, 0.0, 1.0]
						
						effectRotation[3] = mTransform.to_quaternion()[0]
						effectRotation[0] = mTransform.to_quaternion()[1]
						effectRotation[1] = mTransform.to_quaternion()[2]
						effectRotation[2] = mTransform.to_quaternion()[3]
						
						try:
							effect_copy = int(child.name.split("_")[3].split(".")[0])
						except:
							try:
								effect_copy = int(child["effect_copy"])
							except:
								#print("ERROR: effect object %s is missing parameters %s. Effects will not be exported." % (child.name, '"effect_copy"'))
								#continue
								effect_copy = 0
						
						try:
							EffectData = child["EffectData"]
						except:
							EffectData = None
						
						effect_copy_instance.append([effect_copy, [effectLocation, effectRotation], EffectData])
						
					
					effect_instance = [EffectId, effect_index, effect_copy_instance[:]]
					instances_effects.append(effect_instance)
					
					continue
				
				if mModelId in (rows[0] for rows in models):
					continue
				
				try:
					is_model_shared_asset = object["is_shared_asset"]
				except:
					print("WARNING: object %s is missing parameter %s. Assuming as False." % (object.name, '"is_shared_asset"'))
					is_model_shared_asset = False
				
				if is_model_shared_asset == True:
					model_path = os.path.join(shared_model_dir, mModelId + ".dat")
					if not os.path.isfile(model_path):
						#print("WARNING: %s %s is set as a shared asset although it may not exist on MW2012 PC." % ("model", mModelId))
						if debug_shared_not_found == True:
							#print("WARNING: setting %s %s is_shared_asset to False." % ("model", mModelId))
							is_model_shared_asset = False
				
				if is_model_shared_asset == True:
					models.append([mModelId, [[], []], is_model_shared_asset])
					continue
				
				renderables_info = []
				
				num_objects = 0
				for child in object.children:
					if child.type != "MESH":
						continue
					if child.hide_get() == True and ignore_hidden_meshes == True:
						continue
					num_objects += 1
				
				if num_objects == 0:
					# It is an empty dummy, probably a duplicated model making reference to the same renderables
					continue
				
				for child in object.children:
					if child.type != "MESH":
						continue
					
					if child.hide_get() == True and ignore_hidden_meshes == True:
						continue
					
					if force_rotation == True:
						transform_args[1] = True
						apply_transfrom(child, global_rotation, *transform_args)
					
					
					mRenderableId = child.name
					mRenderableId = mRenderableId.split(".")[0]
					if is_valid_id(mRenderableId) == False:
						return {"CANCELLED"}
					
					try:
						is_shared_asset = child["is_shared_asset"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as False." % (child.name, '"is_shared_asset"'))
						is_shared_asset = False
					
					if is_shared_asset == True:
						renderable_path = os.path.join(shared_renderable_dir, mRenderableId + ".dat")
						if not os.path.isfile(renderable_path):
							print("WARNING: %s %s is set as a shared asset although it may not exist on NFSMW PC." % ("renderable", mRenderableId))
							if debug_shared_not_found == True:
								print("WARNING: setting %s %s is_shared_asset to False." % ("renderable", mRenderableId))
								is_shared_asset = False
					
					try:
						renderable_index = child["renderable_index"]
					except:
						if num_objects == 1:
							renderable_index = 0
						else:
							print("ERROR: object %s is missing parameter %s." % (child.name, '"renderable_index"'))
							return {"CANCELLED"}
					
					renderables_info.append([mRenderableId, [renderable_index]])
					
					if mRenderableId in (rows[0] for rows in renderables):
						continue
					
					if is_shared_asset == True:
						renderables.append([mRenderableId, [[], [], [], []], is_shared_asset, ""])
						continue
					
					bbox_x, bbox_y, bbox_z = [[point[i] for point in child.bound_box] for i in range(3)]
					object_center = [(max(bbox_x) + min(bbox_x))*0.5, (max(bbox_y) + min(bbox_y))*0.5, (max(bbox_z) + min(bbox_z))*0.5]
					object_radius = math.dist(object_center, child.bound_box[0])
					
					meshes_info, indices_buffer, vertices_buffer, object_center, object_radius, status = read_object(child, resource_type_child, shared_dir, copy_uv_layer)
					
					if status == 1:
						return {'CANCELLED'}
					
					num_meshes = len(meshes_info)
					renderable_properties = [object_center, object_radius, num_meshes]
					
					renderables.append([mRenderableId, [meshes_info, renderable_properties, indices_buffer, vertices_buffer], is_shared_asset, ""])
					
					for k, mesh_info in enumerate(meshes_info):
						mMaterialId = mesh_info[1]
						if is_valid_id(mMaterialId) == False:
							return {"CANCELLED"}
						
						mat = bpy.data.materials.get(mMaterialId) or bpy.data.materials.get(id_swap(mMaterialId))
						
						try:
							is_material_shared_asset = mat["is_shared_asset"]
						except:
							print("WARNING: material %s is missing parameter %s. Assuming as False." % (mat.name, '"is_shared_asset"'))
							is_material_shared_asset = False
						
						if is_material_shared_asset == True:
							material_path = os.path.join(shared_material_dir, mMaterialId + ".dat")
							if not os.path.isfile(material_path):
								print("WARNING: %s %s is set as a shared asset although it may not exist on MW2012 PC." % ("material", mMaterialId))
								if debug_shared_not_found == True:
									print("WARNING: setting %s %s is_shared_asset to False." % ("material", mMaterialId))
									is_material_shared_asset = False
							else:
								mShaderId, mSamplerStateIds, = read_material_get_shader_type(material_path)
								shader_path = os.path.join(shared_shader_dir, mShaderId + "_83.dat")
								shader_type, _, _, _, _, _, _ = read_shader(shader_path)
								
								for mSamplerStateId in mSamplerStateIds:
									if mSamplerStateId not in samplerstates:
										samplerstates.append(mSamplerStateId)
						
						try:
							if is_material_shared_asset == False:
								shader_type = mat["shader_type"]
						except:
							#print("WARNING: material %s is missing parameter %s. Defining it as 'VehicleNFS13_BodyPaint_Livery'." % (mat.name, '"shader_type"'))
							#shader_type = 'VehicleNFS13_BodyPaint_Livery'
							print("WARNING: material %s is missing parameter %s." % (mat.name, '"shader_type"'))
							shader_type = ""
						
						mShaderId, shader_type = get_mShaderID(shader_type, resource_type)
						if mShaderId == "":
							print("ERROR: material %s is set to a nonexistent %s: %s." % (mat.name, '"shader_type"', shader_type))
							return {"CANCELLED"}
						
						# Reading shader for getting required raster types and properties
						if mShaderId in shaders:
							mVertexDescriptorId, num_sampler_states_shader, required_raster_types, material_parameters_from_shader, material_constants_from_shader, texture_samplers = shaders[mShaderId]
						else:
							shader_path = os.path.join(shared_shader_dir, mShaderId + "_83.dat")
							shader_description_, mVertexDescriptorId, num_sampler_states_shader, required_raster_types, material_parameters_from_shader, material_constants_from_shader, texture_samplers = read_shader(shader_path)
							shaders[mShaderId] = (mVertexDescriptorId, num_sampler_states_shader, required_raster_types, material_parameters_from_shader, material_constants_from_shader, texture_samplers)
						required_raster_types = dict((v,k) for k,v in required_raster_types.items())
						
						mesh_info.append(mVertexDescriptorId)
						
						if mMaterialId in (rows[0] for rows in materials):
							continue
						
						if is_material_shared_asset == True:
							materials.append([mMaterialId, ["", [], [], [], [], [], []], is_material_shared_asset])
							continue
						
						material_color = []
						for node in mat.node_tree.nodes:
							if node.type in ["BSDF_GLOSSY", "BSDF_DIFFUSE", "EMISSION", "BSDF_GLASS", "BSDF_REFRACTION", "EEVEE_SPECULAR", "SUBSURFACE_SCATTERING", "BSDF_PRINCIPLED", "PRINCIPLED_VOLUME", "BSDF_TRANSLUCENT", "VOLUME_ABSORPTION", "VOLUME_SCATTER"]:
								material_color = node.inputs[0].default_value[:]
						
						parameters_Indices = []
						parameters_Ones = []
						parameters_NamesHash = []
						parameters_Data = []
						parameters_Names = []
						material_constants = []
						miChannel = []
						raster_type_offsets = []
						
						try:
							if debug_use_default_samplerstates == True:
								raise Exception
							sampler_states_info = mat["SamplerStateIds"]
						except:
							if debug_use_default_samplerstates == False:
								print("WARNING: material %s is missing parameter %s. Using default ones." % (mat.name, '"SamplerStateIds"'))
							
							try:
								sampler_states_info = get_default_sampler_states(shader_type, mShaderId, num_sampler_states_shader)
							except:
								print("WARNING: get_default_sampler_states function not found. Custom data will not be available.")
								sampler_states_info = ["7F_77_6A_0A"]*num_sampler_states_shader
						
						num_sampler_states = len(sampler_states_info)
						if num_sampler_states != num_sampler_states_shader:
							print("WARNING: number of sampler states (%d) on material %s is different from the %d required by the shader %s." % (num_sampler_states, mMaterialId, num_sampler_states_shader, mShaderId))
						
						if debug_use_shader_material_parameters == True:
							parameters_Indices = material_parameters_from_shader[0]
							parameters_Ones = material_parameters_from_shader[1]
							parameters_NamesHash = material_parameters_from_shader[2]
							parameters_Data = material_parameters_from_shader[3][:]
							parameters_Names = material_parameters_from_shader[4]
						else:
							try:
								status, material_parameters = get_default_material_parameters(shader_type)
								material_parameters = [list(param) for param in material_parameters]
							except:
								print("WARNING: get_default_material_parameters function not found. Custom data will not be available.")
								status = 1
							
							if status == 0:
								parameters_Indices = material_parameters[0]
								parameters_Ones = material_parameters[1]
								parameters_NamesHash = material_parameters[2]
								parameters_Data = material_parameters[3][:]
								parameters_Names = material_parameters[4]
							else:
								parameters_Indices = material_parameters_from_shader[0]
								parameters_Ones = material_parameters_from_shader[1]
								parameters_NamesHash = material_parameters_from_shader[2]
								parameters_Data = material_parameters_from_shader[3][:]
								parameters_Names = material_parameters_from_shader[4]
							
							for i in range(0, len(parameters_Names)):
								if parameters_Names[i] in mat:
									parameters_Data[i] = mat[parameters_Names[i]]
								elif (parameters_Names[i] == "PbrMaterialDiffuseColour" or parameters_Names[i] == "MaterialColour_SimpleMultiply") and material_color != [] and status != 0:
									parameters_Data[i] = material_color[:]
						
						# Fix the order of the material parameters
						parameters_Indices_fixed = []
						if shader_type == "VehicleNFS13_Wheel_Alpha1bit_Normalmap":
							parameters_Indices_fixed = [3, 5, 4, 2, 1, 0]
						elif shader_type == "VehicleNFS13_Wheel_Alpha1bit_Textured_Normalmap":
							parameters_Indices_fixed = [3, 2, 1, 0]
						elif shader_type == "VehicleNFS13_Wheel_Alpha_Textured_Normalmap":
							parameters_Indices_fixed = [3, 2, 1, 0]
						elif shader_type == "VehicleNFS13_Wheel_Alpha_Textured_Normalmap_BlurFade":
							parameters_Indices_fixed = [3, 2, 1, 0]
						elif shader_type == "VehicleNFS13_Wheel_Alpha_Textured_Normalmap_Blurred_Doublesided_PixelAO":
							parameters_Indices_fixed = [4, 3, 2, 1, 0]
						elif shader_type == "VehicleNFS13_Wheel_Textured_Normalmap_Blurred":
							parameters_Indices_fixed = [4, 3, 2, 1, 0]
						elif shader_type == "VehicleNFS13_Wheel_Textured_Roughness":
							parameters_Indices_fixed = [4, 3, 2, 1, 0]
						elif shader_type == "VehicleNFS13_Wheel_Tyre_Textured_Normalmap_Blurred":
							parameters_Indices_fixed = [4, 3, 2, 1, 0]
						elif shader_type == "PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Lightmap_Singlesided_Rough":
							parameters_Indices_fixed = [9, 11, 5, 7, 8, 1, 10, 6, 2, 3, 4, 0]
						elif shader_type == "PlotPBR_AO_Normal_Specular_Opaque_Singlesided":
							parameters_Indices_fixed = [8, 10, 5, 7, 1, 9, 6, 2, 3, 4, 0]
						elif shader_type == "PlotPBR_AO_Normal_Specular_Opaque_Lightmap_Singlesided":
							parameters_Indices_fixed = [9, 11, 5, 7, 8, 1, 10, 6, 2, 3, 4, 0]
						elif shader_type == "PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Singlesided_Rough":
							parameters_Indices_fixed = [8, 10, 5, 7, 1, 9, 6, 2, 3, 4, 0]
						elif shader_type == "PlotPBR_AO_Normal_Specular_Opaque_Lightmap_Singlesided_Rough":
							parameters_Indices_fixed = [9, 11, 5, 7, 8, 1, 10, 6, 2, 3, 4, 0]
						
						# if len(parameters_Indices) == len(parameters_Indices_fixed):
							# parameters_Order = [parameters_Indices.index(index) for index in parameters_Indices_fixed]
							
							# parameters_Indices = [parameters_Indices[i] for i in parameters_Order]
							# parameters_Ones = [parameters_Ones[i] for i in parameters_Order]
							# #parameters_NamesHash = [parameters_NamesHash[i] for i in parameters_Order]
							# parameters_Data = [parameters_Data[i] for i in parameters_Order]
							# parameters_Names = [parameters_Names[i] for i in parameters_Order]
						
						if "g_flipUvsOnFlippedTechnique" in parameters_Names:
							index = parameters_Names.index("g_flipUvsOnFlippedTechnique")
							
							parameters_Indices.insert(0, parameters_Indices.pop(index))
							#parameters_Ones.insert(0, parameters_Ones.pop(index))
							#parameters_NamesHash.insert(0, parameters_NamesHash.pop(index))
							parameters_Data.insert(0, parameters_Data.pop(index))
							parameters_Names.insert(0, parameters_Names.pop(index))
						
						if parameters_Indices_fixed != []:
							parameters_Indices = parameters_Indices_fixed[:]
						
						material_constants = material_constants_from_shader
						miChannel = [0]*num_sampler_states_shader
						raster_type_offsets = [0]*num_sampler_states_shader
						
						material_parameters = [parameters_Indices[:], parameters_Ones[:], parameters_NamesHash[:], parameters_Data[:], parameters_Names[:]]
						sampler_properties = [material_constants, miChannel, raster_type_offsets]
						textures_info = []
						
						for i, mSamplerStateId in enumerate(sampler_states_info):
							if is_valid_id(mSamplerStateId) == False:
								return {"CANCELLED"}
							
							if mSamplerStateId not in samplerstates:
								samplerstates.append(mSamplerStateId)
						
						for node in mat.node_tree.nodes:
							if node.type == "TEX_IMAGE":
								raster_type = node.name.split(".")[0]
								
								try:
									texture_sampler_code = required_raster_types[raster_type]
								except:
									texture_sampler_code = 0xFF
								
								raster = node.image
								if raster == None:
									print("WARNING: No image on texture node %s of the material %s. Ignoring it." % (node.label, mMaterialId))
									continue
								
								mRasterId = raster.name.split(".")[0]
								if is_valid_id(mRasterId) == False:
									return {"CANCELLED"}
								
								# Not used texture by shader
								if texture_sampler_code != 0xFF:
									textures_info.append([mRasterId, texture_sampler_code, raster_type])
								
								try:
									is_raster_shared_asset = raster.is_shared_asset
								except:
									print("WARNING: image %s is missing parameter %s. Assuming as False." % (raster.name, '"is_shared_asset"'))
									is_raster_shared_asset = False
								
								if is_raster_shared_asset == True:
									raster_path = os.path.join(shared_raster_dir, mRasterId + ".dat")
									raster_dds_path = os.path.join(shared_raster_dir, mRasterId + ".dds")
									if os.path.isfile(raster_path) or os.path.isfile(raster_dds_path):
										mRasterId = mRasterId
									else:
										print("WARNING: %s %s is set as a shared asset although it may not exist on NFSMW PC." % ("texture", mRasterId))
										if debug_shared_not_found == True:
											print("WARNING: setting %s %s is_shared_asset to False." % ("texture", mRasterId))
											is_raster_shared_asset = False
								
								if mRasterId in (rows[0] for rows in rasters):
									continue
								
								if is_raster_shared_asset == True:
									rasters.append([mRasterId, [], is_raster_shared_asset, ""])
									continue
								
								width, height = raster.size
								if width < 4 or height < 4:
									print("ERROR: image %s resolution smaller than the supported by the game. It must be bigger than or equal to 4x4." % raster.name)
									return {"CANCELLED"}
								
								is_packed = False
								if len(raster.packed_files) > 0:
									is_packed = True
									raster.unpack(method='WRITE_LOCAL')	# Default method, it unpacks to the current .blend directory
								
								#raster_path = bpy.path.abspath(raster.filepath)
								raster_path = os.path.realpath(bpy.path.abspath(raster.filepath))
								raster.filepath = raster_path
								
								raster_source_extension = os.path.splitext(os.path.basename(raster_path))[-1]
								if raster_source_extension != ".dds":
									if raster_source_extension in (".tga", ".png", ".psd", ".jpg", ".bmp"):
										if nvidiaGet() == None:
											print("ERROR: NVIDIA Texture Tools not found. Unable to convert %s to .dds" % raster_source_extension)
											return {"CANCELLED"}
										print("WARNING: converting texture %s format from %s to .dds." % (os.path.splitext(os.path.basename(raster_path))[0], raster_source_extension))
										raster_path = convert_texture_to_dxt5(raster_path, False)
									else:
										print("ERROR: texture format %s not supported. Please use .dds format." % raster_source_extension)
										return {"CANCELLED"}
								
								try:
									unknown_0x20 = raster.flags
									if unknown_0x20 == -1:
										raise Exception
								except:
									try:
										unknown_0x20 = raster.unknown_0x20
										if unknown_0x20 == -1:
											raise Exception
									except:
										try:
											unknown_0x20 = raster["unknown_0x20"]
											if unknown_0x20 == -1:
												raise Exception
										except:
											if raster_type == "NormalTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (NormalTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "EffectsTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (EffectsTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "BlurEffectsTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (BlurEffectsTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "CrumpleTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (CrumpleTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "LightmapLightsTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (LightmapLightsTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "EmissiveTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (EmissiveTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "DisplacementSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (DisplacementSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "AmbientOcclusionTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (AmbientOcclusionTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "AOMapTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (AOMapTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif "Normal" in raster_type:
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (normal texture)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											else:
												print("WARNING: image %s is missing parameter %s. Setting as 0x30" % (raster.name, '"flags"'))
												unknown_0x20 = 0x30
								
								raster_properties = [unknown_0x20]
								
								rasters.append([mRasterId, [raster_properties], is_raster_shared_asset, raster_path])
								
								if is_packed == True:
									raster.pack()
						
						if len(textures_info) != num_sampler_states_shader:
							print("WARNING: number of textures (%d) on material %s is different from the %d required by the shader %s." % (len(textures_info), mMaterialId, num_sampler_states_shader, mShaderId))
							
							texture_sampler_codes = [texture_info[1] for texture_info in textures_info]
							for raster_type, miChannel in required_raster_types.items():
								if miChannel in texture_sampler_codes:
									continue
								
								try:
									mRasterId, raster_properties, is_raster_shared_asset, raster_path = get_default_mRasterId(shader_type, mShaderId, raster_type, resource_type)
								except:
									print("WARNING: get_default_mRasterId function not found. Custom data will not be available.")
									
									is_raster_shared_asset = True
									raster_path = ""
									raster_properties = []
									if resource_type == "InstanceList":
										mRasterId = "1D_F3_05_00"
									else:
										mRasterId = "30_A7_06_00"
									
									if resource_type == "InstanceList":
										mRasterId = "1D_F3_05_00"
									else:
										if raster_type == 'DiffuseTextureSampler':
											mRasterId = "30_A7_06_00"
										elif raster_type == 'NormalTextureSampler':
											mRasterId = "06_88_13_00"
										elif raster_type == 'ExternalNormalTextureSampler':
											mRasterId = "06_88_13_00"
										elif raster_type == 'InternalNormalTextureSampler':
											mRasterId = "06_88_13_00"
										elif raster_type == 'CrackedGlassNormalTextureSampler':
											mRasterId = "30_A7_06_00"
										elif raster_type == 'SpecularTextureSampler':
											mRasterId = "30_A7_06_00"
										elif raster_type == 'CrumpleTextureSampler':
											mRasterId = "49_02_06_00"
										elif raster_type == 'EffectsTextureSampler':
											#mRasterId = "1C_8D_0D_00"
											mRasterId = "30_A7_06_00"
										elif raster_type == 'LightmapTextureSampler':
											mRasterId = "0A_08_11_00"
										elif raster_type == 'LightmapLightsTextureSampler':
											mRasterId = "0A_08_11_00"
										elif raster_type == 'EmissiveTextureSampler':
											mRasterId = "0A_08_11_00"
										elif raster_type == 'ColourSampler':
											mRasterId = "0B_08_11_00"
										elif raster_type == 'DisplacementSampler':
											#mRasterId = "30_A7_06_00"
											mRasterId = "7D_A1_02_A1"
											raster_properties = [0x20]
											is_raster_shared_asset = False
											raster_path = "create_texture"
										elif raster_type == 'CrackedGlassTextureSampler':
											mRasterId = "7F_07_11_00"
											#mRasterId = "30_A7_06_00"
								
								textures_info.append([mRasterId, miChannel, raster_type])
								rasters.append([mRasterId, [raster_properties[:]], is_raster_shared_asset, raster_path])
								
							
						materials.append([mMaterialId, [mShaderId, textures_info, sampler_states_info, material_parameters, sampler_properties, texture_samplers], is_material_shared_asset])
				
				renderable_indices = [renderable_info[1][0] for renderable_info in renderables_info]
				indices_range = list(range(0, max(renderable_indices) + 1))
				if sorted(renderable_indices) != indices_range:
					print("ERROR: missing or duplicated renderable indices on object %s childs. Verify the %s parameters for skipped or duplicated entries." % (object.name, '"renderable_index"'))
					print("renderable_indices =", renderable_indices, indices_range)
					return {"CANCELLED"}
				
				mu8NumRenderables = len(renderables_info)
				mu8NumStates = 5
				
				has_tint_data = 0
				TintData = []
				try:
					has_tint_data = object["model_has_tint_data"]
				except:
					if resource_type == "InstanceList":
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"model_has_tint_data"'))
						has_tint_data = 0
						TintData = [[], [], ["AOMapTextureSampler", "LightMapTextureSampler"], ["D5_4F_91_2F", "D5_4F_91_2F"], ["D5_66_04_00", "D5_66_04_00"]]
					else:
						pass
				
				if has_tint_data == True:
					all_parameters_names = ["model_diffuseTintColour", "model_InstanceAdditiveAndAO", "model_AdditiveIntensities"]
					parameters_names = []
					parameters_data = []
					
					for parameter_name in all_parameters_names:
						try:
							tint_data = object[parameter_name]
							parameters_names.append(parameter_name.replace("model_", ""))
							parameters_data.append(tint_data)
						except:
							pass
					
					try:
						samplers_names = object["model_samplers_names"]
						sampler_states = object["model_SamplerStateIds"]
						textures = object["model_TextureIds"]
					except:
						samplers_names = []
						sampler_states = []
						textures = []
					
					if parameters_data == [] and samplers_names == []:
						has_tint_data = False
						#TintData = []
						TintData = [[], [], ["AOMapTextureSampler", "LightMapTextureSampler"], ["D5_4F_91_2F", "D5_4F_91_2F"], ["D5_66_04_00", "D5_66_04_00"]]
					else:
						TintData = [parameters_names, parameters_data, samplers_names, sampler_states, textures]
						
						# Collecting texture data (same/similar loop is used later)
						if len(textures) != 0:
							for mRasterId, raster_type in zip(textures, samplers_names):
								try:
									raster = bpy.data.images[mRasterId]
								except:
									print("WARNING: No image data for texture %s. Ignoring it." % (mRasterId))
									continue
								
								if raster == None:
									print("WARNING: No image for texture %s. Ignoring it." % (mRasterId))
									continue
								
								if is_valid_id(mRasterId) == False:
									return {"CANCELLED"}
								
								try:
									is_raster_shared_asset = raster.is_shared_asset
								except:
									print("WARNING: image %s is missing parameter %s. Assuming as False." % (raster.name, '"is_shared_asset"'))
									is_raster_shared_asset = False
								
								if is_raster_shared_asset == True:
									raster_path = os.path.join(shared_raster_dir, mRasterId + ".dat")
									raster_dds_path = os.path.join(shared_raster_dir, mRasterId + ".dds")
									if os.path.isfile(raster_path) or os.path.isfile(raster_dds_path):
										mRasterId = mRasterId
									else:
										print("WARNING: %s %s is set as a shared asset although it may not exist on NFSMW PC." % ("texture", mRasterId))
										if debug_shared_not_found == True:
											print("WARNING: setting %s %s is_shared_asset to False." % ("texture", mRasterId))
											is_raster_shared_asset = False
								
								if mRasterId in (rows[0] for rows in rasters):
									continue
								
								if is_raster_shared_asset == True:
									rasters.append([mRasterId, [], is_raster_shared_asset, ""])
									continue
								
								width, height = raster.size
								if width < 4 or height < 4:
									print("ERROR: image %s resolution smaller than the supported by the game. It must be bigger than or equal to 4x4." % raster.name)
									return {"CANCELLED"}
								
								is_packed = False
								if len(raster.packed_files) > 0:
									is_packed = True
									raster.unpack(method='WRITE_LOCAL')	# Default method, it unpacks to the current .blend directory
								
								#raster_path = bpy.path.abspath(raster.filepath)
								raster_path = os.path.realpath(bpy.path.abspath(raster.filepath))
								raster.filepath = raster_path
								
								raster_source_extension = os.path.splitext(os.path.basename(raster_path))[-1]
								if raster_source_extension != ".dds":
									if raster_source_extension in (".tga", ".png", ".psd", ".jpg", ".bmp"):
										if nvidiaGet() == None:
											print("ERROR: NVIDIA Texture Tools not found. Unable to convert %s to .dds" % raster_source_extension)
											return {"CANCELLED"}
										print("WARNING: converting texture %s format from %s to .dds." % (os.path.splitext(os.path.basename(raster_path))[0], raster_source_extension))
										raster_path = convert_texture_to_dxt5(raster_path, False)
									else:
										print("ERROR: texture format %s not supported. Please use .dds format." % raster_source_extension)
										return {"CANCELLED"}
								
								try:
									unknown_0x20 = raster.flags
									if unknown_0x20 == -1:
										raise Exception
								except:
									try:
										unknown_0x20 = raster.unknown_0x20
										if unknown_0x20 == -1:
											raise Exception
									except:
										try:
											unknown_0x20 = raster["unknown_0x20"]
											if unknown_0x20 == -1:
												raise Exception
										except:
											if raster_type == "NormalTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (NormalTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "EffectsTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (EffectsTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "BlurEffectsTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (BlurEffectsTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "CrumpleTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (CrumpleTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "LightmapLightsTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (LightmapLightsTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "EmissiveTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (EmissiveTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "DisplacementSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (DisplacementSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "AmbientOcclusionTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (AmbientOcclusionTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif raster_type == "AOMapTextureSampler":
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (AOMapTextureSampler)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											elif "Normal" in raster_type:
												print("WARNING: image %s is missing parameter %s. Setting as 0x20 (normal texture)" % (raster.name, '"flags"'))
												unknown_0x20 = 0x20
											else:
												print("WARNING: image %s is missing parameter %s. Setting as 0x30" % (raster.name, '"flags"'))
												unknown_0x20 = 0x30
								
								raster_properties = [unknown_0x20]
								
								rasters.append([mRasterId, [raster_properties], is_raster_shared_asset, raster_path])
								
								if is_packed == True:
									raster.pack()
				
				model_properties = [mu8NumRenderables, mu8NumStates, TintData]
				
				models.append([mModelId, [renderables_info, model_properties], is_model_shared_asset])
			
			# Removing models from intancesList that do not have a model file (generic or not)
			instances[:] = [instance for instance in instances if instance[1][0] in (rows[0] for rows in models)]
			instances_wheel[:] = [instance for instance in instances_wheel if instance[1][0] in (rows[0] for rows in models)]
		
		if len(instances) == 0 and len(instances_wheel) == 0 and len(instances_character) == 0 and resource_type != "InstanceList" and (resource_type != "PolygonSoupList" and resource_type != "Collision"):
			print("ERROR: no models in the proper structure. Nothing to export on this collection.")
			return {"CANCELLED"}
		
		if resource_type == "GraphicsSpec":
			object_indices = [instance[0] for instance in instances]
			indices_range = list(range(0, max(object_indices) + 1))
			if sorted(object_indices) != indices_range:
				print("ERROR: missing or duplicated object indices. Verify the %s parameters for skipped or duplicated entries." % '"ObjectIndex"')
				print("object_indices =", object_indices)
				return {"CANCELLED"}
		
		if len(instances_wheel) > 0:
			instances_wheelGroups = {object[1][3]: [] for object in instances_wheel}
			for object in instances_wheel:
				object_index, [mModelId, [mTransform], is_spinnable, object_placement] = object
				mModelId = object[1][0]
				is_spinnable = object[1][2]
				object_placement = object[1][3]
				
				instances_wheelGroups[object_placement].append([object_index, [mModelId, [mTransform], is_spinnable, object_placement]])
			
			for object in instances_wheelGroups.items():
				object[1].sort(key=lambda x:x[0])
			
			if len(instances_wheelGroups) < 4:
				print("ERROR: missing a wheel placement. Verify if the scene has all four wheels correctly placed and if their custom properties are properly set.")
				return {"CANCELLED"}
		
		if len(PolygonSoups) > 0:
			if resource_type == "InstanceList":
				mPolygonSoupList = "TRK_COL_" + str(track_unit_number)
			elif resource_type == "GraphicsSpec":
				mPolygonSoupList = "VEH_COL_" + str(vehicle_number)
			mPolygonSoupListId = calculate_resourceid(mPolygonSoupList.lower())
			PolygonSoups.sort(key=lambda x:x[0])
			instance_collision = [mPolygonSoupListId, PolygonSoups]
		
		if len(instances_effects) > 0:
			effect_indices = [effect_instance[1] for effect_instance in instances_effects]
			indices_range = list(range(0, max(effect_indices) + 1))
			for i in indices_range:
				if i not in effect_indices:
					print("ERROR: effects instance is missing effect %d. Effects will not be exported." % i)
					export_effects = False
					break
			
			instances_effects.sort(key=lambda x:x[1])
		
		## Writing data
		print("\tWriting data...")
		writing_time = time.time()
		
		mResourceIds = []
		mPolygonSoupListId_previous = ""
		if resource_type == "InstanceList":
			library_trk_path = os.path.join(shared_dir, "TRKs", track_unit_name)
			if os.path.isdir(library_trk_path):
				print("WARNING: track unit folder %s exists on library. Copying it." % track_unit_name)
				shutil.copytree(library_trk_path, directory_path)
			else:
				print("WARNING: track unit folder %s does not exist on library." % track_unit_name)
				pass
			
			instancelist_path = os.path.join(instancelist_dir, mInstanceListId + ".dat")
			compoundinstancelist_path = os.path.join(compoundinstancelist_dir, mCompoundInstanceListId + ".dat")
			dynamicinstancelist_path = os.path.join(dynamicinstancelist_dir, mDynamicInstanceListId + ".dat")
			groundcovercollection_path = os.path.join(groundcovercollection_dir, mGroundcoverCollectionId + ".dat")
			lightinstancelist_path = os.path.join(lightinstancelist_dir, mLightInstanceListId + ".dat")
			polygonsouplist_path = os.path.join(polygonsouplist_dir, mPolygonSoupListId + ".dat")
			propinstancelist_path = os.path.join(propinstancelist_dir, mPropInstanceListId + ".dat")
			zoneheader_path = os.path.join(zoneheader_dir, mZoneHeaderId + ".dat")
			navigationmesh_path = os.path.join(navigationmesh_dir, mNavigationMeshId + ".dat")
			
			if len(PolygonSoups) == 0:
				instance_collision = [mPolygonSoupListId, []]
			
			if os.path.isfile(instancelist_path):
				print("WARNING: file %s already exists in track unit %s. Replacing it with new file if there are entries." %(mInstanceListId, track_unit_name))
				if len(instances) > 0:
					write_instancelist(instancelist_path, instances)
			else:
				write_instancelist(instancelist_path, instances)
				mResourceIds.append([mInstanceListId, "InstanceList", id_to_int(mInstanceListId)])
			
			if os.path.isfile(polygonsouplist_path):
				print("WARNING: file %s already exists in track unit %s. Replacing it with new file if there are entries." %(mPolygonSoupListId, track_unit_name))
				if len(instance_collision[1]) > 0:
					write_polygonsouplist(polygonsouplist_path, instance_collision[1])
			else:
				write_polygonsouplist(polygonsouplist_path, instance_collision[1])
				mResourceIds.append([mPolygonSoupListId, "PolygonSoupList", id_to_int(mPolygonSoupListId)])
			
			if os.path.isfile(compoundinstancelist_path):
				print("WARNING: file %s already exists in track unit %s. Skipping it." %(mCompoundInstanceListId, track_unit_name))
			else:
				write_compoundinstancelist(compoundinstancelist_path)
				mResourceIds.append([mCompoundInstanceListId, "CompoundInstanceList", id_to_int(mCompoundInstanceListId)])
			
			if os.path.isfile(dynamicinstancelist_path):
				print("WARNING: file %s already exists in track unit %s. Skipping it." %(mDynamicInstanceListId, track_unit_name))
			else:
				write_dynamicinstancelist(dynamicinstancelist_path)
				mResourceIds.append([mDynamicInstanceListId, "DynamicInstanceList", id_to_int(mDynamicInstanceListId)])
			
			if os.path.isfile(groundcovercollection_path):
				print("WARNING: file %s already exists in track unit %s. Skipping it." %(mGroundcoverCollectionId, track_unit_name))
			else:
				write_groundcovercollection(groundcovercollection_path)
				mResourceIds.append([mGroundcoverCollectionId, "GroundcoverCollection", id_to_int(mGroundcoverCollectionId)])
			
			if os.path.isfile(lightinstancelist_path):
				print("WARNING: file %s already exists in track unit %s. Skipping it." %(mLightInstanceListId, track_unit_name))
			else:
				write_lightinstancelist(lightinstancelist_path)
				mResourceIds.append([mLightInstanceListId, "LightInstanceList", id_to_int(mLightInstanceListId)])
			
			if os.path.isfile(propinstancelist_path):
				print("WARNING: file %s already exists in track unit %s. Skipping it." %(mPropInstanceListId, track_unit_name))
			else:
				write_propinstancelist(propinstancelist_path)
				mResourceIds.append([mPropInstanceListId, "PropInstanceList", id_to_int(mPropInstanceListId)])
			
			if os.path.isfile(navigationmesh_path):
				print("WARNING: file %s already exists in track unit %s. Skipping it." %(mNavigationMeshId, track_unit_name))
			else:
				write_navigationmesh(navigationmesh_path)
				mResourceIds.append([mNavigationMeshId, "NavigationMesh", id_to_int(mNavigationMeshId)])
			
			if os.path.isfile(zoneheader_path):
				print("WARNING: file %s already exists in track unit %s. Skipping it." %(mZoneHeaderId, track_unit_name))
			else:
				write_zoneheader(zoneheader_path, mInstanceListId, mDynamicInstanceListId, mLightInstanceListId, mCompoundInstanceListId, mPropInstanceListId, mGroundcoverCollectionId)
				mResourceIds.append([mZoneHeaderId, "ZoneHeader", id_to_int(mZoneHeaderId)])
		
		elif resource_type == "GraphicsSpec":
			library_vehicle_path = os.path.join(shared_dir, "VEHICLES", vehicle_name)
			if os.path.isdir(library_vehicle_path):
				shutil.copytree(library_vehicle_path, directory_path)
				if len(instances_wheel) > 0:
					try:
						clean_model_data(directory_path, True, True)
					except:
						print("WARNING: clean_model_data function not found. Cleaning original wheel data will not be possible.")
				#else:
				#	clean_model_data(directory_path, True, False)
			else:
				print("WARNING: vehicle folder %s does not exist on library." % vehicle_name)
			
			graphicsspec_path = os.path.join(graphicsspec_dir, mGraphicsSpecId + ".dat")
			if os.path.exists(graphicsspec_dir):
				for file in os.listdir(graphicsspec_dir):
					if mGraphicsSpecId in file:
						graphicsspec_path = os.path.join(graphicsspec_dir, file)
						break
			
			status, mPolygonSoupListId_previous = edit_graphicsspec(graphicsspec_path, instances, instances_wheelGroups, instance_collision)
			
			if len(instances_wheel) > 0:
				genesysobject_path = os.path.join(genesysobject_dir, mGraphicsSpecId + "_2.dat")
				if os.path.exists(genesysobject_dir):
					for file in os.listdir(genesysobject_dir):
						if mGraphicsSpecId in file and mGraphicsSpecId + '.dat' != file:
							genesysobject_path = os.path.join(genesysobject_dir, file)
							break
				
				if os.path.isfile(genesysobject_path) == True:
					edit_genesysobject2(genesysobject_dir, genesysobject_path, instances_wheelGroups)
				
				elif os.path.isfile(genesysobject_path) == False:
					if os.path.exists(shared_trafficattribs_dir):
						shutil.copytree(shared_trafficattribs_dir, trafficattribs_dir)
						traffic_genesysobject_dir = os.path.join(trafficattribs_dir, "GenesysObject")
						for file in os.listdir(traffic_genesysobject_dir):
							if mGraphicsSpecId in file and mGraphicsSpecId + '.dat' != file:
								genesysobject_path = os.path.join(traffic_genesysobject_dir, file)
								break
						edit_genesysobject2(traffic_genesysobject_dir, genesysobject_path, instances_wheelGroups)
						if pack_bundle_file == True:
							tr_resources_table_path = os.path.join(trafficattribs_dir, "IDs_TRAFFICATTRIBS.BNDL")
							tr_resources_table_path2 = os.path.join(trafficattribs_dir, "IDs.BNDL")
							if os.path.isfile(tr_resources_table_path):
								status = pack_bundle_mw(tr_resources_table_path, trafficattribs_dir, "TRAFFICATTRIBS.BNDL")
							elif os.path.isfile(tr_resources_table_path2):
								status = pack_bundle_mw(tr_resources_table_path2, trafficattribs_dir, "TRAFFICATTRIBS.BNDL")
					else:
						print("WARNING: it was not possible to edit the wheels coordinates. Consider adding the unpacked TRAFFICATTRIBS in the library folder")
			
			if len(instance_collision) > 0:
				# Deleting default file (deleting before writing the exported one, in case it is the same ID)
				polygonsouplist_default_path = os.path.join(polygonsouplist_dir, mPolygonSoupListId_previous + "_96.dat")
				if os.path.isfile(polygonsouplist_default_path):
					os.remove(polygonsouplist_default_path)
					# Removing from IdsTable later
				
				polygonsouplist_path = os.path.join(polygonsouplist_dir, instance_collision[0] + "_96.dat")
				write_polygonsouplist(polygonsouplist_path, instance_collision[1])
				mResourceIds.append([instance_collision[0], "PolygonSoupList", id_to_int(instance_collision[0])])
			
			if len(instances_character) > 0:
				genesysobject_path = os.path.join(genesysobject_dir, mGraphicsSpecId + ".dat")
				edit_genesysobject1(genesysobject_dir, genesysobject_path, instances_character)
			
			if len(instances_effects) > 0:
				edit_graphicsspec_effects(graphicsspec_path, instances_effects)
			
			
			#status = write_graphicsspec(graphicsspec_path, instances, muPartsCount, muShatteredGlassPartsCount)
			#if status == 1:
			#	return {'CANCELLED'}
			#mResourceIds.append([mGraphicsSpecId, "GraphicsSpec", id_to_int(mGraphicsSpecId)])
		
		elif resource_type == "CharacterSpec":
			if os.path.isdir(directory_path):
				print("WARNING: folder %s already exists. Adding data to it." % os.path.basename(directory_path))
			elif os.path.isdir(shared_characters_dir):
				print("WARNING: ALL_CHARS folder exists on library. Copying it.")
				shutil.copytree(shared_characters_dir, directory_path)
			else:
				print("WARNING: ALL_CHARS folder does not exist on library.")
			
			if len(instances) > 0:
				#characterspec_path = os.path.join(characterspec_dir, mCharacterSpecId + ".dat")
				#write_characterspec(characterspec_path, mSkeletonID, mAnimationListID, instances)
				#mResourceIds.append([mCharacterSpecId, "CharacterSpec", id_to_int(mCharacterSpecId)])
				##mResourceIds.append([mSkeletonID, "Skeleton", id_to_int(mSkeletonID)])
				##mResourceIds.append([mAnimationListID, "AnimationList", id_to_int(mAnimationListID)])
				
				characterspec_path = os.path.join(characterspec_dir, mCharacterSpecId + ".dat")
				already_is_file = False
				if os.path.isfile(characterspec_path):
					print("WARNING: file %s already exists in %s. Replacing it with new file." %(mCharacterSpecId, main_collection.name))
					already_is_file = True
				write_characterspec(characterspec_path, mSkeletonID, mAnimationListID, instances)
				if already_is_file == False:
					mResourceIds.append([mCharacterSpecId, "CharacterSpec", id_to_int(mCharacterSpecId)])
		
		for model in models:
			mModelId = model[0]
			is_shared_asset = model[2]
			if is_shared_asset == True:
				continue
			
			model_path = os.path.join(model_dir, mModelId + ".dat")
			already_is_file = False
			if os.path.isfile(model_path):
				print("WARNING: file %s already exists in %s. Replacing it with new file." %(mModelId, main_collection.name))
				already_is_file = True
			write_model(model_path, model, resource_type)
			if already_is_file == False:
				mResourceIds.append([mModelId, "Model", id_to_int(mModelId)])
		
		
		for renderable in renderables:
			mRenderableId = renderable[0]
			is_shared_asset = renderable[2]
			if is_shared_asset == True:
				continue
			
			renderable_path = os.path.join(renderable_dir, mRenderableId + ".dat")
			already_is_file = False
			if os.path.isfile(renderable_path):
				print("WARNING: file %s already exists in %s. Replacing it with new file." %(mRenderableId, main_collection.name))
				already_is_file = True
			write_renderable(renderable_path, renderable, resource_type, shared_dir)
			if already_is_file == False:
				mResourceIds.append([mRenderableId, "Renderable", id_to_int(mRenderableId)])
		
		
		for material in materials:
			mMaterialId = material[0]
			is_shared_asset = material[2]
			if is_shared_asset == True:
				shared_material_path = os.path.join(shared_material_dir, mMaterialId + ".dat")
				
				if os.path.isfile(shared_material_path) and (resource_type == "GraphicsSpec" or resource_type == "CharacterSpec"):
					# Vehicles and character does not have truely shared materials, but can use the same material
					print("WARNING: Moving shared material %s. Be sure its textures are shared or they exist in the output file." %mMaterialId)
					material_path = os.path.join(material_dir, mMaterialId + ".dat")
					if os.path.isfile(material_path):
						print("WARNING: Material %s already exists in vehicle %s. Skipping it." %(mMaterialId, main_collection.name))
						continue
					
					status = move_shared_resource(material_path, mMaterialId, shared_material_dir)
					if status == 0:
						mResourceIds.append([mMaterialId, "Material", id_to_int(mMaterialId)])
					else:
						print("WARNING: Material %s does not exist on library. Add it manually to the Material folder." %mMaterialId)
						mResourceIds.append([mMaterialId, "Material", id_to_int(mMaterialId)])
				continue
			
			material_path = os.path.join(material_dir, mMaterialId + ".dat")
			already_is_file = False
			if os.path.isfile(material_path):
				print("WARNING: file %s already exists in %s. Replacing it with new file." %(mMaterialId, main_collection.name))
				already_is_file = True
			write_material(material_path, material)
			if already_is_file == False:
				mResourceIds.append([mMaterialId, "Material", id_to_int(mMaterialId)])
		
		
		for raster in rasters:
			mRasterId = raster[0]
			is_shared_asset = raster[2]
			if is_shared_asset == True:
				continue
			
			raster_path = os.path.join(raster_dir, mRasterId + ".dat")
			already_is_file = False
			if os.path.isfile(raster_path):
				print("WARNING: file %s already exists in %s. Replacing it with new file." %(mRasterId, main_collection.name))
				already_is_file = True
			write_raster(raster_path, raster)
			if already_is_file == False:
				mResourceIds.append([mRasterId, "Texture", id_to_int(mRasterId)])
		
		
		for mSamplerStateId in samplerstates:
			samplerstate_path = os.path.join(samplerstate_dir, mSamplerStateId + ".dat")
			if os.path.isfile(samplerstate_path):
				print("WARNING: SamplerState %s already exists in %s. Skipping it." %(mSamplerStateId, main_collection.name))
				continue
			
			status = move_shared_resource(samplerstate_path, mSamplerStateId, shared_samplerstate_dir)
			if status == 0:
				mResourceIds.append([mSamplerStateId, "SamplerState", id_to_int(mSamplerStateId)])
			else:
				print("WARNING: SamplerState %s does not exist on library. Add it manually to the SamplerState folder." %mSamplerStateId)
				mResourceIds.append([mSamplerStateId, "SamplerState", id_to_int(mSamplerStateId)])
		
		mResourceIds_ = [mResourceId[0] for mResourceId in mResourceIds]
		if len(mResourceIds_) != len(set(mResourceIds_)):
			print("ERROR: duplicated resource IDs. Verify the list below for the duplicated IDs and do the proper fixes.")
			print(mResourceIds)
			return {'CANCELLED'}
		
		ids_table_path = os.path.join(directory_path, "IDs.BIN")
		if resource_type == "InstanceList":
			resources_table_path = os.path.join(directory_path, "IDs_" + track_unit_name + ".BIN")
			resources_table_path2 = os.path.join(directory_path, "IDs_" + track_unit_name + ".BNDL")
			if os.path.isfile(resources_table_path2):
				resources_table_path = resources_table_path2
			
		elif resource_type == "GraphicsSpec":
			resources_table_path = os.path.join(directory_path, "IDs_" + vehicle_name + ".BIN")
		elif resource_type == "CharacterSpec":
			resources_table_path = os.path.join(directory_path, "IDs_ALL_CHARS.BNDL")
		else:
			resources_table_path = os.path.join(directory_path, "IDs_chr" + ".BIN")
		
		if os.path.isfile(resources_table_path):
			write_header = False
		else:
			write_header = True
		
		write_resources_table(ids_table_path, mResourceIds, resource_type, write_header)
		if os.path.isfile(resources_table_path) and resource_type == "GraphicsSpec":
			if len(instance_collision) > 0:
				# Removing default collision file
				remove_resource_from_resources_table(resources_table_path, mPolygonSoupListId_previous)
			merge_resources_table(ids_table_path, resources_table_path)
			os.remove(ids_table_path)
		elif os.path.isfile(resources_table_path) and resource_type == "InstanceList":
			merge_resources_table(ids_table_path, resources_table_path)
			os.remove(ids_table_path)
		elif os.path.isfile(resources_table_path) and resource_type == "CharacterSpec":
			merge_resources_table(ids_table_path, resources_table_path)
			os.remove(ids_table_path)
		else:
			resources_table_path = ids_table_path
		
		
		if resource_type == "GraphicsSpec" and debug_redirect_vehicle == True:
			new_vehicle_number = new_vehicle_name.upper().replace("VEH", "").replace("HI", "").replace("LO", "").replace("TR", "").replace("GR", "").replace("MS", "").replace("_", "")
			try:
				test = int(new_vehicle_number)
			except:
				print("ERROR: redirect vehicle name is in the wrong format. Use something like VEH_122672_HI or VEH_122672_LO.")
			
			# Renaming GraphicsSpec related IDs
			mGraphicsSpecId_new = int_to_id(new_vehicle_number)
			for file in os.listdir(graphicsspec_dir):
				if mGraphicsSpecId in file:
					graphicsspec_path = os.path.join(graphicsspec_dir, file)
					graphicsspec_path_new = os.path.join(graphicsspec_dir, mGraphicsSpecId_new + file[11:])
					os.rename(graphicsspec_path, graphicsspec_path_new)
					change_mResourceId_on_file(resources_table_path, mGraphicsSpecId, mGraphicsSpecId_new, True)
					break
			
			genesysobject_dir = genesysobject_dir
			genesysobject_dir2 = os.path.join(trafficattribs_dir, "GenesysObject")
			genesysobject_dir_backup = os.path.join(shared_trafficattribs_dir, "GenesysObject")
			if os.path.isdir(genesysobject_dir):
				for file in os.listdir(genesysobject_dir):
					if mGraphicsSpecId in file:
						genesysobject_path = os.path.join(genesysobject_dir, file)
						genesysobject_path_new = os.path.join(genesysobject_dir, mGraphicsSpecId_new + file[11:])
						os.rename(genesysobject_path, genesysobject_path_new)
						
						change_mResourceId_on_file(genesysobject_path_new, mGraphicsSpecId, mGraphicsSpecId_new, True)
						change_mResourceId_on_file(resources_table_path, mGraphicsSpecId, mGraphicsSpecId_new, True)
			if os.path.isdir(genesysobject_dir2):
				for file in os.listdir(genesysobject_dir2):
					if mGraphicsSpecId in file:
						genesysobject_path = os.path.join(genesysobject_dir2, file)
						genesysobject_path_new = os.path.join(genesysobject_dir2, mGraphicsSpecId_new + file[11:])
						shutil.copy2(genesysobject_path, genesysobject_path_new)
						change_mResourceId_on_file(genesysobject_path_new, mGraphicsSpecId, mGraphicsSpecId_new, True)
						shutil.copy2(os.path.join(genesysobject_dir_backup, file), genesysobject_path)
			
			# Renaming PolygonSoupList related IDs
			mPolygonSoupList = "VEH_COL_" + str(new_vehicle_number)
			mPolygonSoupListId_new = calculate_resourceid(mPolygonSoupList.lower())
			polygonsouplist_path_new = os.path.join(polygonsouplist_dir, mPolygonSoupListId_new + "_96.dat")
			if len(instance_collision) > 0:
				mPolygonSoupListId_old = instance_collision[0]
			else:
				mPolygonSoupListId_old = mPolygonSoupListId_previous
			polygonsouplist_path = os.path.join(polygonsouplist_dir, mPolygonSoupListId_old + "_96.dat")
			os.rename(polygonsouplist_path, polygonsouplist_path_new)
			change_mResourceId_on_file(graphicsspec_path_new, mPolygonSoupListId_old, mPolygonSoupListId_new, True)
			change_mResourceId_on_file(resources_table_path, mPolygonSoupListId_old, mPolygonSoupListId_new, True)
			
			# Renaming VehicleSound related IDs
			vehiclesound_dir = os.path.join(directory_path, "VehicleSound")
			vehiclesound_dir2 = os.path.join(trafficattribs_dir, "VehicleSound")
			vehiclesound_dir_backup = os.path.join(export_path, "TRAFFICATTRIBS", "VehicleSound")
			generic_file = False
			if os.path.isdir(vehiclesound_dir):
				vehiclesound_dir = vehiclesound_dir
			elif os.path.isdir(vehiclesound_dir2):
				vehiclesound_dir = vehiclesound_dir2
				generic_file = True
			
			try:
				vehiclesound = str(vehicle_number) + "_vehiclesound"
				mVehicleSoundID = calculate_resourceid(vehiclesound.lower())
				vehiclesound_new = str(new_vehicle_number) + "_vehiclesound"
				mVehicleSoundID_new = calculate_resourceid(vehiclesound_new.lower())
				vehiclesound_path = os.path.join(vehiclesound_dir, mVehicleSoundID + ".dat")
				vehiclesound_path_new = os.path.join(vehiclesound_dir, mVehicleSoundID_new + ".dat")
				if generic_file == False:
					os.rename(vehiclesound_path, vehiclesound_path_new)
					change_mResourceId_on_file(resources_table_path, mVehicleSoundID, mVehicleSoundID_new, True)
				elif generic_file == True:
					shutil.copy2(vehiclesound_path, vehiclesound_path_new)
					shutil.copy2(os.path.join(vehiclesound_dir_backup, mVehicleSoundID + ".dat"), vehiclesound_path)
			except:
				pass
			
			try:
				competitorsound = str(vehicle_number) + "_competitorsound"
				mCompetitorSoundID = calculate_resourceid(competitorsound.lower())
				competitorsound_new = str(new_vehicle_number) + "_competitorsound"
				mCompetitorSoundID_new = calculate_resourceid(competitorsound_new.lower())
				competitorsound_path = os.path.join(vehiclesound_dir, mCompetitorSoundID + ".dat")
				competitorsound_path_new = os.path.join(vehiclesound_dir, mCompetitorSoundID_new + ".dat")
				if generic_file == False:
					os.rename(competitorsound_path, competitorsound_path_new)
					change_mResourceId_on_file(resources_table_path, mCompetitorSoundID, mCompetitorSoundID_new, True)
				elif generic_file == True:
					shutil.copy2(competitorsound_path, competitorsound_path_new)
					shutil.copy2(os.path.join(vehiclesound_dir_backup, mCompetitorSoundID + ".dat"), competitorsound_path)
			except:
				pass
			
			if pack_bundle_file == True and os.path.isdir(trafficattribs_dir):
				tr_resources_table_path = os.path.join(trafficattribs_dir, "IDs_TRAFFICATTRIBS.BNDL")
				tr_resources_table_path2 = os.path.join(trafficattribs_dir, "IDs.BNDL")
				if os.path.isfile(tr_resources_table_path):
					status = pack_bundle_mw(tr_resources_table_path, trafficattribs_dir, "TRAFFICATTRIBS.BNDL")
				elif os.path.isfile(tr_resources_table_path2):
					status = pack_bundle_mw(tr_resources_table_path2, trafficattribs_dir, "TRAFFICATTRIBS.BNDL")
		
		if pack_bundle_file == True:
			if os.path.isfile(resources_table_path):
				if resource_type == "CharacterSpec" and os.path.isdir(shared_characters_dir):
					status = pack_bundle_mw(resources_table_path, directory_path, "ALL_CHARS.BNDL")
				else:
					#status = pack_bundle_mw(resources_table_path, directory_path, main_collection.name + ".BNDL")
					if resource_type == "GraphicsSpec" and debug_redirect_vehicle == True:
						status = pack_bundle_mw(resources_table_path, directory_path, new_vehicle_name + ".BNDL")
					else:
						status = pack_bundle_mw(resources_table_path, directory_path, main_collection.name + ".BNDL")
		
		elapsed_time = time.time() - writing_time
		print("\t... %.4fs" % elapsed_time)
	
	print("Finished")
	elapsed_time = time.time() - start_time
	print("Elapsed time: %.4fs" % elapsed_time)
	return {'FINISHED'}


def read_object(object, resource_type, shared_dir, copy_uv_layer):
	# Definitions
	shared_material_dir = os.path.join(shared_dir, "Material")
	#shared_vertex_descriptor_dir = os.path.join(shared_dir, "VertexDescriptor")
	#shared_vertex_descriptor_ported_x360_dir = os.path.join(shared_dir, "VertexDescriptor_port_X360")
	#shared_vertex_descriptor_ported_ps3_dir = os.path.join(shared_dir, "VertexDescriptor_port_PS3")
	
	# Mesh data definitions
	num_meshes = len(object.material_slots)
	not_used_material_slots = [x for x in range(num_meshes)]
	indices_buffer = [[] for _ in range(num_meshes)]
	vertices_buffer = [[] for _ in range(num_meshes)]
	meshes_info = [[] for _ in range(num_meshes)]
	object_center = []
	object_radius = 1.0
	
	# Inits
	mesh = object.data
	mesh.calc_normals_split()
	loops = mesh.loops
	bm = bmesh.new()
	bm.from_mesh(mesh)
	
	has_uv = len(mesh.uv_layers) > 0
	if has_uv:
		uv_layers = bm.loops.layers.uv
	else:
		uv_layers = []
	
	if num_meshes == 0:
		print("ERROR: no materials applied on mesh %s." % mesh.name)
		return (meshes_info, indices_buffer, vertices_buffer, object_center, object_radius, 1)
	
	blend_index1 = bm.verts.layers.int.get("blend_index1")
	blend_index2 = bm.verts.layers.int.get("blend_index2")
	blend_index3 = bm.verts.layers.int.get("blend_index3")
	blend_index4 = bm.verts.layers.int.get("blend_index4")
	
	blend_weight1 = bm.verts.layers.float.get("blend_weight1")
	blend_weight2 = bm.verts.layers.float.get("blend_weight2")
	blend_weight3 = bm.verts.layers.float.get("blend_weight3")
	blend_weight4 = bm.verts.layers.float.get("blend_weight4")
	
	mesh_indices = [[] for _ in range(num_meshes)]
	mesh_vertices_buffer = [{} for _ in range(num_meshes)]
	vert_indices = [{} for _ in range(num_meshes)]
	
	ind = [0] * num_meshes
	
	mMaterialIds = [""] * num_meshes
	
	vertices_x = []
	vertices_y = []
	vertices_z = []
	positions = [{} for _ in range(num_meshes)]
	normals = [{} for _ in range(num_meshes)]
	blends_indices = [{} for _ in range(num_meshes)]
	blends_weights = [{} for _ in range(num_meshes)]
	uv = [{} for _ in range(num_meshes)]
	
	for face in bm.faces:
		if face.hide == False:
			mesh_index = face.material_index
			indices = []
			
			if mMaterialIds[mesh_index] == "":
				if mesh.materials[mesh_index] == None:
					print("ERROR: face without material found on mesh %s." % mesh.name)
					return (meshes_info, indices_buffer, vertices_buffer, object_center, object_radius, 1)
				mMaterialId = mesh.materials[mesh_index].name
				mMaterialIds[mesh_index] = mMaterialId.split(".")[0]
				not_used_material_slots.remove(mesh_index)
			
			if len(face.verts) > 3:
				print("ERROR: non triangular face on mesh %s." % mesh.name)
				return (meshes_info, indices_buffer, vertices_buffer, object_center, object_radius, 1)
			
			for vert in face.verts:
				if vert.index not in vert_indices[mesh_index]:
					vert_indices[mesh_index][vert.index] = ind[mesh_index]
					ind[mesh_index] += 1
				vert_index = vert_indices[mesh_index][vert.index]
				indices.append(vert_index)
				if vert_index in positions[mesh_index]:
					continue
				vertices_x.append(vert.co[0])
				vertices_y.append(vert.co[1])
				vertices_z.append(vert.co[2])
				positions[mesh_index][vert_index] = vert.co
				#normals[mesh_index][vert_index] = vert.normal
				#print(vert.normal)
				if None in [blend_index1, blend_index2, blend_index3, blend_index4]:
					blends_indices[mesh_index][vert_index] = [0, 0, 0, 0]
				else:
					blends_indices[mesh_index][vert_index] = [vert[blend_index1], vert[blend_index2], vert[blend_index3], vert[blend_index4]]
				if None in [blend_weight1, blend_weight2, blend_weight3, blend_weight4]:
					blends_weights[mesh_index][vert_index] = [0xFF, 0, 0, 0]
				else:
					blends_weights[mesh_index][vert_index] = [int(round(vert[blend_weight1]*255.0/100.0)), int(round(vert[blend_weight2]*255.0/100.0)),
															  int(round(vert[blend_weight3]*255.0/100.0)), int(round(vert[blend_weight4]*255.0/100.0))]
			
			indices_buffer[mesh_index].append(indices)
			
			if has_uv:
				for loop in face.loops:
					uvs = []
					for layer in range(0, len(uv_layers)):
						uv_layer = bm.loops.layers.uv[layer]
						uvs.append(loop[uv_layer].uv)
					uv[mesh_index][vert_indices[mesh_index][loop.vert.index]] = uvs
			
			for index in indices:
				if index in mesh_indices[mesh_index]:
					continue
				mesh_indices[mesh_index].append(index)
				
				position = positions[mesh_index][index]
				#normal = normals[mesh_index][index]
				normal = [0.0, 0.0, 0.0]
				tangent = [0.0, 0.0, 0.0]
				binormal = [0.0, 0.0, 0.0]
				#color = [0, 0, 0, 0xFF]
				color = [0xFF, 0xFF, 0xFF, 0xFF]
				color2 = [0, 0, 0, 0]
				if len(uv_layers) >= 6:
					uv1 = uv[mesh_index][index][0]
					uv2 = uv[mesh_index][index][1]
					uv3 = uv[mesh_index][index][2]
					uv4 = uv[mesh_index][index][3]
					uv5 = uv[mesh_index][index][4]
					uv6 = uv[mesh_index][index][5]
				elif len(uv_layers) == 5:
					uv1 = uv[mesh_index][index][0]
					uv2 = uv[mesh_index][index][1]
					uv3 = uv[mesh_index][index][2]
					uv4 = uv[mesh_index][index][3]
					uv5 = uv[mesh_index][index][3]
					if copy_uv_layer == True:
						uv6 = uv1[:]
					else:
						uv6 = [0.0, 0.0]
				elif len(uv_layers) == 4:
					uv1 = uv[mesh_index][index][0]
					uv2 = uv[mesh_index][index][1]
					uv3 = uv[mesh_index][index][2]
					uv4 = uv[mesh_index][index][3]
					if copy_uv_layer == True:
						uv5 = uv1[:]
						uv6 = uv1[:]
					else:
						uv5 = [0.0, 0.0]
						uv6 = [0.0, 0.0]
				elif len(uv_layers) == 3:
					uv1 = uv[mesh_index][index][0]
					uv2 = uv[mesh_index][index][1]
					uv3 = uv[mesh_index][index][2]
					if copy_uv_layer == True:
						uv4 = uv1[:]
						uv5 = uv1[:]
						uv6 = uv1[:]
					else:
						uv4 = [0.0, 0.0]
						uv5 = [0.0, 0.0]
						uv6 = [0.0, 0.0]
				elif len(uv_layers) == 2:
					uv1 = uv[mesh_index][index][0]
					uv2 = uv[mesh_index][index][1]
					if copy_uv_layer == True:
						uv3 = uv1[:]
						uv4 = uv1[:]
						uv5 = uv1[:]
						uv6 = uv1[:]
					else:
						uv3 = [0.0, 0.0]
						uv4 = [0.0, 0.0]
						uv5 = [0.0, 0.0]
						uv6 = [0.0, 0.0]
				elif len(uv_layers) == 1:
					uv1 = uv[mesh_index][index][0]
					if copy_uv_layer == True:
						uv2 = uv1[:]
						uv3 = uv1[:]
						uv4 = uv1[:]
						uv5 = uv1[:]
						uv6 = uv1[:]
					else:
						uv2 = [0.0, 0.0]
						uv3 = [0.0, 0.0]
						uv4 = [0.0, 0.0]
						uv5 = [0.0, 0.0]
						uv6 = [0.0, 0.0]
				else:
					uv1 = [0.0, 0.0]
					uv2 = [0.0, 0.0]
					uv3 = [0.0, 0.0]
					uv4 = [0.0, 0.0]
					uv5 = [0.0, 0.0]
					uv6 = [0.0, 0.0]
				blend_indices = blends_indices[mesh_index][index]
				blend_weight = blends_weights[mesh_index][index]
				mesh_vertices_buffer[mesh_index][index] = [index, position[:], normal[:], tangent[:], color[:], uv1[:], uv2[:], uv3[:], uv4[:], uv5[:], uv6[:], blend_indices[:], blend_weight[:], binormal[:], color2[:]]
	
	max_vertex = (max(vertices_x), max(vertices_y), max(vertices_z))
	min_vertex = (min(vertices_x), min(vertices_y), min(vertices_z))
	
	vertices_x.clear()
	vertices_y.clear()
	vertices_z.clear()
	
	object_center = [(max_vertex[0] + min_vertex[0])*0.5, (max_vertex[1] + min_vertex[1])*0.5, (max_vertex[2] + min_vertex[2])*0.5]
	object_radius = math.dist(object_center, max_vertex)
	
	ao_layer = True
	vcolor2_layer = True
	try:
		mesh_vertex_colors = mesh.color_attributes
		using_color_attributes = True
	except:
		mesh_vertex_colors = mesh.vertex_colors
		using_color_attributes = False
	
	if len(mesh_vertex_colors) > 0:
		if "Ambient Occlusion" in mesh_vertex_colors:
			ao_layer_index = mesh_vertex_colors.keys().index("Ambient Occlusion")
		elif "Ambient occlusion" in mesh_vertex_colors:
			ao_layer_index = mesh_vertex_colors.keys().index("Ambient occlusion")
		elif "AO" in mesh_vertex_colors:
			ao_layer_index = mesh_vertex_colors.keys().index("AO")
		elif "ao" in mesh_vertex_colors:
			ao_layer_index = mesh_vertex_colors.keys().index("ao")
		elif "VColor1" in mesh_vertex_colors:
			ao_layer_index = mesh_vertex_colors.keys().index("VColor1")
		elif "vcolor1" in mesh_vertex_colors:
			ao_layer_index = mesh_vertex_colors.keys().index("vcolor1")
		else:
			print("WARNING: no Ambient Occlusion or AO layer on mesh %s. Default AO colors will be used." % mesh.name)
			ao_layer = False
		
		if "VColor2" in mesh_vertex_colors:
			vcolor2_layer_index = mesh_vertex_colors.keys().index("VColor2")
		elif "vcolor2" in mesh_vertex_colors:
			vcolor2_layer_index = mesh_vertex_colors.keys().index("vcolor2")
		else:
			print("WARNING: no additional vertex color (VColor2) on mesh %s. Default VColor2 will be used if needed." % mesh.name)
			vcolor2_layer = False
		
	else:
		print("WARNING: no vertex colors layer on mesh %s. Default AO colors will be used." % mesh.name)
		ao_layer = False
		vcolor2_layer = False
	
	normals = [{} for _ in range(num_meshes)]
	colors = [{} for _ in range(num_meshes)]
	colors2 = [{} for _ in range(num_meshes)]
	for face in mesh.polygons:
		if face.hide == False:
			mesh_index = face.material_index
			
			mat = bpy.data.materials.get(mMaterialIds[mesh_index])
			try:
				shader_type = mat["shader_type"]
			except:
				shader_type = ""
			
			for loop_ind in face.loop_indices:
				vert_index = vert_indices[mesh_index][loops[loop_ind].vertex_index]
				if vert_index in normals[mesh_index]:
					continue
				normals[mesh_index][vert_index] = loops[loop_ind].normal[:]
				if ao_layer:
					color = list(mesh_vertex_colors[ao_layer_index].data[loop_ind].color[:])
					for i in range(0, 4):
						if i < 3 and using_color_attributes == True:
							color[i] = lin2s1(color[i])
						color[i] = round(color[i]*255.0)
					colors[mesh_index][vert_index] = color[:]
				elif shader_type.lower() == "glass":
					colors[mesh_index][vert_index] = [0, 0, 0, 179] #0.709
				elif shader_type.lower() == "glass_black":
					colors[mesh_index][vert_index] = [0, 0, 0, 255] #1.0
				elif shader_type.lower() == "mirror" or shader_type == "VehicleNFS13_Mirror":
					colors[mesh_index][vert_index] = [255, 255, 255, 255]
				else:
					colors[mesh_index][vert_index] = [255, 255, 255, 255]
				if vcolor2_layer:
					color = list(mesh_vertex_colors[vcolor2_layer_index].data[loop_ind].color[:])
					for i in range(0, 4):
						if i < 3 and using_color_attributes == True:
							color[i] = lin2s1(color[i])
						color[i] = round(color[i]*255.0)
					colors2[mesh_index][vert_index] = color[:]
				else:
					colors2[mesh_index][vert_index] = [0, 0, 0, 0]
					#colors2[mesh_index][vert_index] = [119, 254, 144, 129]
				mesh_vertices_buffer[mesh_index][vert_index][2] = normals[mesh_index][vert_index][:]
				mesh_vertices_buffer[mesh_index][vert_index][4] = colors[mesh_index][vert_index][:]
				mesh_vertices_buffer[mesh_index][vert_index][14] = colors2[mesh_index][vert_index][:]
	
	bm.clear()
	bm.free()
	
	for mesh_index in range(0, num_meshes):
		if len(indices_buffer[mesh_index]) == 0:
			continue
		calculate_tangents(indices_buffer[mesh_index], mesh_vertices_buffer[mesh_index])
		
		vertices_buffer[mesh_index] = [mesh_vertices_buffer[mesh_index], mesh_indices[mesh_index]]
		
		mMaterialId = mMaterialIds[mesh_index]
		mat = bpy.data.materials.get(mMaterialId)
		try:
			is_shared_asset = mat["is_shared_asset"]
		except:
			is_shared_asset = False
		
		if is_shared_asset == True:
			material_path = os.path.join(shared_material_dir, mMaterialId + ".dat")
		
		meshes_info[mesh_index] = [mesh_index, mMaterialId]
		
		triangle_strips = convert_triangle_to_strip(indices_buffer[mesh_index])
		cte_min = min(triangle_strips)
		cte_max = max(index for index in triangle_strips if index != 0xFFFF)
		for j in range(0, len(triangle_strips)):
			if triangle_strips[j] == 0xFFFF:
				continue
			triangle_strips[j] = triangle_strips[j] - cte_min
		
		#j=0
		#cte=0
		#v=0
		#while (j < len(triangle_strips)):
		#	if triangle_strips[j] == 0xFFFF:
		#		triangle_strips[j] = triangle_strips[j-1]
		#		index_insert = triangle_strips[j+1]
		#		triangle_strips.insert(j+1, index_insert)
		#		if (v+cte)%2 != 0:
		#			triangle_strips.insert(j+1, index_insert)
		#			j += 2
		#		else:
		#			cte += -1
		#			j += 1
		#	j = j + 1
		#	v = v + 1
		indices_buffer[mesh_index] = triangle_strips[:]
		
		if len(vertices_buffer[mesh_index]) >= 0xFFFF:
			print("ERROR: number of vertices higher than the supported by the game on mesh %s. Each material cannot have more than 65535 vertices." % mesh.name)
			return (meshes_info, indices_buffer, vertices_buffer, object_center, object_radius, 1)
		
	
	# Verifying if some material is not used
	if len(not_used_material_slots) != 0:
		for material_index in reversed(not_used_material_slots):
			mesh_index = material_index
			del meshes_info[mesh_index]
			del indices_buffer[mesh_index]
			del vertices_buffer[mesh_index]
		
		num_meshes = num_meshes - len(not_used_material_slots)
		
		for mesh_index in range(0, num_meshes):
			meshes_info[mesh_index][0] = mesh_index
	
	return (meshes_info, indices_buffer, vertices_buffer, object_center, object_radius, 0)


def read_polygonsoup_object(object, translation, scale):
	PolygonSoupVertices = []
	PolygonSoupPolygons = []
	PolygonSoupPolygons_triangles = []
	
	# Inits
	mesh = object.data
	loops = mesh.loops
	bm = bmesh.new()
	bm.from_mesh(mesh)
	
	edge_cosine1 = bm.faces.layers.int.get("edge_cosine1")
	edge_cosine2 = bm.faces.layers.int.get("edge_cosine2")
	edge_cosine3 = bm.faces.layers.int.get("edge_cosine3")
	edge_cosine4 = bm.faces.layers.int.get("edge_cosine4")
	collision_tag0 = bm.faces.layers.int.get("collision_tag0")
	
	for vert in bm.verts:
		if vert.hide == False:
			#PolygonSoupVertices.append(vert.co[:])
			#PolygonSoupVertices.append([round(vert_co) for vert_co in vert.co])
			PolygonSoupVertices.append([vert_co*scale + translation[i] for i, vert_co in enumerate(vert.co)])
	
	if len(PolygonSoupVertices) >= 0xFF:
		print("ERROR: number of vertices higher than the supported by the game on collision mesh %s. It should have less than 255 vertices." % mesh.name)
		return (1, [], [], 0)
	
	for face in bm.faces:
		if face.hide == False:
			if len(face.verts) > 4 or len(face.verts) < 3:
				print("ERROR: non triangular or quad face on mesh %s." % mesh.name)
				return (1, [], [], 0)
			
			material_index = face.material_index
			#if mesh.materials[material_index] == None:
				#print("ERROR: face without material found on mesh %s." % mesh.name)
				#return (1, [], [], 0)
				#print("WARNING: face without material found on mesh %s." % mesh.name)
			
			has_material = True
			try:
				if mesh.materials[material_index] == None:
					print("WARNING: face without material found on mesh %s." % mesh.name)
					has_material = False
			except:
				print("WARNING: face without material found on mesh %s." % mesh.name)
				has_material = False
			
			if collision_tag0 == None:
				mu16CollisionTag_part0 = 0
			else:
				mu16CollisionTag_part0 = face[collision_tag0]
				# all_faces_driveable = True
				# if all_faces_driveable == True:
					# if mu16CollisionTag_part0 == 0x2040 or mu16CollisionTag_part0 == 0x2000:
						# mu16CollisionTag_part0 = 0x8001
			#mu16CollisionTag_part1 = mesh.materials[material_index].name.split(".")[0]
			try:
				mu16CollisionTag_part1 = mesh.materials[material_index].name.split(".")[0]
				mu16CollisionTag_part1 = int(mu16CollisionTag_part1, 16)
			except:
				#print("ERROR: face material name %s (collision tag) is not in the proper formating." % mesh.materials[material_index].name)
				#return (1, [], [], 0)
				if has_material:
					print("WARNING: face material name %s (collision tag) is not in the proper formating. Setting it to 0xA010." % mesh.materials[material_index].name)
				else:
					print("WARNING: setting collision tag as 0x0000 to the face without material.")
				mu16CollisionTag_part1 = 0x0000
			
			mau8VertexIndices = []
			for vert in face.verts:
				vert_index = PolygonSoupVertices.index([vert_co*scale for vert_co in vert.co])
				mau8VertexIndices.append(vert_index)
			
			if None in [edge_cosine1, edge_cosine2, edge_cosine3, edge_cosine4]:
				mau8EdgeCosines = [0xFF, 0xFF, 0xFF, 0xFF]
			else:
				mau8EdgeCosines = [face[edge_cosine1], face[edge_cosine2], face[edge_cosine3], face[edge_cosine4]]
			
			if len(face.verts) == 4:
				mau8VertexIndices = [mau8VertexIndices[0], mau8VertexIndices[1], mau8VertexIndices[3], mau8VertexIndices[2]]
				PolygonSoupPolygons.append([[mu16CollisionTag_part0, mu16CollisionTag_part1], mau8VertexIndices, mau8EdgeCosines])
			elif len(face.verts) == 3:
				PolygonSoupPolygons_triangles.append([[mu16CollisionTag_part0, mu16CollisionTag_part1], mau8VertexIndices, mau8EdgeCosines])
	
	mu8NumQuads = len(PolygonSoupPolygons)
	PolygonSoupPolygons.extend(PolygonSoupPolygons_triangles)
	
	if len(PolygonSoupPolygons) >= 0xFF:
		print("ERROR: number of faces higher than the supported by the game on collision mesh %s." % mesh.name)
		return (1, [], [], 0)
	
	return (0, PolygonSoupVertices, PolygonSoupPolygons, mu8NumQuads)


def read_vertex_descriptor(vertex_descriptor_path): 	#ok
	vertex_properties = []
	with open(vertex_descriptor_path, "rb") as f:
		unk1 = struct.unpack("<i", f.read(0x4))[0]
		attibutes_flags = struct.unpack("<i", f.read(0x4))[0]
		_ = struct.unpack("<i", f.read(0x4))[0] #null
		num_vertex_attibutes = struct.unpack("<i", f.read(0x4))[0]
		
		semantic_properties = []
		for i in range(0, num_vertex_attibutes):
			semantic_type = struct.unpack("<B", f.read(0x1))[0]
			semantic_index = struct.unpack("<B", f.read(0x1))[0]
			input_slot = struct.unpack("<B", f.read(0x1))[0]
			element_class = struct.unpack("<B", f.read(0x1))[0]
			data_type = struct.unpack("<i", f.read(0x4))[0]
			data_offset = struct.unpack("<i", f.read(0x4))[0]
			step_rate = struct.unpack("<i", f.read(0x4))[0] #null
			vertex_size = struct.unpack("<i", f.read(0x4))[0]
			
			semantic_type = get_vertex_semantic(semantic_type)
			data_type = get_vertex_data_type(data_type)
			
			semantic_properties.append([semantic_type, data_type, data_offset])
		
		vertex_properties = [vertex_size, [semantic_properties]]
		
	return vertex_properties


def read_material_get_shader_type(material_path):	#ok
	mShaderId = ""
	mSamplerStateIds = []
	with open(material_path, "rb") as f:
		f.seek(0x6, 0)
		resources_pointer = struct.unpack("<H", f.read(0x2))[0]
		f.seek(0x20, 0)
		miNumSamplers = struct.unpack("<i", f.read(0x4))[0]
		f.seek(resources_pointer, 0)
		mShaderId = bytes_to_id(f.read(0x4))
		f.seek(0xC, 1)
		f.seek(0x10*miNumSamplers, 1)
		
		for i in range(0, miNumSamplers):
			mSamplerStateId = bytes_to_id(f.read(0x4))
			_ = struct.unpack("<i", f.read(0x4))[0]
			muOffset = struct.unpack("<I", f.read(0x4))[0]
			padding = struct.unpack("<i", f.read(0x4))[0]
			
			mSamplerStateIds.append(mSamplerStateId)
		
	return (mShaderId, mSamplerStateIds)


def read_shader(shader_path):	#ok
	ShaderType = ""
	raster_types = []
	texture_samplers = []
	with open(shader_path, "rb") as f:
		file_size = os.path.getsize(shader_path)
		
		# Shader description
		f.seek(0x8, 0)
		shader_description_offset = struct.unpack("<i", f.read(0x4))[0]
		f.seek(0x10, 0)
		end_sampler_types_offset = struct.unpack("<H", f.read(0x2))[0]
		resources_pointer = struct.unpack("<H", f.read(0x2))[0]
		f.seek(shader_description_offset, 0)
		shader_description = f.read(resources_pointer-shader_description_offset).split(b'\x00')[0]
		shader_description = str(shader_description, 'ascii')
		
		# Shader parameters
		f.seek(0x14, 0)
		shader_parameters_indices_pointer = struct.unpack("<i", f.read(0x4))[0]
		shader_parameters_ones_pointer = struct.unpack("<i", f.read(0x4))[0]
		shader_parameters_nameshash_pointer = struct.unpack("<i", f.read(0x4))[0]
		shader_parameters_data_pointer = struct.unpack("<i", f.read(0x4))[0]
		num_shader_parameters = struct.unpack("<B", f.read(0x1))[0]
		num_shader_parameters_withdata = struct.unpack("<B", f.read(0x1))[0]
		f.seek(0x2, 1)
		shader_parameters_names_pointer = struct.unpack("<i", f.read(0x4))[0]
		shader_parameters_end_pointer = struct.unpack("<i", f.read(0x4))[0]
		
		f.seek(shader_parameters_indices_pointer, 0)
		shader_parameters_Indices = list(struct.unpack("<%db" % num_shader_parameters, f.read(0x1*num_shader_parameters)))
		
		f.seek(shader_parameters_ones_pointer, 0)
		shader_parameters_Ones = list(struct.unpack("<%db" % num_shader_parameters, f.read(0x1*num_shader_parameters)))
		
		f.seek(shader_parameters_nameshash_pointer, 0)
		shader_parameters_NamesHash = list(struct.unpack("<%dI" % num_shader_parameters, f.read(0x4*num_shader_parameters)))
		
		f.seek(shader_parameters_data_pointer, 0)
		shader_parameters_Data = []
		for i in range(0, num_shader_parameters):
			if shader_parameters_Indices[i] == -1:
				shader_parameters_Data.append(None)
			else:
				shader_parameters_Data.append(struct.unpack("<4f", f.read(0x10)))
		
		#shader_parameters_Names = []
		shader_parameters_Names = [""]*num_shader_parameters
		for i in range(0, num_shader_parameters):
			f.seek(shader_parameters_names_pointer + i*0x4, 0)
			pointer = struct.unpack("<i", f.read(0x4))[0]
			f.seek(pointer, 0)
			parameter_name = f.read(shader_parameters_end_pointer-pointer).split(b'\x00')[0]
			parameter_name = str(parameter_name, 'ascii')
			#shader_parameters_Names.append(parameter_name)
			shader_parameters_Names[shader_parameters_Indices[i]] = parameter_name
		
		shader_parameters = [shader_parameters_Indices, shader_parameters_Ones, shader_parameters_NamesHash, shader_parameters_Data, shader_parameters_Names]
		
		# Samplers and material constants
		f.seek(0x5C, 0)
		miNumSamplers = struct.unpack("<B", f.read(0x1))[0]
		f.seek(0x3, 1)
		mpaMaterialConstants = struct.unpack("<i", f.read(0x4))[0]
		mpaSamplersChannel = struct.unpack("<i", f.read(0x4))[0]
		mpaSamplers = struct.unpack("<i", f.read(0x4))[0]
		f.seek(0x80, 0)
		end_raster_types_offset = struct.unpack("<i", f.read(0x4))[0]
		if end_raster_types_offset == 0:
			end_raster_types_offset = end_sampler_types_offset
		
		f.seek(mpaMaterialConstants, 0)
		material_constants = struct.unpack("<%dH" % miNumSamplers, f.read(0x2*miNumSamplers))
		
		f.seek(mpaSamplersChannel, 0)
		miChannel = struct.unpack("<%dB" % miNumSamplers, f.read(0x1*miNumSamplers))
		
		f.seek(mpaSamplers, 0)
		raster_type_offsets = list(struct.unpack("<%di" % miNumSamplers, f.read(0x4*miNumSamplers)))
		raster_type_offsets.append(end_raster_types_offset)
		
		for i in range(0, miNumSamplers):
			f.seek(raster_type_offsets[i], 0)
			if raster_type_offsets[i] > raster_type_offsets[i+1]:
				raster_type = f.read(end_raster_types_offset-raster_type_offsets[i]).split(b'\x00')[0]
			else:
				raster_type = f.read(raster_type_offsets[i+1]-raster_type_offsets[i]).split(b'\x00')[0]
			raster_type = str(raster_type, 'ascii')
			raster_types.append([miChannel[i], raster_type])
			texture_samplers.append(raster_type)
		
		raster_types.sort(key=lambda x:x[0])
		
		raster_types_dict = {}
		for raster_type_data in raster_types:
			raster_types_dict[raster_type_data[0]] = raster_type_data[1]
		
		# VertexDescriptor
		f.seek(resources_pointer, 0)
		mVertexDescriptorId = bytes_to_id(f.read(0x4))
	
	return (shader_description, mVertexDescriptorId, miNumSamplers, raster_types_dict, shader_parameters, material_constants, texture_samplers)


def write_instancelist(instancelist_path, instances):
	os.makedirs(os.path.dirname(instancelist_path), exist_ok = True)
	
	with open(instancelist_path, "wb") as f:
		mpaInstances = 0x10
		muArraySize = len(instances)
		if muArraySize == 0:
			mpaInstances = 0
		muNumInstances = 0
		muVersionNumber = 0x3
		
		instances_properties = []
		instances_properties_backdrop = []
		
		for instance in instances:
			if instance[1][2] == True:
				muNumInstances += 1
				instances_properties.append(instance)
			else:
				instances_properties_backdrop.append(instance)
		instances_properties.sort(key=lambda x:x[0])
		instances_properties_backdrop.sort(key=lambda x:x[0])
		
		instances_properties.extend(instances_properties_backdrop)
		instances = instances_properties[:]
		
		f.write(struct.pack('<I', mpaInstances))
		f.write(struct.pack('<I', muArraySize))
		f.write(struct.pack('<I', muNumInstances))
		f.write(struct.pack('<I', muVersionNumber))
		
		# if muArraySize == 0:
			# f.write(struct.pack('<I', 3))
			# f.write(struct.pack('<I', 0))
			# f.write(struct.pack('<I', 0))
			# f.write(struct.pack('<I', 0))
			# return 0
		
		tint_data_size = 0
		muOffsets = []
		mResourceIds = []
		mBUnknowns = []
		for i in range(0, muArraySize):
			instance = instances[i]
			object_index, [mModelId, [mTransform], is_instance_always_loaded, unknown_0x4, unknown_0x8, TintData] = instance
			
			mpModel = 0
			unknown_0x4 = instance[1][3]
			unknown_0x8 = instance[1][4]
			unknown_0xC = 0
			if TintData != []:
				mpTintData = mpaInstances + muArraySize*0x60 + tint_data_size
			else:
				mpTintData = 0
			unknown_0x14 = 0
			unknown_0x18 = 0
			unknown_0x1C = 0
			
			f.seek(mpaInstances + 0x60*i, 0)
			f.write(struct.pack('<i', mpModel))
			f.write(struct.pack('<f', unknown_0x4))
			f.write(struct.pack('<i', unknown_0x8))
			f.write(struct.pack('<i', unknown_0xC))
			f.write(struct.pack('<I', mpTintData))
			f.write(struct.pack('<i', unknown_0x14))
			f.write(struct.pack('<i', unknown_0x18))
			f.write(struct.pack('<i', unknown_0x1C))
			
			f.write(struct.pack('<4f', *mTransform[0][:-1], 1.0))
			f.write(struct.pack('<4f', *mTransform[1][:-1], 1.0))
			f.write(struct.pack('<4f', *mTransform[2][:-1], 1.0))
			f.write(struct.pack('<4f', *mTransform[3]))
			
			# f.seek(mpaInstances + 0x60*muArraySize + 0x10*i, 0)
			# f.write(id_to_bytes(mModelId))
			# f.write(struct.pack("<i", 0))
			# f.write(struct.pack("<i", mpaInstances + 0x60*i))
			# f.write(struct.pack("<i", 0))
			
			if mpTintData != 0:
				parameters_names, parameters_data, samplers_names, sampler_states, textures = TintData
				f.seek(mpTintData, 0)
				unknown_0x0 = 1
				num_parameters = len(parameters_names)
				num_samplers = len(samplers_names)
				unknown_0x3 = 0
				offset_0 = 0
				offset_0_1 = []
				offset_1 = 0
				offset_2 = 0
				offset_3 = 0
				offset_3_1 = []
				offset_4 = 0
				mpaSamplersStates = 0
				mpaTextures = 0
				offset_end = mpTintData + 0x20
				
				# if num_parameters != 0:
					# offset_1 = mpTintData + 0x20
					# offset_2 = offset_1 + num_parameters + calculate_padding(offset_1 + num_parameters, 0x10)
					# offset_0 = offset_2 + num_parameters*0x10
					
					# offset = offset_0 + num_parameters*0x4
					# offset_0_1 = []
					# for parameters_name in parameters_names:
						# offset_0_1.append(offset)
						# offset += len(parameters_name) + 1
						# offset += calculate_padding(offset, 0x4)
					
					# offset_end = offset
				
				if num_samplers != 0:
					offset_4 = offset_end
					mpaSamplersStates = offset_4 + num_samplers*0x1 + calculate_padding(offset_4 + num_samplers*0x1, 0x4)
					mpaTextures = mpaSamplersStates + num_samplers*0x4
					offset_3 = mpaTextures + num_samplers*0x4
					
					offset = offset_3 + num_samplers*0x4
					offset_3_1 = []
					for sampler_name in samplers_names:
						offset_3_1.append(offset)
						offset += len(sampler_name) + 1
					
					offset_end = offset
					
					muOffsets_samplers = []
					muOffsets_textures = []
					mResourceIds_samplers = []
					mResourceIds_textures = []
					mBUnknowns_samplers = []
					mBUnknowns_textures = []
					
					for j in range(0, num_samplers):
						mSamplerStateId = sampler_states[j]
						mTextureId = textures[j]
						
						muOffsets_samplers.append(mpaSamplersStates + 0x4*j)
						muOffsets_textures.append(mpaTextures + 0x4*j)
						mResourceIds_samplers.append(mSamplerStateId)
						mResourceIds_textures.append(mTextureId)
						mBUnknowns_samplers.append(0)
						mBUnknowns_textures.append(1)
					
					muOffsets.extend(muOffsets_samplers)
					muOffsets.extend(muOffsets_textures)
					mResourceIds.extend(mResourceIds_samplers)
					mResourceIds.extend(mResourceIds_textures)
					mBUnknowns.extend(mBUnknowns_samplers)
					mBUnknowns.extend(mBUnknowns_textures)
				
				if num_parameters != 0:
					offset_1 = offset_end
					offset_2 = offset_1 + num_parameters + calculate_padding(offset_1 + num_parameters, 0x10)
					offset_0 = offset_2 + num_parameters*0x10
					
					offset = offset_0 + num_parameters*0x4
					offset_0_1 = []
					for parameters_name in parameters_names:
						offset_0_1.append(offset)
						offset += len(parameters_name) + 1
						offset += calculate_padding(offset, 0x4)
					
					offset_end = offset
				
				tint_data_size += offset_end - mpTintData
				
				#print(i, num_parameters, num_samplers, hex(mpTintData), hex(offset_0), hex(offset_1), hex(offset_2), hex(offset_3), hex(offset_4), hex(mpaSamplersStates), hex(mpaTextures), hex(tint_data_size))
				
				f.write(struct.pack('<B', unknown_0x0))
				f.write(struct.pack('<B', num_parameters))
				f.write(struct.pack('<B', num_samplers))
				f.write(struct.pack('<B', unknown_0x3))
				f.write(struct.pack('<I', offset_0))
				f.write(struct.pack('<I', offset_1))
				f.write(struct.pack('<I', offset_2))
				f.write(struct.pack('<I', offset_3))
				f.write(struct.pack('<I', offset_4))
				f.write(struct.pack('<I', mpaSamplersStates))
				f.write(struct.pack('<I', mpaTextures))
				
				f.seek(offset_0, 0)
				f.write(struct.pack('<%dI' % num_parameters, *offset_0_1))
				for j, parameters_name in enumerate(parameters_names):
					f.seek(offset_0_1[j], 0)
					f.write(parameters_name.encode('utf-8'))
				
				f.seek(offset_1, 0)
				f.write(struct.pack('<%db' % num_parameters, *[-1]*num_parameters))
				
				f.seek(offset_2, 0)
				for parameter_data in parameters_data:
					f.write(struct.pack('<4f', *parameter_data))
				
				f.seek(offset_3, 0)
				f.write(struct.pack('<%dI' % num_samplers, *offset_3_1))
				for j, sampler_name in enumerate(samplers_names):
					f.seek(offset_3_1[j], 0)
					f.write(sampler_name.encode('utf-8'))
				
				f.seek(offset_4, 0)
				f.write(struct.pack('<%db' % num_samplers, *[-1]*num_samplers))
		
		tint_data_size += calculate_padding(tint_data_size, 0x10)
		
		if tint_data_size == 0:
			tint_data_size = 0x10
			f.write(struct.pack('<I', 3))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
		
		for i in range(0, muArraySize):
			instance = instances[i]
			mModelId = instance[1][0]
			f.seek(mpaInstances + 0x60*muArraySize + tint_data_size + 0x10*i, 0)
			f.write(id_to_bytes(mModelId))
			f.write(struct.pack("<i", 0))
			f.write(struct.pack("<i", mpaInstances + 0x60*i))
			f.write(struct.pack("<i", 0))
		
		for mResourceId, muOffset, mBUnknown in zip(mResourceIds, muOffsets, mBUnknowns):
			f.write(id_to_bytes(mResourceId))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', mBUnknown))
			f.write(struct.pack('<I', muOffset))
			f.write(struct.pack('<i', 0))
	
	return 0


def write_compoundinstancelist(compoundinstancelist_path):
	os.makedirs(os.path.dirname(compoundinstancelist_path), exist_ok = True)
	
	with open(compoundinstancelist_path, "wb") as f:
		f.write(struct.pack("<i", 2))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
	
	return 0


def write_dynamicinstancelist(dynamicinstancelist_path):
	os.makedirs(os.path.dirname(dynamicinstancelist_path), exist_ok = True)
	
	with open(dynamicinstancelist_path, "wb") as f:
		f.write(struct.pack("<i", 3))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
	
	return 0


def write_lightinstancelist(lightinstancelist_path):
	os.makedirs(os.path.dirname(lightinstancelist_path), exist_ok = True)
	
	with open(lightinstancelist_path, "wb") as f:
		f.write(struct.pack("<i", 1))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
	
	return 0


def write_propinstancelist(propinstancelist_path):
	os.makedirs(os.path.dirname(propinstancelist_path), exist_ok = True)
	
	with open(propinstancelist_path, "wb") as f:
		f.write(struct.pack("<i", 2))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
	
	return 0


def write_groundcovercollection(groundcovercollection_path):
	os.makedirs(os.path.dirname(groundcovercollection_path), exist_ok = True)
	
	with open(groundcovercollection_path, "wb") as f:
		f.write(struct.pack("<i", 4))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 3))
		f.write(struct.pack("<i", 0x40))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
	
	return 0


def write_navigationmesh(navigationmesh_path):
	os.makedirs(os.path.dirname(navigationmesh_path), exist_ok = True)
	
	with open(navigationmesh_path, "wb") as f:
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 2))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
	
	return 0


def write_zoneheader(zoneheader_path, mInstanceListId, mDynamicInstanceListId, mLightInstanceListId, mCompoundInstanceListId, mPropInstanceListId, mGroundcoverCollectionId):
	os.makedirs(os.path.dirname(zoneheader_path), exist_ok = True)
	
	with open(zoneheader_path, "wb") as f:
		f.write(struct.pack("<i", 9))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		f.write(struct.pack("<i", 0))
		# IDs
		f.write(bytearray.fromhex(mInstanceListId.replace('_', '')))
		f.write(struct.pack("<i", 0))
		f.write(b'\x04\x00\x00\x80')
		f.write(struct.pack("<i", 0))
		f.write(bytearray.fromhex(mDynamicInstanceListId.replace('_', '')))
		f.write(struct.pack("<i", 0))
		f.write(b'\x0C\x00\x00\x80')
		f.write(struct.pack("<i", 0))
		f.write(bytearray.fromhex(mLightInstanceListId.replace('_', '')))
		f.write(struct.pack("<i", 0))
		f.write(b'\x14\x00\x00\x80')
		f.write(struct.pack("<i", 0))
		f.write(bytearray.fromhex(mCompoundInstanceListId.replace('_', '')))
		f.write(struct.pack("<i", 0))
		f.write(b'\x1C\x00\x00\x80')
		f.write(struct.pack("<i", 0))
		f.write(bytearray.fromhex(mPropInstanceListId.replace('_', '')))
		f.write(struct.pack("<i", 0))
		f.write(b'\x24\x00\x00\x80')
		f.write(struct.pack("<i", 0))
		f.write(bytearray.fromhex(mGroundcoverCollectionId.replace('_', '')))
		f.write(struct.pack("<i", 0))
		f.write(b'\x2C\x00\x00\x80')
		f.write(struct.pack("<i", 0))
	
	return 0


def write_characterspec(characterspec_path, mSkeletonID, mAnimationListID, instances):
	os.makedirs(os.path.dirname(characterspec_path), exist_ok = True)
	
	with open(characterspec_path, "wb") as f:
		mNumModels = len(instances)
		mNumResources = len(instances) + 1 + 1
		mppModels = 0x20
		mppAllocatedSpace = mppModels + mNumModels*4	# Or header size
		padding0 = calculate_padding(mppAllocatedSpace, 0x10)
		
		muOffsets = [mppModels + 0x4*x for x in range(mNumModels)]
		
		# Writing
		f.write(struct.pack('<i', mppModels))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', mNumModels))		# Or always 0x1
		f.write(struct.pack('<B', mNumResources))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<B', mppAllocatedSpace))
		f.write(struct.pack('<B', 0))
		f.seek(mppAllocatedSpace + padding0, 0)
		
		#f.write(id_to_bytes(mSkeletonID))
		f.write(struct.pack('<I', mSkeletonID))
		f.write(struct.pack('<H', 0))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<B', 1))
		f.write(struct.pack('<I', 0x4))
		f.write(struct.pack('<i', 0))
		
		#f.write(id_to_bytes(mAnimationListID))
		f.write(struct.pack('<I', mAnimationListID))
		f.write(struct.pack('<H', 0))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<B', 1))
		f.write(struct.pack('<I', 0x8))
		f.write(struct.pack('<i', 0))
		
		for instance, muOffset in zip(instances, muOffsets):
			f.write(id_to_bytes(instance[1][0]))
			f.write(struct.pack('<H', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<I', muOffset))
			f.write(struct.pack('<i', 0))
		
	return 0


def write_model(model_path, model, resource_type):	#ok
	os.makedirs(os.path.dirname(model_path), exist_ok = True)
	
	with open(model_path, "wb") as f:
		renderables_info = model[1][0]
		model_properties = model[1][1]
		
		minLodDistance = 40000
		maxLodDistance = 1000000
		mpTintData = 0
		mu8NumRenderables = model_properties[0]
		mu8Flags = 0
		mu8NumStates = model_properties[1]
		TintData = model_properties[2]
		
		if mu8NumRenderables == 1:
			mu8NumStates = 1
			muNumLodDistances = 1
		else:
			mu8NumStates = 5
			muNumLodDistances = 5
		mu8VersionNumber = 5
		
		mpu8StateRenderableIndices = 0x1C
		mpfLodDistances = mpu8StateRenderableIndices + 0x1*mu8NumStates
		mpfLodDistances += calculate_padding(mpfLodDistances, 0x4)
		mppRenderables = mpfLodDistances + 0x4*muNumLodDistances
		padding = calculate_padding(mppRenderables + 0x4*mu8NumRenderables, 0x10)
		
		tint_data_size = 0
		muTintOffsets = []
		mTintResourceIds = []
		mBTintUnknowns = []
		
		if TintData != []:
			mpTintData = mppRenderables + 0x4*mu8NumRenderables + padding
		
		if mpTintData != 0:
			parameters_names, parameters_data, samplers_names, sampler_states, textures = TintData
			#f.seek(mpTintData, 0)
			unknown_0x0 = 1
			num_parameters = len(parameters_names)
			num_samplers = len(samplers_names)
			unknown_0x3 = 0
			offset_0 = 0
			offset_0_1 = []
			offset_1 = 0
			offset_2 = 0
			offset_3 = 0
			offset_3_1 = []
			offset_4 = 0
			mpaSamplersStates = 0
			mpaTextures = 0
			offset_end = mpTintData + 0x20
			
			if num_samplers != 0:
				offset_4 = offset_end
				mpaSamplersStates = offset_4 + num_samplers*0x1 + calculate_padding(offset_4 + num_samplers*0x1, 0x4)
				mpaTextures = mpaSamplersStates + num_samplers*0x4
				offset_3 = mpaTextures + num_samplers*0x4
				
				offset = offset_3 + num_samplers*0x4
				offset_3_1 = []
				for sampler_name in samplers_names:
					offset_3_1.append(offset)
					offset += len(sampler_name) + 1
				
				offset_end = offset
				
				muOffsets_samplers = []
				muOffsets_textures = []
				mResourceIds_samplers = []
				mResourceIds_textures = []
				mBUnknowns_samplers = []
				mBUnknowns_textures = []
				
				for j in range(0, num_samplers):
					mSamplerStateId = sampler_states[j]
					mTextureId = textures[j]
					
					muOffsets_samplers.append(mpaSamplersStates + 0x4*j)
					muOffsets_textures.append(mpaTextures + 0x4*j)
					mResourceIds_samplers.append(mSamplerStateId)
					mResourceIds_textures.append(mTextureId)
					mBUnknowns_samplers.append(0)
					mBUnknowns_textures.append(1)
				
				muTintOffsets.extend(muOffsets_samplers)
				muTintOffsets.extend(muOffsets_textures)
				mTintResourceIds.extend(mResourceIds_samplers)
				mTintResourceIds.extend(mResourceIds_textures)
				mBTintUnknowns.extend(mBUnknowns_samplers)
				mBTintUnknowns.extend(mBUnknowns_textures)
			
			if num_parameters != 0:
				offset_1 = offset_end
				offset_2 = offset_1 + num_parameters + calculate_padding(offset_1 + num_parameters, 0x10)
				offset_0 = offset_2 + num_parameters*0x10
				
				offset = offset_0 + num_parameters*0x4
				offset_0_1 = []
				for parameters_name in parameters_names:
					offset_0_1.append(offset)
					offset += len(parameters_name) + 1
					offset += calculate_padding(offset, 0x4)
				
				offset_end = offset
			
			tint_data_size += offset_end - mpTintData
			padding = calculate_padding(tint_data_size, 0x10)
		
		renderable_indices = [-1]*mu8NumStates
		lod_distances = []
		if mu8NumRenderables == 1:
			renderable_indices[0] = 0
			lod_distances.append(maxLodDistance)
		else:
			for i in range(0, muNumLodDistances):
				lod_distances.append(minLodDistance*(i+1)*(i+1))
			for i in range(0, mu8NumRenderables-1):
				renderable_indices[i] = i
			renderable_indices[-1] = mu8NumRenderables - 1
		
		mppRenderables_ = [0]*mu8NumRenderables
		
		mResourceIds = [None]*mu8NumRenderables
		for renderable_info in renderables_info:
			mResourceId = renderable_info[0]
			renderable_index = renderable_info[1][0]
			mResourceIds[renderable_index] = mResourceId
			#mResourceIds[0] = mResourceId
		
		muOffsets = [mppRenderables + 0x4*x for x in range(mu8NumRenderables)]
		
		# Writing
		f.write(struct.pack('<i', mppRenderables))
		f.write(struct.pack('<i', mpu8StateRenderableIndices))
		f.write(struct.pack('<i', mpfLodDistances))
		f.write(struct.pack('<f', maxLodDistance))
		f.write(struct.pack('<i', mpTintData))
		f.write(struct.pack('<B', mu8NumRenderables))
		f.write(struct.pack('<B', mu8Flags))
		f.write(struct.pack('<B', mu8NumStates))
		f.write(struct.pack('<B', mu8VersionNumber))
		f.write(struct.pack('<B', muNumLodDistances))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<B', 0))
		
		f.seek(mpu8StateRenderableIndices, 0)
		f.write(struct.pack('<%db' % mu8NumStates, *renderable_indices))
		
		f.seek(mpfLodDistances, 0)
		f.write(struct.pack('<%df' % muNumLodDistances, *lod_distances))
		
		f.seek(mppRenderables, 0)
		f.write(struct.pack('<%di' % mu8NumRenderables, *mppRenderables_))
		
		if mpTintData != 0:
			f.seek(mpTintData, 0)
			f.write(struct.pack('<B', unknown_0x0))
			f.write(struct.pack('<B', num_parameters))
			f.write(struct.pack('<B', num_samplers))
			f.write(struct.pack('<B', unknown_0x3))
			f.write(struct.pack('<I', offset_0))
			f.write(struct.pack('<I', offset_1))
			f.write(struct.pack('<I', offset_2))
			f.write(struct.pack('<I', offset_3))
			f.write(struct.pack('<I', offset_4))
			f.write(struct.pack('<I', mpaSamplersStates))
			f.write(struct.pack('<I', mpaTextures))
			
			f.seek(offset_0, 0)
			f.write(struct.pack('<%dI' % num_parameters, *offset_0_1))
			for j, parameters_name in enumerate(parameters_names):
				f.seek(offset_0_1[j], 0)
				f.write(parameters_name.encode('utf-8'))
			
			f.seek(offset_1, 0)
			f.write(struct.pack('<%db' % num_parameters, *[-1]*num_parameters))
			
			f.seek(offset_2, 0)
			for parameter_data in parameters_data:
				f.write(struct.pack('<4f', *parameter_data))
			
			f.seek(offset_3, 0)
			f.write(struct.pack('<%dI' % num_samplers, *offset_3_1))
			for j, sampler_name in enumerate(samplers_names):
				f.seek(offset_3_1[j], 0)
				f.write(sampler_name.encode('utf-8'))
			
			f.seek(offset_4, 0)
			f.write(struct.pack('<%db' % num_samplers, *[-1]*num_samplers))
			
			#tint_data_size += calculate_padding(tint_data_size, 0x10)
		
			f.seek(mpTintData + tint_data_size, 0)
		
		#padding = calculate_padding(mppRenderables + 0x4*mu8NumRenderables, 0x10)
		f.write(bytearray([0])*padding)
		
		for mResourceId, muOffset in zip(mResourceIds, muOffsets):
			f.write(id_to_bytes(mResourceId))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', muOffset))
			f.write(struct.pack('<i', 0))
		
		# for mResourceId, muOffset in zip(mResourceIds_samplers, muOffsets_samplers):
			# f.write(id_to_bytes(mResourceId))
			# f.write(struct.pack('<i', 0))
			# f.write(struct.pack('<I', muOffset))
			# f.write(struct.pack('<i', 0))
		
		# for mResourceId, muOffset in zip(mResourceIds_textures, muOffsets_textures):
			# f.write(id_to_bytes(mResourceId))
			# f.write(struct.pack('<B', 0))
			# f.write(struct.pack('<B', 0))
			# f.write(struct.pack('<B', 0))
			# f.write(struct.pack('<B', 1))
			# f.write(struct.pack('<I', muOffset))
			# f.write(struct.pack('<i', 0))
		
		for mResourceId, muOffset, mBUnknown in zip(mTintResourceIds, muTintOffsets, mBTintUnknowns):
			f.write(id_to_bytes(mResourceId))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', mBUnknown))
			f.write(struct.pack('<I', muOffset))
			f.write(struct.pack('<i', 0))
	
	return 0


def write_renderable(renderable_path, renderable, resource_type, shared_dir):	#ok
	shared_vertex_descriptor_dir = os.path.join(shared_dir, "VertexDescriptor")
	
	os.makedirs(os.path.dirname(renderable_path), exist_ok = True)
	
	renderable_body_path = renderable_path[:-4] + "_model" + renderable_path[-4:]
	
	with open(renderable_path, "wb") as f, open(renderable_body_path, "wb") as g:
		mRenderableId = renderable[0]
		meshes_info = renderable[1][0]
		renderable_properties = renderable[1][1]
		indices_buffer = renderable[1][2]
		vertices_buffer = renderable[1][3]
		
		object_center = renderable_properties[0]
		object_radius = renderable_properties[1]
		mu16VersionNumber = 0xC
		num_meshes = renderable_properties[2]
		meshes_table_pointer = 0x20
		flags0 = 0
		flags1 = -1
		padding = 0
		
		meshes_data_pointer = meshes_table_pointer + 0x4*num_meshes
		meshes_data_pointer += calculate_padding(meshes_data_pointer, 0x10)
		
		mesh_header_size = 0x60
		meshes_data_pointers = [meshes_data_pointer + mesh_header_size*x for x in range(num_meshes)]
		
		unknown_0x0 = [0.0, 0.0, 0.0]
		unknown_0xC = 0
		constant_0x10 = 5
		constant_0x14 = 0
		constant_0x18 = 0
		null_0x20 = 0
		sub_part_code = 0
		unknown_0x25 = 1
		unknown_0x26 = 0
		unknown_0x27 = 4
		constant_0x30 = 0
		constant_0x34 = 1
		constant_0x38 = 3
		constant_0x44 = 2
		constant_0x48 = 0
		constant_0x4C = 1
		constant_0x50 = 2
		constant_0x5C = 0
		
		mMaterialIds = [0]*num_meshes
		pointers_1 = [0]*num_meshes
		pointers_2 = [0]*num_meshes
		indices_buffer_offset = [0]*num_meshes
		indices_buffer_counts = [0]*num_meshes
		indices_buffer_sizes = [0]*num_meshes
		vertices_buffer_offset = [0]*num_meshes
		vertices_buffer_sizes = [0]*num_meshes
		vertices_properties = [[] for _ in range(num_meshes)]
		for mesh_info in meshes_info:
			mesh_index = mesh_info[0]
			mMaterialId = mesh_info[1]
			mVertexDescriptorId = mesh_info[2]
			
			vertex_descriptor_path = os.path.join(shared_vertex_descriptor_dir, mVertexDescriptorId + ".dat")
			vertex_properties = read_vertex_descriptor(vertex_descriptor_path)
			vertex_size = vertex_properties[0]
			vertices_properties[mesh_index] = vertex_properties[:]
			
			pointers_1[mesh_index] = meshes_data_pointers[mesh_index] + 0x30
			pointers_2[mesh_index] = pointers_1[mesh_index] + 0x18
			
			if mesh_index == 0:
				indices_buffer_offset[mesh_index] = 0
			else:
				indices_buffer_offset[mesh_index] = vertices_buffer_offset[mesh_index - 1] + vertices_buffer_sizes[mesh_index - 1]
				indices_buffer_offset[mesh_index] += calculate_padding(indices_buffer_offset[mesh_index], 0x10)
			
			indices_buffer_counts[mesh_index] = len(indices_buffer[mesh_index])
			indices_buffer_sizes[mesh_index] = indices_buffer_counts[mesh_index] * 0x2
			
			vertices_buffer_offset[mesh_index] = indices_buffer_offset[mesh_index] + indices_buffer_sizes[mesh_index]
			vertices_buffer_offset[mesh_index] += calculate_padding(vertices_buffer_offset[mesh_index], 0x10)
			vertices_buffer_sizes[mesh_index] = len(vertices_buffer[mesh_index][0]) * vertex_size
			
			mMaterialIds[mesh_index] = mMaterialId
		
		muOffsets_material = [x + 0x20 for x in meshes_data_pointers]
		
		
		# Writing header
		f.write(struct.pack('<fff', *object_center))
		f.write(struct.pack('<f', object_radius))
		f.write(struct.pack('<H', mu16VersionNumber))
		f.write(struct.pack('<H', num_meshes))
		f.write(struct.pack('<i', meshes_table_pointer))
		f.write(struct.pack('<b', flags0))
		f.write(struct.pack('<b', flags1))
		f.write(struct.pack('<H', padding))
		f.write(struct.pack('<i', padding))
		
		f.seek(meshes_table_pointer, 0)
		f.write(struct.pack('<%di' % num_meshes, *meshes_data_pointers))
		
		for i in range(0, num_meshes):
			f.seek(meshes_data_pointers[i], 0)
			f.write(struct.pack('<3f', *unknown_0x0))
			f.write(struct.pack('<i', unknown_0xC))
			f.write(struct.pack('<i', constant_0x10))
			f.write(struct.pack('<i', constant_0x14))
			f.write(struct.pack('<i', constant_0x18))
			f.write(struct.pack('<i', indices_buffer_counts[i]))
			f.write(struct.pack('<i', null_0x20))
			f.write(struct.pack('<B', sub_part_code))
			f.write(struct.pack('<B', unknown_0x25))
			f.write(struct.pack('<B', unknown_0x26))
			f.write(struct.pack('<B', unknown_0x27))
			f.write(struct.pack('<i', pointers_1[i]))
			f.write(struct.pack('<i', pointers_2[i]))
			f.write(struct.pack('<i', constant_0x30))
			f.write(struct.pack('<i', constant_0x34))
			f.write(struct.pack('<i', constant_0x38))
			
			f.write(struct.pack('<i', indices_buffer_offset[i]))
			f.write(struct.pack('<i', indices_buffer_sizes[i]))
			
			f.write(struct.pack('<i', constant_0x44))
			f.write(struct.pack('<i', constant_0x48))
			f.write(struct.pack('<i', constant_0x4C))
			f.write(struct.pack('<i', constant_0x50))
			
			f.write(struct.pack('<i', vertices_buffer_offset[i]))
			f.write(struct.pack('<i', vertices_buffer_sizes[i]))
			f.write(struct.pack('<i', constant_0x5C))
		
		f.seek(meshes_data_pointers[-1] + mesh_header_size, 0)
		for i in range(0, num_meshes):
			f.write(id_to_bytes(mMaterialIds[i]))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 1))
			f.write(struct.pack('<I', muOffsets_material[i]))
			f.write(struct.pack('<i', 0))
		
		# Writing body
		for mesh_index in range(0, num_meshes):
			mesh_index_error = -1
			g.seek(indices_buffer_offset[mesh_index], 0)
			g.write(struct.pack('<%sH' % indices_buffer_counts[mesh_index], *indices_buffer[mesh_index]))
			
			padding = calculate_padding(indices_buffer_sizes[mesh_index], 0x10)
			if padding == 0:
				padding = 0x10
			padding_buffer = padding // 2
			g.write(struct.pack("<%sH" % (padding_buffer), *[0]*(padding_buffer)))
			
			g.seek(vertices_buffer_offset[mesh_index], 0)
			
			vertex_size = vertices_properties[mesh_index][0]
			semantic_properties = vertices_properties[mesh_index][1][0]
			
			mesh_vertices_buffer, mesh_indices = vertices_buffer[mesh_index]
			for index in sorted(mesh_indices):
				index_, position, normal, tangent, color, uv1, uv2, uv3, uv4, uv5, uv6, blend_indices, blend_weight, binormal, color2 = mesh_vertices_buffer[index]
				
				for semantic in semantic_properties:
					g.seek(vertices_buffer_offset[mesh_index] + index * vertex_size, 0)
					
					semantic_type = semantic[0]
					data_type = semantic[1]
					data_offset = semantic[2]
					g.seek(data_offset, 1)
					
					if semantic_type == "POSITION":
						values = position
					elif semantic_type == "POSITIONT":
						print("Skipping POSITIONT")
						pass
					elif semantic_type == "NORMAL":
						values = normal
					elif semantic_type == "COLOR":
						values = color
					elif semantic_type == "TEXCOORD1":
						values = [uv1[0], -uv1[1]]
					elif semantic_type == "TEXCOORD2":
						if data_type[0] == "4B":
							values = color2
						else:
							values = [uv2[0], -uv2[1]]
					elif semantic_type == "TEXCOORD3":
						if data_type[0] == "4B":
							values = color2
						else:
							values = [uv3[0], -uv3[1]]
					elif semantic_type == "TEXCOORD4":
						if data_type[0] == "4B":
							values = color2
						else:
							values = [uv4[0], -uv4[1]]
					elif semantic_type == "TEXCOORD5":		#custom normal
						if data_type[0] == "2e":
							values = [uv5[0], -uv5[1]]
						else:
							values = normal
					elif semantic_type == "TEXCOORD6":
						if data_type[0] == "2e":
							values = [uv6[0], -uv6[1]]
						else:
							values = normal
					elif semantic_type == "TEXCOORD7":
						print("Skipping TEXCOORD7")
						pass
					elif semantic_type == "TEXCOORD8":
						print("Skipping TEXCOORD8")
						pass
					elif semantic_type == "BLENDINDICES":
						values = blend_indices
						#values = [0, 0, 0, 0]
					elif semantic_type == "BLENDWEIGHT":
						values = blend_weight
						#values = [0xFF, 0, 0, 0]
					elif semantic_type == "TANGENT":
						values = tangent
					elif semantic_type == "BINORMAL":
						values = binormal
					elif semantic_type == "COLOR2":
						print("Skipping COLOR2")
						pass
					elif semantic_type == "PSIZE":
						print("Skipping PSIZE")
						pass
					
					if data_type[0][-1] == "e":
						try:
							g.write(struct.pack("<%s" % data_type[0], *values))
						except:
							g.write(struct.pack("<%s" % data_type[0], *[0]*int(data_type[0][0])))
					elif "norm" in data_type[0]:
						data_type = data_type[0].replace("norm", "")
						if semantic_type == "TEXCOORD5" or semantic_type == "TEXCOORD6":	#NORMAL_PACKED and NORMAL_PACKED for wheels
							x, y, z, w = calculate_packed_normals(values)
							x = round(x)
							y = round(y)
							z = round(z)
							w = round(w)
						else:
							scale = 10.0
							w = 32767.0
							x = round(values[0]/scale*w)
							y = round(values[1]/scale*w)
							z = round(values[2]/scale*w)
							w = round(32767.0)
						g.write(struct.pack("<%s" % data_type, x, y, z, w))
					else:
						try:
							g.write(struct.pack("<%s" % data_type[0], *values))
						except:
							if mesh_index_error != mesh_index:
								print("WARNING: unknown vertex type found on %s mesh index %i. It is a type %s with data type %s with length %s. Writing a null data." %(mRenderableId, mesh_index, semantic_type, data_type[0], str(hex(data_type[1]))))
								mesh_index_error = mesh_index
							g.write(struct.pack("<%s" % data_type[0], *[0]*int(data_type[0][0])))
		
		#g.seek(vertices_buffer_offset[-1] + vertices_buffer_sizes[-1], 0)
		padding = calculate_padding(vertices_buffer_offset[-1] + vertices_buffer_sizes[-1], 0x80)
		g.write(bytearray([0])*padding)
	
	return 0


def write_material(material_path, material):	#ok
	os.makedirs(os.path.dirname(material_path), exist_ok = True)
	
	with open(material_path, "wb") as f:
		#[mMaterialId, [mShaderId, textures_info, sampler_states_info, material_parameters, sampler_properties, texture_samplers], is_shared_asset] = material
		mMaterialId = material[0]
		mShaderId = material[1][0]
		textures_info = material[1][1]
		sampler_states_info = material[1][2]
		material_parameters = material[1][3]
		sampler_properties = material[1][4]
		texture_samplers = material[1][5]
		
		parameters_Indices, parameters_Ones, parameters_NamesHash, parameters_Data, parameters_Names = material_parameters
		material_constants, miChannel, raster_type_offsets = sampler_properties
		
		num_parameters = len(parameters_Indices)
		num_parameters_withdata = len(parameters_Data)
		miNumSamplers = len(textures_info)
		
		mMaterialId = material[0]
		unk_0x4 = 0
		const_0x5 = 4
		null = 0
		parameters_indices_pointer = 0x30
		parameters_ones_pointer = parameters_indices_pointer + num_parameters
		_ = parameters_ones_pointer + num_parameters
		padding0 = calculate_padding(_, 0x4)
		parameters_nameshash_pointer = _ + padding0
		_ = parameters_nameshash_pointer + 0x4*num_parameters
		padding1 = calculate_padding(_, 0x10)
		parameters_data_pointer = _ + padding1
		mpaMaterialConstants = parameters_data_pointer + 0x10*num_parameters_withdata
		_ = mpaMaterialConstants + 0x2*miNumSamplers
		padding2 = calculate_padding(_, 0x4)
		mpaSamplers = _ + padding2
		mpaSamplersChannel = mpaSamplers + 0x4*miNumSamplers
		#_ = mpaSamplers + 0x4*num_parameters + 0x4*miNumSamplers
		_ = mpaSamplersChannel + 0x4*miNumSamplers
		padding3 = calculate_padding(_, 0x10)
		resources_pointer = _ + padding3
		
		# Writing header
		f.write(id_to_bytes(mMaterialId))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<B', 4))
		f.write(struct.pack('<H', resources_pointer))
		f.write(struct.pack('<i', null))
		if num_parameters > 0:
			f.write(struct.pack('<I', parameters_indices_pointer))
			f.write(struct.pack('<I', parameters_ones_pointer))
			f.write(struct.pack('<I', parameters_nameshash_pointer))
			f.write(struct.pack('<I', parameters_data_pointer))
		else:
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<i', 0))
		f.write(struct.pack('<B', num_parameters))
		f.write(struct.pack('<B', num_parameters_withdata))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<i', miNumSamplers))
		if miNumSamplers > 0:
			f.write(struct.pack('<I', mpaMaterialConstants))
			f.write(struct.pack('<I', mpaSamplersChannel))
			f.write(struct.pack('<I', mpaSamplers))
		else:
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
		
		if num_parameters > 0:
			f.seek(parameters_indices_pointer, 0)
			for i in range(0, num_parameters):
				f.write(struct.pack('<b', parameters_Indices[i]))
			f.seek(parameters_ones_pointer, 0)
			for i in range(0, num_parameters):
				f.write(struct.pack('<b', parameters_Ones[i]))
			f.seek(parameters_nameshash_pointer, 0)
			for i in range(0, num_parameters):
				f.write(struct.pack('<I', parameters_NamesHash[i]))
			f.seek(parameters_data_pointer, 0)
			for i in range(0, num_parameters_withdata):
				if parameters_Indices[i] != -1:
					f.write(struct.pack('<4f', *parameters_Data[i]))
		
		if miNumSamplers > 0:
			f.seek(mpaMaterialConstants, 0)
			for i in range(0, miNumSamplers):
				f.write(struct.pack('<H', material_constants[i]))
			f.seek(mpaSamplersChannel, 0)
			for i in range(0, miNumSamplers):
				f.write(struct.pack('<B', miChannel[i]))
			f.seek(mpaSamplers, 0)
			for i in range(0, miNumSamplers):
				f.write(struct.pack('<i', raster_type_offsets[i]))
		
		f.seek(resources_pointer, 0)
		# mResourceIds
		f.write(id_to_bytes(mShaderId))
		f.write(struct.pack('<H', 0x53))
		f.write(struct.pack('<B', 0))
		f.write(struct.pack('<B', 1))
		f.write(struct.pack('<I', 0x8))
		f.write(struct.pack('<i', 0))
		
		for i in range(0, miNumSamplers):
			raster_type = texture_samplers[i]
			for texture_info in textures_info:
				if texture_info[2] == raster_type:
					break
					
			f.write(id_to_bytes(texture_info[0]))
			f.write(struct.pack('<H', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 1))
			f.write(struct.pack('<I', mpaSamplers + 0x4*i))
			f.write(struct.pack('<i', 0))
		
		for i in range(0, miNumSamplers):
			f.write(id_to_bytes(sampler_states_info[i]))
			f.write(struct.pack('<H', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<I', mpaSamplers + 0x4*miNumSamplers + 0x4*i))
			f.write(struct.pack('<i', 0))
	
	return 0


def write_raster(raster_path, raster): #ok
	os.makedirs(os.path.dirname(raster_path), exist_ok = True)
	
	raster_body_path = raster_path[:-4] + "_texture" + raster_path[-4:]
	raster_source_path = raster[3]
	
	if raster_source_path == "create_texture":
		raster_source_path = raster_path.replace(".dat", ".dds")
		if raster[0] == "7D_A1_02_A1":
			create_displacementsampler(raster_source_path)
		elif raster[0] == "4F_1F_A7_2D":
			create_blacksampler(raster_source_path)
		else:
			create_displacementsampler(raster_source_path)
	
	with open(raster_source_path, "rb") as f:
		DDS_MAGIC = struct.unpack("<I", f.read(0x4))[0]
		header_size = struct.unpack("<I", f.read(0x4))[0]
		flags = struct.unpack("<I", f.read(0x4))[0]
		height = struct.unpack("<I", f.read(0x4))[0]
		width = struct.unpack("<I", f.read(0x4))[0]
		pitchOrLinearSize = struct.unpack("<I", f.read(0x4))[0]
		depth = struct.unpack("<I", f.read(0x4))[0]
		mipMapCount = struct.unpack("<I", f.read(0x4))[0]
		reserved1 = struct.unpack("<11I", f.read(0x4*11))
		
		# DDS_PIXELFORMAT
		dwSize = struct.unpack("<I", f.read(0x4))[0]
		dwFlags = struct.unpack("<I", f.read(0x4))[0]
		dwFourCC = f.read(0x4).decode()
		dwRGBBitCount = struct.unpack("<I", f.read(0x4))[0]
		dwRBitMask = struct.unpack("<I", f.read(0x4))[0]
		dwGBitMask = struct.unpack("<I", f.read(0x4))[0]
		dwBBitMask = struct.unpack("<I", f.read(0x4))[0]
		dwABitMask = struct.unpack("<I", f.read(0x4))[0]
		
		caps = struct.unpack("<I", f.read(0x4))[0]
		caps2 = struct.unpack("<I", f.read(0x4))[0]
		caps3 = struct.unpack("<I", f.read(0x4))[0]
		caps4 = struct.unpack("<I", f.read(0x4))[0]
		reserved2 = struct.unpack("<I", f.read(0x4))[0]
		
		data = f.read()
	
	if depth == 0:
		depth = 1
	
	with open(raster_path, "wb") as f, open(raster_body_path, "wb") as g:
		unk1 = 1
		#unk2 = 0x30		# normal is 0x20
		unk2 = raster[1][0][0]
		mu32VersionNumber = 0x7
		format = get_raster_format(dwFourCC)
		dimension = 1
		main_mipmap = 1
		mipmap = mipMapCount
		padding_texture = calculate_padding(len(data), 0x80)
		
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', unk1))
		f.write(struct.pack('<i', mu32VersionNumber))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', format))
		f.write(struct.pack('<i', unk2))
		f.write(struct.pack('<HHH', width, height, depth))
		f.write(struct.pack('<H', dimension))
		f.write(struct.pack('<BB', main_mipmap, mipmap))
		f.write(struct.pack('<H', 0))
		
		g.write(data)
		g.write(bytearray([0])*padding_texture)
	
	return 0


def write_polygonsouplist(polygonsouplist_path, PolygonSoups):
	os.makedirs(os.path.dirname(polygonsouplist_path), exist_ok = True)
	
	with open(polygonsouplist_path, "wb") as f:
		scale = 500/0x8000 #0.0152587890625
		miVertexOffsetConstant = 500.0

		miNumPolySoups = len(PolygonSoups)
		if miNumPolySoups == 0:
			f.write(struct.pack('<3f', 0, 0, 0))
			f.write(struct.pack('<f', 0))
			f.write(struct.pack('<3f', 0, 0, 0))
			f.write(struct.pack('<f', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<i', 0x30))
			return 0
		
		mMin_w = 0
		mMax_w = 0
		mpapPolySoups = 0x30
		miNumPolySoups = len(PolygonSoups)
		mpaPolySoupBoxes = mpapPolySoups + 0x4*miNumPolySoups
		padding = calculate_padding(mpaPolySoupBoxes, 0x10)
		mpaPolySoupBoxes += padding
		mpaPolySoupBoxesEnd = mpaPolySoupBoxes + math.ceil(miNumPolySoups/4.0)*0x70
		
		mpPolySoup_0 = calculate_mpPolySoup(miNumPolySoups, mpaPolySoupBoxesEnd)
		#mpPolySoup_0 -= 0x20
		padding_PolySoup = calculate_padding(mpPolySoup_0 + 0x20, 0x80)
		mpPolySoup_0 += padding_PolySoup
		
		mpPolySoups = []
		PolySoupBoxes = []
		maabVertexOffsetMultiply = [[] for _ in range(miNumPolySoups)]
		header_size = 0x10
		mpPolySoups.append(mpPolySoup_0)
		for i in range(0, miNumPolySoups):
			#mpPolySoups.append(cte)
			object_index, PolySoupBox, maiVertexOffsets, mfComprGranularity, PolygonSoupVertices, PolygonSoupPolygons, mu8NumQuads = PolygonSoups[i]
			
			PolySoupBoxes.append(PolySoupBox)
			
			mpaVertices = mpPolySoups[i] + header_size
			
			mu8TotalNumPolys = len(PolygonSoupPolygons)
			mu8NumQuads = mu8NumQuads
			mu8NumVertices = len(PolygonSoupVertices)
			
			mpaPolygons = mpaVertices + mu8NumVertices*0x6
			mpaPolygons += calculate_padding(mpaPolygons, 0x10)
			mu16DataSize = mpaPolygons + mu8TotalNumPolys*0xC - mpPolySoups[i] + padding_PolySoup
			
			# Transforming PolygonSoupVertices
			for mAabbMin in PolySoupBoxes[i][0]:
				mbVertexOffsetMultiply = int(math.floor(mAabbMin/miVertexOffsetConstant))
				#if mbVertexOffsetMultiply > 0:
				#	mbVertexOffsetMultiply -= 1
				maabVertexOffsetMultiply[i].append(mbVertexOffsetMultiply)
			
			for PolygonSoupVertex in PolygonSoupVertices:
				for j, vertex_co in enumerate(PolygonSoupVertex):
					PolygonSoupVertex[j] = int((vertex_co - maabVertexOffsetMultiply[i][j] * miVertexOffsetConstant) / scale)
			
			#Checking out of bounds coordinates
			coordinates = list(zip(*PolygonSoupVertices))
			translation = [0, 0, 0]
			for j in range(0, 3):
				if min(coordinates[j]) < 0:
					translation[j] = min(coordinates[j])
			
			# if translation != [0, 0, 0]:
				# print("WARNING: Negative value on PolygonSoupMesh %d. Translate your mesh origin and the empty coordinates. Trying to apply a solution." % object_index)
				# maiVertexOffsets[0] += translation[0]
				# maiVertexOffsets[1] += translation[1]
				# maiVertexOffsets[2] += translation[2]
				# for j in range(0, mu8NumVertices):
					# PolygonSoupVertices[j][0] -= translation[0]
					# PolygonSoupVertices[j][1] -= translation[1]
					# PolygonSoupVertices[j][2] -= translation[2]
			
			coordinates = list(zip(*PolygonSoupVertices))
			min_coord = 0xFFFF
			max_coord = 0
			for j in range(0, 3):
				if max(coordinates[j]) > max_coord:
					max_coord = max(coordinates[j])
				if min(coordinates[j]) < min_coord:
					min_coord = min(coordinates[j])
			
			if max_coord > 0xFFFF:
				print("ERROR: Out of bounds (>0xFFFF) value on PolygonSoupMesh %d. Translate your mesh origin and the empty coordinates or modify the object scale." % object_index)
			
			PolygonSoups[i] = [maabVertexOffsetMultiply[i][:], mfComprGranularity, mpaPolygons, mpaVertices, mu16DataSize, mu8TotalNumPolys, mu8NumQuads, mu8NumVertices, PolygonSoupVertices, PolygonSoupPolygons]
			
			mpPolySoup_next = mpaPolygons + mu8TotalNumPolys*0xC
			padding_PolySoup = calculate_padding(mpPolySoup_next - mpPolySoup_0, 0x80)
			mpPolySoup_next += padding_PolySoup
			mpPolySoups.append(mpPolySoup_next)
		
		del mpPolySoups[-1]
		
		mMin = [min([mAabbMin[0][i] for mAabbMin in PolySoupBoxes]) for i in range(0, 3)]
		mMax = [max([mAabbMax[1][i] for mAabbMax in PolySoupBoxes]) for i in range(0, 3)]
		
		miDataSize = PolygonSoups[-1][2] + PolygonSoups[-1][5]*0xC # mpPolySoups[-1] + PolygonSoups[-1][4] - padding_PolySoup
		#miDataSize += 0x60
		
		
		#Writing
		f.write(struct.pack('<3f', *mMin))
		f.write(struct.pack('<f', mMin_w))
		f.write(struct.pack('<3f', *mMax))
		f.write(struct.pack('<f', mMax_w))
		f.write(struct.pack('<I', mpapPolySoups))
		f.write(struct.pack('<I', mpaPolySoupBoxes))
		f.write(struct.pack('<i', miNumPolySoups))
		f.write(struct.pack('<i', miDataSize))			# Verify
		
		f.seek(mpapPolySoups, 0)
		f.write(struct.pack('<%dI' % miNumPolySoups, *mpPolySoups))
		
		f.seek(mpaPolySoupBoxes, 0)
		for i in range(0, miNumPolySoups):
			f.seek(int(mpaPolySoupBoxes + 0x70*(i//4) + 0x4*(i%4)), 0)
			f.write(struct.pack('<f', PolySoupBoxes[i][0][0]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][0][1]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][0][2]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][1][0]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][1][1]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][1][2]))
			f.seek(0xC, 1)
			f.write(struct.pack('<i', PolySoupBoxes[i][2]))
		
		# Todo
		for i in range(0, miNumPolySoups):
			f.seek(mpPolySoups[i], 0)
			
			mabVertexOffsetMultiply, mfComprGranularity, mpaPolygons, mpaVertices, mu16DataSize, mu8TotalNumPolys, mu8NumQuads, mu8NumVertices, PolygonSoupVertices, PolygonSoupPolygons = PolygonSoups[i]
			f.write(struct.pack('<I', mpaPolygons))
			f.write(struct.pack('<I', mpaVertices))
			f.write(struct.pack('<H', mu16DataSize))
			
			f.write(struct.pack('<bbb', *mabVertexOffsetMultiply))
			
			f.write(struct.pack('<B', mu8NumQuads))
			f.write(struct.pack('<B', mu8TotalNumPolys))
			f.write(struct.pack('<B', mu8NumVertices))
			
			f.seek(mpaVertices, 0)
			for j in range(0, mu8NumVertices):
				f.write(struct.pack('<3H', *PolygonSoupVertices[j]))
			
			f.seek(mpaPolygons, 0)
			for j in range(0, mu8NumQuads):
				mu16CollisionTag, mau8VertexIndices, mau8EdgeCosines = PolygonSoupPolygons[j]
				f.write(struct.pack('<H', mu16CollisionTag[0]))
				f.write(struct.pack('<H', mu16CollisionTag[1]))
				f.write(struct.pack('<4B', *mau8VertexIndices))
				f.write(struct.pack('<4B', *mau8EdgeCosines))
			
			for j in range(mu8NumQuads, mu8TotalNumPolys):
				mu16CollisionTag, mau8VertexIndices, mau8EdgeCosines = PolygonSoupPolygons[j]
				f.write(struct.pack('<H', mu16CollisionTag[0]))
				f.write(struct.pack('<H', mu16CollisionTag[1]))
				f.write(struct.pack('<3B', *mau8VertexIndices))
				f.write(struct.pack('<B', 0xFF))
				f.write(struct.pack('<4B', *mau8EdgeCosines))
		
		#f.write(bytearray([0])*0x60)
		padding = calculate_padding(miDataSize, 0x10)
		f.write(bytearray([0])*padding)


def write_resources_table(resources_table_path, mResourceIds, resource_type, write_header):
	with open(resources_table_path, "wb") as f:
		#if resource_type == "InstanceList" and write_header == True:
		if write_header == True:
			macMagicNumber = b'bnd2'
			muVersion = 5
			muPlatform = 1
			muHeaderOffset = 0x70
			muDebugDataOffset = -1
			muResourceEntriesCount = len(mResourceIds)
			muResourceEntriesOffset = 0xD0
			mauResourceDataOffset = [0x0, 0x0, 0x0, 0x0]
			if resource_type == "CharacterSpec":
				muFlags = 0x1
			else:
				muFlags = 0x9
			pad1 = 0
			pad2 = 0
			
			f.write(macMagicNumber)
			f.write(struct.pack("<H", muVersion))
			f.write(struct.pack("<H", muPlatform))
			f.write(struct.pack("<i", muDebugDataOffset))
			f.write(struct.pack("<I", muResourceEntriesCount))
			f.write(struct.pack("<I", muResourceEntriesOffset))
			f.write(struct.pack("<IIII", *mauResourceDataOffset))
			f.write(struct.pack("<I", muFlags))
			f.write(struct.pack("<I", pad1))
			f.write(struct.pack("<I", pad2))
			
			f.write(struct.pack("<i", -1))
			if resource_type == "CharacterSpec":
				pass
			else:
				f.write(b'GRAPHICS')
				f.seek(0x7, 1)
				f.write(b'PHYSICS')
				f.seek(0x8, 1)
				f.write(b'NAV')
			
			f.seek(muHeaderOffset, 0)
			f.write(b'Resources generated by NFSMW 2012 Exporter 3.0 for Blender by DGIorio')
			f.write(b'...........Hash:.3bb42e1d')
			f.seek(muResourceEntriesOffset, 0)
		
		muStreamIndex_0 = b''
		muStreamIndex_1 = b''
		muStreamIndex_2 = b''
		muStreamIndex_3 = b''
		
		mResourceIds.sort(key=lambda x:x[2])
		for mResourceId, muResourceType, _ in mResourceIds:
			count = 0
			unkByte_0x4 = 0
			unkByte = 0
			muStreamIndex = 0
			if muResourceType  == "PolygonSoupList":
				unkByte_0x4 = 0x60
				unkByte = 1
				if resource_type == "InstanceList":
					unkByte_0x4 = 0x0
					unkByte = 0
					muStreamIndex = 1
			elif muResourceType  == "NavigationMesh":
				muStreamIndex = 2
			elif muResourceType == "Texture" or muResourceType == "Material" or muResourceType == "CharacterSpec":
				unkByte = 1
			# f.write(id_to_bytes(mResourceId))
			# f.write(struct.pack("<B", unkByte_0x4))
			# f.write(struct.pack("<B", 0))
			# f.write(struct.pack("<B", count))
			# f.write(struct.pack("<B", unkByte))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# f.write(struct.pack("<I", 0))
			# muResourceTypeId = resourcetype_to_type_id(muResourceType)
			# f.write(id_to_bytes(muResourceTypeId))
			# f.write(struct.pack("<H", 0))
			# f.write(struct.pack("<B", 0))
			# f.write(struct.pack("<B", 0))
			# f.write(struct.pack("<I", 0))
			
			muResourceTypeId = resourcetype_to_type_id(muResourceType)
			
			resource_entry = b''
			resource_entry += id_to_bytes(mResourceId)
			resource_entry += struct.pack("<B", unkByte_0x4)
			resource_entry += struct.pack("<B", 0)
			resource_entry += struct.pack("<B", count)
			resource_entry += struct.pack("<B", unkByte)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += struct.pack("<I", 0)
			resource_entry += id_to_bytes(muResourceTypeId)
			resource_entry += struct.pack("<H", 0)
			resource_entry += struct.pack("<B", 0)
			resource_entry += struct.pack("<B", muStreamIndex)
			resource_entry += struct.pack("<I", 0)
			
			if muStreamIndex == 0:
				muStreamIndex_0 += resource_entry
			elif muStreamIndex == 1:
				muStreamIndex_1 += resource_entry
			elif muStreamIndex == 2:
				muStreamIndex_2 += resource_entry
			elif muStreamIndex == 3:
				muStreamIndex_3 += resource_entry
		
		f.write(muStreamIndex_0)
		f.write(muStreamIndex_1)
		f.write(muStreamIndex_2)
		f.write(muStreamIndex_3)
	
	return 0


def edit_graphicsspec(graphicsspec_path, instances, instances_wheelGroups, instance_collision):
	if os.path.isfile(graphicsspec_path) == False:
		return (0, "")
	
	with open(graphicsspec_path, "rb") as f:
		file_size = os.path.getsize(graphicsspec_path)
		
		mppModels = struct.unpack("<I", f.read(0x4))[0]
		f.seek(0xC, 0)
		mpWheelsData = struct.unpack("<I", f.read(0x4))[0]
		muPartsCount = struct.unpack("<B", f.read(0x1))[0]
		
		mpWheelAllocateSpace = []
		object_placements = []
		mNumWheelParts = 0
		for i in range(0, 4):
			f.seek(mpWheelsData + 0x90*i + 0x78, 0)
			mpWheelAllocateSpace.append(struct.unpack("<I", f.read(0x4))[0])
			spinnable_models = struct.unpack("<B", f.read(0x1))[0]
			f.seek(0x3, 1)
			mNumWheelParts += struct.unpack("<B", f.read(0x1))[0]
			f.seek(0x1, 1)
			object_placement = f.read(0xE).split(b'\x00')[0]
			object_placement = str(object_placement, 'ascii').lower()
			object_placements.append(object_placement)
		
		first_wheel_pointer = min(mpWheelAllocateSpace)
		
		f.seek(-0x8, 2)
		last_resource_pointer = struct.unpack("<I", f.read(0x4))[0]
		mpResourceIds = last_resource_pointer + 0x4
		mpResourceIds += calculate_padding(mpResourceIds, 0x10)
		f.seek(mpResourceIds, 0)
		muOffset = 0
		mpModel = mpResourceIds
		while muOffset != mppModels:
			f.seek(0x8, 1)
			muOffset = struct.unpack("<I", f.read(0x4))[0]
			_ = struct.unpack("<I", f.read(0x4))[0]
			mpModel += 0x10
		mpModel -= 0x10
		
		f.seek(0x0, 0)
		header_data = f.read(first_wheel_pointer)
		wheel_allocate_space = f.read(mpResourceIds - first_wheel_pointer)
		resources_up_data = f.read(mpModel - mpResourceIds)
		f.seek(0x10*muPartsCount, 1)
		resources_down_data = f.read(file_size - (mpModel + 0x10*muPartsCount) - 0x10*mNumWheelParts)
		resouces_wheel = f.read(0x10*mNumWheelParts)
		
		f.seek(mpResourceIds + 0x8, 0)
		muOffset = struct.unpack("<I", f.read(0x4))[0]
		if muOffset == 0x8:
			f.seek(-0xC, 1)
		else:
			f.seek(0x4, 1)
		mpPolygonSoupListId_relative = f.tell() - mpResourceIds
		mPolygonSoupListId = bytes_to_id(f.read(0x4))
	
	instances.sort(key=lambda x:x[0])
	
	if len(instances_wheelGroups) > 0:
		mResourceIds = []
		muOffsets = []
		# mpWheelAllocateSpace = []
		# spinnable_models = []
		# maNumWheelParts = []
		# muNumWheelParts = 0
		
		# for i, (object_placement, group) in enumerate(instances_wheelGroups.items()):
			# mpWheelAllocateSpace.append(first_wheel_pointer + muNumWheelParts*0x4)
			
			# is_spinnable = ''
			# for j, instance in enumerate(group):
				# is_spinnable += str(instance[1][2])
				# mResourceIds.append(instance[1][0])
				# muOffsets.append(mpWheelAllocateSpace[i] + j*0x4)
			
			# spinnable_models.append(int(is_spinnable, 2))
			# maNumWheelParts.append(len(group))
			
			# muNumWheelParts += len(group)
		
		mpWheelAllocateSpace = {}
		spinnable_models = {}
		wheels_offset = {}
		maNumWheelParts = {}
		muNumWheelParts = 0
		for i in range(0, 4):
			try:
				group = instances_wheelGroups[object_placements[i]]
			except:
				continue
			mpWheelAllocateSpace[object_placements[i]] = first_wheel_pointer + muNumWheelParts*0x4
			
			is_spinnable = ''
			for j, instance in enumerate(group):
				is_spinnable += str(instance[1][2])
				mResourceIds.append(instance[1][0])
				muOffsets.append(mpWheelAllocateSpace[object_placements[i]] + j*0x4)
			
			is_spinnable = is_spinnable[::-1]
			spinnable_models[object_placements[i]] = int(is_spinnable, 2)
			maNumWheelParts[object_placements[i]] = len(group)
			#wheels_offset[object_placements[i]] = list(group[0][1][1][0].transposed().translation)[::-1]
			wheels_offset[object_placements[i]] = list(group[0][1][1][0].transposed().translation)
			
			muNumWheelParts += len(group)
		
		mpResourceIds = first_wheel_pointer + muNumWheelParts*0x4
		mpResourceIds += calculate_padding(mpResourceIds, 0x10)
	
	if len(instances) > 4:
		mppModels = mpResourceIds
		mpResourceIds += len(instances)*0x4
		mpResourceIds += calculate_padding(mpResourceIds, 0x10)
	
	with open(graphicsspec_path, "wb") as f:
		f.write(header_data)
		#f.write(wheel_allocate_space)
		f.seek(mpResourceIds, 0)
		f.write(resources_up_data)
		for i, instance in enumerate(instances):
			mModelId = instance[1][0]
			f.write(id_to_bytes(mModelId))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', mppModels + i*0x4))
			f.write(struct.pack('<i', 0))
		f.write(resources_down_data)
		f.seek(0x0, 0)
		f.write(struct.pack('<I', mppModels))
		f.seek(0x10, 0)
		f.write(struct.pack('<B', len(instances)))
		
		f.seek(0, 2)
		if len(instances_wheelGroups) > 0:
			#instances_wheelGroups[object_placement].append([object_index, [mModelId, [mTransform], is_spinnable, object_placement]])
			#{"FR", [[object_index, [mModelId, [mTransform], is_spinnable, object_placement]], [object_index, [mModelId, [mTransform], is_spinnable, object_placement]]]
			
			# Erasing original wheel data in order to avoid using them in case len(instances_wheelGroups) < 4
			for i in range(0, 4):
				f.seek(mpWheelsData + 0x90*i + 0x78, 0)
				f.write(struct.pack('<I', first_wheel_pointer))
				f.write(struct.pack('<B', 0))
				f.seek(0x3, 1)
				f.write(struct.pack('<B', 0))
				
			#for i in range(0, len(instances_wheelGroups)):
			for i in range(0, 4):
				f.seek(mpWheelsData + 0x90*i, 0)
				try:
					
					f.write(struct.pack('<3f', *wheels_offset[object_placements[i]]))
					f.write(struct.pack('<f', 0.0))
					f.seek(0x68, 1)
					f.write(struct.pack('<I', mpWheelAllocateSpace[object_placements[i]]))
					f.write(struct.pack('<B', spinnable_models[object_placements[i]]))
					f.seek(0x3, 1)
					f.write(struct.pack('<B', maNumWheelParts[object_placements[i]]))
				except:
					continue
				
			f.seek(0, 2)
			for mResourceId, muOffset in zip(mResourceIds, muOffsets):
				f.write(id_to_bytes(mResourceId))
				f.write(struct.pack('<i', 0))
				f.write(struct.pack('<I', muOffset))
				f.write(struct.pack('<i', 0))
		
		else:
			f.write(resouces_wheel)
		
		if len(instance_collision) > 0:
			f.seek(mpResourceIds, 0)
			f.seek(mpPolygonSoupListId_relative, 1)
			f.write(id_to_bytes(instance_collision[0]))
	
	return (0, mPolygonSoupListId)


def edit_graphicsspec_effects(graphicsspec_path, instances_effects):
	if os.path.isfile(graphicsspec_path) == False:
		return 1
	
	with open(graphicsspec_path, "rb") as f:
		file_size = os.path.getsize(graphicsspec_path)
		
		mppModels = struct.unpack("<I", f.read(0x4))[0]
		f.seek(0xC, 0)
		mpWheelsData = struct.unpack("<I", f.read(0x4))[0]
		muPartsCount = struct.unpack("<B", f.read(0x1))[0]
		
		f.seek(0x1C, 0)
		effects_count = struct.unpack("<I", f.read(0x4))[0]
		mpEffectsId = struct.unpack("<I", f.read(0x4))[0]
		mpEffectsTable = struct.unpack("<I", f.read(0x4))[0]
		
		mpWheelAllocateSpace = []
		mNumWheelParts = 0
		for i in range(0, 4):
			f.seek(mpWheelsData + 0x90*i + 0x78, 0)
			mpWheelAllocateSpace.append(struct.unpack("<I", f.read(0x4))[0])
			spinnable_models = struct.unpack("<B", f.read(0x1))[0]
			f.seek(0x3, 1)
			mNumWheelParts += struct.unpack("<B", f.read(0x1))[0]
			f.seek(0x1, 1)
			object_placement = f.read(0xE).split(b'\x00')[0]
			object_placement = str(object_placement, 'ascii').lower()
		
		first_wheel_pointer = min(mpWheelAllocateSpace)
		
		f.seek(0x0, 0)
		data_up = f.read(file_size - mpEffectsId)
		
		f.seek(first_wheel_pointer, 0)
		data = f.read(file_size - first_wheel_pointer)
	
	if len(instances_effects) != effects_count:
		print("ERROR: number of effect objects %d is different than the original model data %d. Effects will not be exported." % (len(instances_effects), effects_count))
		return 1
	
	effects_count = len(instances_effects)
	mpEffectsId = mpEffectsId
	mpEffectsTable = mpEffectsTable
	
	mpEffect0 = mpEffectsTable + 0xC*effects_count
	mpEffect0 += calculate_padding(mpEffect0, 0x10)
	
	mpEffects = []
	mpEffect = mpEffect0
	effect_copies_previous = 0
	num_effects_data = 0
	for i in range(0, effects_count):
		_, _, effect_copies = instances_effects[i]
		mpEffect = mpEffect + 0x20*effect_copies_previous
		effect_copies_previous = len(effect_copies)
		mpEffects.append(mpEffect)
		
		has_unknow_value = any(value[-1] is not None for value in effect_copies)
		if has_unknow_value == True:
			num_effects_data += len(effect_copies)
	
	# Fixing pointers
	first_wheel_pointer_fixed = mpEffects[-1] + 0x20*effect_copies_previous + num_effects_data*0x4
	first_wheel_pointer_fixed += calculate_padding(first_wheel_pointer_fixed, 0x10)
	delta_pointer = first_wheel_pointer_fixed - first_wheel_pointer
	for i in range(0, 4):
		mpWheelAllocateSpace[i] += delta_pointer
	
	muOffsets_Wheels = []
	for i in range(0, mNumWheelParts):
		muOffsets_Wheels.append(first_wheel_pointer_fixed + 0x4*i)
	
	muOffsets_Models = []
	if mppModels >= first_wheel_pointer:
		mppModels += delta_pointer
		for i in range(0, muPartsCount):
			muOffsets_Models.append(mppModels + 0x4*i)
	
	mpResourceIds = first_wheel_pointer_fixed + mNumWheelParts*0x4
	mpResourceIds += calculate_padding(mpResourceIds, 0x10)
	if mppModels >= first_wheel_pointer:
		mpResourceIds += muPartsCount*0x4
		mpResourceIds += calculate_padding(mpResourceIds, 0x10)
	
	k = 0
	with open(graphicsspec_path, "wb") as f:
		f.write(data_up)
		
		f.seek(0x0, 0)
		f.write(struct.pack('<I', mppModels))
		f.write(struct.pack('<I', 0))
		f.write(struct.pack('<I', 0))
		f.write(struct.pack('<I', mpWheelsData))
		f.write(struct.pack('<B', muPartsCount))
		
		f.seek(0x1C, 0)
		f.write(struct.pack('<I', effects_count))
		f.write(struct.pack('<I', mpEffectsId))
		f.write(struct.pack('<I', mpEffectsTable))
		
		for i in range(0, 4):
			f.seek(mpWheelsData + 0x90*i + 0x78, 0)
			f.write(struct.pack('<I', mpWheelAllocateSpace[i]))
		
		for i in range(0, effects_count):
			EffectId, effect_index_, effect_copies = instances_effects[i]
			effect_count = len(effect_copies)
			unknown_pointer = 0
			
			has_unknow_value = any(value[-1] is not None for value in effect_copies)
			if has_unknow_value == True:
				unknown_pointer = mpEffects[-1] + 0x20*effect_copies_previous + k*0x4
				k += effect_count
			
			#for j in range(0, effect_count):
			#	print(effect_copies[j][-1])
			#	if effect_copies[j][-1] != None:
			#		unknown_pointer = mpEffects[-1] + 0x20*effect_copies_previous + k*0x4		#0x4? found in a car
			#		k += effect_count
			#		break
			
			f.seek(mpEffectsId + 0x4*i, 0)
			f.write(struct.pack('<i', EffectId))
			
			f.seek(mpEffectsTable + 0xC*i, 0)
			f.write(struct.pack('<i', effect_count))
			f.write(struct.pack('<i', mpEffects[i]))
			f.write(struct.pack('<i', unknown_pointer))
			
			for j in range(0, effect_count):
				f.seek(mpEffects[i] + 0x20*j, 0)
				f.write(struct.pack('<ffff', *effect_copies[j][1][1]))
				f.write(struct.pack('<fff', *effect_copies[j][1][0]))
				f.write(struct.pack('<f', 0.0))
			
				if has_unknow_value == True:
					f.seek(unknown_pointer + j*0x4, 0)
					f.write(struct.pack('<i', effect_copies[j][-1]))
		
		f.seek(first_wheel_pointer_fixed, 0)
		f.write(data)
		
		f.seek(mpResourceIds, 0)
		f.seek(0x20, 1)
		if mppModels >= first_wheel_pointer:
			for i in range(0, muPartsCount):
				f.seek(0x8, 1)
				f.write(struct.pack('<I', muOffsets_Models[i]))
				f.seek(0x4, 1)
		else:
			f.seek(0x10*muPartsCount, 1)
		#print(hex(file_size - (0x20 + 0x10*muPartsCount) - 0x10*mNumWheelParts)
		#f.seek(mpResourceIds + (0x20 + 0x10*muPartsCount) - 0x10*mNumWheelParts, 0)
		f.seek(- 0x10*mNumWheelParts, 2)
		
		for i in range(0, mNumWheelParts):
			f.seek(0x8, 1)
			f.write(struct.pack('<I', muOffsets_Wheels[i]))
			f.seek(0x4, 1)
		
	return 0


def edit_genesysobject1(genesysobject_dir, genesysobject_path, instances_character):
	if os.path.isfile(genesysobject_path) == False:
		return 1
	
	with open(genesysobject_path, "rb") as f:
		#f.seek(0xF0, 0)
		f.seek(-0x8, 2)
		muOffset = struct.unpack("<H", f.read(0x2))[0]
		while muOffset != 0x2C:
			f.seek(-0x12, 1)
			muOffset = struct.unpack("<H", f.read(0x2))[0]
		f.seek(-0xA, 1)
		mResourceId = bytes_to_id(f.read(0x4))
	
	genesysobject_path = os.path.join(genesysobject_dir, mResourceId + ".dat")
	with open(genesysobject_path, "r+b") as f:
		instances_character[1][1] = -instances_character[1][1]
		
		f.seek(0x10, 0)
		f.write(struct.pack('<fff', *instances_character[1]))
		f.seek(0x24, 0)
		#f.write(id_to_bytes(instances_character[0]))
		f.write(struct.pack('<I', instances_character[0]))
	
	return 0


def edit_genesysobject2(genesysobject_dir, genesysobject_path, instances_wheelGroups):
	if os.path.isfile(genesysobject_path) == False:
		return 1
	
	pointers_offset_y = []
	with open(genesysobject_path, "rb") as f:
		# f.seek(0xB40, 0)
		# mResourceId = bytes_to_id(f.read(0x4))
		
		f.seek(os.path.getsize(genesysobject_path) - 0x8, 0)
		check = struct.unpack("<H", f.read(0x2))[0]
		while check != 0x60:
			f.seek(-0x12, 1)
			check = struct.unpack("<H", f.read(0x2))[0]
		f.seek(-0xA, 1)
		mResourceId = bytes_to_id(f.read(0x4))
		
		# Wheel Y offset
		f.seek(-0x10, 2)
		mGenesysObjectId = bytes_to_id(f.read(0x4))
		count = struct.unpack("<i", f.read(0x4))[0]
		while mGenesysObjectId != '9D_27_00_00' or count != 0x01050002:
			f.seek(-0x18, 1)
			mGenesysObjectId = bytes_to_id(f.read(0x4))
			count = struct.unpack("<i", f.read(0x4))[0]
		f.seek(-0x38, 1)
		offset = f.tell()
		
		mu8NumWheels = 4
		for i in range(0, mu8NumWheels):
			f.seek(offset + 0x8 + 0x10*i, 0)
			muOffset = struct.unpack("<H", f.read(0x2))[0]
			pointers_offset_y.append(muOffset + 0x58)
	
	offsetsY = []
	genesysobject2_path = os.path.join(genesysobject_dir, mResourceId + ".dat")
	with open(genesysobject2_path, "r+b") as f:
		f.seek(0x170, 0)
		mu8NumWheels = 4
		for i in range(0, mu8NumWheels):
			f.seek(0x170 + i*0x10, 0)
			mResourceId = bytes_to_id(f.read(0x4))
			_ = struct.unpack("<i", f.read(0x4))[0]
			muOffset = struct.unpack("<H", f.read(0x2))[0]
			_ = struct.unpack("<H", f.read(0x2))[0]
			padding = struct.unpack("<i", f.read(0x4))[0]
			
			genesysobject3_path = os.path.join(genesysobject_dir, mResourceId + ".dat")
			with open(genesysobject3_path, "r+b") as g:
				g.seek(0xC, 0)
				placement_string_pointer = struct.unpack("<i", g.read(0x4))[0]
				placement_string_size = struct.unpack("<i", g.read(0x4))[0]
				g.seek(placement_string_pointer - 0x8, 1)
				placement = g.read(placement_string_size).split(b'\x00')[0]
				placement = str(placement, 'ascii')
				placement = placement.split('.WheelRigidBody')[0].lower()
				
				wheel_data = instances_wheelGroups[placement]
				g.seek(0x38, 0)
				g.write(struct.pack('<f', wheel_data[0][1][1][0].transposed().translation[0]))
				offsetsY.append(wheel_data[0][1][1][0].transposed().translation[1])
			
			if i == 0:
				f.seek(0x8C, 0)
				f.write(struct.pack('<f', wheel_data[0][1][1][0].transposed().translation[2]))
				f.seek(0xD0, 0)
				f.write(struct.pack('<f', wheel_data[0][1][1][0].transposed().translation[2]))
			elif i == 2:
				f.seek(0x94, 0)
				f.write(struct.pack('<f', wheel_data[0][1][1][0].transposed().translation[2]))
				f.seek(0xF8, 0)
				f.write(struct.pack('<f', wheel_data[0][1][1][0].transposed().translation[2]))
	
	with open(genesysobject_path, "r+b") as f:
		mu8NumWheels = 4
		for i in range(0, mu8NumWheels):
			f.seek(pointers_offset_y[i], 0)
			f.write(struct.pack('<f', offsetsY[i]))
	
	return 0


def change_mResourceId_on_file(file_path, mResourceId, mResourceId_new, stop):
	if os.path.isfile(file_path) == False:
		return 1
	
	file_size = os.path.getsize(file_path)
	count = int(file_size/0x4)
	offsets = []
	
	# with open(file_path, "rb") as f:
		# for i in range(0, count):
			# id = bytes_to_id(f.read(0x4))
			# if id == mResourceId:
				# offsets.append(f.tell() - 0x4)
				# if stop == True:
					# break
	
	# with open(file_path, "wb+") as f:
		# for offset in offsets:
			# f.seek(offset, 0)
			# f.write(id_to_bytes(mResourceId_new))
	
	with open(file_path, "rb+") as f:
		for i in range(0, count):
			id = bytes_to_id(f.read(0x4))
			if id == mResourceId:
				f.seek(-0x4, 1)
				f.write(id_to_bytes(mResourceId_new))
				if stop == True:
					break
	
	return 0


def merge_resources_table(ids_table_path, resources_table_path):
	with open(resources_table_path, "rb") as f, open(ids_table_path, "rb") as g:
		f.seek(0x10, 0)
		muResourceEntriesOffset = struct.unpack("<I", f.read(0x4))[0]
		f.seek(0x0, 0)
		header_data = f.read(muResourceEntriesOffset)
		resource_data = f.read()
		append_data = g.read()
		f.seek(0x70, 0)
		text = f.read(0x2A)
	
	with open(resources_table_path, "wb") as f:
		muResourceEntriesOffset += 0x60
		f.write(header_data)
		if text != b'Resources generated by NFSMW 2012 Exporter':
			f.write(b'Resources generated by NFSMW 2012 Exporter 3.0 for Blender by DGIorio')
			f.write(b'...........Hash:.3bb42e1d')
			f.seek(0x10, 0)
			f.write(struct.pack("<I", muResourceEntriesOffset))
			f.seek(muResourceEntriesOffset, 0)
		f.write(append_data)
		f.write(resource_data)
	
	return 0


def remove_resource_from_resources_table(resources_table_path, mResourceId):
	# Header is not edited at this point, number of IDs is not correct
	with open(resources_table_path, "rb") as f:
		file_size = os.path.getsize(resources_table_path)
		header_size = 0x70
		muResourceEntriesCount = int((file_size - header_size) / 0x48)
		muResourceEntryOffset = -1
		for i in range(0, muResourceEntriesCount):
			f.seek(header_size + i*0x48, 0)
			mResourceId_ = bytes_to_id(f.read(0x4))
			if mResourceId_ == mResourceId:
				muResourceEntryOffset = header_size + i*0x48
				f.seek(0, 0)
				resource_data_before = f.read(muResourceEntryOffset)
				f.seek(muResourceEntryOffset + 0x48, 0)
				#resource_data_after = f.read(file_size - (muResourceEntryOffset + 0x48))
				resource_data_after = f.read()
				break
		
	if muResourceEntryOffset != -1:
		with open(resources_table_path, "wb") as f:
			f.write(resource_data_before)
			f.write(resource_data_after)
		

def move_shared_resource(resource_path, mResourceId, shared_resource_dir):
	os.makedirs(os.path.dirname(resource_path), exist_ok = True)
	
	shared_resource = os.path.join(shared_resource_dir, mResourceId + ".dat")
	if os.path.isfile(shared_resource):
		shutil.copy2(shared_resource, resource_path)
	else:
		return 1
	
	return 0


def create_displacementsampler(raster_source_path):
	os.makedirs(os.path.dirname(raster_source_path), exist_ok = True)
	
	with open(raster_source_path, "wb") as f:
		f.write(b'\x44\x44\x53\x20\x7C\x00\x00\x00\x07\x10\x0A\x00\x20\x00\x00\x00')
		f.write(b'\x20\x00\x00\x00\x00\x02\x00\x00\x01\x00\x00\x00\x06\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00')
		f.write(b'\x04\x00\x00\x00\x44\x58\x54\x31\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x10\x40\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		for i in range(0, 87):
			f.write(b'\xE0\x07\xE0\x07\x00\x00\x00\x00')
	
	return 0


def create_blacksampler(raster_source_path):
	os.makedirs(os.path.dirname(raster_source_path), exist_ok = True)
	
	with open(raster_source_path, "wb") as f:
		f.write(b'\x44\x44\x53\x20\x7C\x00\x00\x00\x07\x10\x0A\x00\x10\x00\x00\x00')
		f.write(b'\x10\x00\x00\x00\x80\x00\x00\x00\x01\x00\x00\x00\x05\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00')
		f.write(b'\x04\x00\x00\x00\x44\x58\x54\x31\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x10\x40\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		for i in range(0, 17):
			f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
	
	return 0


def convert_texture_to_dxt5(raster_path, make_backup):
	if make_backup == True:
		shutil.copy2(raster_path, raster_path + ".bak")
	out_raster_path = os.path.splitext(raster_path)[0] + ".dds"
	nvidia_path = nvidiaGet()
	
	compress_type = "bc3" # DXT5
	
	os.system('"%s -alpha -%s -silent "%s" "%s""' % (nvidia_path, compress_type, raster_path, out_raster_path))
	
	return out_raster_path


def apply_transfrom(ob, global_rotation, use_location=False, use_rotation=False, use_scale=False):
	mb = ob.matrix_basis
	I = Matrix()
	loc, rot, scale = mb.decompose()
	
	euler = Euler(map(math.radians, global_rotation), rot.to_euler().order).to_matrix().to_4x4()
	
	# rotation
	T = Matrix.Translation(loc)
	#R = rot.to_matrix().to_4x4()
	R = mb.to_3x3().normalized().to_4x4()
	S = Matrix.Diagonal(scale).to_4x4()

	transform = [I, I, I]
	#basis = [T, R, S]
	
	basis = [T, euler, S]
	

	def swap(i):
		transform[i], basis[i] = basis[i], transform[i]

	if use_location:
		swap(0)
	if use_rotation:
		swap(1)
	if use_scale:
		swap(2)

	M = transform[0] @ transform[1] @ transform[2]
	if hasattr(ob.data, "transform"):
		ob.data.transform(M)
	for c in ob.children:
		c.matrix_local = M @ c.matrix_local

	ob.matrix_basis = basis[0] @ basis[1] @ basis[2]


def convert_triangle_to_strip(TriangleList):
	TriangleStrip = []
	cte = 0
	for i, Triangle in enumerate(TriangleList):
		if i == 0:
			a, b, c = Triangle
			TriangleStrip.extend([a,b,c])
		else:
			PreviousTriangle = TriangleList[i-1]
			a, b, c = Triangle
			if (i+cte)%2==0:
				if a != PreviousTriangle[0] or b != PreviousTriangle[2]:
					TriangleStrip.extend([0xFFFF, a, b, c])
					cte += 0
				else:
					TriangleStrip.append(c)
			else:
				if a != PreviousTriangle[2] or b != PreviousTriangle[1]:
					TriangleStrip.extend([0xFFFF, a, b, c])
					cte += -1
				else:
					TriangleStrip.append(c)
	return (TriangleStrip)


def calculate_packed_normals(normal):
	normal = np.asarray(normal)
	
	nx = normal[0]
	ny = normal[1]
	nz = normal[2]
	
	packed_normal = [0.0, 0.0, 1.0, 0.0]
	if nx == 0.0 and ny == 0.0:
		if nz < 0.0:
			packed_normal[0] = 1.0
			packed_normal[1] = 0.0
			packed_normal[2] = 0.0
	
	elif math.sqrt(nx*nx + ny*ny + nz*nz) == -nz:		# 1e-5 rounds to zero
		if nz < 0.0:
			packed_normal[0] = 1.0
			packed_normal[1] = 0.0
			packed_normal[2] = 0.0
	
	else:
		#signal = 1.0 if math.sqrt(nx*nx + ny*ny) >= 0.0 else -1.0
		const = 1.0/(nz + math.sqrt(nx*nx + ny*ny + nz*nz))
		
		if math.sqrt(nx*nx + ny*ny) < 0.0:
			const = (math.sqrt(nx*nx + ny*ny + nz*nz) - nz)/(nx*nx + ny*ny)
		
		packed_normal[0] = const * nx
		packed_normal[1] = const * ny
	
	#ChebyshevNorm = max(normal, key=abs)
	#if ChebyshevNorm == 0:
	#	packed_normal = [1.0, 0.0, 1.0, 0.0]
	#packed_normal = [nx/ChebyshevNorm, ny/ChebyshevNorm, nz/ChebyshevNorm, 0.0]
	
	#if nz == 0.0:
	#	nz = 1.0
	#packed_normal = [nx/nz, ny/nz, 1.0, 0.0]
	
	# Normalize
	length = 0
	
	for norm in packed_normal:
		length += norm*norm
	
	length = math.sqrt(length)
	for i, norm in enumerate(packed_normal):
		norm /= length
		if norm == 1:
			norm = 0x7FFF
		else:
			norm *= 0x8000
		packed_normal[i] = np.short(norm)
		
	return packed_normal


def calculate_tangents(indices_buffer, mesh_vertices_buffer):
	tan1 = {}
	tan2 = {}
	
	for face in indices_buffer:
		i1 = face[0]
		i2 = face[1]
		i3 = face[2]
		
		v1 = mesh_vertices_buffer[i1][1]
		v2 = mesh_vertices_buffer[i2][1]
		v3 = mesh_vertices_buffer[i3][1]
		
		w1 = mesh_vertices_buffer[i1][5]
		w2 = mesh_vertices_buffer[i2][5]
		w3 = mesh_vertices_buffer[i3][5]
		
		x1 = v2[0] - v1[0]
		x2 = v3[0] - v1[0]
		y1 = v2[1] - v1[1]
		y2 = v3[1] - v1[1]
		z1 = v2[2] - v1[2]
		z2 = v3[2] - v1[2]
		
		s1 = w2[0] - w1[0]
		s2 = w3[0] - w1[0]
		t1 = w2[1] - w1[1]
		t2 = w3[1] - w1[1]
		
		try:
			r = 1.0/(s1*t2 - s2*t1)
		except:
			#r = 0.0
			r = 1.0
		
		sdir = [(t2 * x1 - t1 * x2) * r, (t2 * y1 - t1 * y2) * r, (t2 * z1 - t1 * z2) * r]
		tdir = [(s1 * x2 - s2 * x1) * r, (s1 * y2 - s2 * y1) * r, (s1 * z2 - s2 * z1) * r]
		
		try:
			_ = tan1[i1]
			_ = tan2[i1]
		except:
			tan1[i1] = [0.0, 0.0, 0.0]
			tan2[i1] = [0.0, 0.0, 0.0]
		
		try:
			_ = tan1[i2]
			_ = tan2[i2]
		except:
			tan1[i2] = [0.0, 0.0, 0.0]
			tan2[i2] = [0.0, 0.0, 0.0]
		
		try:
			_ = tan1[i3]
			_ = tan2[i3]
		except:
			tan1[i3] = [0.0, 0.0, 0.0]
			tan2[i3] = [0.0, 0.0, 0.0]
		
		
		tan1[i1] = list(map(float.__add__, tan1[i1], sdir))
		tan1[i2] = list(map(float.__add__, tan1[i2], sdir))
		tan1[i3] = list(map(float.__add__, tan1[i3], sdir))
		
		tan2[i1] = list(map(float.__add__, tan2[i1], tdir))
		tan2[i2] = list(map(float.__add__, tan2[i2], tdir))
		tan2[i3] = list(map(float.__add__, tan2[i3], tdir))
	
	import warnings
	with warnings.catch_warnings():
		warnings.filterwarnings("ignore", message="invalid value encountered in true_divide")
		for index, vertex in mesh_vertices_buffer.items():
			n = np.asarray(vertex[2])
			t = np.asarray(tan1[index])
			
			#if use_Rotation:
			#	n = np.asarray([n[0], n[2], -n[1]])
			
			# Gram-Schmidt orthogonalize
			tmp = t - n* np.dot(n, t)
			tmp = tmp/np.linalg.norm(tmp)
			
			if np.any(np.isnan(tmp)):
				tmp = [0.0, 0.0, 1.0]
			
			# Calculate handedness
			t_2 = np.asarray(tan2[index])
			signal = -1.0 if (np.dot(np.cross(n, t), t_2) < 0.0) else 1.0
			
			mesh_vertices_buffer[index][3] = tmp[:]
			
			#binormal = np.cross(n, t) #bad result
			binormal = np.cross(t, n)
			binormal = binormal/np.linalg.norm(binormal)
			mesh_vertices_buffer[index][13] = binormal[:]
			
			#tangents[a][0] = signal*tmp[0]
			#tangents[a][1] = signal*tmp[1]
			#tangents[a][2] = signal*tmp[2]
			
			#tangents[a][0] =  tmp[0]
			#tangents[a][1] =  tmp[2]
			#tangents[a][2] = -tmp[1]
	
	return 0


def calculate_mpPolySoup(miNumPolySoups, mpaPolySoupBoxesEnd):
	mpPolySoup = mpaPolySoupBoxesEnd
	for i in range(0, math.ceil(miNumPolySoups/4)):
		mpPolySoup += 0x150
	return int(mpPolySoup)


def get_vertex_semantic(semantic_type):
	semantics = ["", "POSITION", "POSITIONT", "NORMAL", "COLOR",
				 "TEXCOORD1", "TEXCOORD2", "TEXCOORD3", "TEXCOORD4", "TEXCOORD5", "TEXCOORD6", "TEXCOORD7", "TEXCOORD8",
				 "BLENDINDICES", "BLENDWEIGHT", "TANGENT", "BINORMAL", "COLOR2", "PSIZE"]
	
	return semantics[semantic_type]


def get_vertex_data_type(data_type):
	data_types = {2 : ["4f", 0x10],
				  3 : ["4I", 0x10],
				  4 : ["4i", 0x10],
				  6 : ["3f", 0xC],
				  7 : ["3I", 0xC],
				  8 : ["3i", 0xC],
				  10 : ["4e", 0x8], # numpy
				  11 : ["4H", 0x8], #normalized
				  12 : ["4I", 0x10],
				  13 : ["4hnorm", 0x8], #normalized
				  14 : ["4i", 0x10],
				  16 : ["2f", 0x8],
				  17 : ["2I", 0x8],
				  18 : ["2i", 0x8],
				  28 : ["4B", 0x4], #normalized
				  30 : ["4B", 0x4],
				  32 : ["4b", 0x4],
				  34 : ["2e", 0x4],
				  35 : ["2H", 0x4], #normalized
				  36 : ["2H", 0x4],
				  37 : ["2h", 0x4], #normalized
				  38 : ["2h", 0x4],
				  40 : ["1f", 0x4],
				  41 : ["1f", 0x4],
				  42 : ["1I", 0x4],
				  43 : ["1i", 0x4],
				  49 : ["2B", 0x2], #normalized
				  50 : ["2B", 0x2],
				  51 : ["2b", 0x2], #normalized
				  52 : ["2b", 0x2],
				  54 : ["1e", 0x2],
				  57 : ["1H", 0x2],
				  59 : ["1h", 0x2],
				  61 : ["1B", 0x1], #normalized
				  62 : ["1B", 0x1],
				  63 : ["1b", 0x1], #normalized
				  64 : ["1b", 0x1]}
	
	return data_types[data_type]


def get_raster_format(fourcc):
	format_from_fourcc = {	"B8G8R8A8" : 21,
							"R8G8B8A8" : 28,
							"A8R8G8B8" : 255,
							"DXT1" : 71,
							"DXT3" : 73,
							"DXT5" : 77}
	
	try:
		return format_from_fourcc[fourcc]
	except:
		print("WARNING: DXT compression not identified. Setting as 'R8G8B8A8'")
		return 28


def get_mShaderID(shader_description, resource_type):	#ok
	shaders = {	'WorldPBR_Horizontal_VertexLit_Normal_Reflective_AO_Singlesided': '00_87_0F_00',
				'World_UVScrolling_Specular_Illuminance_Singlesided': '02_87_0F_00',
				'Blit2d_ViewGBufferSpecular': '02_E0_05_00',
				'Blit2d_ToRGBM': '05_E0_05_00',
				'WorldPBR_Building_PersistentLitWindows_InstanceAO_Singlesided_Lightmap': '06_D1_0D_00',
				'VehicleNFS13_Body_Driver': '08_15_1F_00',
				'WorldPBR_Building_LitWindows_InstanceAO_Singlesided_Lightmap': '0A_D1_0D_00',
				'World_GbufferBlend_Singlesided': '0B_85_0F_00',
				'TiledLighting_CopMulti4_WORLD1_CAR1': '0B_EC_09_00',
				'TiledLighting_CopMulti4_WORLD1_CAR0': '0D_EC_09_00',
				'VfxSplatter_Dynamic_Opaque': '0E_09_18_00',
				'WorldPBR_Diffuse_Normal_InstanceAO_Lightmap_Singlesided': '0E_D1_0D_00',
				'TiledLighting_CopMulti4_WORLD0_CAR1': '0F_EC_09_00',
				'TiledLighting_CopMulti3_WORLD1_CAR1': '11_EC_09_00',
				'VfxParticles_UVDistortion': '12_7E_0F_00',
				'Chevron': '13_78_00_00',
				'TiledLighting_CopMulti3_WORLD1_CAR0': '13_EC_09_00',
				'Deflicker_World_Diffuse_Specular_Overlay_Illuminance_Singlesided': '15_78_00_00',
				'TiledLighting_CopMulti3_WORLD0_CAR1': '15_EC_09_00',
				'Deflicker_World_Diffuse_Specular_Singlesided': '17_78_00_00',
				'TiledLighting_CopMulti2_WORLD1_CAR1': '17_EC_09_00',
				'VehicleNFS13_Body_Textured_NoDamage_NoEffects': '18_99_10_00',
				'TiledLighting_CopMulti2_WORLD1_CAR0': '19_EC_09_00',
				'WorldShadow_Opaque_Singlesided': '1A_0E_08_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Lightmap_Singlesided': '1B_14_07_00',
				'TiledLighting_CopMulti2_WORLD0_CAR1': '1B_EC_09_00',
				'WorldShadow_Opaque_Doublesided': '1C_0E_08_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Lightmap_Singlesided': '1D_14_07_00',
				'World_Diffuse_Specular_Illuminance_Singlesided_InstanceAdditive': '1D_85_0F_00',
				'TiledLighting_CopMulti1_WORLD1_CAR1': '1D_EC_09_00',
				'PlotPBR_AO_Normal_Specular_Opaque_Lightmap_Singlesided': '1F_14_07_00',
				'TiledLighting_CopMulti1_WORLD1_CAR0': '1F_EC_09_00',
				'TiledLighting_CopMulti1_WORLD0_CAR1': '21_EC_09_00',
				'PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Lightmap_Singlesided': '22_14_07_00',
				'WorldPBR_Diffuse_AO_Lightmap_1Bit_Doublesided': '22_3C_19_00',
				'Blit2d': '22_79_00_00',
				'Blit2d_AlphaAsColour': '23_79_00_00',
				'World_Diffuse_Specular_Singlesided_InstanceAdditive': '23_85_0F_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Singlesided': '23_A7_06_00',
				'UIParticleShader': '24_2F_16_00',
				'Blit2d_AutomaticExposureMeter': '24_79_00_00',
				'WorldPBR_Diffuse_AO_1Bit_Doublesided': '25_3C_19_00',
				'Blit2d_ClearGBuffer': '25_79_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_ObjectTint_Lightmap_Singlesided': '26_7F_15_00',
				'Vfx_ShadowMapTest': '26_BE_07_00',
				'WorldPBR_Diffuse_AO_1Bit_Singlesided': '27_3C_19_00',
				'Blit2d_GammaCorrection': '27_79_00_00',
				'UINoiseShader': '27_CC_06_00',
				'TerrainPBR_Normal_Opaque_Singlesided': '27_F1_06_00',
				'BlobbyShadow_Greyscale_Doublesided': '29_79_00_00',
				'DriveableSurface_Lightmap': '2A_78_00_00',
				'Cable_GreyScale_Doublesided': '2A_79_00_00',
				'LightBuffer_KeylightAndAmbient_LightingOverrideHdrSphere': '2A_DE_04_00',
				'CatsEyes': '2B_79_00_00',
				'PlotPBR_AO_StandingWater_Opaque_Lightmap_Singlesided': '2B_86_0F_00',
				'CatsEyesGeometry': '2C_79_00_00',
				'Character_Greyscale_Textured_Doublesided_Skin': '2E_79_00_00',
				'DriveableSurface_DEPRECATED_RetroreflectivePaint_Lightmap': '2F_78_00_00',
				'Character_Opaque_Textured_NormalMap_SpecMap_Skin': '2F_79_00_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_Doublesided': '2F_86_0F_00',
				'VfxParticles_DiffusePremultiplied_NoAlphaTest': '30_09_18_00',
				'PlotPBR_AO_Normal_Specular_Opaque_Singlesided': '30_13_07_00',
				'VfxParticles_CubeMap_GradientRemap': '31_2A_06_00',
				'ChevronBlockRoad': '31_79_00_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_1Bit_Doublesided': '31_86_0F_00',
				'Fence_GreyScale_Doublesided': '32_78_00_00',
				'WorldPBR_Horizontal_PlanarReflection_VertexLit_Singlesided': '32_87_0F_00',
				'DebugIrradiance_1Bit_Singlesided_2d': '33_79_00_00',
				'Flag_UVFlip_Opaque_Doublesided': '33_86_0F_00',
				'Deflicker_WorldPBR_Emissive_Diffuse_Normal_Specular_Reflective_AO_Singlesided': '34_13_07_00',
				'Flag_Opaque_Doublesided': '34_78_00_00',
				'Diffuse_1Bit_Doublesided': '34_79_00_00',
				'WorldPBR_Horizontal_PlanarReflection_VertexLit_Lightmap_Singlesided': '34_87_0F_00',
				'KeyLightInScattering': '34_EC_09_00',
				'Water_Opaque_Singlesided': '35_0E_08_00',
				'DriveableSurface_FloatingDecal': '35_A7_06_00',
				'Diffuse_1Bit_Doublesided_Skin': '36_79_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Doublesided': '37_0E_08_00',
				'DriveableSurface_FloatingDecal_1Bit': '37_A7_06_00',
				'FogAndBlurredKeyLightInScattering': '37_EC_09_00',
				'Diffuse_1Bit_Singlesided': '38_79_00_00',
				'Glass_Greyscale_Doublesided': '39_0B_08_00',
				'WorldPBR_FloatingDecal_RetroReflectivePaint_Normal_Specular_Reflective_AO_1Bit_Singlesided': '39_A7_06_00',
				'HelicopterRotor_GreyScale_Doublesided': '3B_78_00_00',
				'WorldPBR_FloatingDecal_Diffuse_Normal_Specular_Reflective_AO_Singlesided': '3B_A7_06_00',
				'Diffuse_Opaque_Singlesided': '3C_79_00_00',
				'BlurKeyLightInScattering': '3C_EC_09_00',
				'WorldPBR_FloatingDecal_Diffuse_Normal_Specular_Reflective_AO_1Bit_Singlesided': '3D_A7_06_00',
				'Diffuse_Opaque_Singlesided_Skin': '3E_79_00_00',
				'World_Diffuse_Specular_PersistentIlluminance_Singlesided': '3F_EB_0F_00',
				'BlurKeyLightInScattering2': '3F_EC_09_00',
				'Sign_RetroReflective': '40_78_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_PersistentLightmap_Singlesided': '41_86_0F_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_PersistentLightmap_Singlesided': '41_EB_0F_00',
				'Blit2d_DepthOnly': '42_2A_13_00',
				'Tree_Translucent_1Bit_Doublesided_InstanceTint': '43_78_00_00',
				'DriveableSurface': '43_79_00_00',
				'DriveableSurface_AlphaMask': '44_79_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Lightmap_Doublesided': '46_45_1C_00',
				'Water_Proto_Cheap': '46_78_00_00',
				'DriveableSurface_Decal': '46_79_00_00',
				'DriveableSurface_OBSOLETE_RetroreflectivePaint': '47_79_00_00',
				'DriveableSurface_DEPRECATED_Line_Lightmap_DirectionV': '48_79_00_00',
				'Skin_WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Doublesided': '48_86_0F_00',
				'PlotPBR_Grass_AO_Normal_Opaque_Lightmap_Singlesided': '48_87_0F_00',
				'WorldPBR_Diffuse_Specular_AO_Lightmap_Doublesided': '49_45_1C_00',
				'DriveableSurface_DEPRECATED_Line_DirectionV': '4B_79_00_00',
				'World_Diffuse_Specular_1Bit_Lightmap_Doublesided': '4D_78_00_00',
				'World_Diffuse_Specular_FlashingNeon_Singlesided': '4F_78_00_00',
				'TerrainPBR_Normal_Opaque_Singlesided_Rough': '4F_87_0F_00',
				'World_Diffuse_Specular_Illuminance_Singlesided': '50_78_00_00',
				'FlaptGenericShader': '51_79_00_00',
				'ToneMapSetConstants': '51_9F_06_00',
				'FlaptGenericShader3D': '52_79_00_00',
				'PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Lightmap_Singlesided_Rough': '53_87_0F_00',
				'Groundcover': '56_79_00_00',
				'PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Singlesided_Rough': '56_87_0F_00',
				'PlotPBR_Grass_AO_Normal_Opaque_Lightmap_Singlesided_Rough': '58_87_0F_00',
				'Fog': '59_6E_07_00',
				'World_Diffuse_Specular_Singlesided': '59_78_00_00',
				'UISubtractiveShader': '5C_75_0F_00',
				'MapIconShader': '5D_79_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Lightmap_Doublesided': '5D_87_0F_00',
				'MapIconShaderSubtractive': '5E_75_0F_00',
				'NewSky': '5E_79_00_00',
				'UIDepthTestedShader': '5F_74_0C_00',
				'PlanarReflection_DepthBufferConversion_2d': '60_79_00_00',
				'Skin_World_Diffuse_Specular_1Bit_Singlesided': '61_7D_15_00',
				'WorldPBR_Building_PersistentLitWindows_InstanceAO_InstanceTint_Singlesided_Lightmap': '62_87_0F_00',
				'SeparableGaussian_2d': '63_79_00_00',
				'WorldPBR_NormalSpecInMap3_Normal_Specular_Illuminance_AO_Singlesided': '64_AE_19_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_1Bit_Singlesided': '64_CC_12_00',
				'GBufferComposite': '66_78_00_00',
				'TerrainPBR_TangentSpaceNormal_Opaque_Singlesided_Rough': '66_AE_19_00',
				'VehicleNFS13_BodyPaint_TwoPaintMask_Lightmap': '66_EF_09_00',
				'TextAdditiveShader': '68_79_00_00',
				'VehicleNFS13_BodyPaint_TwoPaintMask': '68_EF_09_00',
				'GBufferCompositeNoMotionBlur': '69_78_00_00',
				'TextBoldDropShadow': '69_79_00_00',
				'GBufferCompositeRearViewMirror': '6A_78_00_00',
				'TextBoldShader': '6A_79_00_00',
				'VehicleNFS13_BodyPaint_TwoPaint_Lightmap': '6A_EF_09_00',
				'UIAdditiveDepthTestedShader': '6B_74_0C_00',
				'TextDropShadow': '6B_79_00_00',
				'LightBuffer_Cone': '6C_78_00_00',
				'TextGlow': '6C_79_00_00',
				'VehicleNFS13_BodyPaint_TwoPaint': '6C_EF_09_00',
				'LightBuffer_Cone2': '6D_78_00_00',
				'TextOutline': '6D_79_00_00',
				'LightBuffer_Cone3': '6E_78_00_00',
				'TextShader': '6E_79_00_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_1Bit_Doublesided_Lightmap': '6E_8C_14_00',
				'VehicleNFS13_BodyPaint_NormalMap_NoDamage': '6E_EF_09_00',
				'UIRoadRibbonShader': '6F_2F_16_00',
				'LightBuffer_Cone4': '6F_78_00_00',
				'TriggerShader': '70_79_00_00',
				'VehicleNFS13_BodyPaint_Livery_Lightmap': '70_EF_09_00',
				'LightBuffer_Cop': '71_78_00_00',
				'UIAdditiveOverlayShader': '71_79_00_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_Doublesided_Lightmap': '71_8C_14_00',
				'LightBuffer_Cop2': '72_78_00_00',
				'UIAdditivePixelate': '72_79_00_00',
				'VehicleNFS13_BodyPaint_Livery': '72_EF_09_00',
				'LightBuffer_Cop3': '73_78_00_00',
				'UIAdditiveShader': '73_79_00_00',
				'LightBuffer_Cop4': '74_78_00_00',
				'UIAutologShader': '74_79_00_00',
				'WorldPBR_Building_LitWindows_InstanceAO_InstanceTint_Singlesided_Lightmap': '74_87_0F_00',
				'VehicleNFS13_BodyPaint_Lightmap': '74_EF_09_00',
				'UIFlameShader': '75_79_00_00',
				'LightBuffer_KeylightAndAmbient': '76_78_00_00',
				'VfxParticles_Diffuse_GradientRemap': '76_90_04_00',
				'VehicleNFS13_BodyPaint': '76_EF_09_00',
				'UIGenericAlphaLuminanceShader': '77_79_00_00',
				'PlotPBR_TilingDecal_Opaque_Lightmap_Singlesided_Rough': '77_AE_19_00',
				'LightBuffer_KeylightAndAmbient_NoSpecular': '78_78_00_00',
				'UIGenericDestAlphaModulateShader': '78_79_00_00',
				'VehicleNFS13_Body_Textured_NormalMap_NoDamage': '78_EF_09_00',
				'LightBuffer_KeylightAndAmbient_ProjectedShadowTexture': '79_78_00_00',
				'UIMapShader': '79_79_00_00',
				'WorldPBR_Building_LitWindows_SliderBlend_Reflective_AO_Singlesided_Lightmap': '7A_14_07_00',
				'LightBuffer_KeylightAndAmbient_ProjectedShadowTexture_LowQuality': '7A_78_00_00',
				'UIMovieAdditiveShader': '7A_79_00_00',
				'PlotPBR_TilingDecal_DriveableGrass_Opaque_Lightmap_Singlesided_Rough': '7A_AE_19_00',
				'VehicleNFS13_Body_Textured_NormalMap_LocalEmissive': '7A_EF_09_00',
				'LightBuffer_KeylightAndAmbient_SingleCSM': '7B_78_00_00',
				'UIMovieShader': '7B_79_00_00',
				'LightBuffer_KeylightAndAmbient_SingleCSM_NoSpecular': '7C_78_00_00',
				'UIMovieShaderAddOverlay': '7C_79_00_00',
				'VehicleNFS13_Body_Textured_NormalMap_EmissiveFourChannel_NoDamage_NoEffects': '7C_EF_09_00',
				'WorldPBR_Diffuse_LOD2LitWindows_Singlesided_Lightmap': '7D_14_07_00',
				'LightBuffer_KeylightAndAmbient_NoShadow': '7D_78_00_00',
				'UIMovieShaderSubOverlay': '7D_79_00_00',
				'WorldPBR_Normal_TextureBlend_Reflective_AO_Lightmap_Singlesided': '7D_AE_19_00',
				'LightBuffer_Point': '7E_78_00_00',
				'UIRearViewMirrorShader': '7E_79_00_00',
				'PlotPBR_AO_Normal_Specular_Opaque_Singlesided_Rough': '7E_7C_15_00',
				'WorldPBR_Building_LitWindows_SliderBlend_Reflective_AO_InstanceIntensity_Singlesided_Lightmap': '7E_AE_19_00',
				'VehicleNFS13_Body_Textured_NormalMap_Lightmap': '7E_EF_09_00',
				'LightBuffer_Point2': '7F_78_00_00',
				'World_SmashedBillboard_InstanceDiffuse_Specular_Singlesided': '80_17_14_00',
				'LightBuffer_Point3': '80_78_00_00',
				'PlotPBR_AO_Normal_Specular_Opaque_Lightmap_Singlesided_Rough': '80_7C_15_00',
				'VehicleNFS13_Body_Textured_NormalMap': '80_EF_09_00',
				'LightBuffer_Point4': '81_78_00_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_InstanceIntensity_Lightmap_Singlesided': '82_AE_19_00',
				'VehicleNFS13_Body_Textured_Emissive_NoDamage_NoEffects': '82_EF_09_00',
				'LightBuffer_ProjectedTexture': '83_78_00_00',
				'VfxCorona_DiffusePremultiplied': '84_CC_12_00',
				'VehicleNFS13_Body_Textured_Lightmap': '84_EF_09_00',
				'WorldPBR_Diffuse_LOD2LitWindows_InstanceIntensity_Singlesided_Lightmap': '86_AE_19_00',
				'BilateralBlurSSAO': '86_CC_12_00',
				'VehicleNFS13_Body_Textured': '86_EF_09_00',
				'LightBuffer_VisionModeThermal': '87_BC_07_00',
				'UIDepthTestedScrollingShader': '88_7A_0F_00',
				'VehicleNFS13_Body_Lightmap': '88_EF_09_00',
				'WorldPBR_Diffuse_PersistentLOD2LitWindows_Singlesided': '89_86_0F_00',
				'WorldPBR_Building_PersistentLitWindows_InstanceIntensity_Reflective_AO_Singlesided_Lightmap': '8A_AE_19_00',
				'VehicleNFS13_Body_Alpha1bit_NormalMap_Textured_NoDamage': '8A_EF_09_00',
				'WorldPBR_Building_PersistentLitWindows_Reflective_AO_Singlesided_Lightmap': '8B_86_0F_00',
				'Blit2d_CompressToRGBG': '8B_EB_09_00',
				'VehicleNFS13_Body_Alpha1bit_NormalMap': '8C_EF_09_00',
				'WorldPBR_Building_PersistentLitWindows_Reflective_AO_Singlesided': '8E_86_0F_00',
				'UIPersistentImage_Additive': '8E_EB_09_00',
				'VehicleNFS13_Body_Alpha_NormalMap_Textured_NoDamage': '8E_EF_09_00',
				'WorldPBR_Diffuse_PersistentLOD2LitWindows_Singlesided_Lightmap': '90_86_0F_00',
				'VehicleNFS13_Body_Alpha_NormalMap_DoubleSided': '90_EF_09_00',
				'WorldPBR_Diffuse_Normal_Specular_InstanceTint_Singlesided': '91_7D_15_00',
				'GBufferCompositeVisionModeThermal': '91_BC_07_00',
				'WorldPBR_Building_PersistentLitWindows_InstanceAO_InstanceIntensity_Singlesided_Lightmap': '92_AE_19_00',
				'Blit2d_MaterialId': '92_EB_09_00',
				'VehicleNFS13_Body': '92_EF_09_00',
				'Skin_World_Diffuse_Specular_1Bit_Lightmap_Doublesided': '92_FA_0E_00',
				'WorldPBR_Diffuse_PersistentLOD2LitWindows_InstanceAO_Singlesided': '95_D2_0D_00',
				'Vfx_TyreMarksNew': '96_92_04_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Doublesided_Lightmap': '96_AE_19_00',
				'WorldPBR_Diffuse_LOD2LitWindows_InstanceAO_Singlesided': '98_D2_0D_00',
				'DownsampleMaterialDepthBoundStep1': '98_EB_09_00',
				'Blit2d_LinearToGammaWithMipChoice': '99_D4_10_00',
				'UIRibbonShader': '9A_7C_0F_00',
				'VfxParticles_Wireframe_Pretransformed': '9B_08_18_00',
				'WorldPBR_Diffuse_LOD2LitWindows_InstanceAO_Singlesided_Lightmap': '9B_D2_0D_00',
				'DownsampleMaterialDepthBound': '9B_EB_09_00',
				'VehicleNFS13_Body_Textured_NormalMap_Emissive_NoDamage_NoEffects': '9B_EF_09_00',
				'VehicleNFS13_Body_Textured_NormalMap_Lightmap_Licenseplate': '9C_D4_10_00',
				'VfxParticles_Wireframe': '9D_08_18_00',
				'Skin_WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Singlesided': '9E_09_09_00',
				'TextureMemoryExport': '9E_EB_09_00',
				'VehicleNFS13_Refraction': 'A1_EF_09_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_Singlesided': 'A2_0D_08_00',
				'TiledLightingPointLightsVisibility': 'A2_EB_09_00',
				'VehicleNFS13_Glass_Textured': 'A3_EF_09_00',
				'VfxSplatter_Overlay': 'A5_08_18_00',
				'VehicleNFS13_Glass_Doublesided': 'A5_EF_09_00',
				'PostFX_FisheyeHeatHaze': 'A6_D4_10_00',
				'WorldPBR_Building_LitWindows_ColouredSpecular_Reflective_AO_Singlesided': 'A7_0D_08_00',
				'VehicleNFS13_Glass_Textured_Lightmap': 'A7_EF_09_00',
				'TiledLightingSpotLightsVisibility': 'A8_EB_09_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Singlesided_InstanceAdditive': 'A9_55_1D_00',
				'VehicleNFS13_Glass': 'A9_EF_09_00',
				'World_UVScrolling_Normal_Specular_1Bit_Singlesided': 'AA_45_1C_00',
				'CharacterNew_Opaque_Textured_Normal_Spec_VertexAO': 'AA_D4_10_00',
				'TiledLightingPointLights': 'AB_EB_09_00',
				'VehicleNFS13_Glass_Colourise': 'AB_EF_09_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_PersistentLightmap_Singlesided': 'AC_7D_15_00',
				'DebugKeylightPlusIrradiance_1Bit_Singlesided_2d': 'AD_D4_10_00',
				'World_Diffuse_Specular_FlashingNeon_1_Bit_Singlesided': 'AE_13_07_00',
				'Blit2d_SwizzledDepthStencilToRGBA': 'AE_EB_09_00',
				'Vfx_Corona': 'AF_79_00_00',
				'DebugKeylight_1Bit_Singlesided_2d': 'AF_D4_10_00',
				'Vfx_CoronaFlare': 'B0_79_00_00',
				'Vfx_CoronaVisibilityTest': 'B1_79_00_00',
				'DebugCubemap_1Bit_Singlesided_2d': 'B1_D4_10_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD1_CAR1': 'B1_EB_09_00',
				'PlotPBR_RGBDecal_Normal_Specular_Opaque_Lightmap_Singlesided_Rough': 'B2_55_1D_00',
				'VfxMesh': 'B3_79_00_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD1_CAR0': 'B3_EB_09_00',
				'VehicleNFS13_Wheel_Textured_Normalmap_Blurred': 'B3_EF_09_00',
				'VfxMeshCarPaint': 'B4_79_00_00',
				'TextDropShadowDepthTested': 'B4_7A_0F_00',
				'VfxMeshNormalMap': 'B5_79_00_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD0_CAR1': 'B5_EB_09_00',
				'VehicleNFS13_Wheel_Textured_Roughness': 'B5_EF_09_00',
				'VfxParticles_Diffuse_SubUV': 'B6_79_00_00',
				'VfxParticles_Diffuse': 'B7_79_00_00',
				'DriveableSurface_Lightmap_PlanarReflection': 'B8_33_23_00',
				'VfxParticles_Diffuse_AlphaErosion': 'B8_79_00_00',
				'VehicleNFS13_Wheel_Alpha_Textured_Normalmap_Blurred_Doublesided_PixelAO': 'B9_EF_09_00',
				'VfxParticles_DiffusePremultiplied': 'BA_79_00_00',
				'Glass_Interior_Greyscale_Singlesided': 'BB_33_23_00',
				'VehicleNFS13_Wheel_Tyre_Textured_Normalmap_Blurred': 'BB_5F_0F_00',
				'VfxParticles_DiffusePremultiplied_SubUV': 'BB_79_00_00',
				'Tree_Translucent_1Bit_Doublesided': 'BB_D4_10_00',
				'VehicleNFS13_Wheel_Alpha_Textured_Normalmap_BlurFade': 'BB_EF_09_00',
				'VfxParticles_MotionBlurSpriteUntex': 'BC_79_00_00',
				'Glass_Exterior_Greyscale_Singlesided': 'BD_33_23_00',
				'VehicleNFS13_Wheel_Alpha_Textured_Normalmap': 'BD_EF_09_00',
				'TiledLighting_PointMulti_WORLD0_CAR1': 'BE_EB_09_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_InstanceAO_Lightmap_Singlesided': 'BF_E1_13_00',
				'VehicleNFS13_Wheel_Alpha1bit_Normalmap': 'BF_EF_09_00',
				'TiledLighting_PointMulti_WORLD1_CAR1': 'C0_EB_09_00',
				'TiledLighting_PointMulti_WORLD1_CAR0': 'C2_EB_09_00',
				'VfxSplatter_Dynamic': 'C4_08_18_00',
				'DriveableSurface_Decal_Lightmap': 'C5_C9_12_00',
				'VehicleNFS13_BodyPaint_TwoPaint_Livery_Lightmap': 'C6_EF_09_00',
				'UIStretched': 'C7_77_0F_00',
				'WorldPBR_Normal_TextureBlend_Reflective_AO_Singlesided': 'C8_81_06_00',
				'VehicleNFS13_BodyPaint_TwoPaint_Livery': 'C8_EF_09_00',
				'LinearizeDepth': 'C9_41_08_00',
				'TiledLighting_SpotMulti_WORLD1_CAR1': 'C9_EB_09_00',
				'WorldPBR_Building_LitWindows_SliderBlend_Reflective_AO_Singlesided': 'CB_13_07_00',
				'ComputeHBAO': 'CB_41_08_00',
				'TiledLighting_SpotMulti_WORLD1_CAR0': 'CB_EB_09_00',
				'Skin_World_Diffuse_Specular_Singlesided': 'CC_0A_08_00',
				'TiledLighting_SpotMulti_WORLD0_CAR1': 'CD_EB_09_00',
				'Blit2d_AllChannels': 'CF_41_08_00',
				'TiledLighting_CopMulti_WORLD1_CAR1': 'CF_EB_09_00',
				'TiledLighting_CopMulti_WORLD1_CAR0': 'D1_EB_09_00',
				'TextShaderDepthTested': 'D2_7A_0F_00',
				'TiledLighting_CopMulti_WORLD0_CAR1': 'D3_EB_09_00',
				'World_Weapon_Diffuse_Specular_Singlesided': 'D5_16_14_00',
				'Vfx_Weapon_TeflonSlick': 'D6_BD_07_00',
				'Skin_Weapon_World_Diffuse_Specular_Singlesided': 'D7_16_14_00',
				'LightBuffer_Spot4': 'DA_41_08_00',
				'WorldPBR_Diffuse_LOD2LitWindows_Singlesided': 'DB_11_07_00',
				'TiledLightingCopLightsVisibility': 'DB_EB_09_00',
				'LightBuffer_Spot3': 'DC_41_08_00',
				'PlotPBR_DriveableGrass_AO_Normal_Specular_Opaque_Singlesided': 'DE_0A_08_00',
				'LightBuffer_Spot2': 'DE_41_08_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD0_CAR1_SHADOW0': 'DE_EB_09_00',
				'LightBuffer_Spot': 'E0_41_08_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD1_CAR1_SHADOW0': 'E0_EB_09_00',
				'BlitGBufferVITA': 'E1_F2_09_00',
				'TiledLighting_KeylightAndAmbientMain_WORLD1_CAR0_SHADOW0': 'E2_EB_09_00',
				'UIPersistentImage': 'E3_7C_0F_00',
				'TiledLighting_PointMulti4_WORLD1_CAR1': 'E7_EB_09_00',
				'PostAA': 'E8_DF_05_00',
				'TiledLighting_PointMulti4_WORLD1_CAR0': 'E9_EB_09_00',
				'TiledLighting_PointMulti4_WORLD0_CAR1': 'EB_EB_09_00',
				'Blit2d_SimpleColourWrite': 'EC_DF_05_00',
				'TiledLighting_PointMulti3_WORLD1_CAR1': 'ED_EB_09_00',
				'DriveableSurface_FloatingDecal_Lightmap_1Bit': 'EF_56_09_00',
				'TiledLighting_PointMulti3_WORLD1_CAR0': 'EF_EB_09_00',
				'Blit2d_BiCubicH': 'F0_4E_16_00',
				'Blit2d_GeneratePCTonemapConstants_AverageLumaFinal': 'F0_DF_05_00',
				'CombineLdrParticleIntoHdrBuffer': 'F1_90_0B_00',
				'TiledLighting_PointMulti3_WORLD0_CAR1': 'F1_EB_09_00',
				'LightBuffer_Line': 'F2_41_08_00',
				'DriveableSurface_FloatingDecal_Lightmap': 'F2_56_09_00',
				'Blit2d_GeneratePCTonemapConstants_BuildConstant': 'F2_DF_05_00',
				'TiledLighting_PointMulti2_WORLD1_CAR1': 'F3_EB_09_00',
				'Blit2d_GeneratePCTonemapConstants_AverageLuma': 'F4_DF_05_00',
				'LightBuffer_Line3': 'F5_41_08_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Doublesided': 'F5_85_0F_00',
				'TiledLighting_PointMulti2_WORLD1_CAR0': 'F5_EB_09_00',
				'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Singlesided': 'F6_F0_06_00',
				'LightBuffer_Line2': 'F7_41_08_00',
				'TiledLighting_PointMulti2_WORLD0_CAR1': 'F7_EB_09_00',
				'Deflicker_WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Singlesided': 'F8_12_07_00',
				'LightBuffer_Line4': 'F9_41_08_00',
				'FastDepthRestore': 'F9_90_0B_00',
				'MapIconShaderAdditive': 'F9_AA_05_00',
				'WorldPBR_Diffuse_Normal_ColouredSpecular_Reflective_AO_Lightmap_Singlesided': 'F9_D0_0D_00',
				'LightBuffer_KeylightAndAmbient_EnvironmentMap': 'F9_DF_05_00',
				'TiledLighting_PointMulti1_WORLD1_CAR1': 'F9_EB_09_00',
				'Character_GPMM_Glass_Textured_Doublesided_Skin': 'F9_EE_09_00',
				'TiledLighting_PointMulti1_WORLD1_CAR0': 'FB_EB_09_00',
				'FastDepthRestoreFinalTileTouch': 'FC_90_0B_00',
				'VehicleNFS13_Wheel_Alpha1bit_Textured_Normalmap': 'FC_BF_19_00',
				'VfxParticles_Diffuse_SubUV_NoBlend': 'FD_0A_08_00',
				'TiledLighting_PointMulti1_WORLD0_CAR1': 'FD_EB_09_00',
				'Deflicker_WorldPBR_Diffuse_Normal_Specular_Reflective_AO_Doublesided': 'FE_CF_0D_00',
				'LightBuffer_KeylightAndAmbient_DebugLighting': 'FF_DF_05_00'}
	
	# Adding custom shaders
	try:
		shaders.update(custom_shaders())
	except:
		print("WARNING: custom_shaders function not found. Custom data will not be available.")
		shaders['Glass'] = 'A9_EF_09_00'
		shaders['VehicleNFS13_Mirror'] = 'A9_EF_09_00'
		shaders['Mirror'] = 'A9_EF_09_00'
		shaders['VehicleNFS13_Body_Chrome'] = '92_EF_09_00'
		shaders['VehicleNFS13_Chrome'] = '92_EF_09_00'
		shaders['Chrome'] = '92_EF_09_00'
		shaders['VehicleNFS13_Body_Tyre'] = '9B_EF_09_00'
		shaders['VehicleNFS13_Tyre'] = '9B_EF_09_00'
		shaders['Tyre'] = '9B_EF_09_00'
		shaders['Tire'] = '9B_EF_09_00'
		shaders['Licenseplate'] = '7E_EF_09_00'
		shaders['LicensePlate'] = '7E_EF_09_00'
		shaders['License_Plate'] = '7E_EF_09_00'
		shaders['VehicleNFS13_Licenseplate'] = '7E_EF_09_00'
		shaders['VehicleNFS13_License_Plate'] = '7E_EF_09_00'
		shaders['Licenseplate_Number'] = '9C_D4_10_00'
		shaders['License_Plate_Number'] = '9C_D4_10_00'
		shaders['VehicleNFS13_Licenseplate_Number'] = '9C_D4_10_00'
		shaders['VehicleNFS13_License_Plate_Number'] = '9C_D4_10_00'
		shaders['DullPlastic'] = '92_EF_09_00'
		shaders['Dull_Plastic'] = '92_EF_09_00'
		shaders['dullplastic'] = '92_EF_09_00'
		shaders['Interior'] = '9B_EF_09_00'
		shaders['VehicleNFS13_Interior'] = '9B_EF_09_00'
		shaders['Metal'] = '72_EF_09_00'
		shaders['BodyPaint_Livery'] = '72_EF_09_00'
		shaders['BodyPaint'] = '76_EF_09_00'
		shaders['BodyColor'] = '92_EF_09_00'
		shaders['Badge'] = '8A_EF_09_00'
		shaders['Emblem'] = '8A_EF_09_00'
		shaders['Symbol'] = '8A_EF_09_00'
		shaders['Grill'] = '8A_EF_09_00'
		shaders['Transparent'] = '8A_EF_09_00'
		shaders['VehicleNFS13_Caliper'] = 'B5_EF_09_00'
		shaders['Caliper'] = 'B5_EF_09_00'
		shaders['Caliper_Textured'] = 'B5_EF_09_00'
		shaders['VehicleNFS13_BrakeDisc'] = 'B5_EF_09_00'
		shaders['brakedisc'] = 'B5_EF_09_00'
		shaders['BrakeDisc'] = 'B5_EF_09_00'
	
	try:
		mShaderId = shaders[shader_description]
	except:
		mShaderId = ""
		try:
			from difflib import get_close_matches
			shader_description_ = shader_description
			close_shaders = get_close_matches(shader_description, shaders.keys())
			for i in range(0, len(close_shaders)):
				if resource_type == "InstanceList":
					if not close_shaders[i].startswith("VehicleNFS13"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
				elif resource_type == "CharacterSpec":
					if close_shaders[i].startswith("Character"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
				else:
					if close_shaders[i].startswith("VehicleNFS13"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
		except:
			mShaderId = ""
		if mShaderId == "":
			if resource_type == "InstanceList":
				shader_description = 'WorldPBR_Diffuse_Normal_Specular_Reflective_AO_1Bit_Singlesided'
				mShaderId = shaders[shader_description]
			elif resource_type == "GraphicsSpec":
				shader_description = 'VehicleNFS13_BodyPaint_Livery'
				mShaderId = shaders[shader_description]
			elif resource_type == "CharacterSpec":
				shader_description = 'CharacterNew_Opaque_Textured_Normal_Spec_VertexAO'
				mShaderId = shaders[shader_description]
	
	mShaderId = shaders[shader_description]
	return (mShaderId, shader_description)


def resourcetype_to_type_id(resource_type):
	resources_types = {'Texture' : '01_00_00_00',
					   'Material' : '02_00_00_00',
					   'SamplerState' : '07_00_00_00',
					   'Renderable' : '05_00_00_00',
					   'Model' : '51_00_00_00',
					   'PolygonSoupList' : '60_00_00_00',
					   'CharacterSpec' : '09_02_00_00',
					   'CompoundInstanceList' : '16_02_00_00',
					   'DynamicInstanceList' : '04_02_00_00',
					   'GroundcoverCollection' : '0F_02_00_00',
					   'InstanceList' : '50_00_00_00',
					   'LightInstanceList' : '13_02_00_00',
					   'NavigationMesh' : '68_00_00_00',
					   'PropInstanceList' : '18_02_00_00',
					   'ZoneHeader' : '06_02_00_00'}
	
	return resources_types[resource_type]


def calculate_resourceid(resource_name):
	ID = hex(zlib.crc32(resource_name.lower().encode()) & 0xffffffff)
	ID = ID[2:].upper().zfill(8)
	ID = '_'.join([ID[::-1][x:x+2][::-1] for x in range(0, len(ID), 2)])
	return ID


def is_valid_id(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	if len(id) != 8:
		print("ERROR: ResourceId not in the proper format: %s. The format should be like AA_BB_CC_DD." % id_old)
		return False
	try:
		int(id, 16)
	except ValueError:
		print("ERROR: ResourceId is not a valid hexadecimal string: %s" % id_old)
		return False
	
	return True


def bytes_to_id(id):
	id = binascii.hexlify(id)
	id = str(id,'ascii')
	id = id.upper()
	id = '_'.join([id[x : x+2] for x in range(0, len(id), 2)])
	return id


def int_to_id(id):
	id = str(hex(int(id)))[2:].upper().zfill(8)
	id = '_'.join([id[::-1][x : x+2][::-1] for x in range(0, len(id), 2)])
	return id


def id_to_bytes(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	if len(id) != 8:
		print("ERROR: ResourceId not in the proper format: %s" % id_old)
	try:
		int(id, 16)
	except ValueError:
		print("ERROR: ResourceId is not a valid hexadecimal string: %s" % id_old)
	return bytearray.fromhex(id)


def id_to_int(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	id = ''.join(id[::-1][x:x+2][::-1] for x in range(0, len(id), 2))
	return int(id, 16)


def id_swap(id):
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	id = '_'.join([id[::-1][x:x+2][::-1] for x in range(0, len(id), 2)])
	return id


def lin2s1(x):
	a = 0.055
	if x <= 0.0031308:
		y = x * 12.92
	elif 0.0031308 < x <= 1 :
		y = 1.055*(x**(1.0/2.4)) - 0.055
	return y


def s2lin(x):
	a = 0.055
	if x <=0.04045 :
		y = x * (1.0 / 12.92)
	else:
		y = pow( (x + a) * (1.0 / (1 + a)), 2.4)
	return y


def calculate_padding(length, alignment):
	division1 = (length/alignment)
	division2 = math.ceil(length/alignment)
	padding = int((division2 - division1)*alignment)
	return padding


def NFSMWLibraryGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\NeedForSpeedMostWanted2012'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return tpath
	return None


def nvidiaGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\nvidia-texture-tools-2.1.2-win\\bin64\\nvcompress.exe'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return npath
		tpath = rpath + '\\addons\\nvidia-texture-tools-2.1.1-win64\\bin64\\nvcompress.exe'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return npath
	return None


@orientation_helper(axis_forward='-Y', axis_up='Z')
class ExportNFSMW(Operator, ExportHelper):
	"""Export as a Need for Speed Most Wanted (2012) Model file"""
	bl_idname = "export_nfsmw.data"
	bl_label = "Export to folder"
	bl_options = {'PRESET'}

	filename_ext = ""
	use_filter_folder = True

	filter_glob: StringProperty(
			options={'HIDDEN'},
			default="*.dat",
			maxlen=255,
			)
	
	pack_bundle_file: BoolProperty(
			name="Pack bundle",
			description="Check in order to pack the exported files in a bundle",
			default=True,
			)
	
	copy_uv_layer: BoolProperty(
			name="Copy uv layer",
			description="Check in order to allow making a copy of the first UV layer to other if it is non existent on the mesh and it is requested by the shader",
			default=True,
			)
	
	ignore_hidden_meshes: BoolProperty(
			name="Ignore hidden meshes",
			description="Check in order to not export the hidden meshes",
			default=True,
			)
	
	if bpy.context.preferences.view.show_developer_ui == True:
		debug_shared_not_found: BoolProperty(
			name="Resolve is_shared_asset not found",
			description="Check in order to allow setting is_shared_asset as False if an asset is not found in the default library",
			default=True,
			)
		
		debug_use_shader_material_parameters: BoolProperty(
			name="Use default shader parameters",
			description="Check in order to apply the default shader parameters on materials",
			default=False,
			)
		
		debug_use_default_samplerstates: BoolProperty(
			name="Use default sampler states",
			description="Check in order to apply the default sampler states on materials",
			default=False,
			)
		
		#change_vehicle: StringProperty(
		#	name="Export to another vehicle",
		#	description="Write the vehicle you want your model to replace",
		#	default="",
		#	)
		
		debug_redirect_vehicle: BoolProperty(
			name="Export to another vehicle",
			description="Check in order to redirect the exported vehicle to another one",
			default=False,
			)
		
		debug_new_vehicle_name: StringProperty(
			name="Vehicle ID",
			description="Write the vehicle you want your model to replace",
			default="",
			)
		
	else:
		debug_redirect_vehicle = False
		debug_new_vehicle_name = ""
		debug_shared_not_found = False
		debug_use_shader_material_parameters = False
		debug_use_default_samplerstates = False
	
	force_rotation: BoolProperty(
		name="Force rotation on objects",
		description="Check in order to use the global rotation option",
		default=False,
		)
	
	global_rotation: FloatVectorProperty(
		name="Global rotation",
		description="Write the global objects rotation (local space). Use it only if your model got wrongly oriented in-game",
		default=(-90.0, 0.0, 0.0),
		)

	
	def execute(self, context):
		userpath = self.properties.filepath
		if os.path.isfile(userpath):
			self.report({"ERROR"}, "Please select a directory not a file\n" + userpath)
			return {"CANCELLED"}
		if NFSMWLibraryGet() == None:
			self.report({"ERROR"}, "Game library not found, please check if you installed it correctly.")
			return {"CANCELLED"}
		
		global_matrix = axis_conversion(from_forward='Z', from_up='Y', to_forward=self.axis_forward, to_up=self.axis_up).to_4x4()
		
		status = main(context, self.filepath, self.pack_bundle_file, self.ignore_hidden_meshes, self.copy_uv_layer, self.force_rotation, [False, False, False], self.global_rotation,
					  self.debug_shared_not_found, self.debug_use_shader_material_parameters, self.debug_use_default_samplerstates, self.debug_redirect_vehicle, self.debug_new_vehicle_name, global_matrix)
		if status == {"CANCELLED"}:
			self.report({"ERROR"}, "Exporting has been cancelled. Check the system console for information.")
		return status
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False  # No animation.
		
		sfile = context.space_data
		operator = sfile.active_operator
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Settings", icon="SETTINGS")
		
		box.prop(operator, "pack_bundle_file")
		box.prop(operator, "ignore_hidden_meshes")
		box.prop(operator, "copy_uv_layer")
		box.prop(operator, "force_rotation")
		if operator.force_rotation == True:
			box.prop(operator, "global_rotation")
		
		##
		if bpy.context.preferences.view.show_developer_ui == True:
			box = layout.box()
			split = box.split(factor=0.75)
			col = split.column(align=True)
			col.label(text="Debug options", icon="MODIFIER")
			
			box.prop(operator, "debug_shared_not_found")
			box.prop(operator, "debug_use_shader_material_parameters")
			box.prop(operator, "debug_use_default_samplerstates")
			box.prop(operator, "debug_redirect_vehicle")
			if operator.debug_redirect_vehicle == True:
				box.prop(operator, "debug_new_vehicle_name")
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Blender orientation", icon="OBJECT_DATA")
		
		row = box.row(align=True)
		row.label(text="Forward axis")
		row.use_property_split = False
		row.prop_enum(operator, "axis_forward", 'X', text='X')
		row.prop_enum(operator, "axis_forward", 'Y', text='Y')
		row.prop_enum(operator, "axis_forward", 'Z', text='Z')
		row.prop_enum(operator, "axis_forward", '-X', text='-X')
		row.prop_enum(operator, "axis_forward", '-Y', text='-Y')
		row.prop_enum(operator, "axis_forward", '-Z', text='-Z')
		
		row = box.row(align=True)
		row.label(text="Up axis")
		row.use_property_split = False
		row.prop_enum(operator, "axis_up", 'X', text='X')
		row.prop_enum(operator, "axis_up", 'Y', text='Y')
		row.prop_enum(operator, "axis_up", 'Z', text='Z')
		row.prop_enum(operator, "axis_up", '-X', text='-X')
		row.prop_enum(operator, "axis_up", '-Y', text='-Y')
		row.prop_enum(operator, "axis_up", '-Z', text='-Z')


def menu_func_export(self, context):
	self.layout.operator(ExportNFSMW.bl_idname, text="Need for Speed Most Wanted (2012) (.dat)")


classes = (
		ExportNFSMW,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
	register()
