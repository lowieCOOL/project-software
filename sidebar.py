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
from pygame_widgets import Button, Dropdown
from main import target,latlon_to_screen
from aircraft import Aircraft, position 

def sidebar(screen):
    # Sidebar dimensions and width
    sidebar_width = screen.get_width() / 4  # 1/4 of the screen width
    sidebar_height = screen.get_height()
    
    pygame.draw.rect(screen, (30, 30, 30), (0, 0, sidebar_width, sidebar_height))
    
aircraft_list = ['123', '456', '789']  

class dropdown:   
    def __init__(self, screen, aircraft_list,WIDTH,HEIGHT):  # Example aircraft list
        self.screen = screen
        self.aircraft_list = aircraft_list
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        WIDTH,HEIGHT = screen.get_size()
    def dropdown(self,screen, aircraft_list, WIDTH, HEIGHT):
        super().__init__(self,screen,aircraft_list,WIDTH,HEIGHT)    
        Dropdown(
            self.screen,
            self.WIDTH * 3/5, 
            self.HEIGHT / 20, 
            self.WIDTH / 60, 
            self.HEIGHT / 80, 
            name='arrivals', 
            choices=aircraft_list, 
            borderRadius=5,
            colour=(50, 50, 50),
            direction='down',
            textHalign='left',
            font=pygame.font.SysFont('calibri', 10), 
            backgroundColour=(50, 50, 50), 
            textColour=(255, 255, 255), 
            )


# for this code you need to set all the aircrafts in a list

# def create_button(self, screen, min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING):
#     x,y = latlon_to_screen(self.position[0], self.position[1], min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING)
#     self.button = Button( self.screen, x, y, 40,60, onClick = self.click_handler, text=self.callsign, fontSize=10, fontColour=(255, 255, 255), hoverColour=(0, 0, 0), pressedColour=(0, 0, 0), radius=5)


# def update_buttonscreen(self, min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING,button):
#     x, y = latlon_to_screen(self.position[0], self.position[1], min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING)
#     self.button.setPos(x,y)
# from main import latlon_to_screen

class aircraft_buton(Aircraft): 
    def __init__(self, screen, position, target,WIDTH,HEIGHT):
        super.__init__(WIDTH,HEIGHT)
        self.screen = screen
        self.aircraft
        self.x = position[0]
        self.y = position[1]
        self.target = target
        
        # Create the button
        def button(self):
            super.__init__(self,screen,)
            Button(
                self.screen, 
                self.x,
                self.y,
                image=target  # Display aircraft callsign
                # onClick=self.click_handler
                )

    def update_position(self):
        # Update the button's position based on the aircraft's current screen coordinates
        x, y = latlon_to_screen(
            self.aircraft.position[0], self.aircraft.position[1],
            self.min_lat, self.max_lat, self.min_lon, self.max_lon,
            self.WIDTH, self.HEIGHT, self.PADDING
        )
        self.button.setPosition(x, y)