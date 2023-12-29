from invasionEngine.components import ComponentBase
import pygame
class HealthSystem(ComponentBase):
    """ 游戏对象生命系统. """

    def __init__(self, max_health: int, health_bar_size: tuple[int,int] = (50, 10)):
        self.max_health: float = max_health
        self.current_health: float = max_health
        self.health_bar_size: tuple[int,int] = health_bar_size
        #如果元组中存在负数则报错
        if self.health_bar_size[0] < 0 or self.health_bar_size[1] < 0:
            raise ValueError("health_bar_size",health_bar_size,"中存在负数")
        
        #绘制血条边框
        self.bar_surface = pygame.Surface(self.health_bar_size, pygame.SRCALPHA)
        border_color = (192, 192, 192)  # 银色
        border_rect = pygame.Rect(0, 0, self.health_bar_size[0], self.health_bar_size[1])
        pygame.draw.rect(self.bar_surface, border_color, border_rect, 2)  # 最后一个参数是边框的宽度

    def take_damage(self, amount: float) -> None:
        """ 接受伤害.不论正负都是接受伤害"""
        self.current_health -= abs(amount)
        if self.current_health < 0:
            self.current_health = 0

    def heal(self, amount: float) -> None:
        """ 恢复生命值.不论正负都是恢复"""
        self.current_health += abs(amount)
        if self.current_health > self.max_health:
            self.current_health = self.max_health

    @property
    def alive(self) -> bool:
        """ Returns True if the object is still alive, otherwise False. """
        return self.current_health > 0
    @property
    def health_status(self) -> float:
        """ 返回当前生命值与最大生命值的比值. """
        return self.current_health/self.max_health#TODO:检查一下为什么当前生命会大于最大生命
    @property
    def health_bar(self) -> pygame.Surface:
        """ 返回一个血条surface. """
        green = int(255 * self.health_status)
        red = max(0,255 - green)
        color = (red, green, 0)

        # 计算血条的宽度
        health_width = int((self.health_bar_size[0] - 4) * self.health_status)  # 减去边框的宽度
        bar_surface = self.bar_surface.copy()
        # 在Surface对象上绘制血条
        pygame.draw.rect(bar_surface, color, pygame.Rect(2, 2, health_width, self.health_bar_size[1] - 4))  # 减去边框的宽度

        return bar_surface

    @property
    def current_health(self):
        return self._current_health

    @current_health.setter
    def current_health(self, value: float):
        if value > self.max_health:
            self._current_health = self.max_health
        elif value < 0:
            self._current_health = 0
        else:
            self._current_health = value
    
    def update(self) -> None:
        pass
    
    def destroy(self) -> None:  
        pass
