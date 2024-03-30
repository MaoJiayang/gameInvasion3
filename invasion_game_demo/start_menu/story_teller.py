
import pygame
import sys
import os
from invasionEngine.constants import Constants
# 访问游戏固定常量
screen_width = Constants.SCREEN_WIDTH
screen_height = Constants.SCREEN_HEIGHT


class StoryTeller:
    def __init__(self, width = Constants.SCREEN_WIDTH, height = Constants.SCREEN_HEIGHT, font_size = 20, text_speed = 0.025, bg_color=(0, 0, 0), font_color=(255, 255, 255)):
        pygame.init()

        self.WIDTH, self.HEIGHT = width, height
        self.BG_COLOR = bg_color
        self.FONT_COLOR = font_color
        self.FONT_SIZE = font_size
        self.TEXT_SPEED = text_speed  # 用于控制字幕显示的速度
        self.running = False

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Text Display")

        self.font = pygame.font.Font('resources\\fonts\simhei\SIMHEI.TTF', self.FONT_SIZE)

        self.background_images = ["resources\preface\\text1.jpg", "resources\preface/text2.jpg", "resources\preface/text3.jpg",
                                  "resources\preface/text4.jpg"]

    def display_text_with_background(self, text, background_image):
        background = pygame.image.load(background_image)
        background = pygame.transform.scale(background, (self.WIDTH, self.HEIGHT))

        i = 0
        text_complete = False
        while not text_complete:
            self.screen.blit(background, (0, 0))
            text_surface = self.font.render(text[:i + 1], True, self.FONT_COLOR)
            self.screen.blit(text_surface, (120, 100))
            pygame.display.flip()

            if i < len(text):
                i += 1
            else:
                text_complete = True  # 完成整个文本的展示

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Skip to end of text and display it all
                        i = len(text)
                        text_surface = self.font.render(text, True, self.FONT_COLOR)
                        self.screen.blit(text_surface, (120, 100))
                        pygame.display.flip()
                        text_complete = True

            pygame.time.wait(int(self.TEXT_SPEED * 1000))

    def run(self, texts):
        self.running = True
        for i, text in enumerate(texts):
            self.display_text_with_background(text, self.background_images[i])

            continue_text = self.font.render("按空格键继续...", True, self.FONT_COLOR)
            text_rect = continue_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 125))
            self.screen.blit(continue_text, text_rect)
            pygame.display.flip()

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        waiting = False
        self.running = False
        return True

