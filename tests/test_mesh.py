import unittest
import numpy as np
from sscanss.core.math import Vector3, matrix_from_xyz_eulers, Plane
from sscanss.core.mesh import (Mesh, closest_triangle_to_point, closest_point_on_triangle,
                               mesh_plane_intersection, segment_plane_intersection, BoundingBox)


class TestMeshClass(unittest.TestCase):
    def setUp(self):
        vertices = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        normals = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
        indices = np.array([0, 1, 2])
        self.mesh_1 = Mesh(vertices, indices, normals)

        vertices = np.array([[7, 8, 9], [4, 5, 6], [1, 2, 3]])
        normals = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
        indices = np.array([1, 0, 2])
        self.mesh_2 = Mesh(vertices, indices, normals)

    def testComputeNormals(self):
        vertices = np.array([[1, 1, 0], [1, 0, 0], [0, 1, 0]])
        indices = np.array([1, 0, 2])
        mesh = Mesh(vertices, indices)

        expected = np.array([[0, 0, 1], [0, 0, 1], [0, 0, 1]])

        # Check that correct normals are generated also vertices and indices are unchanged
        np.testing.assert_array_almost_equal(mesh.vertices, vertices, decimal=5)
        np.testing.assert_array_almost_equal(mesh.normals, expected, decimal=5)
        np.testing.assert_array_equal(mesh.indices, indices)

    def testComputeBoundingBox(self):
        box = self.mesh_1.bounding_box
        np.testing.assert_array_almost_equal(box.max, np.array([7, 8, 9]), decimal=5)
        np.testing.assert_array_almost_equal(box.min, np.array([1, 2, 3]), decimal=5)
        np.testing.assert_array_almost_equal(box.center, np.array([4., 5., 6.]), decimal=5)
        self.assertAlmostEqual(box.radius, 5.1961524, 5)

        box = self.mesh_2.bounding_box
        np.testing.assert_array_almost_equal(box.max, np.array([7, 8, 9]), decimal=5)
        np.testing.assert_array_almost_equal(box.min, np.array([1, 2, 3]), decimal=5)
        np.testing.assert_array_almost_equal(box.center, np.array([4., 5., 6.]), decimal=5)
        self.assertAlmostEqual(box.radius, 5.1961524, 5)

    def testAppendAndSplit(self):
        self.mesh_1.append(self.mesh_2)

        vertices = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [7, 8, 9], [4, 5, 6], [1, 2, 3]])
        normals = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]])
        indices = np.array([0, 1, 2, 4, 3, 5])

        np.testing.assert_array_almost_equal(self.mesh_1.vertices, vertices, decimal=5)
        np.testing.assert_array_almost_equal(self.mesh_1.normals, normals, decimal=5)
        np.testing.assert_array_equal(self.mesh_1.indices, indices)

        split_mesh = self.mesh_1.splitAt(3)
        np.testing.assert_array_equal(self.mesh_1.indices, np.array([0, 1, 2]))
        np.testing.assert_array_equal(split_mesh.indices, np.array([0, 1, 2]))
        expected = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        np.testing.assert_array_almost_equal(self.mesh_1.vertices, expected, decimal=5)
        expected = np.array([[4, 5, 6], [7, 8, 9], [1, 2, 3]])
        np.testing.assert_array_almost_equal(split_mesh.vertices, expected, decimal=5)
        expected = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
        np.testing.assert_array_almost_equal(self.mesh_1.normals, expected, decimal=5)
        expected = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
        np.testing.assert_array_almost_equal(split_mesh.normals, expected, decimal=5)

    def testTransform(self):
        angles = np.radians([30, 60, 90])
        matrix = matrix_from_xyz_eulers(Vector3(angles))
        self.mesh_1.rotate(matrix)

        expected_vertices = np.array([[1.59807621, -0.75, 3.29903811],
                                       [2.69615242, -0.20096189, 8.34807621],
                                       [3.79422863, 0.34807621, 13.39711432]])
        expected_normals = np.array([[0.866025, -0.25, 0.433013], [-0.5, -0.433013, 0.75], [0, 0.866025, 0.5]])

        np.testing.assert_array_almost_equal(self.mesh_1.vertices, expected_vertices, decimal=5)
        np.testing.assert_array_almost_equal(self.mesh_1.normals, expected_normals, decimal=5)
        np.testing.assert_array_equal(self.mesh_1.indices, np.array([0, 1, 2]))

        offset = Vector3([10, -11, 12])
        self.mesh_1.translate(offset)
        expected_vertices = np.array([[11.59807621, -11.75, 15.29903811],
                                     [12.69615242, -11.20096189, 20.34807621],
                                     [13.79422863, -10.6519237, 25.39711432]])

        np.testing.assert_array_almost_equal(self.mesh_1.vertices, expected_vertices, decimal=5)
        np.testing.assert_array_almost_equal(self.mesh_1.normals, expected_normals, decimal=5)
        np.testing.assert_array_equal(self.mesh_1.indices, np.array([0, 1, 2]))

        transform_matrix = np.eye(4, 4)
        transform_matrix[0:3, 0:3] = matrix.transpose()
        transform_matrix[0:3, 3] = -offset.dot(matrix)
        self.mesh_1.transform(transform_matrix)
        expected = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        np.testing.assert_array_almost_equal(self.mesh_1.vertices, expected, decimal=5)
        expected = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
        np.testing.assert_array_almost_equal(self.mesh_1.normals, expected, decimal=5)
        np.testing.assert_array_equal(self.mesh_1.indices, np.array([0, 1, 2]))

    def testCopy(self):
        mesh = self.mesh_1.copy()
        np.testing.assert_array_almost_equal(mesh.vertices, self.mesh_1.vertices, decimal=5)
        np.testing.assert_array_almost_equal(mesh.normals, self.mesh_1.normals, decimal=5)
        np.testing.assert_array_equal(mesh.indices, self.mesh_1.indices)
        self.assertIsNot(mesh.vertices, self.mesh_1.vertices)
        self.assertIsNot(mesh.normals, self.mesh_1.normals)
        self.assertIsNot(mesh.indices, self.mesh_1.indices)


class TestBoundingBoxClass(unittest.TestCase):
    def testConstruction(self):
        max_position = np.array([1., 1., 1.])
        min_position = np.array([-1., -1., -1.])

        box = BoundingBox(max_position, min_position)
        max_pos, min_pos = box.bounds
        np.testing.assert_array_almost_equal(max_pos, max_position, decimal=5)
        np.testing.assert_array_almost_equal(min_pos, min_position, decimal=5)
        np.testing.assert_array_almost_equal(box.center, [0., 0., 0.], decimal=5)
        np.testing.assert_array_almost_equal(box.radius, 1.73205, decimal=5)

        max_position = Vector3([1., 2., 3.])
        min_position = Vector3([-1., -2., -3.])
        box = BoundingBox(max_position, min_position)
        np.testing.assert_array_almost_equal(box.max, max_position, decimal=5)
        self.assertIsNot(max_position, box.max)  # make sure this are not the same object
        np.testing.assert_array_almost_equal(box.min, min_position, decimal=5)
        self.assertIsNot(min_position, box.min)  # make sure this are not the same object
        np.testing.assert_array_almost_equal(box.center, [0., 0., 0.], decimal=5)
        np.testing.assert_array_almost_equal(box.radius, 3.74166, decimal=5)

        points = [[1., 1., 0.], [-1., 0., -1.], [0., -1., 1.]]
        box = BoundingBox.fromPoints(points)
        np.testing.assert_array_almost_equal(box.max, [1., 1., 1.], decimal=5)
        np.testing.assert_array_almost_equal(box.min, [-1., -1., -1.], decimal=5)
        np.testing.assert_array_almost_equal(box.center, [0., 0., 0.], decimal=5)
        np.testing.assert_array_almost_equal(box.radius, 1.73205, decimal=5)

    def testTranslation(self):
        box = BoundingBox([1, 1, 1], [-1, -1, -1])
        box.translate(-2)
        np.testing.assert_array_almost_equal(box.max, [-1., -1., -1.], decimal=5)
        np.testing.assert_array_almost_equal(box.min, [-3., -3., -3.], decimal=5)
        np.testing.assert_array_almost_equal(box.center, [-2., -2., -2.], decimal=5)
        np.testing.assert_array_almost_equal(box.radius, 1.73205, decimal=5)

        box.translate([1, 2, 3])
        np.testing.assert_array_almost_equal(box.max, [0., 1., 2.], decimal=5)
        np.testing.assert_array_almost_equal(box.min, [-2., -1., 0.], decimal=5)
        np.testing.assert_array_almost_equal(box.center, [-1., 0., 1.], decimal=5)
        np.testing.assert_array_almost_equal(box.radius, 1.73205, decimal=5)



class TestMeshGeometryFunctions(unittest.TestCase):
    def testClosestTriangleToPoint(self):
        faces = np.array([[1., 1., 0., 1., 0., 0., 0., 0., 0.],
                          [1., 1., 0., 0., 0., 0., 0., 1., 0.]])
        point = np.array([0., 1., 0.])
        face, sq_dist = closest_triangle_to_point(faces, point)

        np.testing.assert_array_almost_equal(face, [1., 1., 0., 0., 0., 0., 0., 1., 0.], decimal=5)
        self.assertAlmostEqual(sq_dist, 0.0, 5)

        point = np.array([2., 0.5, -0.1])
        face, sq_dist = closest_triangle_to_point(faces, point)

        np.testing.assert_array_almost_equal(face, [1., 1., 0., 1., 0., 0., 0., 0., 0.], decimal=5)
        self.assertAlmostEqual(sq_dist, 1.01, 5)

    def testClosestPointOnTriangle(self):
        vertices = np.array([[1, 1, 0], [1, 0, 0], [0, 0, 0]])
        vertex_a = vertices[0]
        vertex_b = vertices[1]
        vertex_c = vertices[2]

        # test point on edge of the triangle
        test_point = np.array([0.5, 0.5, 1])
        result_point = closest_point_on_triangle(vertex_a, vertex_b, vertex_c, test_point)
        np.testing.assert_array_almost_equal(result_point, [0.5, 0.5, 0.], decimal=5)

        test_point = np.array([0.5, 0.0, 1])
        result_point = closest_point_on_triangle(vertex_a, vertex_b, vertex_c, test_point)
        np.testing.assert_array_almost_equal(result_point, [0.5, 0.0, 0.], decimal=5)

        # test point on vertex of triangle
        test_point = np.array([1., 1., -1])
        result_point = closest_point_on_triangle(vertex_a, vertex_b, vertex_c, test_point)
        np.testing.assert_array_almost_equal(result_point, [1., 1., 0.], decimal=5)

        # test point in the triangle's boundary
        test_point = np.array([0.7, 0.6, 3])
        result_point = closest_point_on_triangle(vertex_a, vertex_b, vertex_c, test_point)
        np.testing.assert_array_almost_equal(result_point, [0.7, 0.6, 0.], decimal=5)

        # test point outside the triangle's boundary
        test_point = np.array([1.7, -12.6, -4.5])
        result_point = closest_point_on_triangle(vertex_a, vertex_b, vertex_c, test_point)
        np.testing.assert_array_almost_equal(result_point, [1, 0., 0.], decimal=5)

    def testSegmentPlaneIntersection(self):
        point_a, point_b = np.array([1., 0., 0.]), np.array([-1., 0., 0.])
        plane = Plane.fromCoefficient(1., 0., 0., 0.)
        intersection = segment_plane_intersection(point_a, point_b, plane)
        np.testing.assert_array_almost_equal(intersection, [0., 0., 0.], decimal=5)

        # segment lies on plane
        # This is currently expected to return None
        point_a, point_b = np.array([0., 1., 0.]), np.array([0., -1., 0.])
        intersection = segment_plane_intersection(point_a, point_b, plane)
        self.assertIsNone(intersection)

        # segment end is on plane
        point_a, point_b = np.array([0.5, 1., 0.]), np.array([0., -1., 0.])
        intersection = segment_plane_intersection(point_a, point_b, plane)
        np.testing.assert_array_almost_equal(intersection, [0., -1., 0.], decimal=5)

        # segment that above plane
        point_a, point_b = np.array([0.5, 1., 0.]), np.array([1.0, -1., 0.])
        intersection = segment_plane_intersection(point_a, point_b, plane)
        self.assertIsNone(intersection)


    def testMeshPlaneIntersection(self):
        np.array([[1., 1., 0., 1., 0., 0., 0., 0., 0.],
                  [1., 1., 0., 0., 0., 0., 0., 1., 0.]])

        vertices = np.array([[1., 1., 0.], [1., 0., 0.], [0., 0., 0.], [0., 1., 0.]])
        indices = np.array([0, 1, 2, 0, 2, 3])

        mesh = Mesh(vertices, indices)

        # plane is above mesh
        plane = Plane.fromCoefficient(1., 0., 0., 2.)
        segments = mesh_plane_intersection(mesh, plane)
        self.assertEqual(len(segments), 0)

        # plane is intersects edge
        plane = Plane.fromCoefficient(1., 0., 0., -1.)
        segments = mesh_plane_intersection(mesh, plane)
        self.assertEqual(len(segments), 2)

        # plane is intersects face
        plane = Plane.fromCoefficient(1., 0., 0., -0.5)
        segments = mesh_plane_intersection(mesh, plane)
        self.assertEqual(len(segments), 4)

        # plane is flush with face
        # This is currently expected to return nothing
        plane = Plane.fromCoefficient(0., 0., 1., 0.)
        segments = mesh_plane_intersection(mesh, plane)
        self.assertEqual(len(segments), 0)
