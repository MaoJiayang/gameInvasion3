from custom_components.constants import CustomConstants as Constants
from custom_components.gyroscope import Gyroscope
from invasionEngine.events import Event
from invasionEngine.game_objects import Event, Projectile, PhysicalGO
from invasionEngine.components import EventManager, ResourceManager
from invasionEngine.utils import GeometryUtils
import pygame
import math
from pygame import Surface
import pymunk
from pymunk import Vec2d
from typing import Tuple, List, Literal
class Bullet(Projectile):
    def __init__(self, 
            position: Tuple[int, int], 
            space: pymunk.space, 
            screen: Surface,
            angle: float = 0,
            mass: float = 0.5,
            shape_type: Literal['box', 'circle', 'poly'] = 'circle',
            elasticity: float = 1,
            friction: float= 0,
            assets: ResourceManager = None,
            time_to_live: int = 3000,
            collision_type: int = Constants.BULLET,
            **kwargs
            ):
        '''
        子弹类
        position: 初始位置
        images: 图片列表
        space: 物理空间
        screen: 屏幕
        angle: 初始角度
        mass: 质量
        moment: 转动惯量
        shape_type: 形状类型
        elasticity: 弹性
        friction: 摩擦力
        time_to_live: 子弹存活时间（毫秒）
        '''
        super().__init__(
            position = position,
            space = space,
            screen = screen,
            angle = angle,
            mass = mass,
            shape_type = shape_type,
            elasticity = elasticity,
            friction = friction,
            assets = assets,
            time_to_live= time_to_live,
            **kwargs
        )
        self.physics_part.shape.collision_type = collision_type# 设置碰撞类型
    @property
    def bullet_type(self):
        return self.physics_part.shape.collision_type   
    
# default_missile_assets = ResourceManager('resources\missile')
# class Missile(Projectile):
#     def __init__(self, 
#                  position: Tuple[int, int],
#                  target: PhysicalGO,
#                  space: pymunk.Space,
#                  screen: Surface,
#                  angle: float = 0,
#                  mass: float = 1,
#                  thrust: float = 100000.0,
#                  time_to_live: int = 10000,
#                  guidance_gain: float = 1.5,  # 比例制导增益
#                  max_torque: float = 7000,
#                  assets: ResourceManager = default_missile_assets,
#                  **kwargs):
#         super().__init__(position=position, space=space, screen=screen, angle=angle, mass=mass, assets=assets,time_to_live=time_to_live, **kwargs)
#         self.target = target
#         self.thrust = thrust
#         self.guidance_gain = guidance_gain  # 添加比例制导增益
#         self.gyroscope = Gyroscope(max_torque = max_torque)
#         self.active = False
#         self.cold_launch_countdown : int = 250#冷发射倒计时

#         if time_to_live < self.cold_launch_countdown:
#             raise ValueError('Time to live must be greater than cold launch countdown:', self.cold_launch_countdown)

#     def angle_difference(self,x, y):
#         """计算两个角度之间的最小差值，结果在 -180 到 180 之间"""
#         diff = (x - y) % 360
#         if diff >= 180:
#             diff -= 360
#         return diff
    
#     def activate(self, speed: Tuple[float, float] = (0, 0)):
#         super().activate(speed=speed)
#         self.activate_time = pygame.time.get_ticks()

#     def physical_update(self) -> None:
#         if self.active and pygame.time.get_ticks() - self.activate_time > self.cold_launch_countdown:
#             rotation_torque = self.proportional_navigation_guidance_update()
#             self.physics_part.update(force=(0,0),
#                                      rotation_torque = rotation_torque)
#             self.physics_part.body.apply_force_at_local_point((0, self.thrust), (0, 0))


#     def proportional_navigation_guidance_update(self) -> float:
#         if self.target:
#             # 获取目标位置
#             target_position = GeometryUtils.to_vec2d(self.target.position)
#             missile_position = GeometryUtils.to_vec2d(self.physics_part.body.position)

#             # 计算视线角度和导弹当前角度
#             line_of_sight_angle = math.atan2(target_position.x - missile_position.x, 
#                                              target_position.y - missile_position.y)
#             current_angle = math.radians(self.physics_part.body.angle)

#             # 计算视线角速率
#             los_rate = self.guidance_gain * ((line_of_sight_angle - current_angle) % (2 * math.pi))
#             if los_rate > math.pi:
#                 los_rate -= 2 * math.pi

#             # 计算目标角度
#             target_angle = math.degrees(current_angle + los_rate)
#             # 计算角度差值
#             diff = self.angle_difference(self.physics_part.body.angle, target_angle)

#             # 使用陀螺仪计算力矩
#             torque = self.gyroscope.update(diff, 0)
#             return torque
#         return 0.0

