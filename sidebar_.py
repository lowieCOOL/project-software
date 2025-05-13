'''
import pygame
from pygame_widgets import *
from pygame_widgets.button import Button
from pygame_widgets.dropdown import Dropdown
from aircraft import *

      

class DropdownMenu:
    def __init__(self, screen, aircraft_list):  # Example aircraft list
        self.screen = screen
        self.aircraft_list = aircraft_list
        self.WIDTH, self.HEIGHT = screen.get_size()  # Get screen dimensions dynamically

    def draw_sidebar(screen):
    # Sidebar dimensions and width
        sidebar_width = screen.get_width() *(1/4) # 1/4 of the screen width
        sidebar_height = screen.get_height()
        pygame.draw.rect(screen, (40,40,40), (0, 0, sidebar_width, sidebar_height)) # 30, 30, 30
    def create_dropdown(self):    
        Dropdown(
            self.screen,
            self.WIDTH // 4,  # Adjust position dynamically
            self.HEIGHT // 20,  # Adjust position dynamically
            self.WIDTH // 6,  # Dropdown width
            30,  # Dropdown height
            name='Arrivals', 
            choices= self.aircraft_list, 
            borderRadius= 5,
            colour=(150, 150, 150),
            direction='down',
            textHalign='left',
            font=pygame.font.SysFont('calibri', 10), 
            backgroundColour=(255, 255, 255), 
            textColour=(0, 0, 0), 
            Oncklicked=lambda: Aircraft.clickhandler(),  # Callback function when an item is selected
        )


'''