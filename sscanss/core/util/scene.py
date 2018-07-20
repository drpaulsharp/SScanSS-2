from enum import Enum, unique
from collections import namedtuple
import numpy as np
from .vector import Vector3
from .matrix import Matrix44
from .colour import Colour


BoundingBox = namedtuple('BoundingBox', ['max', 'min', 'center', 'radius'])


@unique
class RenderType(Enum):
    Solid = 'Solid'
    Wireframe = 'Wireframe'
    Transparent = 'Transparent'


class Node:
    def __init__(self):
        self.vertices = np.array([])
        self.indices = np.array([])
        self.normals = np.array([])
        self.bounding_box = None
        self.render_type = RenderType.Solid

        self.transform = Matrix44.identity()
        self.colour = None

        self.children = []


def createSampleNode(samples):
    sample_node = Node()
    sample_node.colour = Colour(0.4, 0.4, 0.4)
    sample_node.render_type = RenderType.Solid

    max_pos = [np.nan, np.nan, np.nan]
    min_pos = [np.nan, np.nan, np.nan]
    for _, sample in samples.items():
        child = Node()
        child.vertices = sample.vertices
        child.indices = sample.indices
        child.normals = sample.normals
        child.bounding_box = sample.bounding_box
        child.colour = None
        child.render_type = None

        sample_node.children.append(child)

        max_pos = np.fmax(max_pos, np.max(child.vertices, axis=0))
        min_pos = np.fmin(min_pos, np.min(child.vertices, axis=0))

    bb_max = Vector3(max_pos)
    bb_min = Vector3(min_pos)
    center = Vector3(bb_max + bb_min) / 2
    radius = np.linalg.norm(bb_max - bb_min) / 2

    sample_node.bounding_box = BoundingBox(bb_max, bb_min, center, radius)

    return sample_node


def createFiducialNode(fiducials):
    import sscanss.core.mesh.create as mesh

    fiducial_node = Node()
    fiducial_node.render_type = RenderType.Solid

    for point, enabled in fiducials:
        fiducial_mesh = mesh.create_sphere(5)
        fiducial_mesh.translate(point)

        child = Node()
        child.vertices = fiducial_mesh.vertices
        child.indices = fiducial_mesh.indices
        child.normals = fiducial_mesh.normals
        child.bounding_box = fiducial_mesh.bounding_box
        child.colour = Colour(0.4, 0.9, 0.4) if enabled else Colour(0.9, 0.4, 0.4)
        child.render_type = None

        fiducial_node.children.append(child)

    return fiducial_node
