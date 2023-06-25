# Globle
Globle - An online 2 player country guessing game with written in pygame

# How To Run
### Prerequisites
Globle needs a couple of libraries to run:
- pip install pygame
- pip install pyshp

### Server
GlobleServer.py expects 1 command line argument, the port - for the communication with the clients. 
(port is 21567 by default)

### Client
GlobleClient.py expects 2 arguments, the server ip and the previously chosen port. 

# How To Play
At the start of each game the server chooses a random country.
The player's goal is to be the one that guesses what it is.


Each player guesses a country in his turn, typing its name into the text box.

The guessed country is highlighted for both players with a color indicating how close it is to the secret country.
The darker the color the closer you are to the secret country.
