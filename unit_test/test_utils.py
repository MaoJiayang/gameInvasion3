import unittest
from invasionEngine.utils import GeometryUtils, TextureUtils
import pygame
from scipy.spatial import distance
import numpy as np

class TestGeometryUtils(unittest.TestCase):
    def test_distance_point_to_line(self):
        distance = GeometryUtils.distance_point_to_line((0, 0), (0, 0), (1, -1))
        self.assertEqual(distance, 0)

    def test_douglas_peucker(self):
        points = [(0, 0), (1, 1), (2, 0), (1, -1)]
        simplified = GeometryUtils.douglas_peucker(points, 1)
        self.assertEqual(simplified, [(0, 0), (2, 0)])

    def test_make_centroid(self):
        polygon = [(0, 0), (2, 0), (2, 2), (0, 2)]
        centroid = GeometryUtils.make_centroid(polygon)
        self.assertEqual(centroid, [(-1, -1), (1, -1), (1, 1), (-1, 1)])

    def test_generate_segment_from_endpoints(self):
        points = [(0, 0), (2, 0)]
        segment = GeometryUtils.generate_segment_from_endpoints(points, 1)
        self.assertEqual(segment, [(0, -1), (0, 1), (2, 1), (2, -1)])

class TestTextureUtils(unittest.TestCase):
    def test_fill_polygon_with_texture(self):
        polygon = [(0, 0), (2, 0), (2, 2), (0, 2)]
        texture = pygame.Surface((1, 1))
        texture.fill((255, 255, 255))
        filled = TextureUtils.fill_polygon_with_texture(polygon, texture)
        self.assertEqual(filled.get_at((0, 0)), (255, 255, 255, 255))
        self.assertEqual(filled.get_at((1, 1)), (255, 255, 255, 255))