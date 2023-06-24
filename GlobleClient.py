#newer comment 


import sys

import pygame
import shapefile

import socket, threading






# general purpose functions
def mult(tup, scalar):
    if type(scalar) == tuple:
        return (tup[0] * scalar[0], tup[1] * scalar[1])
    return tuple(i * scalar for i in tup)


def add(tup, shift):
    return (tup[0] + shift[0], tup[1] + shift[1])


def sub(tup1, tup2):
    return (tup1[0] - tup2[0], tup1[1] - tup2[1])


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


# map points from the sphere to the screen
def sphere_to_screen(point):
    x = translate(point[0], -180, 180, 0, width)
    y = translate(point[1], 90, -90, 0, height)
    return (x, y)


def clamp_bg_pos():
    global bg_width
    # width
    if bg_width <= bg_default_width:
        bg_width = bg_default_width
    # left bound
    if bg_pos[0] > 0:
        bg_pos[0] = 0
    if bg_pos[1] > 0:
        bg_pos[1] = 0
    # right bound
    if bg_pos[0] + bg_width < width:
        bg_pos[0] = width - bg_width
    if bg_pos[1] + bg_width / 2 < height:
        bg_pos[1] = height - bg_width / 2


def enlarge_bg():
    global bg_width, bg_img, resize_factor
    center_before_scaling = (bg_pos[0] + bg_width / 2, bg_pos[1] + (bg_width / 2) / 2)
    bg_width *= bg_resize_speed
    center_after_scaling = (bg_pos[0] + bg_width / 2, bg_pos[1] + (bg_width / 2) / 2)

    dist = sub(center_after_scaling, center_before_scaling)

    # update bg_pos to be in center
    bg_pos[0] -= dist[0]
    bg_pos[1] -= dist[1]

    clamp_bg_pos()

    # apply scale
    bg_img = pygame.transform.scale(earth_img, (int(bg_width), int(bg_width / 2)))

    resize_factor = bg_width / bg_default_width


def shrink_bg():
    global bg_width, bg_img, resize_factor
    center_before_scaling = (bg_pos[0] + bg_width / 2, bg_pos[1] + (bg_width / 2) / 2)
    bg_width /= bg_resize_speed
    center_after_scaling = (bg_pos[0] + bg_width / 2, bg_pos[1] + (bg_width / 2) / 2)

    dist = sub(center_after_scaling, center_before_scaling)

    # update bg_pos to be in center
    bg_pos[0] -= dist[0]
    bg_pos[1] -= dist[1]

    clamp_bg_pos()

    # apply scale
    bg_img = pygame.transform.scale(earth_img, (int(bg_width), int(bg_width / 2)))

    resize_factor = bg_width / bg_default_width


def draw_bg():
    screen.blit(bg_img, (bg_pos[0], bg_pos[1]))


def draw_countries():
    for i in range(country_count):
        if country_visible[i]:
            draw_shape(screen, country_colors[i], shapes[i])

def draw_info_line(line, line_pos):
    shadow_surf = info_font.render(line, True, (0, 0, 0))
    text_surf = info_font.render(line, True, (255, 255, 255))
    
    
    #draw shadow, (its just the info text multiple times in black in various offsets)
    outline_offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for offset in outline_offsets:
        screen.blit(shadow_surf, (line_pos[0] + offset[0], line_pos[1] + offset[1]))
        
    screen.blit(text_surf, line_pos)

def draw_info():
    pos = (30, 550)
    line_distance = 30
    
    for line in info_lines:
        draw_info_line(line, pos)
        pos = (pos[0], pos[1] + line_distance)
    

def draw_earth():
    draw_bg()
    draw_countries()
    draw_info()


def is_in_screen(point):
    return point[0] >= 0 and point[0] < width and point[1] >= 0 and point[1] < height


def draw_shape(screen, color, shape):
    part_index = 0
    current_part = []
    part_has_point_in_screen = False
    for i, point in enumerate(shape.points):
        # maybe reset part
        if part_index < len(shape.parts) and i >= shape.parts[part_index]:
            if (
                len(current_part) > 2 and part_has_point_in_screen
            ):  # if there's shape to draw in it's in screen
                pygame.draw.polygon(screen, color, current_part)

            part_index += 1
            current_part = []  # reset points in current part
            part_has_point_in_screen = False

        # only use a fourth of the points
        # if(i % 4 > 0):
        #    continue

        # transform points from world coords to aptly positioned screen coords
        point = sphere_to_screen(point)  # world to screen
        point = mult(
            point, (1.125 * resize_factor, resize_factor)
        )  # according to resize factor, and a little manual strech
        point = add(point, bg_pos)
        current_part.append(point)

        if not part_has_point_in_screen:  # if we still don't know the if part's visible
            if is_in_screen(point):  # check if it is visible
                part_has_point_in_screen = True

    if len(current_part) > 2 and part_has_point_in_screen:  # if there's shape to draw
        pygame.draw.polygon(screen, color, current_part)


def draw_input_box():
    textbox_center = (width / 2, 15 * height / 16)
    textbox_height = 60

    # rectangle
    text_rect = pygame.Rect(
        textbox_center[0] - textbox_width / 2,
        textbox_center[1] - textbox_height / 2,
        textbox_width,
        textbox_height,
    )
    backcolor = gray
    if input_active:
        backcolor = white
    pygame.draw.rect(screen, backcolor, text_rect)  # rect bg
    pygame.draw.rect(screen, 0, text_rect, width=1)  # rect outline

    # text itself
    text_surf = textbox_font.render(text, True, (10, 10, 10))
    screen.blit(text_surf, text_surf.get_rect(center=textbox_center))


def update_textbox_width():
    global textbox_width

    # if text fits within default
    if len(text) < max_text_len:
        textbox_width = textbox_default_width
        return

    add_amount = (len(text) - max_text_len) * add_amount_per_char
    textbox_width = textbox_default_width + add_amount
    
    if(textbox_width > 1000):
        textbox_width = 1000;


def reset_textbox():
    global text
    text = ""
    update_textbox_width()
    draw_earth()


def highlight_country(country_index, color):
    country_visible[country_index] = True

    country_colors[country_index] = color


def move_earth():
    global bg_vel, bg_pos

    mouse_pressed = pygame.mouse.get_pressed()

    # move earth
    vel = pygame.mouse.get_rel()
    if mouse_pressed[0]:
        bg_vel[0] = vel[0]
        bg_vel[1] = vel[1]

    # friction
    bg_vel[0] *= 0.5
    bg_vel[1] *= 0.5

    # round
    if abs(bg_vel[0]) < 0.001:
        bg_vel[0] = 0
    if abs(bg_vel[1]) < 0.001:
        bg_vel[1] = 0

    # if earth wants to move
    if bg_vel[0] != 0 or bg_vel[1] != 0:
        # apply velocity
        bg_pos[0] += bg_vel[0] * bg_move_speed * dt
        bg_pos[1] += bg_vel[1] * bg_move_speed * dt

        # clamp earth coords to in screen
        clamp_bg_pos()

        # redraw earth
        draw_earth()


# pygame stuff
pygame.init()
fps = 60
fpsClock = pygame.time.Clock()
dt = 0.1
log_fps = False
width, height = 1280, 720
screen = pygame.display.set_mode((width, height))
white = (255, 255, 255)
gray = (200, 200, 200)

# bg
bg_pos = [-35, 0]
bg_default_width = height * 2
bg_width = bg_default_width
bg_resize_speed = 1.2
bg_scaler = 1
bg_move_speed = 60
bg_vel = [0, 0]
earth_img = pygame.image.load("earth.png")
bg_img = pygame.transform.scale(earth_img, (bg_width, bg_width / 2))

# text box
add_amount_per_char = 24
textbox_default_width = 300
textbox_width = textbox_default_width
max_text_len = 10
hebrew_mode = False

# shapes
# sf = shapefile.Reader("ne_50m_admin_0_countries/ne_50m_admin_0_countries")
sf = shapefile.Reader("ne_50m_admin_0_countries/ne_50m_admin_0_countries")
shapes = sf.shapes()
# records = sf.records()

country_count = len(shapes)
# country_names = read_names_from_file()
country_visible = [False] * country_count
# country_available = [True] * country_count
country_colors = [white] * country_count
resize_factor = bg_width / bg_default_width

# x [-180, 180]
# y [-90, 83.6]
# reset_game()

# text
textbox_font = pygame.font.Font("Fonts/Assistant-SemiBold_0.ttf", 40)
info_font = pygame.font.Font("Fonts/CascadiaMono.ttf", 16)
text = ""
input_active = False
info_lines = [];
info_line_index = 0

def add_info_line(line):
    global info_line_index
    
    info_lines.append(str(info_line_index) + " > " + line)
    info_line_index+=1;
    
    if(len(info_lines) > 5):
        info_lines.pop(0);

def send(msg):
    global server
    message = msg.encode()
    msg_length = len(message)  # should be less than 256 if got up to here, fits in a single byte
    msg_length = msg_length.to_bytes(1, byteorder="little")  # convert to byte
    full_message = msg_length + message
    server.send(full_message)


def connect_to_server():
    global server, connected
    server = socket.socket()

    server_IP = "127.0.0.1"
    port = 21567
    
    if(len(sys.argv) == 3):
        server_IP = sys.argv[1];
        port = int(sys.argv[2]);
    
    print(f"\nConnecting To Server. <{server_IP}>")
    add_info_line(f"Connecting To Server <{server_IP}:{port}> ")
    
    while(not connected and game_alive):
        try:
            server.connect((server_IP, port))
            connected = True;
        except Exception as e:
            #print("Could Not Connect " + str(random.randint(0, 1000)));
            pass
        
    add_info_line("Connected Successfuly")
    
    if(game_alive):
        thread = threading.Thread(target=listen_to_server)
        thread.start()
    
    

def recv_from_server():
    global server
    
    try:
        msg_length = int.from_bytes(server.recv(1), "little")  # single msg length byte
        msg = server.recv(msg_length).decode()
    except Exception as e:
        return 'LEAVE' # if server malfunctions, we pretend it told us to leave
    
    return msg


# get messages from the server and act accordingly
def listen_to_server():
    global server, connected, input_active, game_alive

    while connected:
        # wait for message from server
        response = recv_from_server()
        response_parts = response.split("~")

        if response_parts[0] == "Game Start":
            print("GAME START!!!")
            # add_info_line("Game Start! Secret Country Chosen")
        elif response_parts[0] == "Your Turn":
            input_active = True
            print("Your Turn.")
            if(info_line_index == 2):
                add_info_line("Guess The Secret Country.")
        elif response_parts[0] == "Not Your Turn":
            input_active = False
            print("Not Your Turn.")
            if(info_line_index == 2):
                add_info_line("Guess The Secret Country When It's Your Turn.")
            #add_info_line("Other Player's Turn")

        elif response_parts[0] == "YOU WON":
            print("YOU WIN!! LET'S GOOO")
            add_info_line("Correct Guess! You Win")
        elif response_parts[0] == "YOU LOST":
            print("YOU LOSE!! HA AHAA")
            add_info_line("Other Player Guessed. You Lose :(")

        elif response_parts[0] == "WAITFORTURN":
            # guess was found in list
            print("bruh, it ain't your turn")
            add_info_line("Wait For Your Turn")

        elif response_parts[0] == "INVALID":
            # bad name
            print("The requested country was not found in the database")
            add_info_line("Country Name Not Recognised")

        elif response_parts[0] == "GUESSED":
            # country already guessed
            print("Country Was Already Guessed")
            add_info_line("Country Already Guessed")

        elif response_parts[0] == "HIGHLIGHT":
            # highlight the country
            index = int(response_parts[1])
            name = response_parts[2]
            color = pygame.Color(response_parts[3])
            # highlight country
            print(f"highlighting the guessed country which is {index}")
            if(response_parts[3] == '#3cd23c'):
                add_info_line(f"Secret Country: {name}")
            else:
                add_info_line(f"Country Guessed: {name}")
            highlight_country(index, color)
            draw_earth()

        elif response_parts[0] == "RESETTEXT":
            reset_textbox()

        elif response_parts[0] == "CLEARMAP":
            for i in range(country_count):
                country_visible[i] = False
            draw_earth()
            add_info_line("Game Reset, New Secret Country")

        elif response_parts[0] == "LEAVE" or response_parts[0] == '':
            server.close()
            game_alive = False
            return
        
        else:
            print("UNRECOGNISED RESPONSE FROM SERVER: " + response)


def main():
    global dt, input_active, hebrew_mode, text, connected, thread, game_alive

    draw_earth()
    pygame.display.flip()

    connected = False
    
    
    
    connection_thread =threading.Thread(target=connect_to_server)
    connection_thread.start();
    
    

    game_alive = True
    print(country_count)
    
    # Game loop.
    while game_alive:
        # Events
        for event in pygame.event.get():
            # Zoom Scroll
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    enlarge_bg()
                else:
                    shrink_bg()

            elif event.type == pygame.QUIT:
                if(connected):
                    send("LEAVING")
                else:
                    game_alive = False;
                    pygame.quit()
                    sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                # text box
                if event.key == pygame.K_KP_ENTER or event.key == pygame.K_RETURN:
                    if text == "reset":
                        if(connected): send("RESET")
                    elif not input_active:
                        add_info_line("Not Your Turn")
                    else:
                        send("GUESS~" + text)

                # backspace
                elif event.key == pygame.K_BACKSPACE:
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        # with ctrl, delete whole word
                        if hebrew_mode:
                            text = " ".join(text.split(" ")[1:])
                        else:
                            text = " ".join(text.split(" ")[:-1])
                    else:
                        #delete one character
                        if hebrew_mode:
                            text = text[1:]
                        else:
                            text = text[:-1]

                    draw_earth()  # draw earth behind the resized text box
                    update_textbox_width()

                # debug
                elif event.key == pygame.K_DELETE:
                    reset_textbox()
                    input_active = not input_active
                    print(input_active)
                    
                elif event.key == pygame.K_ESCAPE:
                    send("LEAVING")

                # character typed into textbox
                else:
                    # text too long, don't add any more characters
                    if(len(text) >= 48):
                        continue;
                    
                    # if change mode, reset text
                    if (
                        not hebrew_mode
                        and event.unicode >= "א"
                        and event.unicode <= "ת"
                    ):
                        hebrew_mode = True
                        text = ""
                    elif hebrew_mode and event.unicode >= "A" and event.unicode <= "z":
                        hebrew_mode = False
                        text = ""

                    if hebrew_mode:
                        text = event.unicode + text
                    else:
                        text = text + event.unicode

                    update_textbox_width()



        move_earth()

        draw_earth()
        
        # Text
        draw_input_box()

        if log_fps:
            print(fpsClock.get_fps())

        # Draw to screen
        pygame.display.flip()
        dt = fpsClock.tick(fps) / 1000


if __name__ == "__main__":
    main()
