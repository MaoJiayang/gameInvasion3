from invasionEngine.game_objects import PhysicalGO
from invasionEngine.components import Camera,ResourceManager,KeyboardController
from invasionEngine.events import Event
from invasionEngine.scenes import Scene
from invasionEngine.utils import GeometryUtils
from custom_components.custom_events import RadarSearchEvent,RadarEchoEvent
from custom_components.thruster import Thruster
from custom_components.gun import Autocannon,Railgun,Gatling,Gun
from custom_components.gyroscope import Gyroscope
from custom_components.constants import CustomConstants as Constants
from custom_components.custom_events import KineticHitEvent
from custom_components.health import HealthSystem
from custom_components.npc_behavior import ChaseAndAimingBehavior,Behavior
import pygame
from pygame import Surface
import pymunk
import math
from typing import Literal
class ArmedShip(PhysicalGO):
    '''
    武装飞船类，继承自PhysicalGO
    玩家和敌人都是武装飞船
    '''
    def __init__(self, 
                scene: Scene,#这里传入了scene，是为了方便在自动注册事件
                position: tuple[int, int], 
                space: pymunk.space, 
                screen: Surface,
                gun: Gun,
                assets: ResourceManager,
                angle: float = 0,
                mass: float = 5,#5
                shape_type: Literal['box', 'circle', 'poly'] = 'poly',
                elasticity: float = 1,
                friction: float= 0.05,
                gyroscope_torque: float = 50000000,#0.01, 0.00001, 10
                thruster_force: float = 4000,
                health: float = 60000,
                target_point_color: tuple[int,int,int] = (255,0,0),
                health_bar_size: tuple[int,int] = (-1,-1),#(-1,-1)表示按照游戏对象贴图短边作为长度，长：宽 = 7.5自动计算大小
                collision_type: int = Constants.SHIP,
                scaling: float = 1,
                **kwargs
                 ):
        
        super().__init__(position,space,screen,angle,mass,shape_type,elasticity,friction,assets,scaling=scaling,**kwargs)

        self.targetX = position[0]
        self.targetY = position[1]
        if health_bar_size == (-1,-1):
            health_length = min(self.current_image.get_width(),self.current_image.get_height()) * scaling
            health_bar_size = (health_length,health_length // 7.5)

        self.gun = gun
        self.event_manager = scene.event_manager
        self.gyroscope = Gyroscope(max_torque=gyroscope_torque)
        self.thruster = Thruster(maxForce=thruster_force)
        self.behavior : Behavior = ChaseAndAimingBehavior(self,min_distance = 5,max_distance = 15)#请注意，这里的行为没有附加目标，需要在外部设置
        self.health_system = HealthSystem(max_health = health,health_bar_size = health_bar_size)

        self.physics_part.shape.collision_type = collision_type
        self.target_point_color = target_point_color
        self.font = pygame.font.Font('resources\\fonts\simhei\SIMHEI.TTF', 20)#用于显示测试文字

        self.auto_register()

    @property
    def center(self):
        return self.physics_part.center 

    def angle_difference(self,x, y):
        """计算两个角度之间的最小差值，结果在 -180 到 180 之间.该方法理应抽取到几何工具类中"""
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
        if self.health_system.health_status == 0:
            self.destroy()
            return
        target_position, target_angle = self.behavior.update()  # 使用行为来更新
        #print(target_position, target_angle)
        self.targetX = target_position[0]
        self.targetY = target_position[1]
        rotation_torque = self.angular_update(target_angle)  # 更新角度
        self.physics_part.update(
            force=self.thruster.update(self.center, target_position), 
            rotation_torque=rotation_torque
        )

            
    
    def render(self, camera: Camera) -> None:
        '''
        这里为了方便，直接调用了父类的render方法，故使用了传入的camera，而不是自己的camera
        '''
        super().render(camera)
        #在目标位置渲染一个点
        pygame.draw.circle(self.screen, self.target_point_color, camera.apply((self.targetX, self.targetY)), 4)
        # 生命值不满时绘制血条
        if self.health_system.health_status < 1:
            # bias = min(self.current_image.get_width(), self.current_image.get_height()) / 2
            health_bar_surface = self.health_system.health_bar
            health_bar_position = camera.apply(self.center)
            self.screen.blit(health_bar_surface, health_bar_position)

    def handle_event(self, event: Event) -> None:
        super().handle_event(event)
        if event.event_type == Constants.KINETIC_HIT_EVENT:
            event: KineticHitEvent   
            if event.target == self:
                event: KineticHitEvent
                relative_velocity: pymunk.Vec2d = (self.physics_part.velocity - event.speed)#因为下面使用了模所以无所谓谁减谁
                mass = event.mass
                #计算动能
                kinetic_energy = 0.5 * mass * relative_velocity.length ** 2
                #print('对象受到伤害：', kinetic_energy,'伤害来源：',event.source)
                self.health_system.take_damage(kinetic_energy)

    def auto_register(self):
        """自动注册对象所需的事件。可以在这边管理对象需要关注的事件。该方法会在初始化的时候调用"""
        self.event_manager.subscribe(self,Constants.KINETIC_HIT_EVENT)

    def destroy(self):
        #print('对象被摧毁,剩余生命百分比：',self.health_system.health_status)
        self.gun.destroy()
        self.behavior.destroy()
        self.health_system.destroy()
        super().destroy()

default_player_assets = ResourceManager('resources\playership_pics')
class Player(ArmedShip):
    '''
    玩家类
    '''
    def __init__(self, 
                scene: Scene,#这里传入了scene，是为了方便在自动注册事件
                position: tuple[int, int], 
                space: pymunk.space, 
                screen: Surface,
                camera: Camera,
                assets: ResourceManager = default_player_assets,
                angle: float = 0,
                mass: float = 5,#5
                gyroscope_torque: float = 50000,#0.01, 0.00001, 10
                thruster_force: float = 4000,
                health: float = 60000,
                target_point_color: tuple[int,int,int] = (0,255,0),
                health_bar_size: tuple[int,int] = (-1,-1),#(-1,-1)表示按照游戏对象贴图短边作为长度，长：宽 = 7.5自动计算大小
                collision_type: int = Constants.PLAYERSHIP,
                scaling: float = 1,
                **kwargs
                 ):
        self.gun_list: list[Gun] = [Gatling(self,fire_rate=9.2),Autocannon(self,fire_rate=5),Railgun(self,max_charge_time=2500,power=130)]
        super().__init__(scene = scene, position = position, space = space,screen = screen,
                         gun = self.gun_list[0], assets = assets, angle = angle, mass = mass,
                         gyroscope_torque = gyroscope_torque, thruster_force = thruster_force,
                         health = health, target_point_color = target_point_color,
                         health_bar_size = health_bar_size, collision_type = collision_type,
                         scaling = scaling, **kwargs
                         )
        self.clock = scene.clock
        self.camera = camera
        self.controller = KeyboardController()
        self.hud_state: int = 2#0,1,2分别表示三种显示状态
        self.railgun_charge_progress: HealthSystem = HealthSystem(max_health = 1,health_bar_size = (70,20))
        self.hud_surface = Surface(self.screen.get_size(), pygame.SRCALPHA)#用于绘制hud
        self.hud_needs_update = True  # HUD 是否需要更新
        #渲染一个'x'字符surface作为瞄准点
        self.target_point_surface = self.font.render('x', True, (255, 100, 0))
        self.last_hud_update_time = pygame.time.get_ticks()
        self.tab_pressed = False
        
    def keyboard_event_update(self):
        control_values = self.controller.control_values
        self.targetX += control_values[0]*5*0.618/self.camera.zoom
        self.targetY += control_values[1]*5*0.618/self.camera.zoom
        # 如果空格键被按下，将目标位置设置为当前位置
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.targetX = self.center[0]
            self.targetY = self.center[1]
        # 数字键切换武器
        for i in range(1,min(10,len(self.gun_list)+1)):
            if keys[getattr(pygame, f'K_{i}')]:
                self.gun = self.gun_list[i - 1]
        #Tab键切换hud状态
        if keys[pygame.K_TAB]:
            if not self.tab_pressed:
                self.hud_state = (self.hud_state + 1) % 3
                self.tab_pressed = True
        else:
            self.tab_pressed = False


    def angular_update(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        screen_position_x, screen_position_y = self.camera.apply(self.position)
        angle = math.atan2(mouse_y - screen_position_y, mouse_x - screen_position_x)
        angle = math.degrees((angle + math.pi / 2))#试出来的，这样更新的角度才是正确的，这个偏置可能需要根据实际情况调整。因为飞船的图像朝向可能会存在偏差
        # 使用 PID 控制器计算出需要施加的力矩
        diff = self.angle_difference(self.physics_part.body.angle,angle)
        torque = self.gyroscope.update(diff, 0)

        return torque

    def physical_update(self) -> None:#在这里更新所有自己的组件
        # 从枪械列表找到Railgun类成员
        for guns in self.gun_list:
            if isinstance(guns,Railgun):
                railgun = guns
                break
        else:
            raise Exception('玩家没有Railgun类成员')
        if self.behavior.target == None:
            # 发送一个雷达搜索事件
            radar_search_event = RadarSearchEvent(self,Constants.ENEMYSHIP)
            self.pending_events.append(radar_search_event)
        self.behavior.update(allow_firing=False)
        if self.health_system.health_status == 0:
            self.destroy()
            return
        self.gun.update()
        self.keyboard_event_update()
        rotationTorque = self.angular_update()
        self.physics_part.update(
            force = self.thruster.update(self.center, (self.targetX, self.targetY)), 
            rotation_torque = rotationTorque
        )
        self.gun.update()
        if self.health_system.health_status == 0:
            self.destroy()
        self.railgun_charge_progress.current_health = railgun.current_power / railgun.power


    def render(self, camera: Camera) -> None:
        super().render(camera)
        self.hud_render()
        # 通过ai行为计算瞄准点
        self.behavior: ChaseAndAimingBehavior
        target_x,target_y = self.behavior.predicted_position  # 使用行为来更新
        #print(self.behavior.target)
        # print(target_x,target_y)
        # 在self.camera.apply((target_x, target_y)渲染self.target_point_surface
        self.screen.blit(self.target_point_surface, camera.apply((target_x, target_y)))

    def hud_render(self):
        current_time = pygame.time.get_ticks()
        time_diff = current_time - self.last_hud_update_time
        self.hud_needs_update = time_diff > Constants.ANIMATION_INTERVAL

        if self.hud_needs_update:
            self.hud_surface.fill((0, 0, 0, 0))  # 清空HUD

            line_height = 20  # 设置统一的行高
            y_offset = 0  # 初始Y偏移量

            if self.hud_state >= 1:
                # 绘制飞船状态的各行
                status_lines = [
                    f'目标位置: {(round(self.targetX, 2), round(self.targetY, 2))}',
                    f'当前位置: {(round(self.center[0], 2), round(self.center[1], 2))}',
                    f'速度: {round(self.physics_part.velocity.length, 2)} m/s',
                    f'方向: {round(self.angle, 2)} °'
                ]

                # 计算最大宽度
                max_width = max(self.font.size(line)[0] for line in status_lines)

                for line in status_lines:
                    text = self.font.render(line, True, (106, 153, 85))
                    # 使用最大宽度来渲染文本
                    self.hud_surface.blit(text, (self.screen.get_width() - max_width, y_offset))
                    y_offset += line_height

                # 绘制充能进度和相关文本
                charge_bar = self.railgun_charge_progress.health_bar
                charge_bar_position = (self.screen.get_width() - charge_bar.get_width(), y_offset)
                self.hud_surface.blit(charge_bar, charge_bar_position)
                charge_text = self.font.render('磁轨炮充能：', True, (106, 153, 85))
                charge_text_position = (charge_bar_position[0] - charge_text.get_width(), charge_bar_position[1])
                self.hud_surface.blit(charge_text, charge_text_position)
                y_offset += charge_bar.get_height() + 10  # 增加偏移量

            if self.hud_state >= 2:
                # 绘制HUD状态的文本
                y_offset = 0
                hud_lines = [
                    '按Tab切换hud状态',
                    'WASD控制飞船目标位置(绿点处)',
                    '鼠标控制方向，左键射击',
                    '如果发现无法移动请切换英文输入法',
                    '空格键将目标位置设为当前位置',
                    f'数字键1-{len(self.gun_list)}切换武器',
                    '游戏目标：击败敌人，努力生存',
                    f'当前帧率：{round(self.clock.get_fps(),2)}',
                    '关闭hud以提升帧率'
                ]
                for line in hud_lines:
                    text = self.font.render(line, True, (106, 153, 85))
                    self.hud_surface.blit(text, (0, y_offset))
                    y_offset += line_height

            self.last_hud_update_time = current_time

        self.screen.blit(self.hud_surface, (0, 0))

    def auto_register(self):
        self.event_manager.subscribe(self,Constants.RADAR_ECHO)
        super().auto_register()

    def handle_event(self, event: Event) -> None:
        #print("得到事件",event)
        super().handle_event(event)
        #print(event.event_type)
        if event.event_type == Constants.RADAR_ECHO:
            if event.target == self:
                #print('玩家得到雷达回波事件')
                self.behavior.target = event.source

default_enemy_assets = ResourceManager('resources\playership_big')
class EnemyFighter(ArmedShip):
    def __init__(self, 
            scene: Scene,#这里传入了scene，是为了方便在自动注册事件
            position: tuple[int, int], 
            space: pymunk.space, 
            screen: Surface,
            assets: ResourceManager = default_enemy_assets,
            gun_type: Literal['Gatling','Autocannon','Railgun'] = 'Gatling',
            angle: float = 0,
            mass: float = 5,#5
            gyroscope_torque: float = 5000000,#0.01, 0.00001, 10
            thruster_force: float = 4000,
            health: float = 60000,
            target_point_color: tuple[int,int,int] = (255,0,0),
            health_bar_size: tuple[int,int] = (-1,-1),#(-1,-1)表示按照游戏对象贴图短边作为长度，长：宽 = 7.5自动计算大小
            collision_type: int = Constants.ENEMYSHIP,
            scaling: float = 1,
            **kwargs
                ):
        if gun_type == 'Gatling':
            gun  = Gatling(self,fire_rate=30)
        elif gun_type == 'Railgun':
            gun = Railgun(self,max_charge_time=3000)
        elif gun_type == 'Autocannon':
            gun = Autocannon(self,fire_rate=4)
            
        super().__init__(scene = scene, position = position, space = space,screen = screen,
                         gun = gun, assets = assets, angle = angle, mass = mass,
                         gyroscope_torque = gyroscope_torque, thruster_force = thruster_force,
                         health = health, target_point_color = target_point_color,
                         health_bar_size = health_bar_size, collision_type = collision_type,
                         scaling = scaling, **kwargs
                         )
        
    def handle_event(self, event: Event) -> None:
        #print("得到事件",event)
        super().handle_event(event)
        # print(event.event_type)
        if event.event_type == Constants.RADAR_ECHO:
            if event.target == self:
                self.behavior.target = event.source

    def auto_register(self):
        self.event_manager.subscribe(self,Constants.RADAR_ECHO)
        super().auto_register()

    def physical_update(self) -> None:
        
        if self.behavior.target == None:
            # 发送一个雷达搜索事件
            radar_search_event = RadarSearchEvent(self,Constants.PLAYERSHIP)
            self.pending_events.append(radar_search_event)
        super().physical_update()