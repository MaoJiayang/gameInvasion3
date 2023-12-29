from invasionEngine.components import ResourceManager,EventManager,Camera
from invasionEngine.events import CreateEvent
from invasionEngine.game_objects import GameObject,PhysicalGO
from invasionEngine.scenes import Scene
from custom_gos.armed_ship import Player,EnemyFighter
from custom_components.constants import CustomConstants as Constants 
from pygame import Surface
import pygame
import random

class SceneManager(GameObject):
    def __init__(self, 
                 scene: Scene,
                 screen: Surface, 
                 position: tuple[int, int] = (0,0),
                 assets: ResourceManager = None,
                 scaling: float = 1,):
        super(). __init__(
                 position = position, 
                 space = None, 
                 screen = screen, 
                 assets = assets,
                 scaling = scaling
                 )
        
        self.scene: Scene = scene
        self.pending_score: float = 0#待加分
        self.score_count: float = 0#计分器
        self.font = pygame.font.Font('resources\\fonts\simhei\SIMHEI.TTF', 60)#用于显示测试文字
        self.score_font = pygame.font.Font('resources\\fonts\simhei\SIMHEI.TTF', 25)
        self.time_score:float = 0#时间得分

    def update(self, event_manager: EventManager) -> None:
        if self.scene.player.destroyed:
            self.scene.camera.set_focus(None)
            self.respawn()

        self.spawn_enemy()
        self.time_score = (pygame.time.get_ticks() - self.initial_time) / 1000 *1.07



        super().update(event_manager)
        
    def render(self, camera: Camera) -> None:
        """完全重写render,因为这是个不可见对象"""
        zoom = self.scaling
        image_to_render = pygame.transform.rotate(self.current_image, -self.angle)#渲染角度和物理角度相反
        image_to_render = pygame.transform.scale(image_to_render, (int(image_to_render.get_width() * zoom ), int(image_to_render.get_height() * zoom )))
        rect = image_to_render.get_rect()
        
        rect.center = self.position  # 设置rect的中心为screen_position
        self.rect = rect

        self.screen.blit(image_to_render, rect.topleft)  # 使用rect的左上角作为渲染位置

        #在屏幕右下角显示得分
        score_text = self.score_font.render('击杀得分：{:.2f}'.format(self.score_count), True, (86, 156, 179))
        time_score_text = self.score_font.render('时间分：{:.2f}'.format(self.time_score), True, (86, 156, 179))
        self.screen.blit(score_text, (self.screen.get_width() - score_text.get_width() - 10, self.screen.get_height() - score_text.get_height() - 10))
        self.screen.blit(time_score_text, (self.screen.get_width() - time_score_text.get_width() - 10, self.screen.get_height() - time_score_text.get_height() - 40))

    def spawn_enemy(self):
        """生成敌人"""
        enemy_count = 0
        # 遍历精灵列表，如果有敌人，就不生成
        for sprite in self.scene.all_sprites:
            try:
                if sprite.physics_part.shape.collision_type == Constants.ENEMYSHIP:
                    enemy_count += 1
            except:
                pass
        if enemy_count < 0:
            # 生成敌人
            self.score_count += self.pending_score
            gun_list = ['Gatling', 'Autocannon', 'Railgun']
            gun_type = random.choice(gun_list)
            # player_position = self.scene.player.position
            random_position = (random.randint(-2000,2000),random.randint(-2000,2000))
            scaling = random.uniform(0.09,0.21)#尺寸。越大的敌人越容易被命中且不灵活
            health = random.randint(30000,60000)#生命值
            enemy = EnemyFighter(self.scene,random_position,self.scene.space,self.scene.screen,scaling=scaling,gun_type=gun_type,health=health)
            self.scene.all_sprites.add(enemy)
            self.pending_score = (1 - scaling) * health * 0.01#击杀得分

    def respawn(self):
        """
        询问是否重生。包括重置计分器，（只能重置物理对象！）
        生成玩家，相机聚焦
        """
        living_time = (pygame.time.get_ticks() - self.initial_time) /1000
        self.score_count += self.time_score
        content1 = '你存活了{:.2f}秒，得分：{:.2f}'.format(living_time, self.score_count)
        content2 = '按R重生，按ESC退出'

        # 渲染文字并绘制到屏幕上
        text1 = self.font.render(content1, True, (255, 255, 255))
        text2 = self.font.render(content2, True, (255, 255, 255))
        # 计算文本的中心位置
        text1_x = (self.scene.screen.get_width() - text1.get_width()) // 2
        text1_y = (self.scene.screen.get_height() - text1.get_height()) // 2
        text2_x = (self.scene.screen.get_width() - text2.get_width()) // 2
        text2_y = text1_y + 100  # 在第一行文本下方留出一些空间

        while True:
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # 玩家选择重生
                        new_player = Player(self.scene, (0, 0), self.scene.space, self.screen, camera=self.scene.camera, shape_type='poly')
                        self.scene.camera.set_focus(new_player)
                        self.scene.all_sprites.add(new_player)
                        self.scene.player = new_player
                        self.score_count = 0
                        self.initial_time = pygame.time.get_ticks()
                        return  # 退出重生循环
                    elif event.key == pygame.K_ESCAPE:
                        # 玩家选择退出
                        pygame.quit()
                        quit()
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            # 每次循环都重新绘制文本
            self.scene.screen.blit(text1, (text1_x, text1_y))
            self.scene.screen.blit(text2, (text2_x, text2_y))
            pygame.display.flip()

    def spawn_astorids(self):
        """生成小行星"""