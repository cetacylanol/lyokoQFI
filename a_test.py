#For testing files from CL:CFI for further reversing
import struct
import os
import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix, Euler
from math import radians,ceil

# read unsigned byte from file
def read_byte(file_object, endian = '>'):
    data = struct.unpack(endian+'B', file_object.read(1))[0]
    return data

# read unsgned short from file
def read_short(file_object, endian = '>'):
    data = struct.unpack(endian+'H', file_object.read(2))[0]
    return data

# read unsgned long from file
def read_long(file_object, endian = '>'):
    data = struct.unpack(endian+'L', file_object.read(4))[0]
    return data

# read floating point number from file
def read_float(file_object, endian = '>'):
    data = struct.unpack(endian+'f', file_object.read(4))[0]
    return data

# read string from file
def read_str(file_object,len, endian = '>'):
    data = file_object.read(len).decode('ascii', 'ignore')

    return data

def do_anim_imp(fileName, context):
    arm = context.active_object

    arm.animation_data_create()


    with open(fileName, 'rb') as model_f:
        model_f.seek(592,1)
        obm_count = read_long(model_f)
        model_f.seek(8,1)

        v_nums = []
        f_nums = []
        b_nums = []
        anim_num = 0

        for i in range(obm_count):
            model_f.seek(6,1)
            #bone numbers
            b_nums.append(read_byte(model_f))

            model_f.seek(2,1)
            anim_num += read_byte(model_f)

            model_f.seek(18,1)
            #read vertex and face counts
            v_nums.append(read_short(model_f))
            f_nums.append(read_short(model_f))

            #seek to name
            model_f.seek(442,1)
            #read name
            for j in range(8):
                #seek to next chars
                model_f.seek(24,1)
            
            #seek to end of obm header
            model_f.seek(34,1)
            #---header end---
        
        #angle precision
        a_prec = float(360/65536)


        for i in range(obm_count):
            #object attributes
            #---face section start---
            #seek to face indices
            model_f.seek(f_nums[i]*20, 1)

            #---face section end---
            #---vert section start---
            model_f.seek(v_nums[i] * 32, 1)

            #---vert section end---
            #---bone section start---
            #skip if no bones
            if(b_nums[i] != 0):
                model_f.seek(b_nums[i]*8,1)
                #model_f.seek(1, 1)
                model_f.seek(b_nums[i], 1)

                #skip padding if any...
                p_padding = ceil((b_nums[i]*8 + b_nums[i]) / 8) * 8
                model_f.seek(p_padding - (b_nums[i]*8 +b_nums[i]), 1)

            #---heirarchy section end---
        
        model_f.seek(2 * anim_num, 1)
        model_f.seek(8 - (2 * anim_num) % 8, 1)
        for ani in range(4):
            mp = read_long(model_f)
            if(mp == 0):
                model_f.seek(4, 1)

            anim_size = read_long(model_f)
            model_f.seek(4, 1)
            anim_name = read_str(model_f, 32)

            anim_end = model_f.tell() + anim_size

            arm.animation_data.action = bpy.data.actions.new(anim_name)

            keep_going = True
            seccount = 0
            while(keep_going):
                frame12 = read_short(model_f)
                frame8 = read_short(model_f)

                if(seccount >= b_nums[0]):
                    keep_going = False
                else:
                    seccount += 1

                    for f in range(frame8):
                        frm8 = read_short(model_f)
                        frame8temp = "{0:012}".format(bytes.hex(model_f.read(6)))
                        # f8vala = int(frame8temp[0:3],16)
                        # f8valb = int(frame8temp[3:6],16)
                        # f8valc = int(frame8temp[6:9],16)


                    sec_b = 'Bone.' + "{0:>003}".format(str(seccount - 1))
                    
                    fcu_x = arm.animation_data.action.fcurves.new(data_path='pose.bones["'+sec_b+'"].rotation_euler',index = 0)
                    fcu_y = arm.animation_data.action.fcurves.new(data_path='pose.bones["'+sec_b+'"].rotation_euler',index = 1)
                    fcu_z = arm.animation_data.action.fcurves.new(data_path='pose.bones["'+sec_b+'"].rotation_euler',index = 2)

                    for f in range(frame12):
                        frm = read_short(model_f)
                        model_f.seek(2,1)
                        valb = (read_short(model_f)-32767) * a_prec
                        valc = (read_short(model_f)-32767) * a_prec
                        vala = (read_short(model_f)-32767) * a_prec
                        model_f.seek(2,1)

                        fcu_z.keyframe_points.insert(frm,radians(vala))
                        fcu_x.keyframe_points.insert(frm,radians(valb))
                        fcu_y.keyframe_points.insert(frm,radians(valc))
            print(seccount)
            model_f.seek(anim_end, 0)
            

def add_keys_test(context):
    arm = context.active_object

    arm.animation_data_create()
    arm.animation_data.action = bpy.data.actions.new('ThisisTest')
    fcu_z = arm.animation_data.action.fcurves.new(data_path='pose.bones["Bone.013"].rotation_euler',index = 2)
    fcu_z.keyframe_points.insert(0,1.4)


    

def mwld_anim_valid(file,context):
    fn, ft = os.path.splitext(file)
    if (ft == '.gcn' or ft == '.mwld'):
        do_anim_imp(fn + ft, context)
    else:
        print("not an mwld")

class OT_mwld_anim_import(bpy.types.Operator, ImportHelper):
    bl_idname = 'file.import_mwld_anim'
    bl_label = 'import mwld/gcn animation'

    def execute(self, context):
        mwld_anim_valid(self.filepath,context)
        #add_keys_test(context)
        return {'FINISHED'}

class VIEW3D_PT_import_mwld2(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Model_imports"
    bl_label = "Mwld2"

    def draw(self, context):
        layout = self.layout
        layout.operator("file.import_mwld_anim")

def register():
    bpy.utils.register_class(OT_mwld_anim_import)
    bpy.utils.register_class(VIEW3D_PT_import_mwld2)

def unregister():
    bpy.utils.unregister_class(OT_mwld_anim_import)
    bpy.utils.unregister_class(VIEW3D_PT_import_mwld2)

if __name__ == "__main__":
    register()