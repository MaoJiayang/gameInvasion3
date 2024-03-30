import pygame

class Button:
    def __init__(self, rect, color, text, font, text_color, action=None):
        self.rect = rect
        self.color = color
        self.text = text
        self.font = font
        self.text_color = text_color
        self.action = action
        self.clicked = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        self.draw_text(screen)

    def draw_text(self, screen):
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.clicked = True  # 设置为 True，表示按钮被点击
                if self.action is not None:
                    self.action()

    def get_click_status(self):
        return self.clicked

