a. A brief description of your code

The whole program contains two files: Server.py and Client.py.

The Client.py acts as the client side of the chat room, after connected to the server, it is used to get the request typed in by user, send the user request to server and receive feedback and message from server.

For the Server.py, it firstly bind it self to the local IP and a specific port and read all the combination of user name and password. After that it listen to TCP from clients. When a client ask to found a new TCP, a new thread is built to process the operation between server and a specific client.  

When the socket is built, the server will first ask the client to keep entering user name until the user name typed in by client match the user name in database. After that, the server asks client to enter the password, only when the password and user name combination fit the combination in database, the server will allow client to login. If the client cannot enter the right password for 3 consecutive times, the server will block the client with same IP and user name combination out for 60 second.
 
After login, the server can receive and reflect to all client commands:  wholes, whilst <number>, broadcast message <message>, broadcast user <user 1> <user 2> … <user n> message <message>, message <user> <message> and logout. When the client have dong no operation for over half an hour, the server can also force the client off the server.

b. Details on development environment

The program is built based on Python 2.7.10, it has been fully tested on Mac OS. I have gone to the CLIC Lab, but because I do not have the CS ID, I can not log in to the computer in CLIC Lab. But I managed to test the code on my Linux virtual machine with python 2.7.6. There is only one thing different as the result of testing it on virtual machine, my server code used to be able to print the IP my the test machine, but in virtual machine, it can only return the local IP (127.0.0.1) which can only help client in the same machine to connect to server. If this happens, please manually find the server IP by typing “ifconfig” in terminal.

c. Instructions on how to run your code

1. Open the terminal, cd to the folder where Server.py is stored, enter ‘python Server.py <server port number>’, for example ‘python Server.py 4119’

2. Then in the terminal the server will print the IP that the server has binded to. Remember the server IP in mind.

3. Open another terminal on any computer, cd to the folder with Client.py. Run the Client.py by entering the sentence ‘python Client.py  <Server IP address> <server port number>’, for example ‘python Client.py 129.236.236.47 4119’. Then the server can connect to the server.

4. Type in the correct user name on the Client.py, if the user name is wrong, the user need to enter the user name again and again until the user name is in the database.

5. Type in the correct password on the Client.py, if the password is incorrect, the system will ask the client to re-enter the password, if the client can not enter a correct password for more than 3 times, the client (with same user name and IP address) will be blocked out for 60 seconds.

6. When login successful, the client can enter the following request
wholes: Displays name of other connected users

wholast <number> (eg. wholast 1): Display name of those users connected within the last number of minutes

broadcast message <message>(eg. broadcast message Hello): Broadcasts <message> to all connected users

broadcast user <user 1> <user 2> … <user n> message <message>(eg. broadcast user columbia google message Good morning): Broadcasts <message> to the list of users

message <user> <message>(eg. message columbia it is a good university!):Private <message> to a <user>

logout (eg. logout): Log out this user

7. If user do nothing in 30 minutes, the server will automatically logout the client

8. User can log out by either enter logout in the command, or directly press ‘control+C’. When pressing ‘control+C’, if the user already logged in, it is the same as logout, which record the logout time for the user. If the user has not logged in, pressing ‘control+C’ will just close the client program and disconnect with the server.

d. Sample commands to invode your code

1. Client Login Security Sample:

rockydeMacBook-Pro:Computer Network rocky$ python Socket_train.py 192.168.0.2 4119
Socket Created
Socket Connected to server on IP 192.168.0.2 with port 4119
Welcome to server!
Please enter your user name: Columbia
User not valid, please enter the user name again: columbia 
Please enter your password: wrongpassword1
Password not valid, please enter again:wrongpassword2
Password not valid, please enter again:wrongpassword3
You have enter wrong password for over 3 times, please wait for 60 seconds

rockydeMacBook-Pro:Computer Network rocky$ python Socket_train.py 192.168.0.2 4119
Socket Created
Socket Connected to server on IP 192.168.0.2 with port 4119
Welcome to server!
Please enter your user name: columbia
Blocked, please wait for 37.13 seconds

2. Client Operation Demo

Google:
rockydeMacBook-Pro:Computer Network rocky$ python Socket_train.py 192.168.0.2 4119
Socket Created
Socket Connected to server on IP 192.168.0.2 with port 4119
Welcome to server!
Please enter your user name: google
Please enter your password: hasglasses
Please enter your request: logout

Columbia:
rockydeMacBook-Pro:Computer Network rocky$ python Socket_train.py 192.168.0.2 4119
Socket Created
Socket Connected to server on IP 192.168.0.2 with port 4119
Welcome to server!
Please enter your user name: columbia
Please enter your password: 116bway
Please enter your request: 
Hold on, network sends broadcast to all: Hello
Please enter your request:
Hold on, network sends you a private message: it is a good university!
Please enter your request:^Cclient closed

Network:
rockydeMacBook-Pro:Computer Network rocky$ python Socket_train.py 192.168.0.2 4119
Socket Created
Socket Connected to server on IP 192.168.0.2 with port 4119
Welcome to server!
Please enter your user name: network
Please enter your password: seemsez
Please enter your request: whoelse
google columbia
Please enter your request: whoelse
columbia
Please enter your request: wholast
Wrong request
Please enter your request: wholast 1
columbiagoogle
Please enter your request: broadcast message Hello
Hold on, network sends broadcast to all: Hello
Please enter your request: message columbia it is a good university!

Server Demo:
rockydeMacBook-Pro:Computer Network rocky$ python Socket_train_Server.py 4119
Socket created
Socket bind to IP 192.168.0.2 complete
Socket now listening
Connected with 192.168.0.2:56379
Connected with 192.168.0.2:56381
Connected with 192.168.0.2:56383
google has logged out
columbia has logged out

e. Description of any additional functionalities and how they should be executed/tested.
Offline message, when sending a private message of broadcast message to a offline user, the system can notify the user who send the message and store the message in server and send message to user when they login.







