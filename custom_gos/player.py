from invasionEngine.game_objects import PhysicalGO
from invasionEngine.components import Camera, PIDController,ResourceManager,EventManager,KeyboardController
from invasionEngine.events import CreateEvent, Event
from custom_components.thruster import Thruster
from custom_components.gun import Autocannon,Railgun,Gatling
from custom_components.gyroscope import Gyroscope
from custom_components.constants import CustomConstants as Constants
from custom_components.custom_events import HitEvent
from custom_components.health import HealthSystem
import pygame
from pygame import Surface
import pymunk
from pymunk import Vec2d
from typing import Tuple, List, Literal
import random
import math
class Player(PhysicalGO):
    '''
    玩家类
    '''
    def __init__(self, 
                position: Tuple[int, int], 
                space: pymunk.space, 
                screen: Surface,
                angle: float = 0,
                mass: float = 5,#5
                shape_type: Literal['box', 'circle', 'poly'] = 'box',
                elasticity: float = 1,
                friction: float= 0.2,
                gyroscope: Gyroscope = Gyroscope(),#0.01, 0.00001, 10
                thruster: Thruster = Thruster(maxForce=3000),
                assets: ResourceManager = None,
                camera: Camera = None,
                controller: KeyboardController = KeyboardController(),
                scaling: float = 0.8,
                **kwargs
                 ):
        super().__init__(position,space,screen,angle,mass,shape_type,elasticity,friction,assets,scaling=scaling,**kwargs)
        self.targetX = position[0]
        self.targetY = position[1]
        self.rotation_PID_controller = gyroscope
        self.thruster = thruster
        # self.gun = Autocannon(self,fire_rate=5)
        self.gun  = Railgun(self,max_charge_time=2500,power=130)
        # self.gun = Gatling(self,fire_rate=9.2)
        self.mouse_left_down = False
        self.camera: Camera = camera#该摄像头是为了方便鼠标的定位
        self.controller = controller
        self.health_system = HealthSystem(max_health=120000)
        self.physics_part.shape.collision_type = Constants.SHIP
        self.font = pygame.font.SysFont('SimHei', 20)#用于显示测试文字
    @property
    def center(self):
        return self.physics_part.center 
        
    def target_coordinate_update(self):#这是一个有关键盘事件的方法，后续需要考虑将其分离
        control_values = self.controller.control_values
        self.targetX += control_values[0]*5
        self.targetY += control_values[1]*5
        # 如果空格键被按下，将目标位置设置为当前位置
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.targetX = self.center[0]
            self.targetY = self.center[1]

    def angle_difference(self,x, y):
        """计算两个角度之间的最小差值，结果在 -180 到 180 之间"""
        diff = (x - y) % 360
        if diff >= 180:
            diff -= 360
        return diff

    def angular_update(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        screen_position_x, screen_position_y = self.camera.apply(self.position)
        angle = math.atan2(mouse_y - screen_position_y, mouse_x - screen_position_x)
        angle = math.degrees((angle + math.pi / 2))#试出来的，这样更新的角度才是正确的，这个偏置可能需要根据实际情况调整。因为飞船的图像朝向可能会存在偏差
        # 使用 PID 控制器计算出需要施加的力矩
        diff = self.angle_difference(self.physics_part.body.angle,angle)

        torque = self.rotation_PID_controller.update(diff, 0)

        return torque

    def physical_update(self) -> None:#在这里更新所有自己的组件
        self.gun.update()
        self.target_coordinate_update()
        rotationTorque = self.angular_update()
        self.physics_part.update(
            force = self.thruster.update(self.center, (self.targetX, self.targetY)), 
            rotation_torque = rotationTorque
        )
        self.gun.update()
        if self.health_system.health_status == 0:
            self.destroy()
    
    def render(self, camera: Camera) -> None:
        '''
        这里为了方便，直接调用了父类的render方法，故使用了传入的camera，而不是自己的camera
        '''
        super().render(camera)
        #在目标位置渲染一个点
        pygame.draw.circle(self.screen, (0,255,0), camera.apply((self.targetX, self.targetY)), 4)
        #在屏幕右上角显示当前目标位置，速度
        self.test_text_render()

    def handle_event(self, event: Event) -> None:
        super().handle_event(event)
        if event.event_type == Constants.HIT_EVENT:
            event: HitEvent
            if event.target == self:
                #sprint('玩家受到伤害：', event.damage)
                self.health_system.take_damage(event.damage - self.physics_part.body.kinetic_energy/(Constants.PIXELS_PER_METER**2))

    def destroy(self) -> None:
        self.gun.destroy()
        self.health_system.destroy()
        super().destroy()

    def test_text_render(self):
        #在屏幕右上角显示当前目标位置，速度
        text = self.font.render('目标位置:' + str((round(self.targetX, 2), round(self.targetY, 2))), True, (106, 153, 85))
        self.screen.blit(text, (self.screen.get_width() - text.get_width(), 0))
        text = self.font.render('current position:' + str((round(self.center[0], 2), round(self.center[1], 2))), True, (106, 153, 85))
        self.screen.blit(text, (self.screen.get_width() - text.get_width(), 20))
        text = self.font.render('speed:' + str((round(self.physics_part.body.velocity[0], 2), round(self.physics_part.body.velocity[1], 2))), True, (106, 153, 85))
        self.screen.blit(text, (self.screen.get_width() - text.get_width(), 40))
        text = self.font.render('angle:' + str(round(self.angle, 2)), True, (106, 153, 85))
        self.screen.blit(text, (self.screen.get_width() - text.get_width(), 60))
        text = self.font.render('rect center:' + str(self.rect.center), True, (106, 153, 85))
        self.screen.blit(text, (self.screen.get_width() - text.get_width(), 80))
        # 生命百分比
        text = self.health_system.health_bar
        self.screen.blit(text, (self.screen.get_width() - text.get_width(), 120))

    

