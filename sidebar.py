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

import pygame


pygame.init()  # Initialize pygame
from pygame_widgets.button import Button
from pygame_widgets.dropdown import Dropdown
from aircraft_generator import generate_flight

aircraft_list = ['123', '456', '789']  

def sidebar(screen):
    # Sidebar dimensions and width
    sidebar_width = screen.get_width() / 4  # 1/4 of the screen width
    sidebar_height = screen.get_height()
    
    pygame.draw.rect(screen, (30, 30, 30), (0, 0, sidebar_width, sidebar_height))

class dropdown(self, screen, aircraft_list,WIDTH,HEIGHT)   
aircraft_list = ['123', '456', '789']  # Example aircraft list
dropdown = Dropdown(
    screen, 
    x=int(WIDTH * 3/5), 
    y=int(HEIGHT / 20), 
    width=int(WIDTH / 6), 
    height=int(HEIGHT / 20), 
    name='arrivals', 
    choices=aircraft_list, 
    borderRadius=5,
    colour=(50, 50, 50),
    direction='down',
    textHalign='left',
    font=pygame.font.SysFont('calibri', 10), 
    backgroundColour=(50, 50, 50), 
    textColour=(255, 255, 255), 
    dropHeight=200
)


# class Radar(Scene):
#     def __init__(self, data, screen_height, screen_width):
#         super().__init__(
#             "radar",
#             data,
#             screen_height,
#             screen_width,
#             {
#                 "top": data["top"],
#                 "bottom": data["bottom"],
#                 "left": data["left"],
#                 "right": data["right"],
#             },
#         )

#     def render(self):
#         self.surface.fill((0, 0, 0))

#         pygame.draw.line(
#             self.surface, (255, 255, 255), self.runway_start, self.runway_end, width=3
#         )

#         for line in self.data["lines"]:
#             pygame.draw.line(
#                 self.surface,
#                 (255, 255, 255),
#                 self.coord_to_pixel((line["start_lat"], line["start_long"])),
#                 self.coord_to_pixel((line["end_lat"], line["end_long"])),
#             )

#         # render traffic pattern
#         draw_line_dashed(
#             self.surface, (86, 176, 91), self.runway_start, self.extended_final
#         )
       
#     def render_label(self, aircraft, selected, label_sweep):
#         # Change color if aircraft is selected
#         if selected == aircraft:
#             aircraft.color = (174, 179, 36)
#         else:
#             aircraft.color = (86, 176, 91)
#         aircraft.textSurf.fill(pygame.Color(0, 0, 0, 0))
#         aircraft.textSurf.set_alpha(255)

#         # Convert altitudes to three didget standard
#         if aircraft.altitude < 1000:
#             altitude = "00" + str(aircraft.altitude)[0]
#         elif aircraft.altitude >= 1000 and aircraft.altitude < 10000:
#             altitude = "0" + str(aircraft.altitude)[0:2]
#         else:
#             altitude = str(aircraft.altitude)[0:3]

#         if aircraft.target_altitude < 1000:
#             target_altitude = "00" + str(aircraft.target_altitude)[0]
#         elif aircraft.target_altitude >= 1000 and aircraft.altitude < 10000:
#             target_altitude = "0" + str(aircraft.target_altitude)[0:2]
#         else:
#             target_altitude = str(aircraft.target_altitude)[0:3]

#         # Determine display text and size
#         displayText1 = f"{aircraft.name} "
#         displayText2 = f"{altitude} {aircraft.speed}  "
#         displayText3 = f"{target_altitude} {aircraft.aircraft_type} "
#         # Determine the x, y size of displayText according to pygame
#         # Then add 5 because it's slightly too small (shrug)
#         displaySize = tuple(n + 5 for n in aircraft.font.size(displayText1))

#         # Clear and redraw the text surface
#         aircraft.textSurf1 = aircraft.font.render(str(displayText1), 1, aircraft.color)
#         if label_sweep:
#             aircraft.textSurf2 = aircraft.font.render(
#                 str(displayText2), 1, aircraft.color
#             )
#         else:
#             aircraft.textSurf2 = aircraft.font.render(
#                 str(displayText3), 1, aircraft.color
#             )
#         aircraft.surf = pygame.Surface(
#             (displaySize[0], displaySize[1] * 2), pygame.SRCALPHA
#         )
#         aircraft.super_surf = pygame.Surface(
#             (displaySize[0] * 2, displaySize[0] * 2), pygame.SRCALPHA
#         )
#         pygame.draw.rect(
#             aircraft.surf,
#             aircraft.color,
#             (0, ((displaySize[1] * 2 - 10) / 2) - 2.5, 5, 5),
#         )
#         aircraft.surf.blit(aircraft.textSurf1, (9, 0))
#         aircraft.surf.blit(aircraft.textSurf2, (9, displaySize[1] - 5))

#         aircraft.super_surf.blit(aircraft.surf, (displaySize[0], ((displaySize[0] * 2) - displaySize[1] * 2) / 2))

#         return displaySize
    




# for this code you need to set all the aircrafts in a list
# def create_button(self, screen, min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING):
#     x,y = latlon_to_screen(self.position[0], self.position[1], min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING)
#     self.button = Button( self.screen, x, y, 40,60, onClick = self.click_handler, text=self.callsign, fontSize=10, fontColour=(255, 255, 255), hoverColour=(0, 0, 0), pressedColour=(0, 0, 0), radius=5)


# def update_buttonscreen(self, min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING,button):
#     x, y = latlon_to_screen(self.position[0], self.position[1], min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING)
#     self.button.setPos(x,y)
# from main import latlon_to_screen
from pygame_widgets import button
from main import latlon_to_screen  # Import the latlon_to_screen function

class buton:
    def __init__(self, aircraft, screen, min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING):
        self.aircraft = aircraft
        self.screen = screen
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.PADDING = PADDING

        # Get initial screen coordinates of the aircraft
        x, y = latlon_to_screen(
            self.aircraft.position[0], self.aircraft.position[1],
            self.min_lat, self.max_lat, self.min_lon, self.max_lon,
            self.WIDTH, self.HEIGHT, self.PADDING
        )

        # Create the button
        self.button = Button(
            self.screen, x, y, 60, 30,  # Button size
            text=self.aircraft.callsign,  # Display aircraft callsign
            fontSize=12,
            fontColour=(255, 255, 255),
            hoverColour=(100, 100, 100),
            pressedColour=(50, 50, 50),
            radius=5,
            onClick=self.click_handler
            image = target
        )

    def update_position(self):
        # Update the button's position based on the aircraft's current screen coordinates
        x, y = latlon_to_screen(
            self.aircraft.position[0], self.aircraft.position[1],
            self.min_lat, self.max_lat, self.min_lon, self.max_lon,
            self.WIDTH, self.HEIGHT, self.PADDING
        )
        self.button.setPosition(x, y)

    def click_handler(self):
        # Handle button clicks (e.g., display aircraft info)
        print(f"Aircraft {self.aircraft.callsign} clicked!")
        
'''