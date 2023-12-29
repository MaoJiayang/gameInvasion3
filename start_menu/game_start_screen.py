import pygame
import sys
import os
from .Button import Button
from invasionEngine.constants import Constants
class GameStartScreen:
    def __init__(self, screen_width=Constants.SCREEN_WIDTH, screen_height=Constants.SCREEN_HEIGHT):
        pygame.init()

        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = screen_width, screen_height

        self.BACKGROUND_COLOR = (255, 255, 255)
        self.BUTTON_COLOR = (50, 50, 50)
        self.TEXT_COLOR = (255, 255, 255)

        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("游戏开始界面")

        self.background_image = pygame.image.load("resources\preface\start.jpg")
        #将图片放缩到屏幕尺寸
        self.background_image = pygame.transform.scale(self.background_image, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.background_rect = self.background_image.get_rect()

        self.font = pygame.font.Font('resources\\fonts\simhei\SIMHEI.TTF', 36)
        self.starting_text = False

        self.start_button = Button(
            pygame.Rect(self.SCREEN_WIDTH // 4, self.SCREEN_HEIGHT // 2, self.SCREEN_WIDTH // 2, 50),
            self.BUTTON_COLOR,
            "开始游戏",
            self.font,
            self.TEXT_COLOR,
            self.start_game
        )

        self.exit_button = Button(
            pygame.Rect(self.SCREEN_WIDTH // 4, self.SCREEN_HEIGHT // 2 + 100, self.SCREEN_WIDTH // 2, 50),
            self.BUTTON_COLOR,
            "退出游戏",
            self.font,
            self.TEXT_COLOR,
            sys.exit
        )

    def get_starting_text(self):
        return self.starting_text

    def draw_text(self, text, x, y):
        text_surface = self.font.render(text, True, self.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)

    def start_game(self):
        self.starting_text = True

    def start_game(self):
        # 用户点击“开始游戏”按钮后，设置 starting_text 为 True
        self.starting_text = True

    def run(self):
        running = True
        start_game = False  # 标志位用于指示是否开始游戏
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # 检查按钮点击
                self.start_button.check_click(event)
                self.exit_button.check_click(event)

                # 获取按钮状态
                start_button_status = self.start_button.get_click_status()
                exit_button_status = self.exit_button.get_click_status()

                # 检查按钮状态
                if start_button_status:
                    start_game = True  # 设置开始游戏标志位为 True
                    running = False
                elif exit_button_status:
                    running = False

            self.screen.blit(self.background_image, self.background_rect)
            self.draw_text("星域之争：守卫文明", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 5)
            self.start_button.draw(self.screen)
            self.exit_button.draw(self.screen)
            pygame.display.flip()

        # 返回 start_game 的值，如果用户选择退出游戏或关闭窗口，这里将返回 False
        return start_game
