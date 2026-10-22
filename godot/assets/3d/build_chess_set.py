"""Generate the Aster chess piece set and a composed preview using Blender.

Run with:
  blender --background --python build_chess_set.py

The exported GLB contains twelve independently named roots. Each root sits at
the center of a board square (XY origin, foot at Z=0), with its geometry as
children. Coordinates are meters; the nominal square width is 1.0 m.
"""

import math
import os
import bpy
from mathutils import Vector


OUT_DIR = os.path.dirname(os.path.abspath(__file__))
GLB_PATH = os.path.join(OUT_DIR, "aster_chess_set.glb")
PREVIEW_PATH = os.path.join(OUT_DIR, "aster_chess_set_preview.png")
SEGMENTS = 48


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for item in list(datablocks):
            if item.users == 0:
                datablocks.remove(item)


def material(name, color, metallic=0.0, roughness=0.34):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


IVORY = material("Porcelain | warm ivory", (0.88, 0.81, 0.67), 0.06, 0.27)
GREEN = material("Enamel | deep forest", (0.075, 0.24, 0.18), 0.12, 0.25)
BRASS = material("Inlay | brushed champagne", (0.65, 0.42, 0.19), 0.72, 0.24)
DARK = material("Eye | polished obsidian", (0.018, 0.025, 0.022), 0.18, 0.18)


def parent_piece(name):
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "CIRCLE"
    root.empty_display_size = 0.12
    return root


def add_mesh_obj(name, verts, faces, mat, root, smooth=False):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = root
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    return obj


def lathe(name, profile, mat, root, segments=SEGMENTS):
    """Revolve (radius, height) points around Z; closed capped manifold."""
    verts, faces = [], []
    for radius, z in profile:
        for i in range(segments):
            a = math.tau * i / segments
            verts.append((radius * math.cos(a), radius * math.sin(a), z))
    for j in range(len(profile) - 1):
        for i in range(segments):
            a = j * segments + i
            b = j * segments + (i + 1) % segments
            c = (j + 1) * segments + (i + 1) % segments
            d = (j + 1) * segments + i
            faces.append((a, b, c, d))
    faces.append(tuple(range(segments - 1, -1, -1)))
    faces.append(tuple((len(profile) - 1) * segments + i for i in range(segments)))
    obj = add_mesh_obj(name, verts, faces, mat, root, smooth=True)
    bevel = obj.modifiers.new("Soft polished transitions", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(30)
    obj.modifiers.new("Weighted studio normals", "WEIGHTED_NORMAL")
    return obj


def uv_sphere(name, loc, scale, mat, root, seg=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.parent = root
    obj.location = loc
    obj.scale = scale
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def cube(name, loc, scale, mat, root, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.parent = root
    obj.location = loc
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Rounded machined edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def make_knight_silhouette(name, mat, root):
    """Low-poly, beveled horse-head profile extruded through the Y axis."""
    outline = [
        (-0.30, 0.17), (-0.36, 0.34), (-0.31, 0.53), (-0.18, 0.72),
        (-0.17, 0.91), (-0.30, 1.13), (-0.24, 1.35), (-0.06, 1.25),
        (0.08, 1.34), (0.19, 1.31), (0.13, 1.18), (0.31, 1.12),
        (0.34, 1.02), (0.24, 0.95), (0.12, 0.93), (0.21, 0.78),
        (0.33, 0.55), (0.34, 0.34), (0.25, 0.17),
    ]
    thickness = 0.25
    n = len(outline)
    verts = [(x, -thickness / 2, z) for x, z in outline]
    verts += [(x, thickness / 2, z) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))[::-1]]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    obj = add_mesh_obj(name, verts, faces, mat, root)
    bevel = obj.modifiers.new("Sculpted edge glints", "BEVEL")
    bevel.width = 0.045
    bevel.segments = 3
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    # Eye studs on each side and a brass bridle accent at the cheek.
    for side in (-1, 1):
        uv_sphere(name + " | obsidian eye", (0.015, side * 0.14, 1.115),
                  (0.033, 0.018, 0.033), DARK, root, 16, 10)
        uv_sphere(name + " | bridle stud", (0.205, side * 0.14, 0.99),
                  (0.023, 0.017, 0.023), BRASS, root, 12, 8)
    return obj


def piece_profile(kind):
    base = [(0.0, 0.025), (0.31, 0.025), (0.36, 0.06), (0.37, 0.105),
            (0.34, 0.15), (0.29, 0.18), (0.27, 0.22), (0.28, 0.25),
            (0.25, 0.28)]
    profiles = {
        "P": base + [(0.20, 0.31), (0.16, 0.38), (0.14, 0.52),
                     (0.19, 0.57), (0.20, 0.62), (0.15, 0.66), (0.0, 0.66)],
        "R": base + [(0.20, 0.31), (0.23, 0.38), (0.22, 0.72),
                     (0.29, 0.75), (0.30, 0.81), (0.0, 0.81)],
        "N": base + [(0.20, 0.31), (0.25, 0.36), (0.26, 0.45), (0.0, 0.45)],
        "B": base + [(0.20, 0.31), (0.18, 0.40), (0.16, 0.53),
                     (0.11, 0.68), (0.08, 0.82), (0.13, 0.87),
                     (0.16, 0.91), (0.13, 0.94), (0.08, 0.90),
                     (0.06, 0.86), (0.0, 0.86)],
        "Q": base + [(0.20, 0.31), (0.19, 0.39), (0.23, 0.48),
                     (0.26, 0.57), (0.22, 0.64), (0.16, 0.69),
                     (0.13, 0.74), (0.0, 0.74)],
        "K": base + [(0.20, 0.31), (0.19, 0.39), (0.23, 0.49),
                     (0.26, 0.58), (0.22, 0.65), (0.16, 0.70),
                     (0.13, 0.76), (0.0, 0.76)],
    }
    return profiles[kind]


def build_piece(color, kind, mat):
    code = kind.upper() if color == "White" else kind.lower()
    root = parent_piece("Aster_" + color + "_" + {
        "P": "Pawn", "N": "Knight", "B": "Bishop", "R": "Rook", "Q": "Queen", "K": "King"
    }[kind])
    # Shared silhouette language: broad, stable foot; softened profile; slim inlay.
    lathe(code + " | body", piece_profile(kind), mat, root)
    # Hairline metal ring catches light and separates the body from the board.
    lathe(code + " | foot inlay", [(0.335, 0.16), (0.342, 0.17),
                                    (0.342, 0.185), (0.325, 0.195)], BRASS, root)
    if kind == "P":
        lathe(code + " | neck ring", [(0.145, 0.51), (0.156, 0.52),
                                       (0.156, 0.54), (0.14, 0.55)], BRASS, root)
        uv_sphere(code + " | orb", (0, 0, 0.705), (0.155, 0.155, 0.155), mat, root)
    elif kind == "R":
        # Six rounded crenellations make a legible rook crown without a noisy skyline.
        for i in range(6):
            a = math.tau * i / 6
            x, y = 0.215 * math.cos(a), 0.215 * math.sin(a)
            cube(code + " | merlon %02d" % (i + 1), (x, y, 0.865),
                 (0.105, 0.105, 0.13), mat, root, 0.018)
        lathe(code + " | crown band", [(0.285, 0.785), (0.30, 0.80),
                                        (0.30, 0.825), (0.28, 0.84)], BRASS, root)
    elif kind == "N":
        # A subtly contrasting raised mane makes the horse read in profile.
        make_knight_silhouette(code + " | horse head", mat, root)
        lathe(code + " | collar", [(0.235, 0.38), (0.26, 0.395),
                                    (0.26, 0.42), (0.23, 0.435)], BRASS, root)
    elif kind == "B":
        # The bishop's traditional split is represented by a slim inset slash.
        uv_sphere(code + " | mitre jewel", (0, 0, 0.885), (0.055, 0.055, 0.055), BRASS, root)
        # Diagonal, narrow brass slit sits on the front-facing side of the mitre.
        cube(code + " | mitre incision", (0.0, -0.073, 0.70), (0.027, 0.025, 0.19), BRASS, root, 0.009)
        bpy.data.objects[code + " | mitre incision"].rotation_euler[1] = math.radians(28)
    elif kind == "Q":
        lathe(code + " | crown rail", [(0.13, 0.70), (0.18, 0.72),
                                        (0.18, 0.75), (0.13, 0.77)], BRASS, root)
        for i in range(5):
            a = math.tau * i / 5 + math.pi / 2
            uv_sphere(code + " | crown pearl %d" % i,
                      (0.14 * math.cos(a), 0.14 * math.sin(a), 0.81),
                      (0.045, 0.045, 0.045), BRASS, root, 16, 10)
    elif kind == "K":
        lathe(code + " | crown rail", [(0.13, 0.73), (0.18, 0.75),
                                        (0.18, 0.78), (0.13, 0.80)], BRASS, root)
        cube(code + " | cross upright", (0, 0, 0.90), (0.065, 0.065, 0.25), mat, root, 0.018)
        cube(code + " | cross arms", (0, 0, 0.94), (0.21, 0.065, 0.065), mat, root, 0.018)
    return root


def create_preview_stage(roots):
    """Render two ranks with a simple checker plinth; stage is excluded from GLB."""
    square_light = material("Preview | limestone", (0.75, 0.69, 0.57), 0.02, 0.72)
    square_dark = material("Preview | deep moss", (0.15, 0.30, 0.23), 0.02, 0.72)
    floor_mat = material("Preview | backdrop", (0.075, 0.095, 0.085), 0.0, 0.82)
    # Put the pieces on a 6 x 2 arrangement at board-square centers.
    for row, color in enumerate(("White", "Black")):
        for col, kind in enumerate(("K", "Q", "B", "N", "R", "P")):
            root = roots[(color, kind)]
            root.location = (col - 2.5, (0.75 if row == 0 else -0.75), 0.0)
    for row in range(2):
        for col in range(6):
            mat = square_light if (row + col) % 2 == 0 else square_dark
            cube("Preview board tile", (col - 2.5, (0.75 if row == 0 else -0.75), -0.10),
                 (0.98, 1.30, 0.20), mat, None, 0.035)
    cube("Preview ground", (0, 0, -0.24), (9.2, 4.2, 0.16), floor_mat, None, 0.08)

    bpy.ops.object.camera_add(location=(6.5, -10.5, 9.3))
    camera = bpy.context.object
    camera.name = "Preview camera"
    target = Vector((0.0, 0.0, 0.47))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 9.5
    bpy.context.scene.camera = camera

    for name, loc, energy, size, color in [
        ("Key | warm softbox", (0, -4, 8), 1500, 7.0, (1.0, 0.86, 0.67)),
        ("Fill | cool softbox", (4, 2, 6), 1100, 6.0, (0.72, 0.84, 1.0)),
        ("Rim | softbox", (-5, 1, 4), 900, 5.0, (1.0, 0.72, 0.42)),
    ]:
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (Vector((0, 0, 0.4)) - light.location).to_track_quat("-Z", "Y").to_euler()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1150
    scene.render.resolution_y = 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = PREVIEW_PATH
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.world.color = (0.19, 0.19, 0.19)
    scene.view_settings.view_transform = "AgX"


def export_glb():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type in {"MESH", "EMPTY"} and not obj.name.startswith("Preview"):
            obj.select_set(True)
    bpy.context.view_layer.objects.active = next(
        obj for obj in bpy.context.scene.objects
        if obj.select_get() and obj.type == "MESH"
    )
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_lights=False,
        export_cameras=False,
        export_materials="EXPORT",
        export_image_format="AUTO",
    )


def main():
    clear_scene()
    roots = {}
    for color, mat in (("White", IVORY), ("Black", GREEN)):
        for kind in ("P", "N", "B", "R", "Q", "K"):
            roots[(color, kind)] = build_piece(color, kind, mat)
    export_glb()
    create_preview_stage(roots)
    bpy.ops.render.render(write_still=True)
    print("ASTER_CHESS_SET_GLB=" + GLB_PATH)
    print("ASTER_CHESS_SET_PREVIEW=" + PREVIEW_PATH)
    print("ASTER_PIECE_ROOTS=" + ",".join(sorted(root.name for root in roots.values())))
    print("ASTER_EXPORT_MESHES=" + str(sum(1 for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("Preview"))))
    print("ASTER_GLB_BYTES=" + str(os.path.getsize(GLB_PATH)))


if __name__ == "__main__":
    main()
