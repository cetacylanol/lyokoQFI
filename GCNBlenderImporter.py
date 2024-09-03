#Script for importing Code Lyoko: Quest for Infinity wii models to blender
#for use on decoded GCN files, (or just one TTT section if I can't find any pointers LOL)(i found vertex counts good enough)
#Author: Cetacylanol
#convenience functions from XENTAXs blender import guide!

# Convenience functions
import struct
import os
import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix, Euler
from math import radians, ceil


# read unsigned byte from file
def read_byte(file_object, endian = '>'):
    data = struct.unpack(endian+'B', file_object.read(1))[0]
    return data

# read signed byte from file
def read_sbyte(file_object):
    data = int.from_bytes(file_object.read(1), signed=True, byteorder='big')
    return data

# read unsgned short from file
def read_short(file_object, endian = '>'):
    data = struct.unpack(endian+'H', file_object.read(2))[0]
    return data

# read signed short from file
def read_sshort(file_object,  endian = '>'):
    if(endian == '>'):
        data = int.from_bytes(file_object.read(2), signed=True, byteorder='big')
    else:
        data = int.from_bytes(file_object.read(2), signed=True, byteorder='little')
    return data

# read unsigned integer from file
def read_uint(file_object, endian = '>'):
    data = struct.unpack(endian+'I', file_object.read(4))[0]
    return data

# read signed integer from file
def read_int(file_object, endian = '>'):
    data = struct.unpack(endian+'i', file_object.read(4))[0]
    return data

# read floating point number from file
def read_float(file_object, endian = '>'):
    data = struct.unpack(endian+'f', file_object.read(4))[0]
    return data

# read 2 byte floating point number from file
def read_half(file_object, endian = '>'):
    data = struct.unpack(endian+'e', file_object.read(2))[0]
    return data

#make mesh with data provided
def make_mesh(verts, name, faces = [], uvs = [],vg_data = [],bone_count = 0 , edges = []):
    mesh_nm = name + '_mesh_' 
    obj_nm = name + '_obj_'
    view_layer = bpy.context.view_layer

    #make mesh and link to object
    n_mesh = bpy.data.meshes.new(mesh_nm)
    n_mesh.from_pydata(verts, edges, faces)

    #if uvs are provided make uv map and assign to mesh
    if(uvs != []):
        add_uvs_mesh(n_mesh, uvs)
    n_obj = bpy.data.objects.new(obj_nm, n_mesh)

    #if vertex group data is provided add to object
    if(vg_data != []):
        add_vertex_groups_obj(n_obj, vg_data, bone_count)

    #link object to view layer
    view_layer.active_layer_collection.collection.objects.link(n_obj)

    return n_obj

#make armature with data provided
def make_armature(bones, bone_parents, name):
    arm_nm = name + '_arm_'
    arm_obj_nm = name + '_arm_obj_'
    view_layer = bpy.context.view_layer

    n_arm = bpy.data.armatures.new(arm_nm)
    n_obj = bpy.data.objects.new(arm_obj_nm, n_arm)
    #link object to view layer
    view_layer.active_layer_collection.collection.objects.link(n_obj)
    #set active
    bpy.context.view_layer.objects.active = n_obj

    #---enter edit mode---
    bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)
    n_bones = n_arm.edit_bones
    #add bones to armature
    for b in range(len(bones)):
        b_name = 'Bone.' + "{0:>003}".format(str(b))
        if (b == 0):
            nb = n_bones.new(b_name)        
        else:
            nb = n_bones.new(b_name)
            pname = 'Bone.' + "{0:>003}".format(str(bone_parents[b - 1]))
            nb.parent = n_bones[pname] 
        
        #set bone position
        nb.head = bones[b]
        nb.tail = [bones[b][0], bones[b][1], bones[b][2] + 0.1]
    
    #---exit edit mode---
    bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)

    return n_obj

def add_uvs_mesh(n_mesh, uvs, uname = "UVMap"):
    n_uv_layer = n_mesh.uv_layers.new(name=uname)

    for poly in n_mesh.polygons:
        for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
            n_uv_layer.data[li].uv = uvs[n_mesh.loops[li].vertex_index]


#add vertex groups to n_object, vg_data in the form: bone[vertex index, weight] 
def add_vertex_groups_obj(n_obj, vg_data, b_num):
    group_suffix = 0
    v_grps = n_obj.vertex_groups

    #add vertex groups to obj 
    for i in range(b_num):
        gname = "Bone." + "{0:>003}".format(str(group_suffix))
        v_grps.new(name = gname)

    for v in range(len(vg_data)):
        b1 = vg_data[v][0][0]
        b2 = vg_data[v][1][0]
        bw1 = vg_data[v][0][1]
        v_grps[b1].add([v], bw1, 'ADD')

        if(b2 != 255):
            bw2 = vg_data[v][1][1]
            v_grps[b2].add([v], bw2, 'ADD')

    # for grp in vg_data:
    #     gname = "Bone." + "{0:>003}".format(str(group_suffix))
    #     cur_grp = n_obj.vertex_groups.new(name = gname)
    #     group_suffix += 1
    #     for vg in grp:
    #         cur_grp.add([vg[0]], vg[1], 'ADD')

#assigns polygons to materials based on index in the face list
#n_obj is a mesh object, mat_indices has the amount of polys assigned to each material
def add_material_indices_obj(n_obj, mat_indices):
    c = 0
    mi = 0
    n_polys = n_obj.data.polygons

    #make first material and assign to slot on obj
    nm = bpy.data.materials.new(n_obj.name + "mat")
    nm.diffuse_color = (0.5,0,1,1)
    nm.use_nodes = True
    n_obj.data.materials.append(nm)

    #assign polygon to materials
    for p in n_polys:
        if (c == mat_indices[mi]):
            nm = bpy.data.materials.new(n_obj.name + "mat" + str(mi))
            nm.diffuse_color = (0.5,0,1,1)
            nm.use_nodes = True
            n_obj.data.materials.append(nm)
            mi += 1
            c = 0
        p.material_index = mi
        c += 1

#fix rotations of bone chains and vertices
#mesh is mesh data, arm is an armature, v_sel is a list of vertex counts
#b_chains are the start bones of the chains to rotate, rotations are euler rotations in degrees
def fix_rotations(mesh, arm, v_sel, b_chains, rotations):
    #---enter edit mode---
    bpy.ops.object.mode_set(mode = 'EDIT', toggle = False)
    c_bmesh = bmesh.new()
    c_bmesh.from_mesh(mesh)

    for i in range(len(b_chains)):
        current_bone_nm = 'Bone.' + "{0:>003}".format(str(b_chains[i]))
        c_bone = arm.edit_bones[current_bone_nm]
        c_chain = c_bone.children_recursive
        pivot_point = c_bone.head
        
        #get matrices
        pp_matrix = Matrix.Translation(pivot_point)
        pp_matrix2 = Matrix.Translation(-pivot_point)
        x = radians(rotations[i][0])
        y = radians(rotations[i][1])
        z = radians(rotations[i][2])
        rotation_matrix = Euler((x, y, z)).to_matrix()

        #moves to pivot, rotates, moves back to original place
        translation_matrix = pp_matrix @ rotation_matrix.to_4x4() @ pp_matrix2
        
        #transorm all bones in chain
        c_bone.transform(translation_matrix)
        #amount of verts to select
        v_count = sum(v_sel[b_chains[i] - 1: b_chains[i] + len(c_chain)])
        v_start = sum(v_sel[0:b_chains[i] - 1])

        for b in c_chain:
            b.transform(translation_matrix)

        c_verts = c_bmesh.verts[v_start: v_start + v_count]
        bmesh.ops.rotate(c_bmesh, cent= pivot_point, matrix= rotation_matrix, verts= c_verts)


    c_bmesh.to_mesh(mesh)
    #---exit edit mode---
    bpy.ops.object.mode_set(mode = 'OBJECT', toggle = False)

def mwld_import(bin_file):
    #full path to file including file name
    #replace this with wherever your files are stored
    # home = os.path.expanduser("~")
    
    # bin_file_store = home + "\\Documents\\BlenderModels2\\Rips\\MyScripts\\decomp\\"
    # bin_file = bin_file_store + "L110.mwld"
    #model scale
    m_scale = 0.001 #Since the files were most likely made in maya, the scale is using centimetres instead of metres
    uv_scale = 1/4095
    
    with open(bin_file, "rb") as model_bin:      
        v_nums = []
        f_nums = []
        b_nums = []
        obm_names = []
        
        #---read file header---
        #go to model count
        model_bin.seek(592,1)
        obm_count = read_uint(model_bin)
        model_bin.seek(8,1)

        for i in range(obm_count):
            model_bin.seek(6,1)
            b_nums.append(read_byte(model_bin))
            model_bin.seek(21,1)

            #read vertex and face counts
            v_nums.append(read_short(model_bin))
            f_nums.append(read_short(model_bin))

            #seek to name
            model_bin.seek(442,1)
            #read name
            obm_name = ""
            for j in range(8):
                temp_char = read_byte(model_bin)
                temp_char2 = read_byte(model_bin)
                if (temp_char != 0):
                    obm_name += chr(temp_char)
                else:
                    obm_name += "."
                if (temp_char2 != 0):
                    obm_name += chr(temp_char2)
                else:
                    obm_name += "."
                #seek to next chars
                model_bin.seek(22,1)
            obm_names.append(obm_name)
            
            #seek to end of obm header

            model_bin.seek(34,1)

            #---header end---

        for i in range(obm_count):
            #object attributes
            
            faces = []
            material_face_count = []
            

            #---face section start---
            #get current file offset so we can return to start of section
            f_offset = model_bin.tell()
            model_bin.seek(19, 1)
            p_mat_index = read_byte(model_bin)
            model_bin.seek(f_offset,0)
            m_count = 0
            for j in range(f_nums[i]):
                #if you want to read normals add here.

                #seek to face indices
                model_bin.seek(8, 1)

                #read vert v1, v2, v3
                v1 = read_short(model_bin)
                v2 = read_short(model_bin)
                v3 = read_short(model_bin)
                
                mat_index = read_int(model_bin)

                #seek to end of stride
                model_bin.seek(2, 1)

                #add face to material face count
                if(mat_index != p_mat_index):
                    material_face_count.append(m_count)
                    m_count = 0
                    p_mat_index = mat_index
                m_count += 1

                #add face to faces list
                new_face = [v1,v2,v3]
                faces.append(new_face)
            
            material_face_count.append(m_count)

            #---face section end---
            #---vert section start---

            #get first bone index and return to start of section
            v_offset = model_bin.tell()
            
            model_bin.seek(28, 1)
            prev_bone_i = read_byte(model_bin)
            model_bin.seek(v_offset, 0)

            bone_v_counter = 0
            b_num = 0
            has_root = False
            verts = []
            verts2 = []
            uvs = []
            bone_vert_counts = []
            bone_vertex_groups = []
            #bones this vert is assigned to and weight, each entry is a vert
            #[((bone1, weight), (bone2, weight))]
            vertex_bone_weights = []

            for j in range(v_nums[i]):
                
                #read z, x, y coords
                z1 = read_sshort(model_bin)
                x1 = read_sshort(model_bin)
                y1 = read_sshort(model_bin)

                model_bin.seek(2, 1)
                #read z, x, y coords
                z2 = read_sshort(model_bin)
                x2 = read_sshort(model_bin)
                y2 = read_sshort(model_bin)

                #read uv coords
                model_bin.seek(10, 1)
                uC1 = read_short(model_bin)
                vC1 = read_short(model_bin)

                #bone indices
                bone1 = read_byte(model_bin)
                bone2 = read_byte(model_bin)
                
                #bone weights
                bone1_weightt = read_byte(model_bin)
                bone2_weightt = read_byte(model_bin)

                bone1_weight = bone1_weightt * (1/255)
                bone2_weight = bone2_weightt * (1/255)
                
                x = x1 * m_scale
                y = y1 * m_scale
                z = z1 * m_scale

                xb2 = x2 * m_scale
                yb2 = y2 * m_scale
                zb2 = z2 * m_scale

                uc = uC1 * uv_scale
                vc = ((vC1 * uv_scale) * -0.5) + 8.5
                if (not has_root and bone1 == 0): has_root = True

                # if(bone1 != prev_bone_i):
                #     bone_vert_counts.append(bone_v_counter)
                #     bone_v_counter = 0
                #     prev_bone_i = bone1
                # bone_v_counter += 1

                #if bone 1 isn't null value
                #to stop big empty lists on models with no bones
                if(bone1 != 255):
                    vertex_bone_weights.append(((bone1, bone1_weight),(bone2, bone2_weight)))
                    verts2.append([xb2,yb2,zb2])

                    #add vertex groups for the bones this vertex is assigned to
                    # while bone1 > len(bone_vertex_groups):
                    #     bone_vertex_groups.append([])
                    
                    # if (bone2 != 255):
                    #     while bone2 > len(bone_vertex_groups):
                    #         bone_vertex_groups.append([])
                    #     bone_vertex_groups[bone2 - 1].append([j, bone2_weight])
                    
                    # bone_vertex_groups[bone1 - 1].append([j, bone1_weight])

                    b_num = bone1

                #add vertex to vertex list
                new_point = [x,y,z]
                verts.append(new_point)

                #add uv point to uvs
                new_uv_point = [uc,vc]
                uvs.append(new_uv_point)

            #bone_vert_counts.append(bone_v_counter)
            #---vert section end---
            #---bone section start---
            #skip if no bones
            if(b_nums[i] != 0):
                bones = []
                bones_temp = []
                #set root
                if has_root:
                    rz1 = read_sshort(model_bin)
                    rx1 = read_sshort(model_bin)
                    ry1 = read_sshort(model_bin)   
                    
                    model_bin.seek(2, 1)
                    
                    rx = rx1 * 0.001
                    ry = ry1 * 0.001
                    rz = rz1 * 0.001

                    #add bone to bones list
                    new_joint = [rx,ry,rz]
                    bones_temp.append(new_joint)
                    bones.append(new_joint)
                else:
                    bones.append ([0,0,0])
                    bones_temp.append([0,0,0])
                    model_bin.seek(8,1)
                
                bone_parents = []

                for j in range(b_num):
                    
                    #read bone position, each one is relative to its parent
                    bz1 = read_sshort(model_bin)
                    bx1 = read_sshort(model_bin)
                    by1 = read_sshort(model_bin)   
                    
                    model_bin.seek(2, 1)
                    
                    bx = bx1 * 0.001
                    by = by1 * 0.001
                    bz = bz1 * 0.001

                    #add bone to bones list
                    new_joint = [bx,by,bz]
                    bones_temp.append(new_joint)
                    bones.append(new_joint)

                model_bin.seek(1, 1)

                for j in range(b_num):
                    cur_bone = read_byte(model_bin)
                    bone_parents.append(cur_bone)
                    bones[j + 1][0] += bones_temp[cur_bone][0] 
                    bones[j + 1][1] += bones_temp[cur_bone][1]
                    bones[j + 1][2] += bones_temp[cur_bone][2]

                #skip padding if any...
                p_padding = ceil((b_nums[i]*8 + b_nums[i]) / 8) * 8
                model_bin.seek(p_padding - (b_nums[i]*8 +b_nums[i]), 1)
                #---heirarchy section end---
                
                #adjust vertex position so it's relative to bone position
                v_inc = 0
                b_inc = 0
                for v in range(len(verts)):
                        
                        b1 = vertex_bone_weights[v][0][0]
                        b2 = vertex_bone_weights[v][1][0]
                        verts[v][0] += bones[b1][0]
                        verts[v][1] += bones[b1][1]
                        verts[v][2] += bones[b1][2]

                        if (b2 != 255):
                            bw1 = vertex_bone_weights[v][0][1]
                            bw2 = vertex_bone_weights[v][1][1]

                            verts2[v][0] += bones[b2][0]
                            verts2[v][1] += bones[b2][1]
                            verts2[v][2] += bones[b2][2]
                            
                            
                            #average positions
                            verts[v][0] = (verts[v][0] * bw1) + (verts2[v][0] * bw2)
                            verts[v][1] = (verts[v][1] * bw1) + (verts2[v][1] * bw2)
                            verts[v][2] = (verts[v][2] * bw1) + (verts2[v][2] * bw2)
                            # verts[v][0] = verts2[v][0] 
                            # verts[v][1] = verts2[v][1] 
                            # verts[v][2] = verts2[v][2]
                

                # if(has_root):
                    
                #         # verts[v][0] += bones[b_inc][0]
                #         # verts[v][1] += bones[b_inc][1]
                #         # verts[v][2] += bones[b_inc][2]

                #     for vert in verts:
                #         vert[0] += bones[b_inc][0]
                #         vert[1] += bones[b_inc][1]
                #         vert[2] += bones[b_inc][2]
                #         v_inc += 1

                #         if(v_inc == bone_vert_counts[b_inc]):            
                #             v_inc = 0
                #             b_inc += 1
                # else:
                #     for vert in verts:
                #         vert[0] += bones[b_inc + 1][0]
                #         vert[1] += bones[b_inc + 1][1]
                #         vert[2] += bones[b_inc + 1][2]
                #         v_inc += 1

                #         if(v_inc == bone_vert_counts[b_inc]):            
                #             v_inc = 0
                #             b_inc += 1
                
                #---bone section end---

                i_obj = make_mesh(verts, obm_names[i], faces, uvs, vertex_bone_weights, len(bones))
                a_obj = make_armature(bones, bone_parents, obm_names[i])
                i_obj.parent = a_obj
                n_mod = i_obj.modifiers.new("Armature",'ARMATURE')
                n_mod.object = a_obj

                # if(i == 0 or i == 4):
                #     #Need to set this manually to the rotations of each vertex group about the bone sorry><
                #     #x,y,z
                #     rotations = [[0,180,0],[-90,0,0],[0,180,0],[-90,0,0],[180,-90,0],[-90,0,0],[180,90,0],[-90,0,0],[0,180,0],[0,180,0],[0,180,0],[0,180,0],[0,180,0],[180,0,0]]
                #     #bone index of start of chain, does the transforms in order of this list so 
                #     #make sure it's ordered correctly
                #     chain_starts = [2,5,6,9,14,17,28,31,42,43,44,45,46,47]
                #     fix_rotations(i_obj.data, a_obj.data, bone_vert_counts, chain_starts, rotations)

            else:
                i_obj = make_mesh(verts, obm_names[i], faces, uvs)

            add_material_indices_obj(i_obj, material_face_count)

def mwld_valid(file):
    fn, ft = os.path.splitext(file)
    if (ft == '.gcn' or ft == '.mwld'):
        mwld_import(fn + ft)
    else:
        print("not an mwld")



class OT_mwld_import(bpy.types.Operator, ImportHelper):
    bl_idname = 'file.import_mwld'
    bl_label = 'import mwld/gcn file'

    def execute(self, context):
        mwld_valid(self.filepath)
        return {'FINISHED'}

class VIEW3D_PT_import_mwld(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Model_imports"
    bl_label = "Mwld"

    def draw(self, context):
        layout = self.layout
        layout.operator("file.import_mwld")

def register():
    bpy.utils.register_class(OT_mwld_import)
    bpy.utils.register_class(VIEW3D_PT_import_mwld)

def unregister():
    bpy.utils.unregister_class(OT_mwld_import)
    bpy.utils.unregister_class(VIEW3D_PT_import_mwld)

if __name__ == "__main__":
    register()
    #main()
