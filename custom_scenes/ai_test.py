from invasionEngine.events import Event
from custom_components.custom_events import HitEvent
from invasionEngine.scenes import GameScene
from invasionEngine.game_objects import GameObject,PhysicalGO,TerrainGO
from invasionEngine.components import Camera,physicsComponent,ResourceManager
from custom_components.constants import CustomConstants as Constants

import pygame
import pymunk
from custom_gos.bullet import Bullet
from custom_gos.player import Player
from custom_gos.enemy import Enemy
class AITest(GameScene):
    def __init__(self, title: str = '测试玩家场景'):
        super().__init__(title)
        self.shipBullethandler = self.space.add_collision_handler(Constants.SHIP , Constants.BULLET)#注册碰撞处理器
        self.shipBullethandler.separate = self.on_hit #注册碰撞处理函数
        #设置重力
        # self.space.gravity = (0,-100)
    def load_spirites(self):
        bullet_pics = ResourceManager('resources\\bullets')
        player_pics = ResourceManager('resources\playership_pics')
        enemy_pics = ResourceManager('resources\playership_big')
        bocchi_pics = ResourceManager('resources\\bo2')
        astorid_pics = ResourceManager('resources\\astorid')
        #创建一个测试对象
        #test_object = PhysicalGO((0,150),self.space,self.screen,assets = enemy_pics,shape_type = 'poly',mass = 10)
        enemy1 = Enemy((-400,-400),self.space,self.screen,assets = enemy_pics,shape_type = 'poly')
        enemy2 = Enemy((400,400),self.space,self.screen,assets = player_pics,shape_type = 'poly',scaling=0.8)
        astorid = PhysicalGO((-200,-200),self.space,self.screen,assets = astorid_pics,shape_type = 'poly',mass = 500)
        astorid2 = PhysicalGO((200,200),self.space,self.screen,assets = astorid_pics,shape_type = 'poly',mass = 500)
        astorid3 = PhysicalGO((200,-200),self.space,self.screen,assets = astorid_pics,shape_type = 'poly',mass = 500)
        #test_object3 = Bullet((150,0),self.space,self.screen,assets = bullet_pics,time_to_live=100000,mass=10)
        bocchi = GameObject((400,400),self.space,self.screen,assets = bocchi_pics)
        player = Player((200,200),self.space,self.screen,assets = player_pics,camera = self.camera,shape_type = 'poly')
        #player订阅HIT_EVENT事件
        self.event_manager.subscribe(player,Constants.HIT_EVENT)
        #敌人订阅HIT_EVENT事件
        self.event_manager.subscribe(enemy1,Constants.HIT_EVENT)
        self.event_manager.subscribe(enemy2,Constants.HIT_EVENT)
        enemy1.behavior.target = enemy2#设置敌人的目标
        enemy2.behavior.target = enemy1#设置敌人的目标
        self.camera.set_focus(player)
        #将测试对象加入精灵组
        #self.all_sprites.add(test_object)
        self.all_sprites.add(enemy1)
        self.all_sprites.add(enemy2)
        self.all_sprites.add(player)
        self.all_sprites.add(bocchi)
        self.all_sprites.add(astorid)
        self.all_sprites.add(astorid2)
        self.all_sprites.add(astorid3)
    def load_map(self):
        #为地图创建边界
        terrain_asserts = ResourceManager('resources\edges')
        map_height = 6000
        map_width = 4000

        # 使用线段划定地图边界
        # 设中点为0,0，地图宽度为1900，高度为3000，确定四条线段的端点坐标对
        edges = [
            # 上边界
            [(-map_width/2, map_height/2), (map_width/2, map_height/2)],
            # 右边界
            [(map_width/2, map_height/2), (map_width/2, -map_height/2)],
            # 下边界
            [(map_width/2, -map_height/2), (-map_width/2, -map_height/2)],
            # 左边界
            [(-map_width/2, -map_height/2), (-map_width/2, map_height/2)]
        ]

        # 创建地图边界
        for edge in edges:
            edge_go = TerrainGO((0,0), self.space, self.screen, assets=terrain_asserts, shape_type='segment', shape_size=edge,radius=50,elasticity=0.5)
            self.all_sprites.add(edge_go)

        # edge_go = TerrainGO((0,0), self.space, self.screen, assets=terrain_asserts, shape_type='segment', shape_size=[(100,200),(300,600)],radius=20,elasticity=0.5)
        # self.all_sprites.add(edge_go)
        
    def on_hit(self,arbiter,space,data):
        # 子弹和飞船碰撞后，子弹消失，飞船受到伤害
        #获取碰撞的两个物体
        if arbiter.shapes[0] in self.shapes_go_dict:
            ship = self.shapes_go_dict[arbiter.shapes[0]]
        else:
            return
        if arbiter.shapes[1] in self.shapes_go_dict:
            bullet = self.shapes_go_dict[arbiter.shapes[1]]
        else:
            return
        # 获取子弹的动能
        bullet_energy = bullet.physics_part.body.kinetic_energy/(Constants.PIXELS_PER_METER**2)
        #包装一个HIT_EVENT事件
        hit_event = HitEvent(bullet,ship,bullet_energy)
        #发布事件
        self.event_manager.add_event(hit_event)
        bullet.destroy()
        return True
    
    def update(self):
        super().update()
        #摄像头缩放
        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # 鼠标滚轮向上滚动
                    self.camera.zooming(0.15)  # 放大视角
                elif event.button == 5:  # 鼠标滚轮向下滚动
                    self.camera.zooming(-0.15)  # 缩小视角
    
        