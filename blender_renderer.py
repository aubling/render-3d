import bpy, sys, json, math
from pathlib import Path

MM = 0.001
COUNTER = 0.032
KICK = 0.100

def mm(v): return v * MM

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

def make_mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = 0.55
    return m

def mat_for(color):
    c = (color or "").lower()
    if "white" in c: return MAT_WHITE
    if "brookhill" in c: return MAT_BROOKHILL
    if "shale" in c: return MAT_SHALE
    return MAT_PEARL

def cube(name, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o

def handle(name, loc, vertical=True):
    return cube(name, loc, (0.018, 0.018, 0.28) if vertical else (0.32, 0.018, 0.018), MAT_HANDLE)

def text_label(txt, loc):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(70), 0, 0))
    o = bpy.context.object
    o.data.body = str(txt)
    o.data.size = 0.16
    o.data.align_x = "CENTER"
    o.data.align_y = "CENTER"
    o.data.materials.append(MAT_BLACK)

def front_doors_y(prefix, x, y, z, w, h, doors, material):
    if doors <= 1:
        cube(prefix+"_door", (x, y-0.012, z+h/2), (w*0.94, 0.018, h*0.9), material)
        handle(prefix+"_h", (x+w*0.32, y-0.03, z+h*0.52), True)
    else:
        pw = w/doors
        start = x - w/2 + pw/2
        for i in range(doors):
            cx = start + i*pw
            cube(f"{prefix}_door_{i+1}", (cx, y-0.012, z+h/2), (pw*0.92, 0.018, h*0.9), material)
            handle(f"{prefix}_h_{i+1}", (cx + pw*(0.25 if i == 0 else -0.25), y-0.03, z+h*0.52), True)

def drawers_y(prefix, x, y, z, w, h, material):
    dh = h/3
    for i in range(3):
        cz = z + dh*i + dh/2
        cube(f"{prefix}_drawer_{i+1}", (x, y-0.012, cz), (w*0.94, 0.018, dh*0.82), material)
        handle(f"{prefix}_dh_{i+1}", (x, y-0.03, cz), False)

def front_doors_x(prefix, x, y, z, w, h, doors, material):
    if doors <= 1:
        cube(prefix+"_door", (x+0.012, y, z+h/2), (0.018, w*0.94, h*0.9), material)
        handle(prefix+"_h", (x+0.03, y+w*0.32, z+h*0.52), True)
    else:
        pw = w/doors
        start = y - w/2 + pw/2
        for i in range(doors):
            cy = start + i*pw
            cube(f"{prefix}_door_{i+1}", (x+0.012, cy, z+h/2), (0.018, pw*0.92, h*0.9), material)
            handle(f"{prefix}_h_{i+1}", (x+0.03, cy + pw*(0.25 if i == 0 else -0.25), z+h*0.52), True)

def drawers_x(prefix, x, y, z, w, h, material):
    dh = h/3
    for i in range(3):
        cz = z + dh*i + dh/2
        cube(f"{prefix}_drawer_{i+1}", (x+0.012, y, cz), (0.018, w*0.94, dh*0.82), material)
        handle(f"{prefix}_dh_{i+1}", (x+0.03, y, cz), False)

def base_unit(unit, idx, pos, direction):
    x, y = pos
    w, d, h = mm(unit["width"]), mm(unit["depth"]), mm(unit["height"])
    material = mat_for(unit.get("color"))
    doors = int(unit.get("doors", 1))
    drawer = "drawer" in unit.get("unit_type","").lower()

    if direction == 0:
        cx, cy = x+w/2, y-d/2
        cube(f"{idx}_base", (cx, cy, h/2), (w, d, h), material)
        cube(f"{idx}_kick", (cx, y-0.025, KICK/2), (w, 0.05, KICK), MAT_DARK)
        cube(f"{idx}_top", (cx, cy, h+COUNTER/2), (w+0.04, d+0.04, COUNTER), MAT_COUNTER)
        (drawers_y if drawer else front_doors_y)(str(idx), cx, y, KICK, w, h-KICK, material) if drawer else front_doors_y(str(idx), cx, y, KICK, w, h-KICK, doors, material)
        text_label(idx, (cx, cy, h+0.20))
        return (x+w, y), (x, y-d, w, d, direction)

    if direction == 90:
        cx, cy = x+d/2, y+w/2
        cube(f"{idx}_base", (cx, cy, h/2), (d, w, h), material)
        cube(f"{idx}_kick", (x+d-0.025, cy, KICK/2), (0.05, w, KICK), MAT_DARK)
        cube(f"{idx}_top", (cx, cy, h+COUNTER/2), (d+0.04, w+0.04, COUNTER), MAT_COUNTER)
        if drawer: drawers_x(str(idx), x+d, cy, KICK, w, h-KICK, material)
        else: front_doors_x(str(idx), x+d, cy, KICK, w, h-KICK, doors, material)
        text_label(idx, (cx, cy, h+0.20))
        return (x, y+w), (x, y, d, w, direction)

    # simplified for third run
    cx, cy = x-w/2, y+d/2
    cube(f"{idx}_base", (cx, cy, h/2), (w, d, h), material)
    cube(f"{idx}_top", (cx, cy, h+COUNTER/2), (w+0.04, d+0.04, COUNTER), MAT_COUNTER)
    text_label(idx, (cx, cy, h+0.20))
    return (x-w, y), (x-w, y, w, d, direction)

def tall_unit(unit, idx, pos, direction):
    x, y = pos
    w, d, h = mm(unit["width"]), mm(unit["depth"]), mm(unit["height"])
    material = mat_for(unit.get("color"))
    doors = int(unit.get("doors", 1))
    if direction == 0:
        cx, cy = x+w/2, y-d/2
        cube(f"{idx}_tall", (cx, cy, h/2), (w, d, h), material)
        front_doors_y(str(idx), cx, y, KICK, w, h-KICK, doors, material)
        text_label(idx, (cx, cy, h+0.20))
        return (x+w, y), (x, y-d, w, d, direction)
    if direction == 90:
        cx, cy = x+d/2, y+w/2
        cube(f"{idx}_tall", (cx, cy, h/2), (d, w, h), material)
        front_doors_x(str(idx), x+d, cy, KICK, w, h-KICK, doors, material)
        text_label(idx, (cx, cy, h+0.20))
        return (x, y+w), (x, y, d, w, direction)
    return base_unit(unit, idx, pos, direction)

def wall_unit(unit, idx, last_base):
    if not last_base: return
    x, y, w_base, d_base, direction = last_base
    w, d, h = mm(unit["width"]), mm(unit["depth"]), mm(unit["height"])
    material = mat_for(unit.get("color"))
    z = 1.35
    if direction == 0:
        cx, cy = x+w_base/2, y-d-0.06
        cube(f"{idx}_wall", (cx, cy, z+h/2), (w, d, h), material)
        front_doors_y(str(idx), cx, cy+d/2+0.01, z, w, h, int(unit.get("doors",1)), material)
        text_label(idx, (cx, cy, z+h+0.12))
    elif direction == 90:
        cx, cy = x+w_base+d/2+0.06, y+d_base/2
        cube(f"{idx}_wall", (cx, cy, z+h/2), (d, w, h), material)
        front_doors_x(str(idx), cx-d/2-0.01, cy, z, w, h, int(unit.get("doors",1)), material)
        text_label(idx, (cx, cy, z+h+0.12))

def pantry(unit, idx, pos, direction):
    x, y = pos
    w, d, h = mm(unit["width"]), mm(unit["depth"]), mm(unit["height"])
    material = mat_for(unit.get("color"))
    if direction == 0:
        cube(f"{idx}_pantry_a", (x+w/2, y-d/2, h/2), (w, d, h), material)
        cube(f"{idx}_pantry_b", (x+w-d/2, y-w/2, h/2), (d, w, h), material)
        door = cube(f"{idx}_diagonal_420_door", (x+d/2, y-(d+(w-d)/2), h/2), (0.42, 0.025, h*0.90), material)
        door.rotation_euler[2] = math.radians(-45)
        handle(f"{idx}_pantry_handle", (x+d/2+0.08, y-(d+(w-d)/2)-0.08, h*0.50), True)
        text_label(idx, (x+w/2, y-w/2, h+0.25))
        return (x+w, y-w), 90
    if direction == 90:
        cube(f"{idx}_pantry_a", (x+d/2, y+w/2, h/2), (d, w, h), material)
        cube(f"{idx}_pantry_b", (x+w/2, y+w-d/2, h/2), (w, d, h), material)
        text_label(idx, (x+w/2, y+w/2, h+0.25))
        return (x+w, y+w), 180
    return pos, direction

def floor_corner(unit, idx, pos, direction):
    x, y = pos
    w, d, h = mm(unit["width"]), mm(unit["depth"]), mm(unit["height"])
    door = w-d
    material = mat_for(unit.get("color"))
    if direction == 0:
        cube(f"{idx}_corner_a", (x+w/2, y-d/2, h/2), (w, d, h), material)
        cube(f"{idx}_corner_b", (x+w-d/2, y-w/2, h/2), (d, w, h), material)
        cube(f"{idx}_top_a", (x+w/2, y-d/2, h+COUNTER/2), (w+0.04, d+0.04, COUNTER), MAT_COUNTER)
        cube(f"{idx}_top_b", (x+w-d/2, y-w/2, h+COUNTER/2), (d+0.04, w+0.04, COUNTER), MAT_COUNTER)
        cube(f"{idx}_door_350_a", (x+door/2, y-0.012, KICK+(h-KICK)/2), (door*0.9, 0.018, (h-KICK)*0.9), material)
        cube(f"{idx}_door_350_b", (x+w+0.012, y-d-door/2, KICK+(h-KICK)/2), (0.018, door*0.9, (h-KICK)*0.9), material)
        handle(f"{idx}_h_a", (x+door*0.55, y-0.03, h*0.5), True)
        handle(f"{idx}_h_b", (x+w+0.03, y-d-door*0.55, h*0.5), True)
        text_label(idx, (x+w/2, y-w/2, h+0.20))
        return (x+w, y-w), 90
    if direction == 90:
        cube(f"{idx}_corner_a", (x+d/2, y+w/2, h/2), (d, w, h), material)
        cube(f"{idx}_corner_b", (x+w/2, y+w-d/2, h/2), (w, d, h), material)
        cube(f"{idx}_top_a", (x+d/2, y+w/2, h+COUNTER/2), (d+0.04, w+0.04, COUNTER), MAT_COUNTER)
        cube(f"{idx}_top_b", (x+w/2, y+w-d/2, h+COUNTER/2), (w+0.04, d+0.04, COUNTER), MAT_COUNTER)
        text_label(idx, (x+w/2, y+w/2, h+0.20))
        return (x+w, y+w), 180
    return pos, direction

def room():
    cube("floor", (1.6, -1.2, -0.02), (5.5, 5.0, 0.04), MAT_FLOOR)
    cube("wall_back", (1.6, 0.06, 1.25), (5.5, 0.08, 2.5), MAT_WALL)
    cube("wall_left", (-0.45, -1.2, 1.25), (0.08, 5.0, 2.5), MAT_WALL)

def light_camera():
    bpy.ops.object.light_add(type="AREA", location=(1.5, -3.0, 4.5))
    light = bpy.context.object
    light.data.energy = 850
    light.data.size = 5
    bpy.ops.object.camera_add(location=(3.8, -4.2, 2.4), rotation=(math.radians(62), 0, math.radians(38)))
    bpy.context.scene.camera = bpy.context.object

def render(data, out):
    clear()
    global MAT_PEARL, MAT_WHITE, MAT_BROOKHILL, MAT_SHALE, MAT_COUNTER, MAT_HANDLE, MAT_DARK, MAT_FLOOR, MAT_WALL, MAT_BLACK
    MAT_PEARL = make_mat("Pearl Grey", (0.50,0.48,0.42,1))
    MAT_WHITE = make_mat("White", (0.92,0.90,0.84,1))
    MAT_BROOKHILL = make_mat("Brookhill", (0.48,0.38,0.27,1))
    MAT_SHALE = make_mat("Washed Shale", (0.40,0.40,0.37,1))
    MAT_COUNTER = make_mat("Stone Top", (0.86,0.84,0.78,1))
    MAT_HANDLE = make_mat("Black Handles", (0.02,0.02,0.02,1))
    MAT_DARK = make_mat("Kickplate", (0.22,0.22,0.20,1))
    MAT_FLOOR = make_mat("Floor", (0.56,0.48,0.38,1))
    MAT_WALL = make_mat("Wall", (0.82,0.80,0.75,1))
    MAT_BLACK = make_mat("Black", (0,0,0,1))

    room()
    pos = (0.0, 0.0)
    direction = 0
    last_base = None

    for idx, unit in enumerate(data["units"], 1):
        t = unit.get("unit_type","").lower()
        if t == "wall":
            wall_unit(unit, idx, last_base)
        elif "pantry" in t:
            pos, direction = pantry(unit, idx, pos, direction)
            last_base = None
        elif "corner" in t:
            pos, direction = floor_corner(unit, idx, pos, direction)
            last_base = None
        elif "tall" in t:
            pos, last_base = tall_unit(unit, idx, pos, direction)
        else:
            pos, last_base = base_unit(unit, idx, pos, direction)

    light_camera()
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1100
    bpy.context.scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)

def main():
    args = sys.argv[sys.argv.index("--")+1:]
    data = json.loads(Path(args[0]).read_text())
    render(data, Path(args[1]))

if __name__ == "__main__":
    main()

