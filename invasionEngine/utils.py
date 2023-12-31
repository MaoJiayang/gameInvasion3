'''
工具类
现有工具：
    1.几何工具类
        计算点到线段的距离
        Douglas-Peucker抽稀算法
    2.渲染工具类
'''
from typing import List, Tuple, Union
import pygame
import pymunk
from pymunk.pygame_util import from_pygame, to_pygame
from pymunk.vec2d import Vec2d
from .constants import Constants
class GeometryUtils:
    '''
    几何工具类:
    distance_point_to_line()--计算点到线段的距离
    douglas_peucker()--Douglas-Peucker抽稀算法,用于解析传入多边形轮廓的顶点
    '''
    @staticmethod
    def distance_point_to_line(point: Tuple[float, float], line_start: Tuple[float, float], line_end: Tuple[float, float]) -> float:
        '''计算点到线段的距离'''
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end
        denominator = (y2 - y1)**2 + (x2 - x1)**2
        # 添加检查，避免端点重合导致除零错误
        if denominator == 0:
            return 0
        return abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / (denominator)**0.5

    @staticmethod
    def douglas_peucker(points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
        '''Douglas-Peucker抽稀算法，用于解析传入多边形轮廓的顶点'''
        if len(points) <= 2:
            return points
        # 找到最大距离点
        d_max = 0
        index = 0
        end = len(points) - 2 #避免闭合点由于首尾相接而导致点线距离恒为0，所以这里减2而不是减1
        for i in range(1, end):
            d = GeometryUtils.distance_point_to_line(points[i], points[0], points[end])
            if d > d_max:
                index = i
                d_max = d
        # 检查最大距离是否大于阈值
        if d_max > epsilon:
            # 递归调用
            left_simplified = GeometryUtils.douglas_peucker(points[:index + 1], epsilon)
            right_simplified = GeometryUtils.douglas_peucker(points[index:], epsilon)
            return left_simplified[:-1] + right_simplified
        # 如果最大距离小于阈值，直接返回首尾点
        return [points[0], points[end]]
    
    @staticmethod
    def make_centroid(polygon: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        '''
        将多边形平移到中心位于原点处
        '''
        centroid_x = sum(x for x, _ in polygon) / len(polygon)
        centroid_y = sum(y for _, y in polygon) / len(polygon)
        return [(x - centroid_x, y - centroid_y) for x, y in polygon]
    
    @staticmethod
    def get_edge_pixels(image_surface: pygame.Surface, target_edges: int = Constants.MAX_ALLOWED_POLY_EDGES) -> List[Tuple[int, int]]:
        '''
        获取透明底图像的边缘像素，并返回其多边形顶点坐标(左上角坐标系)
        该多边形重心位于（0,0）
        '''
        # 获取图像的透明掩码
        mask = pygame.mask.from_surface(image_surface)
        # 获取透明区域的边缘像素
        outline = mask.outline()

        # 如果边缘像素数量超过了最大允许的顶点数量，则进行简化，删除在同一条直线（点线距离小于1）上的点，仅保留端点（术语：Douglas-Peucker算法抽稀简化）
        max_iterations = len(outline) - target_edges
        while len(outline) > target_edges and max_iterations > 0:
            outline = GeometryUtils.douglas_peucker(outline, 1)
            max_iterations -= 1
        if max_iterations == 0:
            print(f"警告: 边数大于 {target_edges}. 在有效迭代次数内边数仅能简化到 {len(outline)}")

        return GeometryUtils.make_centroid(outline)
    
    @staticmethod
    def generate_segment_from_endpoints(points: List[Tuple[float, float]], radius: float = 1) -> List[Tuple[float, float]]:
        '''
        根据线段端点和线宽创建一个四个点的线段区域
        不会对坐标进行平移。
        '''
        # 检查points是否为list[tuple]
        assert isinstance(points, list), f"points {points} is not a list"
        assert len(points) == 2, f"points {points} is not a list of length 2"
        if not isinstance(radius, (int, float)):
            raise ValueError("radius must be a number")

        point1, point2 = points

        # 计算线段的方向向量
        direction = pymunk.Vec2d(point2[0],point2[1]) - pymunk.Vec2d(point1[0],point1[1])
        # 将方向向量归一化
        direction = direction.normalized()
        # 计算法向量
        normal = direction.perpendicular()
        # 计算四个点的坐标
        p1 = point1 - radius * normal
        p2 = point1 + radius * normal
        p3 = point2 + radius * normal
        p4 = point2 - radius * normal

        return [tuple(p1), tuple(p2), tuple(p3), tuple(p4)]
    
    @staticmethod
    def scale_polygon(polygon: List[Tuple[float, float]], scale: float) -> List[Tuple[float, float]]:
        '''
        对输入的多边形轮廓进行比例放缩
        '''
        if not isinstance(scale, (int, float)):
            raise ValueError("scale must be a number")
        if scale <= 0:
            raise ValueError("scale must be greater than 0")
        if scale == 1:
            return polygon
        return [(x * scale, y * scale) for x, y in polygon]
    
    @staticmethod
    def to_vec2d(position: Tuple[float, float]) -> Vec2d:
        """将位置元组转换为Vec2d对象"""
        return Vec2d(*position)
    
class TextureUtils:
    '''材质工具类'''
    @staticmethod  
    def fill_polygon_with_texture(polygon: Union[pygame.Surface, List[Tuple[int, int]]], texture: pygame.Surface) -> pygame.Surface:
        '''
        使用纹理填充多边形
        polygon: 多边形，可以是pygame.Surface或者是一个由顶点坐标组成的列表（左上角坐标系）
        texture: 纹理

        返回一个填充了纹理的多边形的pygame.Surface
        '''
        # 检查polygon参数的类型
        if isinstance(polygon, pygame.Surface):
            # 如果polygon是pygame.Surface类型，那么使用get_edge_pixels方法来获取轮廓
            polygon = GeometryUtils.get_edge_pixels(polygon)

        # 找到轮廓中所有点的最小 x 和 y 值
        min_x = min(point[0] for point in polygon)
        min_y = min(point[1] for point in polygon)
        # 将所有点减去最小值，以将轮廓平移到紧贴正半轴
        polygon = [(point[0] - min_x, point[1] - min_y) for point in polygon]

        # 获取多边形的矩形边界
        min_x = min(point[0] for point in polygon)
        min_y = min(point[1] for point in polygon)
        max_x = max(point[0] for point in polygon)
        max_y = max(point[1] for point in polygon)

        # 创建一个与多边形矩形边界相同大小（外接）的矩形 surface
        surface = pygame.Surface((max_x - min_x, max_y - min_y), pygame.SRCALPHA)

        # 在 surface 上重复绘制 texture
        for i in range(0, surface.get_width(), texture.get_width()):
            for j in range(0, surface.get_height(), texture.get_height()):
                surface.blit(texture, (i, j))

        mask_surface = pygame.Surface((max_x - min_x, max_y - min_y), pygame.SRCALPHA)
        pygame.draw.polygon(mask_surface, (255, 255, 255), [(x - min_x, y - min_y) for x, y in polygon])

        # 使用 pygame.BLEND_RGBA_MULT 标志进行颜色混合
        surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return surface