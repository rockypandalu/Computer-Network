__author__ = 'rocky'
import socket,select,sys

if __name__=="__main__":
    #start a TCP
    try:
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print 'Failed to create socket. Error code: '
        sys.exit()
    print 'Socket Created'
    #read the host and port name
    host = sys.argv[1]
    port = int(sys.argv[2])

    #Connect to server
    s.connect((host , port))
    print 'Socket Connected to server on IP ' + host + ' with port ' + str(port)
    #Read, write and send message with server. When user press control+C to quit, the client will send a logout message
    #and exit the system.
    while True:
        try:
            socket_list=[sys.stdin,s]
            read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
        except KeyboardInterrupt:
            s.send('ctrl_C_logout')
            print 'client closed'
            sys.exit()
        for selection in read_sockets:
            if selection == socket_list[0]:
                s.send(sys.stdin.readline())
            else:
                get_message=s.recv(1024)
                if get_message:
                    sys.stdout.write(get_message)
                    sys.stdout.flush()
                else:
                    sys.exit()