from custom_components.npc_behavior import ChaseAndAimingBehavior,Behavior
from invasionEngine.game_objects import PhysicalGO
from invasionEngine.components import Camera, PIDController,ResourceManager,EventManager,KeyboardController
from invasionEngine.events import CreateEvent
from custom_components.thruster import Thruster
from custom_components.gun import Autocannon,Railgun,Gatling
from custom_components.gyroscope import Gyroscope
from custom_components.constants import CustomConstants as Constants
from custom_components.custom_events import HitEvent
from invasionEngine.events import Event
from custom_components.health import HealthSystem
import pygame
from pygame import Surface
import pymunk
from pymunk import Vec2d
from typing import Tuple, List, Literal
import random
import math

class Enemy(PhysicalGO):
    '''
    敌人类
    '''
    def __init__(self, 
                position: Tuple[int, int], 
                space: pymunk.space, 
                screen: Surface,
                angle: float = 0,
                mass: float = 5,#5
                shape_type: Literal['box', 'circle', 'poly'] = 'poly',
                elasticity: float = 1,
                friction: float= 0.2,
                gyroscope: Gyroscope = Gyroscope(max_torque=5000000000000000),#0.01, 0.00001, 10
                thruster: Thruster = Thruster(maxForce=4000),
                gunPower: float = 50,
                bulletTTL: int = 1000,
                assets: ResourceManager = None,
                scaling: float = 0.125,
                **kwargs
                 ):
        super().__init__(position,space,screen,angle,mass,shape_type,elasticity,friction,assets,scaling=scaling,**kwargs)
        self.targetX = position[0]
        self.targetY = position[1]
        self.gyroscope = gyroscope
        self.thruster = thruster

        self.gun  = Gatling(self,fire_rate=30)
        # self.gun = Railgun(self,max_charge_time=3000)
        # self.gun = Autocannon(self,fire_rate=4)
        self.mouse_left_down = False
        self.physics_part.shape.collision_type = Constants.SHIP
        self.behavior : Behavior = ChaseAndAimingBehavior(self,min_distance=5,max_distance=15)
        self.health_system = HealthSystem(max_health=120000,health_bar_size=(400,25))
        self.font = pygame.font.SysFont('arial', 20)#用于显示测试文字
    @property
    def center(self):
        return self.physics_part.center 

    def angle_difference(self,x, y):
        """计算两个角度之间的最小差值，结果在 -180 到 180 之间"""
        diff = (x - y) % 360
        if diff >= 180:
            diff -= 360
        return diff

    def angular_update(self,target_angle:float):
        # 使用 PID 控制器计算出需要施加的力矩
        diff = self.angle_difference(self.physics_part.body.angle,target_angle)

        torque = self.gyroscope.update(diff, 0)

        return torque

    def physical_update(self) -> None:
            target_position, target_angle = self.behavior.update()  # 使用行为来更新
            #print(target_position, target_angle)
            self.targetX = target_position[0]
            self.targetY = target_position[1]
            rotation_torque = self.angular_update(target_angle)  # 更新角度
            self.physics_part.update(
                force=self.thruster.update(self.center, target_position), 
                rotation_torque=rotation_torque
            )
            if self.health_system.health_status == 0:
                self.destroy()
            
    
    def render(self, camera: Camera) -> None:
        '''
        这里为了方便，直接调用了父类的render方法，故使用了传入的camera，而不是自己的camera
        '''
        super().render(camera)
        #在目标位置渲染一个点
        pygame.draw.circle(self.screen, (255,100,0), camera.apply((self.targetX, self.targetY)), 4)
        # 绘制血条
        health_bar_surface = self.health_system.health_bar
        health_bar_position = (self.screen.get_width() / 2 - health_bar_surface.get_width() / 2, 20)
        self.screen.blit(health_bar_surface, health_bar_position)

        text_surface = self.font.render('Enemy Health', True, (255, 0, 0))  # 白色文字
        # 计算文字的位置
        text_position = (health_bar_position[0] - text_surface.get_width() - 10, health_bar_position[1])
        # 将文字绘制到屏幕上
        self.screen.blit(text_surface, text_position)

    def handle_event(self, event: Event) -> None:
        super().handle_event(event)
        if event.event_type == Constants.HIT_EVENT:
            event: HitEvent
            if event.target == self:
                self.health_system.take_damage(event.damage - self.physics_part.body.kinetic_energy/(Constants.PIXELS_PER_METER**2))
    
    def destroy(self):
        print('敌人被摧毁,剩余生命百分比：',self.health_system.health_status)
        self.gun.destroy()
        self.behavior.destroy()
        self.health_system.destroy()
        super().destroy()

