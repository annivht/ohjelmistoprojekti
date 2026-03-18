import pygame
#------------------------------------------------------
#Asennus: pip install pygame-menu
#------------------------------------------------------


# Oletusnäytön asetukset (käytetään vain koordinaatteihin, ei luoda uutta ikkunaa)
WIDTH, HEIGHT = 700, 600

# Standard RGB colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 100, 100)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Main function of the program


def main():
    try:
        import pygame_menu as pm
    except Exception:
        pm = None

    if pm is None:
        _fallback_settings_screen()
        return

    # List that is displayed while selecting the graphics level
    graphics = [("Low", "low"),
                ("Medium", "medium"),
                ("High", "high"),
                ("Ultra High", "ultra high")]

    # List that is displayed while selecting the window resolution level
    resolution = [("1920x1080", "1920x1080"),
                  ("1920x1200", "1920x1200"),
                  ("1280x720", "1280x720"),
                  ("2560x1440", "2560x1440"),
                  ("3840x2160", "3840x2160")]

    # List that is displayed while selecting the difficulty
    difficulty = [("Easy", "Easy"),
                  ("Medium", "Medium"),
                  ("Expert", "Expert")]

    # List that is displayed while selecting the player's perspective
    perspectives = [("FPP", "fpp"),
                    ("TPP", "tpp")]

    # This function displays the currently selected options

    def printSettings():
        print("\n\n")
        # getting the data using "get_input_data" method of the Menu class
        settingsData = settings.get_input_data()

        for key in settingsData.keys():
            print(f"{key}\t:\t{settingsData[key]}")

    # Creating the settings menu
    settings = pm.Menu(title="Settings",
                       width=WIDTH,
                       height=HEIGHT,
                       theme=pm.themes.THEME_GREEN)

    # Adjusting the default values
    settings._theme.widget_font_size = 25
    settings._theme.widget_font_color = BLACK
    settings._theme.widget_alignment = pm.locals.ALIGN_LEFT

    # Text input that takes in the username
    settings.add.text_input(title="User Name : ", textinput_id="username")

    # 2 different Drop-downs to select the graphics level and the resolution level
    settings.add.dropselect(title="Graphics Level", items=graphics,
                            dropselect_id="graphics level", default=0)
    settings.add.dropselect_multiple(title="Window Resolution", items=resolution,
                                     dropselect_multiple_id="Resolution",
                                     open_middle=True, max_selected=1,
                                     selection_box_height=6)

    # Toggle switches to turn on/off the music and sound
    settings.add.toggle_switch(
        title="Muisc", default=True, toggleswitch_id="music")
    settings.add.toggle_switch(
        title="Sounds", default=False, toggleswitch_id="sound")

    # Selector to choose between the types of difficulties available
    settings.add.selector(title="Difficulty\t", items=difficulty,
                          selector_id="difficulty", default=0)

    # Range slider that lets to choose a value using a slider
    settings.add.range_slider(title="FOV", default=60, range_values=(
        50, 100), increment=1, value_format=lambda x: str(int(x)), rangeslider_id="fov")

    # Fancy selector (style added to the default selector) to choose between 
    #first person and third person perspectives
    settings.add.selector(title="Perspective", items=perspectives,
                          default=0, style="fancy", selector_id="perspective")

    # clock that displays the current date and time
    settings.add.clock(clock_format="%d-%m-%y %H:%M:%S",
                       title_format="Local Time : {0}")

    # 3 different buttons each with a different style and purpose
    done = False
    def exit_settings():
        nonlocal done
        done = True

    settings.add.button(title="Return To Main Menu", action=exit_settings, align=pm.locals.ALIGN_CENTER)
    settings.add.button(title="Print Settings", action=printSettings,
                        font_color=WHITE, background_color=GREEN)
    settings.add.button(title="Restore Defaults", action=settings.reset_value,
                        font_color=WHITE, background_color=RED)

    # Creating the main menu
    mainMenu = pm.Menu(title="Main Menu",
                       width=WIDTH,
                       height=HEIGHT,
                       theme=pm.themes.THEME_GREEN)

    # Adjusting the default values
    mainMenu._theme.widget_alignment = pm.locals.ALIGN_CENTER

    # Button that takes to the settings menu when clicked
    mainMenu.add.button(title="Settings", action=settings,
                        font_color=WHITE, background_color=GREEN)

    # An empty label that is used to add a seperation between the two buttons
    mainMenu.add.label(title="")

    # Exit button that is used to terminate the program
    mainMenu.add.button(title="Exit", action=pm.events.EXIT,
                        font_color=WHITE, background_color=RED)

    # Lets us loop the main menu on the screen
    while not done:
        settings.mainloop(pygame.display.get_surface(), disable_loop=True)
    return


def _fallback_settings_screen():
    """Fallback settings page when pygame_menu is not installed."""
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((1600, 800))

    if not pygame.font.get_init():
        pygame.font.init()

    title_font = pygame.font.Font(None, 72)
    info_font = pygame.font.Font(None, 40)
    hint_font = pygame.font.Font(None, 32)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                running = False

        screen.fill((22, 28, 40))

        title = title_font.render("SETTINGS", True, (240, 240, 240))
        info = info_font.render("pygame_menu is not installed.", True, (210, 210, 210))
        hint = hint_font.render("Press ESC, Enter, or click to return.", True, (170, 190, 220))

        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 220)))
        screen.blit(info, info.get_rect(center=(screen.get_width() // 2, 340)))
        screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, 410)))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()