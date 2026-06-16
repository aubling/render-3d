from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

app = FastAPI(title="Kitchen 3D Render API", version="1.0.0")


class Unit(BaseModel):
    unit_type: str
    width: int
    height: int
    depth: int
    color: str = "Pearl Grey"
    doors: int = 1


class RenderRequest(BaseModel):
    project_id: int
    units: List[Unit]


def is_pantry(t: str) -> bool:
    return "pantry" in t.lower()


def is_floor_corner(t: str) -> bool:
    t = t.lower()
    return "corner" in t and "pantry" not in t


def is_wall(t: str) -> bool:
    return t.lower().strip() == "wall"


def is_drawer(t: str) -> bool:
    return "drawer" in t.lower()


def color_for(name: str):
    n = (name or "").lower()
    if "white" in n:
        return (0.93, 0.91, 0.86)
    if "brookhill" in n:
        return (0.58, 0.50, 0.40)
    if "grey" in n or "gray" in n or "pearl" in n:
        return (0.55, 0.53, 0.48)
    return (0.58, 0.56, 0.50)


def cuboid_faces(x, y, z, w, d, h):
    p = [
        (x, y, z), (x+w, y, z), (x+w, y+d, z), (x, y+d, z),
        (x, y, z+h), (x+w, y, z+h), (x+w, y+d, z+h), (x, y+d, z+h)
    ]
    return [
        [p[0], p[1], p[2], p[3]],
        [p[4], p[5], p[6], p[7]],
        [p[0], p[1], p[5], p[4]],
        [p[2], p[3], p[7], p[6]],
        [p[1], p[2], p[6], p[5]],
        [p[3], p[0], p[4], p[7]],
    ]


def draw_cuboid(ax, x, y, z, w, d, h, color):
    faces = cuboid_faces(x, y, z, w, d, h)
    pc = Poly3DCollection(faces, facecolors=color, edgecolors="black", linewidths=0.5, alpha=1)
    ax.add_collection3d(pc)


def draw_details(ax, x, y, z, w, d, h, unit, direction):
    if direction == 0:
        fy = y - 3
        if is_drawer(unit.unit_type):
            for k in range(1, 3):
                zz = z + h * k / 3
                ax.plot([x, x+w], [fy, fy], [zz, zz], color="black", linewidth=1.5)
        elif unit.doors > 1:
            ax.plot([x+w/2, x+w/2], [fy, fy], [z, z+h], color="black", linewidth=1.2)
    elif direction == 90:
        fx = x + 3
        if is_drawer(unit.unit_type):
            for k in range(1, 3):
                zz = z + h * k / 3
                ax.plot([fx, fx], [y, y+d], [zz, zz], color="black", linewidth=1.5)
        elif unit.doors > 1:
            ax.plot([fx, fx], [y+d/2, y+d/2], [z, z+h], color="black", linewidth=1.2)


def place_normal(ax, pos, direction, unit, idx, base_records):
    x, y = pos
    c = color_for(unit.color)
    w, d, h = unit.width, unit.depth, unit.height

    if direction == 0:
        draw_cuboid(ax, x, y-d, 0, w, d, h, c)
        draw_details(ax, x, y-d, 0, w, d, h, unit, 0)
        ax.text(x+w/2, y-d/2, h+40, str(idx), fontsize=9)
        base_records.append((x, y-d, w, d, direction))
        return (x+w, y)
    if direction == 90:
        draw_cuboid(ax, x, y, 0, d, w, h, c)
        draw_details(ax, x+d, y, 0, d, w, h, unit, 90)
        ax.text(x+d/2, y+w/2, h+40, str(idx), fontsize=9)
        base_records.append((x, y, d, w, direction))
        return (x, y+w)
    if direction == 180:
        draw_cuboid(ax, x-w, y, 0, w, d, h, c)
        ax.text(x-w/2, y+d/2, h+40, str(idx), fontsize=9)
        base_records.append((x-w, y, w, d, direction))
        return (x-w, y)
    draw_cuboid(ax, x-d, y-w, 0, d, w, h, c)
    ax.text(x-d/2, y-w/2, h+40, str(idx), fontsize=9)
    base_records.append((x-d, y-w, d, w, direction))
    return (x, y-w)


def place_wall(ax, unit, idx, last_base):
    if not last_base:
        return
    x, y, w, d, direction = last_base
    c = color_for(unit.color)
    z = 1450
    h = unit.height
    dep = unit.depth

    if direction == 0:
        draw_cuboid(ax, x, y-dep-30, z, unit.width, dep, h, c)
        ax.text(x+unit.width/2, y-dep/2, z+h+40, str(idx), fontsize=9)
    elif direction == 90:
        draw_cuboid(ax, x+w+30, y, z, dep, unit.width, h, c)
        ax.text(x+w+dep/2, y+unit.width/2, z+h+40, str(idx), fontsize=9)


def place_pantry(ax, pos, direction, unit, idx):
    x, y = pos
    w, d, h = unit.width, unit.depth, unit.height
    c = color_for(unit.color)

    if direction == 0:
        draw_cuboid(ax, x, y-d, 0, w, d, h, c)
        draw_cuboid(ax, x+w-d, y-w, 0, d, w, h, c)
        ax.plot([x, x+d], [y-d, y-w], [h+10, h+10], color="black", linewidth=4)
        ax.text(x+w/2, y-w/2, h+80, str(idx), fontsize=9)
        return (x+w, y-w), 90
    if direction == 90:
        draw_cuboid(ax, x, y, 0, d, w, h, c)
        draw_cuboid(ax, x, y+w-d, 0, w, d, h, c)
        ax.text(x+w/2, y+w/2, h+80, str(idx), fontsize=9)
        return (x+w, y+w), 180
    if direction == 180:
        draw_cuboid(ax, x-w, y, 0, w, d, h, c)
        draw_cuboid(ax, x-w, y, 0, d, w, h, c)
        ax.text(x-w/2, y+w/2, h+80, str(idx), fontsize=9)
        return (x-w, y+w), 270
    draw_cuboid(ax, x-d, y-w, 0, d, w, h, c)
    draw_cuboid(ax, x-w, y-w, 0, w, d, h, c)
    ax.text(x-w/2, y-w/2, h+80, str(idx), fontsize=9)
    return (x-w, y-w), 0


def place_floor_corner(ax, pos, direction, unit, idx):
    x, y = pos
    w, d, h = unit.width, unit.depth, unit.height
    c = color_for(unit.color)

    if direction == 0:
        draw_cuboid(ax, x, y-d, 0, w, d, h, c)
        draw_cuboid(ax, x+w-d, y-w, 0, d, w, h, c)
        ax.text(x+w/2, y-w/2, h+60, str(idx), fontsize=9)
        return (x+w, y-w), 90
    if direction == 90:
        draw_cuboid(ax, x, y, 0, d, w, h, c)
        draw_cuboid(ax, x, y+w-d, 0, w, d, h, c)
        ax.text(x+w/2, y+w/2, h+60, str(idx), fontsize=9)
        return (x+w, y+w), 180
    if direction == 180:
        draw_cuboid(ax, x-w, y, 0, w, d, h, c)
        draw_cuboid(ax, x-w, y, 0, d, w, h, c)
        ax.text(x-w/2, y+w/2, h+60, str(idx), fontsize=9)
        return (x-w, y+w), 270
    draw_cuboid(ax, x-d, y-w, 0, d, w, h, c)
    draw_cuboid(ax, x-w, y-w, 0, w, d, h, c)
    ax.text(x-w/2, y-w/2, h+60, str(idx), fontsize=9)
    return (x-w, y-w), 0


@app.get("/")
def health():
    return {"status": "ok", "service": "Kitchen 3D Render API"}


@app.post("/render-3d")
def render_3d(data: RenderRequest):
    fig = plt.figure(figsize=(14, 9))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_title(f"Kitchen 3D Render - Project {data.project_id}")

    pos = (0, 0)
    direction = 0
    base_records = []
    last_base = None

    for idx, unit in enumerate(data.units, start=1):
        if is_wall(unit.unit_type):
            place_wall(ax, unit, idx, last_base)
            continue

        if is_pantry(unit.unit_type):
            pos, direction = place_pantry(ax, pos, direction, unit, idx)
            last_base = None
            continue

        if is_floor_corner(unit.unit_type):
            pos, direction = place_floor_corner(ax, pos, direction, unit, idx)
            last_base = None
            continue

        old_count = len(base_records)
        pos = place_normal(ax, pos, direction, unit, idx, base_records)
        if len(base_records) > old_count:
            last_base = base_records[-1]

    all_x, all_y = [], []
    for x, y, w, d, _ in base_records:
        all_x += [x, x+w]
        all_y += [y, y+d]

    if not all_x:
        all_x = [-500, 2500]
        all_y = [-2500, 1000]

    ax.set_xlim(min(all_x)-1200, max(all_x)+1600)
    ax.set_ylim(min(all_y)-1800, max(all_y)+1200)
    ax.set_zlim(0, 2600)
    ax.set_xlabel("Width")
    ax.set_ylabel("Depth")
    ax.set_zlabel("Height")
    ax.view_init(elev=24, azim=-55)
    ax.set_box_aspect((1.6, 1.2, 0.8))
    ax.grid(False)

    buffer = BytesIO()
    plt.tight_layout()
    fig.savefig(buffer, format="png", dpi=160)
    plt.close(fig)
    buffer.seek(0)
    return Response(content=buffer.read(), media_type="image/png")