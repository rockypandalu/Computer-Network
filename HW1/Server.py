__author__ = 'rocky'
import socket,sys,time
from thread import *

HOST = ''   # connect to the localhost
PORT = int(sys.argv[1]) # bind to the port required by user
BLOCK_TIME=60 # The time duration in second the server block the login of user with wrong password
NUM_OF_FAIL_CRITERIA=3 # The number of wrong password the sever can allow without block out
TIME_OUT=30 # The number of minute the server allow the client to stay online
dict_database={}# Database for all valid user name and password
dict_block={}# The user who has been blocked and the blocking start time
dict_login={}# User show has logged in and the log in time
dict_logout={}# User who has logged out and the log out time
dict_offline_message={}#The content of offline message and its corresponding user


#Read data from database
def read_txt_data():
    user_pass=open("user_pass.txt")
    login_database=user_pass.readlines()
    for user_combination in login_database:
        user_combination=user_combination.split()
        dict_database[user_combination[0]]=user_combination[1]
#The receive function is only used in login function to in case the error caused by client pressing Ctrl+C when login
def receive(conn,addr):
    message=conn.recv(1024).strip()
    if message=='ctrl_C_logout':
        print addr[0]+addr[1]+' has logout\n'
        return 0
    else:
        return message
#Login and check whether the login information is correct, if the password is always incorrect, the function also block
#the user with same user name and IP out for 60 seconds
def login(conn,addr):
    conn.send('Please enter your user name: ')
    user_name=receive(conn,addr)
    while not user_name in dict_database.keys():
        if not user_name:
            return 0
        else:
            conn.send('User not valid, please enter the user name again: ')
            user_name=conn.recv(1024).strip()
    if user_name in dict_login.keys():
        conn.send('\nSorry, you are already logged in and cannot login again\n')
        conn.close()
        return 0
    ID=user_name+str(addr[0]).strip()
    if ID in dict_block.keys():
        if time.time()>dict_block[ID]+BLOCK_TIME:
            dict_block.pop(ID)
        else:
            remain_time=dict_block[ID]+BLOCK_TIME-time.time()
            conn.send('Blocked, please wait for %.2f seconds' % remain_time)
            print addr[0]+' with user name '+user_name+' has been blocked\n'
            conn.close()
            return 0
    #parameter for login block
    login_flag=1
    conn.send('Please enter your password: ')
    pass_word=receive(conn,addr)
    while not pass_word==dict_database[user_name]:
        if not pass_word:
            return 0
        else:
            login_flag=login_flag+1
            if login_flag>NUM_OF_FAIL_CRITERIA:
                login_flag=1
                dict_block[ID]=time.time()
                conn.send('You have enter wrong password for over 3 times, please wait for 60 seconds\n')
                print addr[0]+' with user name '+user_name+' has been blocked\n'
                conn.close()
                return 0
            else:
                conn.send('Password not valid, please enter again:')
                pass_word=conn.recv(1024).strip()
    dict_login[user_name]=[time.time(),conn]
    receive_offline_message(conn,user_name)
    if user_name in dict_logout:
        dict_logout.pop(user_name)
    return user_name
#Send the offline message to the corresponding user when they login
def receive_offline_message(conn,user_name):
    if user_name in dict_offline_message.keys():
        conn.send('You have offline messages\n')
        while dict_offline_message[user_name]:
            message=dict_offline_message[user_name].pop(0)
            conn.send(message+'\n')
        dict_offline_message.pop(user_name)
# Receive user's requirement and transfer to the corresponding function
def requirement_process(conn,user_name):
    conn.send('Please enter your request: ')
    requirement_message=conn.recv(1024).strip()
    if not user_name in dict_login:
        return 0
    dict_login[user_name][0]=time.time()
    requirement=requirement_message.split()
    if len(requirement)==1:
        if requirement[0]=='whoelse':
            whoelse(conn,user_name)
        elif requirement[0]=='logout' or requirement[0]=='ctrl_C_logout':
            return logout(conn,user_name)
        else:
            conn.send('Wrong request')
    elif len(requirement)==2 and requirement[0]=='wholast' and requirement[1].isdigit():
        wholast(conn,user_name,int(requirement[1]))
    elif requirement[0]=='broadcast' and requirement[1]== 'message':
        broadcast_all(requirement_message,user_name)
    elif requirement[0]=='broadcast' and requirement[1]== 'user':
        broadcast_user(requirement,user_name)
    elif requirement[0]=='message':
        private_message(requirement,user_name)
    else:
        conn.send('ERROR! Wrong request')
    conn.send('\n')
    return 1


#View other users who are currently online
def whoelse(conn,user_name):
    has_login=0
    for other_user_name in dict_login:
        if not other_user_name==user_name:
            conn.send(other_user_name+' ')
            has_login=1
    if not has_login:
         conn.send('No other user online\n')
#View user who are online and who has logged out within 1 hour
def wholast(conn,user_name,LAST_HOUR):
    has_just_logout=0
    conn.send('Users still on line:\n')
    whoelse(conn,user_name)
    current_time=time.time()
    conn.send('\nUsers just logout:\n')
    for logout_user in dict_logout:
        if current_time-float(dict_logout[logout_user])<LAST_HOUR*60:
            conn.send(logout_user+' ')
            has_just_logout=1
    if not has_just_logout:
        conn.send('No one just logged out\n')
#Send message to all users online
def broadcast_all(requirement,user_name):
    message=requirement.lstrip('broadcast ').lstrip('message').lstrip(' ')
    for user_conn in dict_login.keys():
        dict_login[user_conn][1].send('\nHold on, '+user_name+' sends broadcast to all: '+message)
        dict_login[user_conn][1].send('\nPlease enter your request:' )
#Send message the user required by client, it the user is not online, server will store it in dict_offline_message
def broadcast_user(requirement,user_name):
    split_message=requirement[2:]
    message_index=split_message.index('message')
    send_to_user_name=split_message[:message_index]
    message=' '.join(split_message[(message_index+1):])
    for user in send_to_user_name:
        send_message(user,message,user_name,'broadcast')

#Send the message to the user required by client, if the user is offline, server will store it in dict_offline_message
def private_message(requirement,user_name):
        send_to_user=requirement[1]
        message=' '.join(requirement[2:])
        send_message(send_to_user,message,user_name,'private')

# Called by broadcast_user and private_message function, used to send message and store message is user is offline
def send_message(send_to_user,message,user_name,property):
    if send_to_user in dict_login.keys():
        conn=dict_login[send_to_user][1]
        conn.send('\nHold on, '+user_name+' sends you a '+property+' message: '+message)
        conn.send('\nPlease enter your request:' )
    else:
        conn=dict_login[user_name][1]
        conn.send(send_to_user+' is not online, but we will send your message to '+send_to_user+' when he logs in\n')
        if send_to_user in dict_offline_message.keys():
            dict_offline_message[send_to_user].append(user_name+' has sent you a '+property+' message: '+message)
        else:
            dict_offline_message[send_to_user]=[user_name+' has sent you a '+property+' message: '+message]

#Client logout from server
def logout(conn,user_name):
    dict_logout[user_name]=time.time()
    dict_login.pop(user_name)
    print user_name+' has logged out'
    conn.close()
    return 0

#Function for handling connections, which is used to create threads for client
def clientthread(conn,addr):
    #Make client know he already logged in
    conn.send('Welcome to server!\n')
    user_name=login(conn,addr)
    if user_name==0:
        return
    do_flag=1
    while do_flag:
        do_flag=requirement_process(conn,user_name)
# A thread for sever, used to push user out when they have no action for an hour
def serverthread():
    while True:
        time.sleep(2)
        if not len(dict_login)==0:
            dict_login_copy=dict_login.copy()
            for user in dict_login_copy:
                if time.time()-float(dict_login[user][0])>TIME_OUT*60:
                    conn=dict_login[user][1]
                    conn.send('\nYour are logged out for you did not do anything in the last %d mintues'%TIME_OUT)
                    conn.close()
                    dict_logout[user]=time.time()
                    dict_login.pop(user)


# The main function, used to create the server and start new threat whenever a new client linked in to the server
if __name__=="__main__":

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print 'Socket created'

    #Bind socket to local host and port
    try:
        s.bind((HOST, PORT))
    except socket.error , err_info:
        print 'Bind failed. Error Code : ' + str(err_info[0]) + ' Message ' + err_info[1]
        sys.exit()
    bindIP = socket.gethostbyname(socket.gethostname())
    print 'Socket bind to IP '+bindIP+' complete'

    #Start listening on socket (maximum people the sever can serve is 100)
    s.listen(100)
    print 'Socket now listening'
    read_txt_data()
    start_new_thread(serverthread,())
    while True:
        try:
            conn, addr = s.accept()
            print 'Connected with ' + addr[0] + ':' + str(addr[1])
            start_new_thread(clientthread ,(conn,addr))
        except KeyboardInterrupt:
            print 'Server closed'
            sys.exit()
