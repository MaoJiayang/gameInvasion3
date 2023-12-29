import unittest
import os
import pygame
from invasionEngine.components import ResourceManager

class TestResourceManager(unittest.TestCase):
    def setUp(self):
        #初始化pygame
        pygame.init()
        self.rm = ResourceManager(resources_dir='unit_test\\test_resource\playership_pics')

    def test_get_images(self):
        images = self.rm.get('images')
        self.assertIsInstance(images, list)
        self.assertTrue(all(isinstance(i, pygame.Surface) for i in images))

    def test_get_image_polygons(self):
        image_polygons = self.rm.get('image_polygons')
        self.assertIsInstance(image_polygons, list)
        self.assertTrue(all(isinstance(ip, list) for ip in image_polygons))

    def test_get_textures(self):
        textures = self.rm.get('textures')
        self.assertIsInstance(textures, list)
        self.assertTrue(all(isinstance(t, pygame.Surface) for t in textures))

    def test_get_sounds(self):
        sounds = self.rm.get('sounds')
        self.assertIsInstance(sounds, list)
        self.assertTrue(all(isinstance(s, pygame.mixer.Sound) for s in sounds))

    def test_get_with_filename(self):
        images = self.rm.get('images', filename='test')
        self.assertIsInstance(images, list)
        self.assertTrue(all(isinstance(i, pygame.Surface) for i in images))

    def test_get_with_filename_contains_c(self):
        images = self.rm.get('images', filename='c')
        self.assertIsInstance(images, list)
        self.assertEqual(len(images), 2)
        self.assertTrue(all(isinstance(i, pygame.Surface) for i in images))

    def test_get_with_filename_contains_a(self):
        images = self.rm.get('images', filename='a')
        self.assertIsInstance(images, list)
        self.assertEqual(len(images), 1)
        self.assertTrue(all(isinstance(i, pygame.Surface) for i in images))

    def test_get_with_name(self):
        images = self.rm.get('textured_images', with_name=True)
        self.assertIsInstance(images, dict)
        self.assertTrue(all(isinstance(k, str) and isinstance(v, pygame.Surface) for k, v in images.items()))

    def test_get_invalid_resource_type(self):
        with self.assertRaises(ValueError):
            self.rm.get('invalid')

    def test_get_textured_images(self):
        images = self.rm.get('images')
        textures = self.rm.get('textures')
        textured_images = self.rm.get('textured_images')
        self.assertEqual(len(textured_images), len(images) * len(textures))
        self.assertTrue(all(isinstance(ti, pygame.Surface) for ti in textured_images))
    def tearDown(self):
        self.rm.destroy()

if __name__ == '__main__':
    unittest.main()