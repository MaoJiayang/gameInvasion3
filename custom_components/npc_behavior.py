from typing import Optional
from invasionEngine.components import ComponentBase
from invasionEngine.game_objects import PhysicalGO
from invasionEngine.utils import GeometryUtils
from invasionEngine.constants import Constants
from abc import ABC, abstractmethod
from typing import Tuple
import weakref
from enum import Enum, auto
import pygame
import pymunk
from pymunk.vec2d import Vec2d
import random
import math
import gc

class State(Enum):
    COLLIDE = auto()
    KEEP_DISTANCE = auto()
    ORBIT = auto()

class Behavior(ComponentBase, ABC):
    def __init__(self, game_object: PhysicalGO,random_offset:float = 2.5):
        super().__init__()
        self.game_object = game_object
        self._target: Optional[weakref.ref] = None  # 目标对象的弱引用
        self.target_position: Vec2d = Vec2d(0, 0)  # 目标位置
        self.target_angle: float = 0  # 目标角度（弧度制）
        self.state: State = State.KEEP_DISTANCE  # 初始状态
        self.random_offset:float = random_offset * Constants.PIXELS_PER_METER

        offset_x = random.uniform(-self.random_offset, self.random_offset)
        offset_y = random.uniform(-self.random_offset, self.random_offset)
        self.random_offset_vector = Vec2d(offset_x, offset_y)

    @property
    def target(self) -> Optional[PhysicalGO]:
        if self._target is not None:
            return self._target()
        return None

    @target.setter
    def target(self, target: PhysicalGO):
        self._target = weakref.ref(target)

    @abstractmethod
    def update(self) -> Tuple[Tuple[float, float], float]:
        """根据状态更新行为，并返回目标位置和角度"""
        return tuple(self.target_position), math.degrees(self.target_angle)

    def collide_behavior(self):
        """实现冲撞行为"""
        if self.target:
            self.target_position = GeometryUtils.to_vec2d(self.target.position)
            self.target_angle = self.calculate_angle_towards_target()

    def keep_distance_behavior(self, min_distance: float, max_distance: float):
        """实现保持距离行为"""
        self.random_offset_update()
        if self.target.destroyed:
            return
        if self.target is not None:
            min_distance *= Constants.PIXELS_PER_METER
            max_distance *= Constants.PIXELS_PER_METER
            game_object_position = GeometryUtils.to_vec2d(self.game_object.position)
            target_position = GeometryUtils.to_vec2d(self.target.position)

            distance_vector = game_object_position - target_position
            current_distance = distance_vector.length
            
            # 维持在最小和最大距离之间
            if current_distance < min_distance or current_distance > max_distance:
                distance_vector = distance_vector.normalized() * ((min_distance + max_distance) / 2)
            self.target_position = GeometryUtils.to_vec2d(self.target.position) + distance_vector

            # 在目标周围的范围内添加轻微随机位移
            self.target_position += self.random_offset_vector

            self.target_angle = self.calculate_angle_towards_target()


    def orbit_behavior(self, orbit_distance: float, angular_velocity: float = math.pi / 12):
        """实现环绕行为"""
        self.random_offset_update()
        if not hasattr(self, 'orbit_angle'):
            self.orbit_angle: float= 0  # 如果不存在orbit_angle，则创建一个
        if self.target:
            delta_time = (pygame.time.get_ticks() - self.game_object.last_frame_update_time) / 1000.0  # 获取时间间隔，单位为秒
            self.orbit_angle += angular_velocity * delta_time  # 增加环绕角度
            self.orbit_angle = self.orbit_angle % (2 * math.pi)  # 限制在 0 到 2pi 之间
            self.target_position = self.target.position + Vec2d(math.sin(self.orbit_angle), math.cos(self.orbit_angle)) * orbit_distance * Constants.PIXELS_PER_METER + self.random_offset_vector
            self.target_angle = self.calculate_angle_towards_target()

    def calculate_angle_towards_target(self) -> float:
        """计算应该朝向目标的角度,y+为0度，顺时针增加"""
        if self.target:
            game_object_position = GeometryUtils.to_vec2d(self.game_object.position)
            target_position = GeometryUtils.to_vec2d(self.target.position)
            diff = target_position - game_object_position
            return math.atan2(diff.x, diff.y) 
        
    def random_offset_update(self):
        #通过时间判断self.random_offset_vector是否需要更新
        if pygame.time.get_ticks() % 500 <= 2:
            offset_x = random.uniform(-self.random_offset, self.random_offset)
            offset_y = random.uniform(-self.random_offset, self.random_offset)
            self.random_offset_vector = Vec2d(offset_x, offset_y)

    def destroy(self):
        """销毁对象"""
        self.game_object = None
        super().destroy()
        
from custom_components.gun import Gun
class ChaseAndAimingBehavior(Behavior):
    def __init__(self, game_object: PhysicalGO, min_distance: float = 10, max_distance: float = 20,random_offset:float = 2.5):
        """初始化行为.要设置目标，请使用target属性"""
        super().__init__(game_object,random_offset=random_offset)
        self.state = State.KEEP_DISTANCE  # 固定状态为KEEP_DISTANCE
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.previous_target_velocity = Vec2d(0, 0)
        self.previous_target_position = Vec2d(0, 0)
        self.predicted_position = Vec2d(0, 0)
        #使用自省功能检查game_object内是否有Gun类成员，如果有，则将其赋值给self.gun
        for name, value in vars(game_object).items():
            if isinstance(value, Gun):
                self.gun = value
                break
        else:
            raise Exception('Aiming行为附加的',type(game_object),'内没有Gun类成员')
        
    def calculate_lead_angle(self) -> float:
        # 一阶提前量
        if self.target != None and not self.target.destroyed:
            target_velocity = GeometryUtils.to_vec2d(self.target.physics_part.body.velocity)
            shooter_velocity = GeometryUtils.to_vec2d(self.game_object.physics_part.body.velocity)
            relative_velocity = target_velocity - shooter_velocity
            bullet_speed = self.gun.power

            lead_time = self.calculate_lead_time(relative_velocity, bullet_speed)
            predicted_position = GeometryUtils.to_vec2d(self.target.position) + relative_velocity * lead_time

            diff = predicted_position - GeometryUtils.to_vec2d(self.game_object.position)
            self.predicted_position = predicted_position
            return math.atan2(diff.x, diff.y)
        return 0.0

    def calculate_lead_time(self, relative_velocity: Vec2d, bullet_speed: float) -> float:
        # 一阶时间计算
        # 这里可能需要根据游戏的具体情况进行调整
        return relative_velocity.length / bullet_speed
    
    def update(self,allow_firing:bool = True) -> Tuple[Tuple[float, float], float]:
        """根据状态更新行为，并返回目标位置和角度"""
        for name, value in vars(self.game_object).items():
            if isinstance(value, Gun):
                self.gun = value
                # print(self.game_object,type(self.gun))
                break
        if self.target == None:
            return tuple(self.target_position), math.degrees(self.target_angle)
        self.keep_distance_behavior(self.min_distance, self.max_distance)
        # self.orbit_behavior(orbit_distance=(self.min_distance + self.max_distance) / 2)
        lead_angle = self.calculate_lead_angle()#计算提前量
        self.target_angle = lead_angle

        
        # 生成单位向量
        go_angle = math.radians(self.game_object.angle)
        current_direction = Vec2d(math.cos(go_angle), math.sin(go_angle))
        target_direction = Vec2d(math.cos(self.target_angle), math.sin(self.target_angle))

        # 计算两个向量之间的夹角
        angle_difference = math.degrees(math.acos(current_direction.dot(target_direction)))

        if abs(angle_difference) < 2 and allow_firing:# 如果角度接近目标角度，触发发射
            self.gun.override_launch()

        return tuple(self.target_position), math.degrees(self.target_angle)