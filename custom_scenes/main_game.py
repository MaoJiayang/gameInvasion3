from invasionEngine.events import Event
from custom_components.custom_events import KineticHitEvent,RadarEchoEvent,RadarSearchEvent
from invasionEngine.scenes import GameScene
from invasionEngine.game_objects import GameObject,PhysicalGO,TerrainGO
from invasionEngine.components import Camera,physicsComponent,ResourceManager
from custom_components.constants import CustomConstants as Constants
from custom_gos.bullet import Bullet
from custom_gos.scene_manager import SceneManager
import pygame
import pymunk
from custom_gos.bullet import Bullet
from custom_gos.armed_ship import ArmedShip,Player,EnemyFighter
class MainGame(GameScene):
    def __init__(self, title: str = '测试玩家场景'):
        super().__init__(title)
        self.playership_bullet_handler = self.space.add_collision_handler(Constants.PLAYERSHIP , Constants.BULLET)#注册碰撞处理器
        self.playership_bullet_handler.post_solve = self.on_hit #注册碰撞处理函数
        self.enemy_bullet_handler = self.space.add_collision_handler(Constants.ENEMYSHIP , Constants.BULLET)
        self.enemy_bullet_handler.post_solve = self.on_hit#注册碰撞处理函数
        #订阅雷达搜索事件
        self.event_manager.subscribe(self,Constants.RADAR_SEARCH)
        #设置重力
        # self.space.gravity = (0,-100)
    def load_spirites(self):
        bocchi_pics = ResourceManager('resources\\bo2')
        astorid_pics = ResourceManager('resources\\astorid')
        bullet_pics = ResourceManager('resources\\railgun')
        #创建一个测试对象
        #test_object = PhysicalGO((0,150),self.space,self.screen,assets = enemy_pics,shape_type = 'poly',mass = 10)
        astorid = PhysicalGO((-200,-200),self.space,self.screen,assets = astorid_pics,shape_type = 'poly',mass = 500)
        astorid2 = PhysicalGO((200,200),self.space,self.screen,assets = astorid_pics,shape_type = 'poly',mass = 500)
        astorid3 = PhysicalGO((200,-200),self.space,self.screen,assets = astorid_pics,shape_type = 'poly',mass = 500)
        #test_object3 = Bullet((150,0),self.space,self.screen,assets = bullet_pics,time_to_live=100000,mass=10)
        bocchi = GameObject((0,0),self.space,self.screen,assets = bocchi_pics)
        bullet_test = Bullet((400,0),self.space,self.screen,assets = bullet_pics,time_to_live=100000,mass=10,angle=270)
        player = Player(self,(200,200),self.space,self.screen,camera = self.camera,shape_type = 'poly')
        self.player = player
        self.camera.focus = self.player
        manager = SceneManager(self,self.screen)
        

        # 使用自省功能将所有GameObject的实例加入精灵组
        for var_name, var_value in locals().items():
            if isinstance(var_value, GameObject):
                self.all_sprites.add(var_value)

    def load_map(self):
        #为地图创建边界
        terrain_asserts = ResourceManager('resources\edges')
        map_height = 6000
        map_width = 6000
        # 使用线段划定地图边界
        # 设中点为0,0，确定四条线段的端点坐标对
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
        
    def on_hit(self,arbiter: pymunk.Arbiter,space,data):
        # 子弹和飞船碰撞后，子弹消失，飞船受到伤害
        #获取碰撞的两个物体
        
        if arbiter.shapes[0] in self.shapes_go_dict:

            ship:Player = self.shapes_go_dict[arbiter.shapes[0]]
        else:
            return
        if arbiter.shapes[1] in self.shapes_go_dict:
            bullet: Bullet = self.shapes_go_dict[arbiter.shapes[1]]
        else:
            return
        #包装一个KineticHitEvent事件
        hit_event = KineticHitEvent(bullet,ship,bullet.physics_part.velocity,bullet.physics_part.body.mass)
        #发布事件
        self.event_manager.add_event(hit_event)
        bullet.destroy()
        return False
    
    def update(self):
        super().update()
        #摄像头缩放
        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # 鼠标滚轮向上滚动
                    self.camera.zooming(0.15)  # 放大视角
                if event.button == 5:  # 鼠标滚轮向下滚动
                    self.camera.zooming(-0.15)  # 缩小视角
    
    def handle_event(self, event: Event):
        if event.event_type == Constants.RADAR_SEARCH:
            echo_type = event.echo_type
            # 从精灵组中获取所有和反射类型相同的对象
            for sprite in self.all_sprites:
                try:
                    if sprite.physics_part.shape.collision_type == echo_type:
                        # 创建一个雷达回波对象
                        echo = RadarEchoEvent(sprite, event.source)
                        # 发布雷达回波事件
                        self.event_manager.add_event(echo)
                        #print('雷达回波事件发布成功,源：',sprite,'目标：',event.source,)
                except:
                    continue
        super().handle_event(event)