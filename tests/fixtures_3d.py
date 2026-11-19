"""Small original fixtures in mm unless the caller explicitly converts them."""
import math
from pathlib import Path
import struct
from zipfile import ZipFile, ZIP_DEFLATED


def ring_triangles(outer=10.0, bore=4.0, height=4.0, sides=96):
    result = []
    def point(i, radius, z):
        angle = 2 * math.pi * (i % sides) / sides
        return (radius * math.cos(angle), radius * math.sin(angle), z)
    for i in range(sides):
        a, b = i, i + 1
        for quad in (
            [point(a, outer, 0), point(b, outer, 0), point(b, outer, height), point(a, outer, height)],
            [point(b, bore, 0), point(a, bore, 0), point(a, bore, height), point(b, bore, height)],
            [point(a, outer, height), point(b, outer, height), point(b, bore, height), point(a, bore, height)],
            [point(a, bore, 0), point(b, bore, 0), point(b, outer, 0), point(a, outer, 0)],
        ):
            result.extend([(quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])])
    return result


def write_stl(path, faces, binary=True):
    if binary:
        with path.open("wb") as stream:
            stream.write(b"solid synthetic".ljust(80, b"\0") + struct.pack("<I", len(faces)))
            for tri in faces:
                stream.write(struct.pack("<12fH", 0, 0, 0, *(v for p in tri for v in p), 0))
    else:
        with path.open("w", encoding="ascii") as stream:
            print("solid test", file=stream)
            for tri in faces:
                print("facet normal 0 0 0\nouter loop", file=stream)
                for vertex in tri:
                    print("vertex", *vertex, file=stream)
                print("endloop\nendfacet", file=stream)
            print("endsolid test", file=stream)


def instanced_3mf(path, copies=2):
    # An asymmetric 1 by 2 by 0.5 inch box, instanced through a nested transform.
    points = [(x, y, z) for z in (0, 0.5) for y in (0, 2) for x in (0, 1)]
    faces = [(0,2,3),(0,3,1),(4,5,7),(4,7,6),(0,1,5),(0,5,4),
             (2,6,7),(2,7,3),(0,4,6),(0,6,2),(1,3,7),(1,7,5)]
    vertices = "".join(f'<vertex x="{x}" y="{y}" z="{z}"/>' for x,y,z in points)
    triangles = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in faces)
    placements = "".join(f'<item objectid="2" transform="1 0 0 0 1 0 0 0 1 {3*i} 0 0"/>' for i in range(copies))
    model = (f'<model unit="inch" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources><object id="1" type="model"><mesh><vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object>'
             f'<object id="2" type="model"><components><component objectid="1" transform="1 0 0 0 1 0 0 0 1 0 1 0"/>'
             f'</components></object></resources><build>{placements}</build></model>')
    with ZipFile(Path(path), "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        archive.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="model" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/></Relationships>')
        archive.writestr("3D/3dmodel.model", model)
