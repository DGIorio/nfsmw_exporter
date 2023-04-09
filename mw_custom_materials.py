#-*- coding:utf-8 -*-

def custom_shaders():
	shaders = {}
	shaders['Glass'] = 'A9_EF_09_00' #before it was A7_EF_09_00
	shaders['Glass_Black'] = 'A9_EF_09_00'
	shaders['Glass_black'] = 'A9_EF_09_00'
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
	shaders['LicensePlate_Number'] = '9C_D4_10_00'
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
	shaders['BodyLivery'] = '72_EF_09_00'
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
	shaders['BrakeDisc'] = 'B5_EF_09_00'
	shaders['VehicleNFS13_Chassis'] = '78_EF_09_00'
	shaders['Chassis'] = '78_EF_09_00'
	shaders['VehicleNFS13_Carbonfiber'] = '78_EF_09_00'
	shaders['CarbonFiber'] = '78_EF_09_00'
	shaders['LightCluster'] = '7C_EF_09_00'
	shaders['LightRefracted'] = 'A1_EF_09_00'
	shaders['Rim'] = 'B5_EF_09_00'
	shaders['CarbonFiber2'] = '78_EF_09_00'
	shaders['GlassColourise'] = 'AB_EF_09_00'
	shaders['GlassColour'] = 'AB_EF_09_00'
	shaders['GlassColor'] = 'AB_EF_09_00'
	shaders['CopLight'] = '7A_EF_09_00'
	shaders['CarPaint'] = '76_EF_09_00'
	shaders['CaliperBadge'] = 'FC_BF_19_00'
	shaders['RimBadge'] = 'FC_BF_19_00'
	shaders['RimBadgeFade'] = 'BB_EF_09_00'
	shaders['BodypaintLight'] = '74_EF_09_00'
	shaders['CarpaintLight'] = '74_EF_09_00'
	shaders['BodyPaintNormal'] = '6E_EF_09_00'
	shaders['CarPaintNormal'] = '6E_EF_09_00'
	shaders['LightGlass'] = 'A7_EF_09_00'
	shaders['Engine'] = '78_EF_09_00'
	#CharacterSpec
	shaders['Character'] = 'AA_D4_10_00'
	shaders['Driver'] = 'AA_D4_10_00'
	
	return shaders


def get_default_sampler_states(shader_type, mShaderId, num_sampler_states_shader):
	sampler_states_info = ["7F_77_6A_0A"]*num_sampler_states_shader
	
	if mShaderId == "6E_EF_09_00":	#VehicleNFS13_BodyPaint_NormalMap_NoDamage
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F']
	elif mShaderId == "68_EF_09_00":	#VehicleNFS13_BodyPaint_TwoPaintMask
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "70_EF_09_00":	#VehicleNFS13_BodyPaint_Livery_Lightmap
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "72_EF_09_00":	#VehicleNFS13_BodyPaint_Livery
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "74_EF_09_00":	#VehicleNFS13_BodyPaint_Lightmap
		sampler_states_info = ['D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "76_EF_09_00":	#VehicleNFS13_BodyPaint
		sampler_states_info = ['D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "78_EF_09_00":	#VehicleNFS13_Body_Textured_NormalMap_NoDamage
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "7A_EF_09_00":	#VehicleNFS13_Body_Textured_NormalMap_LocalEmissive
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "7C_EF_09_00":	#VehicleNFS13_Body_Textured_NormalMap_EmissiveFourChannel_NoDamage_NoEffects
		sampler_states_info = ['7F_77_6A_0A', '7F_77_6A_0A', 'D5_4F_91_2F']
	elif mShaderId == "7E_EF_09_00":	#VehicleNFS13_Body_Textured_NormalMap_Lightmap
		sampler_states_info = ['74_2A_D8_6D', '60_7D_0D_2E', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "88_EF_09_00":	#VehicleNFS13_Body_Lightmap
		sampler_states_info = ['D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "8A_EF_09_00":	#VehicleNFS13_Body_Alpha1bit_NormalMap_Textured_NoDamage
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "90_EF_09_00":	#VehicleNFS13_Body_Alpha_NormalMap_DoubleSided
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "92_EF_09_00":	#VehicleNFS13_Body
		sampler_states_info = ['D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "A1_EF_09_00":	#VehicleNFS13_Refraction
		sampler_states_info = ['D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "A5_EF_09_00":	#VehicleNFS13_Glass_Doublesided
		sampler_states_info = ['7F_77_6A_0A', '7F_77_6A_0A', 'D5_4F_91_2F']
	elif mShaderId == "A7_EF_09_00":	#VehicleNFS13_Glass_Textured_Lightmap
		sampler_states_info = ['7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "A9_EF_09_00":	#VehicleNFS13_Glass
		sampler_states_info = ['7F_77_6A_0A', '7F_77_6A_0A', 'D5_4F_91_2F']
	elif mShaderId == "B3_EF_09_00":	#VehicleNFS13_Wheel_Textured_Normalmap_Blurred
		sampler_states_info = ['7F_77_6A_0A', '89_B6_8C_9A', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "B5_EF_09_00":	#VehicleNFS13_Wheel_Textured_Roughness
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "B9_EF_09_00":	#VehicleNFS13_Wheel_Alpha_Textured_Normalmap_Blurred_Doublesided_PixelAO
		sampler_states_info = ['7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', '7F_77_6A_0A', 'D5_4F_91_2F']
	elif mShaderId == "BB_EF_09_00":	#VehicleNFS13_Wheel_Alpha_Textured_Normalmap_BlurFade
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "BF_EF_09_00":	#VehicleNFS13_Wheel_Alpha1bit_Normalmap
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "C8_EF_09_00":	#VehicleNFS13_BodyPaint_TwoPaint_Livery
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "BB_5F_0F_00":	#VehicleNFS13_Wheel_Tyre_Textured_Normalmap_Blurred
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F']
	elif mShaderId == "9C_D4_10_00":	#VehicleNFS13_Body_Textured_NormalMap_Lightmap_Licenseplate
		sampler_states_info = ['74_2A_D8_6D', '60_7D_0D_2E', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "AA_D4_10_00":	#CharacterNew_Opaque_Textured_Normal_Spec_VertexAO
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A']
	elif mShaderId == "FC_BF_19_00":	#VehicleNFS13_Wheel_Alpha1bit_Textured_Normalmap
		sampler_states_info = ['7F_77_6A_0A', 'D5_4F_91_2F', '7F_77_6A_0A', '7F_77_6A_0A']
	elif mShaderId == "08_15_1F_00":	#VehicleNFS13_Body_Driver
		sampler_states_info = ['D5_4F_91_2F', '7F_77_6A_0A']
	
	return sampler_states_info


def get_default_material_parameters(shader_type):
	status = 0
	parameters_Indices = []
	parameters_Ones = []
	parameters_NamesHash = []
	parameters_Data = []
	parameters_Names = []
	
	if shader_type.lower() == "glass" or shader_type.lower() == "glass_black":	#A9_EF_09_00
		parameters_Indices = (1, 2, 5, 6, 7, 3, 8, 4, 0)
		parameters_Ones = (1, 1, 1, 1, 1, 1, 1, 1, 1)
		parameters_NamesHash = (42301036, 422585019, 529556121, 1441692693, 1444230008, 1989249925, 2342768594, 2580468578, 2907884810)
		parameters_Data = [(0.0, 0.0, 0.0, 0.0),
						   (1.0, 0.0, 0.0, 0.0),
						   (0.0010000000474974513, 0.0, 0.0, 0.0),
						   (0.09000000357627869, 0.0, 0.0, 0.0),
						   (0.009721217676997185, 0.009134058840572834, 0.00802319310605526, 0.8767699003219604),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.16200000047683716, 0.0, 0.0, 0.0),
						   (0.12770847976207733, 0.12770847976207733, 0.12770847976207733, 1.0),
						   (1.0, 5.0, 1.0, 0.0)]
		parameters_Names = ['DebugOverride_GlassVolumeColour', 'FresnelFactor', 'MaterialShadowMapBias', 'OpacityMin', 'PbrMaterialDirtColour', 'PbrMaterialDustColour', 'SurfaceSoftness', 'mCrackedGlassSpecularColour', 'mCrackedGlassSpecularControls']
	
	elif shader_type == "VehicleNFS13_Glass_Textured_Lightmap":	#A7_EF_09_00
		parameters_Indices = (1, 2, 5, 10, 7, 8, 3, 9, 4, 0, 6)
		parameters_Ones = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
		parameters_NamesHash = (42301036, 422585019, 529556121, 843472246, 1441692693, 1444230008, 1989249925, 2342768594, 2580468578, 2907884810, 3743314456)
		parameters_Data = [(0.0060069505125284195, 0.0060069505125284195, 0.0060069505125284195, 0.049707602709531784),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.0010000000474974513, 0.0, 0.0, 0.0),
						   (0.2840000092983246, 0.0, 0.0, 0.0),
						   (0.009134058840572834, 0.009134058840572834, 0.009134058840572834, 0.5998314619064331),
						   (0.16826939582824707, 0.1384316086769104, 0.109461709856987, 0.6017727255821228),
						   (9.978223533835262e-05, 0.00012177028111182153, 0.000244140625, 1.0),
						   (0.41499999165534973, 0.0, 0.0, 0.0),
						   (0.12770847976207733, 0.12770847976207733, 0.12770847976207733, 1.0),
						   (1.0, 5.0, 1.0, 0.0), (4.3460001945495605, 0.0, 0.0, 0.0)]
		parameters_Names = ['DebugOverride_GlassVolumeColour', 'FresnelFactor', 'MaterialShadowMapBias', 'OpacityMin', 'PbrMaterialDirtColour', 'PbrMaterialDustColour', 'RunningColour', 'SurfaceSoftness', 'mCrackedGlassSpecularColour', 'mCrackedGlassSpecularControls', 'mSelfIlluminationMultiplier']
	
	elif shader_type.lower() == "mirror" or shader_type == "VehicleNFS13_Mirror":	#A9_EF_09_00
		parameters_Indices = (1, 2, 5, 6, 7, 3, 8, 4, 0)
		parameters_Ones = (1, 1, 1, 1, 1, 1, 1, 1, 1)
		parameters_NamesHash = (42301036, 422585019, 529556121, 1441692693, 1444230008, 1989249925, 2342768594, 2580468578, 2907884810)
		parameters_Data = [(0.00016276036330964416, 0.00020345063239801675, 0.000244140625, 1.0),
						   (1.0, 0.0, 0.0, 0.0),
						   (0.0010000000474974513, 0.0, 0.0, 0.0),
						   (0.35600000619888306, 0.0, 0.0, 0.0),
						   (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 0.10999999940395355),
						   (0.041999999433755875, 0.03500000014901161, 0.028999999165534973, 0.25),
						   (0.5080000162124634, 0.0, 0.0, 0.0),
						   (0.11443537473678589, 0.1946178376674652, 0.21223075687885284, 1.0),
						   (0.10999999940395355, 3.5, 1.0, 0.0)]
		parameters_Names = ['DebugOverride_GlassVolumeColour', 'FresnelFactor', 'MaterialShadowMapBias', 'OpacityMin', 'PbrMaterialDirtColour', 'PbrMaterialDustColour', 'SurfaceSoftness', 'mCrackedGlassSpecularColour', 'mCrackedGlassSpecularControls']
	
	elif shader_type.lower() == "chrome" or shader_type == "VehicleNFS13_Chrome" or shader_type == "VehicleNFS13_Body_Chrome":	#92_EF_09_00
		parameters_Indices = (2, 4, 5, 6, 3, 1, 0)
		parameters_Ones = (1, 1, 1, 1, 1, 1, 1)
		parameters_NamesHash = (108602291, 825258624, 1236639422, 1491944071, 2428116513, 3057425025, 3447747285)
		parameters_Data = [(1.0, 0.0, 0.0, 0.0),
						   (1.0, 0.0, 0.0, 0.0),
						   (0.8784313725490196, 0.8784313725490196, 0.8784313725490196, 1.0),
						   (0.20000000298023224, 0.0, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.699999988079071, 0.30000001192092896, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0)]
		parameters_Names = ['PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular', 'PbrMaterialDiffuseColour', 'PbrMaterialRoughness', 'PbrMaterialScuffColour', 'PbrMaterialScuffSettings', 'PbrMaterialSpecularColour']
	
	elif shader_type.lower() == "tyre" or shader_type == "VehicleNFS13_Tyre" or shader_type == "VehicleNFS13_Body_Tyre":	#9B_EF_09_00
		parameters_Indices = (3, 0, 2, 1)
		parameters_Ones = (1, 1, 1, 1)
		parameters_NamesHash = (843472246, 2143891951, 3057425025, 3447747285)
		parameters_Data = [(0.0, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.27049779891967773, 0.24228112399578094, 0.21223075687885284, 0.047659896314144135)]
		parameters_Names = ['LightmappedLightsGreenChannelColour', 'PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular', 'mSelfIlluminationMultiplier']
	
	elif shader_type.lower() == "license_plate_number" or shader_type.lower() == "licenseplate_number" or shader_type == "VehicleNFS13_Licenseplate_Number" or shader_type == "VehicleNFS13_License_Plate_Number":	#9C_D4_10_00
		parameters_Indices = (4, 7, 5, 6, 0, 3, 2, 1)
		parameters_Ones = (1, 1, 1, 1, 1, 1, 1, 1)
		parameters_NamesHash = (825258624, 843472246, 1236639422, 1491944071, 2143891951, 2428116513, 3057425025, 3447747285)
		parameters_Data = [(0.12583260238170624, 0.12583260238170624, 0.12583260238170624, 1.0),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.20000000298023224, 0.0, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.699999988079071, 0.30000001192092896, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (1.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['LightmappedLightsGreenChannelColour', 'PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular', 'PbrMaterialRoughness', 'PbrMaterialScuffColour', 'PbrMaterialScuffSettings', 'PbrMaterialSpecularColour', 'mSelfIlluminationMultiplier']
	
	elif shader_type.lower() == "license_plate" or shader_type.lower() == "licenseplate" or shader_type == "VehicleNFS13_Licenseplate" or shader_type == "VehicleNFS13_License_Plate":	#7E_EF_09_00
		parameters_Indices = (4, 7, 5, 6, 0, 3, 2, 1)
		parameters_Ones = (1, 1, 1, 1, 1, 1, 1, 1)
		parameters_NamesHash = (825258624, 843472246, 1236639422, 1491944071, 2143891951, 2428116513, 3057425025, 3447747285)
		parameters_Data = [(0.12583260238170624, 0.12583260238170624, 0.12583260238170624, 1.0),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (0.20000000298023224, 0.0, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.699999988079071, 0.30000001192092896, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (1.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['LightmappedLightsGreenChannelColour', 'PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular', 'PbrMaterialRoughness', 'PbrMaterialScuffColour', 'PbrMaterialScuffSettings', 'PbrMaterialSpecularColour', 'mSelfIlluminationMultiplier']
	
	elif shader_type.lower() == "dullplastic" or shader_type.lower() == "dull_plastic":	#92_EF_09_00
		parameters_Indices = (2, 4, 5, 6, 3, 1, 0)
		parameters_Ones = (1, 1, 1, 1, 1, 1, 1)
		parameters_NamesHash = (108602291, 825258624, 1236639422, 1491944071, 2428116513, 3057425025, 3447747285)
		parameters_Data = [(0.0140000004321337, 0.0, 0.0, 0.0),
						   (0.0, 0.0, 0.0, 0.0),
						   (0.072271853685379, 0.072271853685379, 0.072271853685379, 1.0),
						   (0.51800000667572, 0.0, 0.0, 0.0),
						   (0.18000000715255737, 0.18000000715255737, 0.18000000715255737, 1.0),
						   (0.699999988079071, 0.30000001192092896, 0.0, 0.0),
						   (0.056833628565073, 0.0625, 0.056833628565073, 1.0)]
		parameters_Names = ['PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular', 'PbrMaterialDiffuseColour', 'PbrMaterialRoughness', 'PbrMaterialScuffColour', 'PbrMaterialScuffSettings', 'PbrMaterialSpecularColour']
	
	elif shader_type.lower() == "interior" or shader_type == "VehicleNFS13_Interior":	#9B_EF_09_00
		parameters_Indices = (3, 0, 2, 1)
		parameters_Ones = (1, 1, 1, 1)
		parameters_NamesHash = (843472246, 2143891951, 3057425025, 3447747285)
		parameters_Data = [(0.0, 0.0, 0.0, 1.0),
						   (0.004276574589312077, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0),
						   (1.0, 0.0, 0.0, 0.0)]
		parameters_Names = ['LightmappedLightsGreenChannelColour', 'PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular', 'mSelfIlluminationMultiplier']
	
	elif shader_type.lower() == "caliper" or shader_type.lower() == "caliper_textured" or shader_type == "VehicleNFS13_Caliper":	#B5_EF_09_00
		parameters_Indices = (4, 3, 2, 1, 0)
		parameters_Ones = (1, 1, 1, 1, 1)
		parameters_NamesHash = (529556121, 2580468578, 3057425025, 3447747285, 3998419168)
		parameters_Data = [(0.0, 0.0, 0.0, 0.0),
						   (0.2622506618499756, 0.0, 0.0030352699104696512, 1.0),
						   (0.052860647439956665, 0.0, 0.0, 0.0),
						   (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 0.10999999940395355),
						   (0.041999999433755875, 0.03500000014901161, 0.028999999165534973, 0.25)]
		parameters_Names = ['g_flipUvsOnFlippedTechnique', 'PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular', 'PbrMaterialDirtColour', 'PbrMaterialDustColour']
	
	elif shader_type.lower() == "brakedisc" or shader_type == "VehicleNFS13_BrakeDisc":    #B5_EF_09_00
		parameters_Indices = (4, 3, 2, 1, 0)
		parameters_Ones = (1, 1, 1, 1, 1)
		parameters_NamesHash = (529556121, 2580468578, 3057425025, 3447747285, 3998419168)
		parameters_Data = [(0.0, 0.0, 0.0, 0.0),
						   (0.03099999949336052, 0.0, 0.0, 0.0),
						   (0.015208514407277107, 0.0, 0.0, 0.0),
						   (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 0.10999999940395355),
						   (0.041999999433755875, 0.03500000014901161, 0.028999999165534973, 0.25)]
		parameters_Names = ['g_flipUvsOnFlippedTechnique', 'PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular', 'PbrMaterialDirtColour', 'PbrMaterialDustColour']
	
	elif shader_type.lower() == "chassis" or shader_type == "VehicleNFS13_Chassis":	#78_EF_09_00
		parameters_Indices = (1, 0)
		parameters_Ones = (1, 1)
		parameters_NamesHash = (3057425025, 3447747285)
		parameters_Data = [(0.01856684684753418, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular']
	
	elif shader_type.lower() == "carbonfiber" or shader_type == "VehicleNFS13_Carbonfiber":	#78_EF_09_00
		parameters_Indices = (1, 0)
		parameters_Ones = (1, 1)
		parameters_NamesHash = (3057425025, 3447747285)
		parameters_Data = [(0.0, 0.0, 0.0, 0.0),
						   (0.011612244881689548, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular']
	
	elif shader_type.lower() == "carbonfiber2":	#78_EF_09_00
		parameters_Indices = (1, 0)
		parameters_Ones = (1, 1)
		parameters_NamesHash = (3057425025, 3447747285)
		parameters_Data = [(1.0, 0.0, 0.0, 0.0),
						   (0.00039999998989515007, 0.0, 0.0, 0.0)]
		parameters_Names = ['PbrMaterialClearcoatFresnel', 'PbrMaterialClearcoatSpecular']

	else:
		status = 1
	
	return (status, [parameters_Indices, parameters_Ones, parameters_NamesHash, parameters_Data, parameters_Names])


def	get_default_mRasterId(shader_type, mShaderId, raster_type, resource_type):
	is_raster_shared_asset = True
	raster_path = ""
	raster_properties = [0x30]
	if resource_type == "InstanceList":
		mRasterId = "1D_F3_05_00"
	elif resource_type == "CharacterSpec":
		mRasterId = "A2_70_79_2C"
	else:
		mRasterId = "30_A7_06_00"
	
	if mShaderId == "9C_D4_10_00":	# License_Plate_Number
		if raster_type == "NormalTextureSampler":
			mRasterId = "06_88_13_00"
		elif raster_type == "DiffuseTextureSampler":
			mRasterId = "05_88_13_00"
		elif raster_type == "EffectsTextureSampler":
			mRasterId = "1C_8D_0D_00"
		elif raster_type == "LightmapLightsTextureSampler":
			mRasterId = "0A_08_11_00"
	elif shader_type.lower() == "licenseplate" or shader_type == "license_plate" or shader_type == "VehicleNFS13_Licenseplate" or shader_type == "VehicleNFS13_License_Plate":
		if raster_type == "NormalTextureSampler":
			mRasterId = "D5_8C_0D_00"
		elif raster_type == "DiffuseTextureSampler":
			mRasterId = "D4_8C_0D_00"
		elif raster_type == "EffectsTextureSampler":
			mRasterId = "1C_8D_0D_00"
		elif raster_type == "LightmapLightsTextureSampler":
			mRasterId = "0A_08_11_00"
	elif shader_type.lower() == "interior" or shader_type == "VehicleNFS13_Interior":    #Interior
		if raster_type == "NormalTextureSampler":
			mRasterId = "0B_08_11_00"
		elif raster_type == "SpecularTextureSampler":
			mRasterId = "0C_08_11_00"
		elif raster_type == "LightmapLightsTextureSampler":
			mRasterId = "0A_08_11_00"
	elif shader_type.lower() == "glass" or shader_type.lower() == "glass_black" or shader_type.lower() == "mirror" or shader_type == "VehicleNFS13_Mirror": #Mirror
		if raster_type == "CrackedGlassTextureSampler":
			mRasterId = "7F_07_11_00"
		elif raster_type == "CrackedGlassNormalTextureSampler":
			mRasterId = "80_07_11_00"
	elif shader_type.lower() == "caliper" or shader_type.lower() == "caliper_textured" or shader_type == "VehicleNFS13_Caliper":    #Caliper
		if raster_type == "EffectsTextureSampler":
			mRasterId = "B0_FD_05_00"
		elif raster_type == "SpecularTextureSampler":
			mRasterId = "22_53_0F_00"
	elif shader_type.lower() == "brakedisc" or shader_type == "VehicleNFS13_BrakeDisc":    #BrakeDisc_Simplified
		if raster_type == "EffectsTextureSampler":
			mRasterId = "B0_FD_05_00"
	elif shader_type.lower() == "chassis" or shader_type == "VehicleNFS13_Chassis":    #Shared_Car_Chassis
		if raster_type == "NormalTextureSampler":
			mRasterId = "D7_26_04_00"
		elif raster_type == "DiffuseTextureSampler":
			mRasterId = "D6_26_04_00"
		elif raster_type == "SpecularTextureSampler":
			mRasterId = "DA_8C_0D_00"
	elif shader_type.lower() == "carbonfiber" or shader_type == "VehicleNFS13_Carbonfiber":    #Shared_Car_CarbonA
		if raster_type == "NormalTextureSampler":
			mRasterId = "3B_8D_0D_00"
		elif raster_type == "DiffuseTextureSampler":
			mRasterId = "3A_8D_0D_00"
		elif raster_type == "SpecularTextureSampler":
			mRasterId = "3C_8D_0D_00"
	elif shader_type.lower() == "carbonfiber2":
		if raster_type == "NormalTextureSampler":
			mRasterId = "76_28_10_00"
		elif raster_type == "DiffuseTextureSampler":
			mRasterId = "E5_30_0E_00"
		elif raster_type == "SpecularTextureSampler":
			mRasterId = "77_28_10_00"
	
	elif resource_type == "InstanceList":
		mRasterId = "1D_F3_05_00"
		if raster_type in ( 'NormalTextureSampler', 'NormalTexture2Sampler', 'NormalSampler', 'Tiling1NormalSampler', 'Tiling2NormalSampler',
							'Tiling3NormalSampler',	'DetailMap_Normal_Sampler', 'Normal_Sampler', 'SlipNormalSampler', 'RunNormalSampler',
							'SpinNormalSampler', 'SurfNormalTextureSampler',	'Line_NormalPlusSpec_Sampler', 'Decal_NormalPlusSpec_Sampler'):
			mRasterId = "A5_90_02_00"
		elif raster_type == "SpecularTextureSampler" or raster_type == "SpecularTexture2Sampler" or raster_type == "SpecularSampler":
			mRasterId = "9E_0D_08_00"
		elif raster_type == "ReflectionTextureSampler":
			mRasterId = "1F_12_07_00"
		elif raster_type == "OverlayTextureSampler":
			mRasterId = "A4_57_09_00"	#Or "9B_7D_15_00"
		elif raster_type == "NeonMaskTextureSampler":
			mRasterId = "A4_57_09_00"
		elif raster_type == "IlluminanceTextureSampler":
			mRasterId = "4F_1F_A7_2D"	#black
			raster_properties = [48]
			is_raster_shared_asset = False
			raster_path = "create_texture"
	
	elif resource_type == "CharacterSpec":
		if raster_type == "DiffuseTextureSampler":
			mRasterId = "A2_70_79_2C"	#white
			raster_properties = [48]
			is_raster_shared_asset = False
			raster_path = "create_texture"
		elif raster_type == "NormalTextureSampler":
			mRasterId = "06_88_13_FF" #normal
			raster_properties = [32]
			is_raster_shared_asset = False
			raster_path = "create_texture"
		elif raster_type == "SpecularTextureSampler":
			mRasterId = "A2_70_79_2C"	#white
			raster_properties = [32]
			is_raster_shared_asset = False
			raster_path = "create_texture"
		elif raster_type == "AoSpecMapTextureSampler":
			mRasterId = "A2_70_79_2C"	#white
			raster_properties = [32]
			is_raster_shared_asset = False
			raster_path = "create_texture"
	
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
	
	return (mRasterId, raster_properties, is_raster_shared_asset, raster_path)
