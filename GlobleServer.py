import socket, threading, time
import random
import shapefile

port = 21567

turn = 0

secret_country = -2

threads = []


# params: socket, address, int index
def handle_client(client, addr, player_index):
    global turn, secret_country, p1_connected, p2_connected, country_guessed
    
    print(f"Player {player_index} Has Joined.")
    if(player_index == 1):
        p1_connected = True;
    else:
        p2_connected = True;

    # while connected
    while(True):
        #receive first byte, also check if he left
        try:
            msg_length = int.from_bytes(client.recv(1), 'little') # convert first received byte to int
        except Exception as e:
            break
        
        msg = client.recv(msg_length).decode() # get message from one client

        print(f"Player {player_index} Has Sent The Message: \'{msg}\'")
        
        incoming_msg = msg.split("~")
        
        if(incoming_msg[0] == 'GUESS'):
            # check if guess is good,
            # if good, will send HIGHLIGHT~054~Israel~FE03A6
            guess_index = get_country_index_by_name(incoming_msg[1])
            
            outgoing_msg = "DEFAULT OUTGOING MSG IF NOT CHANGE"
            
            # not your turn 
            if(turn != player_index):
                outgoing_msg = "WAITFORTURN"
                print(f"Sending {outgoing_msg} to player {player_index}")
                send(client, outgoing_msg)
                
            # invalid guess
            elif(guess_index == -1):
                outgoing_msg = "INVALID"
                print(f"Sending {outgoing_msg} to player {player_index}")
                send(client, outgoing_msg)
                
            # if country is already guessed, return GUESSED
            elif(country_guessed[guess_index]):
                outgoing_msg = "GUESSED"
                print(f"Sending {outgoing_msg} to player {player_index}")
                send(client, outgoing_msg)
            
            
            elif(guess_index == secret_country):
                # guessed secret country
                outgoing_msg = "HIGHLIGHT~"
                country_guessed[guess_index] = True
                outgoing_msg += str(guess_index) + "~"
                outgoing_msg += records[guess_index].NAME + "~"
                outgoing_msg += color_tuple_to_hex(correct_color)
                
                winner, loser = client1, client2
                if(player_index == 2):
                    winner, loser = loser, winner
                    
                print(f"Player {player_index} Won")

                
                print(f"Sending {outgoing_msg} to both players")
                send(client1, outgoing_msg)
                send(client2, outgoing_msg)
                
                send(winner, "YOU WON")
                send(loser, "YOU LOST")
                
                send(client, "RESETTEXT") # reset guesser text
                
            else:
                #guess is valid
                country_guessed[guess_index] = True
                dist = country_distance(secret_country, guess_index)
                color = closeness_color(dist / 160)
                
                outgoing_msg = "HIGHLIGHT~"
                outgoing_msg += str(guess_index) + "~"
                outgoing_msg += records[guess_index].NAME + "~"
                outgoing_msg += color_tuple_to_hex(color)
                
                
                
                print(f"Sending {outgoing_msg} To BOTH players")
                send(client1, outgoing_msg)
                send(client2, outgoing_msg)

                send(client, "RESETTEXT") # reset guesser text

                # flip turn
                turn ^= 3
                send_turns()
                
        elif(incoming_msg[0] == 'RESET'):
            turn = random.randint(1, 2)

            send_turns()

            secret_country = valid_secret_country()

            send(client1, "CLEARMAP")    
            send(client1, "RESETTEXT")
            send(client2, "CLEARMAP")
            send(client2, "RESETTEXT")    
            
        elif(msg == 'LEAVING'):
            if(client1): send(client1, "LEAVE")
            if(client2): send(client2, "LEAVE")
        
        elif(msg == ''):
            break;
        
        else:
            print(f"UNRECOGNISED MSG FROM PLAYER {player_index}: {msg}")
    
    
    print(f"\nPlayer {player_index} Has Left")
    
    if(player_index == 1):
        p1_connected = False;
    else:
        p2_connected = False;
    
    #main()


def send_turns():
    client1_starts, client2_starts = "Your Turn", "Not Your Turn"
    
    if(turn == 2):
        client1_starts, client2_starts = client2_starts, client1_starts
    
    send(client1, client1_starts)
    send(client2, client2_starts)

def country_distance(a_index, b_index):
    shortest_dist = 10e10
    for point_a in shapes[a_index].points[::10]:
        for point_b in shapes[b_index].points[::10]:
            d = dist(point_a, point_b)
            if(d < shortest_dist):
                shortest_dist = d
    return shortest_dist

     
correct_color = (60, 210, 60)
closest_color = (60, 0, 0)
middlest_color = (200, 0, 0)
farthest_color = (255, 200, 150)
#defines the color of the country based on it's distance (this function receives [0.0, 1.0])
# 0.0 = close, dark color
# 1.0 = far away, light color
def closeness_color(t):

    if(t < 0.3):
        c = lerp(middlest_color, closest_color, translate(t, 0, 0.3, 0, 1))
    else:
        c = lerp(farthest_color, middlest_color, translate(t, 0.3, 1, 0, 1))

    return clamp_color(c)  

def get_country_index_by_name(name):
    
    filtered_name = filter_name(name)
    reverse_name = filtered_name[::-1]
    
    for index in range(country_count):
        if(filtered_name in country_names[index] or reverse_name in country_names[index]):
            return index
    
    return -1 # no such country

bad_chars = [',', '.', ' ', '\\', '/', 'the']
def filter_name(name):
    name = name.lower()
    for bad_char in bad_chars:
        name = name.replace(bad_char, '')
    return name

# gets socket and string to send
def send(client, msg):
    message = msg.encode() # string to bytes
    msg_length = len(message) # get length int
    msg_length = msg_length.to_bytes(1, byteorder='little') # int to byte
    full_message = msg_length + message # append msg length to msg 
    client.send(full_message)

# general purpose functions
def mult(tup, scalar):
    if(type(scalar) == tuple):
        return (tup[0] * scalar[0], tup[1] * scalar[1])
    return tuple(i * scalar for i in tup)
def clamp_color(c):
    #return c
    return tuple(min(255, max(0, round(i))) for i in c)
def add(tup, shift):
    return (tup[0] + shift[0], tup[1] + shift[1])
def dist(tup1, tup2):
    return min(
        min(dist1(tup1, tup2), dist2(tup1, tup2)),
        min(dist3(tup1, tup2), dist4(tup1, tup2)))
def dist1(tup1, tup2):
    return (
        (tup1[0]%360 - tup2[0]%360) ** 2 +
        (tup1[1]%180 - tup2[1]%180) ** 2) ** 0.5

def dist2(tup1, tup2):
    return (
        (tup1[0]%360 - tup2[0]%360) ** 2 +
        (tup1[1] - tup2[1]) ** 2) ** 0.5

def dist3(tup1, tup2):
    return (
        (tup1[0] - tup2[0]) ** 2 +
        (tup1[1]%180 - tup2[1]%180) ** 2) ** 0.5

def dist4(tup1, tup2):
    return (
        (tup1[0] - tup2[0]) ** 2 +
        (tup1[1] - tup2[1]) ** 2) ** 0.5

def lerp(c1, c2, t):
    return tuple(c1[i] * t + c2[i] * (1-t) for i in range(3))
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
def color_tuple_to_hex(color):
    return '#%02x%02x%02x' % color

def read_names_from_file():
    names_array = []
    names_file = open("country_names.txt", 'r', encoding='utf-8')
    lines = names_file.readlines()
    for line in lines:
        names_array.append(line.strip().split(", ")) 
    return names_array

def valid_secret_country():
    index = random.randint(0, country_count - 1)
    
    # standard thresh is 13, 17/18 is easy mode
    while(records[index][37] < 14):
        index = random.randint(0, country_count - 1)
    
    return index # get_country_index_by_name("japan")
    




def main():
    global client1, client2, turn, secret_country, p1_connected, p2_connected

    
    p1_connected = False;
    p2_connected = False;
    
    client1 = None;
    client2 = None;
    
    print()
    
    server = socket.socket()
    server.bind(('0.0.0.0', port))
    server.listen()

    print("\nWaiting For Player 1.")
    conn1, addr = server.accept()        

    client1 = conn1

    thread = threading.Thread(target=handle_client, args=(conn1, addr, 1))
    thread.start()

    threads.append(thread)
    
    
    print("\nWaiting For Player 2.")
    
    server.settimeout(1)
    
    while(not p2_connected):
        try:
            conn2, addr = server.accept()
            p2_connected = True
        except socket.timeout:
            pass
        if(p1_connected == False):
            print("Player 1 Disconnected Before Player 2 Joined, Closing Session")
            return; #client 1 disconnected while waiting for client 2, exit everything
        
    client2 = conn2

    thread = threading.Thread(target=handle_client, args=(conn2, addr, 2))
    thread.start()

    threads.append(thread)
    
    # init turn
    turn = random.randint(1, 2)
    
    # init secret country 
    secret_country = valid_secret_country()
    print(f"secret country is {records[secret_country].NAME}")
    
    time.sleep(2)
    
    
    print("SENDING GAME START TO PLAYERS")
    send_turns()
    
    send(client1, "Game Start")
    send(client2, "Game Start")
    

    # join threads? maybe
    



sf = shapefile.Reader("ne_50m_admin_0_countries/ne_50m_admin_0_countries")
shapes = sf.shapes()
records = sf.records()

country_count = len(shapes)
country_names = read_names_from_file()
country_guessed = [False] * country_count
country_colors  = [(255, 255, 255)] * country_count




if __name__== '__main__':
    main()
    