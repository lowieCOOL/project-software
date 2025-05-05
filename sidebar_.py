'''
dropdown bar arrivals : https://github.com/AustL/PygameWidgets/blob/master/docs/widgets/dropdown.md
                        https://stackoverflow.com/questions/19877900/tips-on-adding-creating-a-drop-down-selection-box-in-pygame
sidebar:                https://github.com/Grimmys/rpg_tactical_fantasy_game/blob/master/src/gui/sidebar.py

                        https://github.com/ppizarror/pygame-menu/blob/master/pygame_menu/examples/game_selector.py
Toolbar:                https://stackoverflow.com/questions/24970676/creating-a-toolbar-in-pygame-window
                        https://stackoverflow.com/questions/24970676/creating-a-toolbar-in-pygame-window
                        https://darth-data410.medium.com/how-to-easily-create-pygame-user-interface-and-heads-up-display-elements-3b1bf424a2c8
start menu:             https://www.geeksforgeeks.org/creating-start-menu-in-pygame/

                        https://pygame.readthedocs.io/en/latest/6_gui/gui.html
pygame widgets mogen we gebreuken voor dropdown menu's, buttons, sliders, etc. : https://pygamewi pygame-widgetsdgets.readthedocs.io/en/stable/
'''
import pygame
from pygame_widgets import *
from pygame_widgets.button import Button
from pygame_widgets.dropdown import Dropdown






def draw_sidebar(screen):
    # Sidebar dimensions and width
    sidebar_width = screen.get_width() *(1/4) # 1/4 of the screen width
    sidebar_height = screen.get_height()
    
    pygame.draw.rect(screen, (100,100,100), (0, 0, sidebar_width, sidebar_height)) # 30, 30, 30
      

class DropdownMenu:
    def __init__(self, screen, aircraft_list):  # Example aircraft list
        self.screen = screen
        self.aircraft_list = aircraft_list
        self.WIDTH, self.HEIGHT = screen.get_size()  # Get screen dimensions dynamically

    def create_dropdown(self):    
        Dropdown(
            self.screen,
            self.WIDTH // 4,  # Adjust position dynamically
            self.HEIGHT // 20,  # Adjust position dynamically
            self.WIDTH // 6,  # Dropdown width
            30,  # Dropdown height
            name='Arrivals', 
            choices=self.aircraft_list, 
            borderRadius=5,
            colour=(150, 150, 150),
            direction='down',
            textHalign='left',
            font=pygame.font.SysFont('calibri', 10), 
            backgroundColour=(255, 255, 255), 
            textColour=(0, 0, 0), 
        )
    def draw(self):
        pygame.display.update()


