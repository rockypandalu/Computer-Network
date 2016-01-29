__author__ = 'rocky'
import sys,socket,threading,select,json
from time import gmtime, strftime
import time
TIMEOUT=100
current_neighbor={}
dictDistTable={}
dictRestoreTable={}
dictOtherNode={}
dictCloseTimeOut={}
#deal with input
def Input():
    localIP=socket.gethostbyname(socket.gethostname())
    thisClient=(localIP, int(sys.argv[1]))
    timeOut=float(sys.argv[2])
    i=5
    if len(sys.argv)%3:
        print 'Input format Error!\n Please use the format \n python HW3.py <localport> <timeout> [ipaddress1 port1 weight1 ...]'
        sys.exit()
    while i<len(sys.argv):
        nodeID=sys.argv[i-2].strip()+':'+sys.argv[i-1].strip()
        dictDistTable[nodeID]=[float(sys.argv[i].strip()), nodeID]
        current_neighbor[nodeID]=float(sys.argv[i].strip())
        #linkedClient.append(InputFile(sys.argv[i-2] ,sys.argv[i-1], sys.argv[i]))
        i+=3
    return [thisClient,timeOut]

#Initial two sockets, one for sending and one for listening
def initSocket():
    try:
         socket_UDP_rcv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        print 'Failed to create UDP socket.'
        sys.exit()

    try:
        socket_UDP_rcv.bind((thisClient[0], thisClient[1]))
    except socket.error , msg:
        print 'Fail to bind. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
    print 'Receiver bind successful'

    try:
         socket_UDP_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        print 'Failed to create UDP socket.'
        sys.exit()
    print 'Send socket build success'
    return [socket_UDP_rcv, socket_UDP_send]


def splitIPPort(a):
    IP,port = a.split(':')
    return [IP,port]

#send current route distance vector to other nodes with poison reverser implemented
def sendRouteDistance(socket_UDP,thisClient):
    global TimeOut
    TimeOut.cancel()
    distanceVector={}
    thisClientID=thisClient[0]+':'+str(thisClient[1])
    distanceVector['sender']=thisClientID
    distanceVector[thisClientID]=0
    for sendObject in dictDistTable:
        distanceVector[sendObject] = dictDistTable[sendObject][0]
    for sendObject in current_neighbor:
        sendDistanceVector=distanceVector.copy()
        #poison reverse
        for object in dictDistTable:
            if dictDistTable[object][1]==sendObject and object!=sendObject:
                sendDistanceVector[object]=float('inf')
        sendIP, sendPort = splitIPPort(sendObject)
        try:
            socket_UDP.sendto(json.dumps(sendDistanceVector),(sendIP,int(sendPort)))
        except:
            print 'Connection refused to '+sendIP+':'+sendPort

    TimeOut = threading.Timer(TIMEOUT, sendRouteDistance, (socket_UDP,thisClient))
    TimeOut.daemon = True
    TimeOut.start()

#show current root distance
def showRT():
    time=strftime("%Y-%m-%d %H:%M:%S", gmtime())
    for destination in dictDistTable:
        if dictDistTable[destination][0]!=float('inf'):
            print time+' Distance vector list is:'
            print 'Destination = '+destination+', Cost = '+str(dictDistTable[destination][0])+', Link = ('+ dictDistTable[destination][1]+')'
    print

#deal with input assignments
def input_process(input_arg,socket_UDP,thisClient):
    allCmd=['linkdown', 'linkup','showrt','close','build']
    input_arg=input_arg.strip().split()
    if len(input_arg)==0:
        print 'Input error, please input your request.'
        return 0
    cmd=input_arg[0].lower()
    if cmd not in allCmd:
        print 'Input error, please input a valid request.'
        return 0
    if cmd == allCmd[0]:
        if len(input_arg)!=3:
            print 'Input error, not enough input for %s command' % cmd
            return 0
        IP=input_arg[1]
        try:
            port=int(input_arg[2])
        except:
            print 'Input error, port should be an integer'
            return 0
        if (str(IP)+':'+str(port)) not in current_neighbor:
            print 'Input error, the port you want to link down in already not link to the node'
            return 0
        linkdown(IP,port,socket_UDP,thisClient)
    elif cmd == allCmd[1]:
        if len(input_arg)==3:
            IP=input_arg[1]
            try:
                port=int(input_arg[2])
            except:
                print 'Input error, port should be an integer'
                return 0
            if (str(IP)+':'+str(port)) not in dictRestoreTable:
                print 'Input error, the port you want to link up has never linked to this node'
                return 0
            linkup(IP,port,socket_UDP,thisClient)
    elif cmd==allCmd[4]:
        if len(input_arg)==4:
            IP=input_arg[1]
            try:
                port=int(input_arg[2])
            except:
                print 'Input error, port should be an integer'
                return 0
            try:
                newDist=float(input_arg[3])
            except:
                print 'Input error, the new distance should be a number'
                return 0
            if ((str(IP)+':'+str(port)) in dictRestoreTable) or ((str(IP)+':'+str(port)) in current_neighbor):
                print 'Input error, can not build a link to a exist or used to exist neighbor'
                return 0
            buildup(IP,port,socket_UDP,thisClient,newDist)
        else:
            print 'Input error, not enough input for %s command' % cmd
            return 0
    elif cmd in ['showrt','close']:
        if len(input_arg)!=1:
            print 'Input error, %s should only have one argument' % cmd
        if cmd=='showrt':
            showRT()
        else:
            close()

#time out function, mark the neighbor who has not receive information for 3 timeouts as dead
def nodeClose(ip, port,socket_UDP,thisClient):
    linkDownNode=ip+':'+str(port)
    print 'Neighbor %s seems has dead T_T'%linkDownNode
    if linkDownNode in current_neighbor:
        dictRestoreTable[linkDownNode]=current_neighbor[linkDownNode]
        del current_neighbor[linkDownNode]
        try:
            del dictOtherNode[linkDownNode]
        except:
            pass
        for node in dictDistTable:
            if dictDistTable[node][1]==linkDownNode:
                dictDistTable[node]=[float('inf'),'']
            if node in current_neighbor:
                dictDistTable[node]=[current_neighbor[node],node]
        sendRouteDistance(socket_UDP,thisClient)

#linkdown with a node
def linkdown(ip, port,socket_UDP,thisClient):
    thisClientID=thisClient[0]+':'+str(thisClient[1])
    message={'sender':thisClientID}
    linkDownNode=ip+':'+str(port)
    dictCloseTimeOut[linkDownNode].cancel()
    if linkDownNode in current_neighbor:
        message[ip+':'+str(port)]=float('inf')
        dictRestoreTable[linkDownNode]=current_neighbor[linkDownNode]
        del current_neighbor[linkDownNode]
        try:
            del dictOtherNode[linkDownNode]
        except:
            pass
        for node in dictDistTable:
            if dictDistTable[node][1]==linkDownNode:
                dictDistTable[node]=[float('inf'),'']
                for senders in dictOtherNode:
                    if dictDistTable[node][0]>dictOtherNode[senders][node]+current_neighbor[senders]:
                         dictDistTable[node]=[dictOtherNode[senders][node]+current_neighbor[senders],senders]
        socket_UDP.sendto(json.dumps(message),(ip,port))
        sendRouteDistance(socket_UDP,thisClient)
    else:
        print 'Nothing to Linkdown, please build the connection to '+linkDownNode+' first.'

#Link up with a used to linked neighbor
def linkup(ip,port,socket_UDP,thisClient):
    linkUpNode=ip+':'+str(port)
    dictCloseTimeOut[linkUpNode]=threading.Timer(3*TIMEOUT,nodeClose,(ip,int(port),socket_UDP_send,thisClient))
    dictCloseTimeOut[linkUpNode].daemon = True
    dictCloseTimeOut[linkUpNode].start()
    current_neighbor[linkUpNode]=dictRestoreTable[linkUpNode]
    if dictRestoreTable[linkUpNode]<dictDistTable[linkUpNode][0]:
        dictDistTable[linkUpNode]=[dictRestoreTable[linkUpNode],linkUpNode]
    sendRouteDistance(socket_UDP,thisClient)

#Build a neighbor with a node who has not linked with current node before
def buildup(ip,port,socket_UDP,thisClient,newDist):
    linkUpNode=ip+':'+str(port)
    current_neighbor[linkUpNode]=newDist
    split_sender=linkUpNode.split(':')
    dictCloseTimeOut[linkUpNode]=threading.Timer(3*TIMEOUT,nodeClose,(split_sender[0],int(split_sender[1]),socket_UDP_send,thisClient))
    dictCloseTimeOut[linkUpNode].daemon = True
    dictCloseTimeOut[linkUpNode].start()
    if linkUpNode in dictDistTable:
        if newDist<dictDistTable[linkUpNode][0]:
            dictDistTable[linkUpNode]=[newDist,linkUpNode]
    else:
        dictDistTable[linkUpNode]=[newDist,linkUpNode]
    sendRouteDistance(socket_UDP,thisClient)

#close the node
def close():
    sys.exit()

#Transfer the received json to dictionary
def reloadDistanceVector(receivedDistanceVector):
    receivedDistanceVector=json.loads(receivedDistanceVector)
    sender=receivedDistanceVector['sender']
    del receivedDistanceVector['sender']
    return [sender, receivedDistanceVector]

#Update all information by the received message
def update(sender,receivedDistanceVector,thisClient,socket_UDP_send):

    thisClientID=thisClient[0]+':'+str(thisClient[1])
    unUpdatedDistanceVector=dictDistTable.copy()
    split_sender=sender.split(':')
    flag=0
#######################deal with new link################
    if sender not in current_neighbor:
        current_neighbor[sender]=receivedDistanceVector[thisClientID]
        dictCloseTimeOut[sender]=threading.Timer(3*TIMEOUT,nodeClose,(split_sender[0],int(split_sender[1]),socket_UDP_send,thisClient))
        dictCloseTimeOut[sender].daemon = True
        dictCloseTimeOut[sender].start()
        print 'A new neighbor %s has join the network'%sender
    else:
        dictCloseTimeOut[sender].cancel()
        dictCloseTimeOut[sender]=threading.Timer(3*TIMEOUT,nodeClose,(split_sender[0],int(split_sender[1]),socket_UDP_send,thisClient))
        dictCloseTimeOut[sender].daemon = True
        dictCloseTimeOut[sender].start()
    if sender in dictRestoreTable:
        del dictRestoreTable[sender]
    if sender not in dictDistTable:
        dictDistTable[sender]=[receivedDistanceVector[thisClientID],sender]
    dictOtherNode[sender]=receivedDistanceVector
#######################deal with link down################
    if len(receivedDistanceVector)==1:
        if receivedDistanceVector.values()==[float('inf')]:
            print 'Neighbor %s has linked down.'%sender
            dictRestoreTable[sender]=current_neighbor[sender]
            dictDistTable[sender]=[float('inf'),'']
            dictCloseTimeOut[sender].cancel()
            del dictOtherNode[sender]
            del current_neighbor[sender]
            for node in dictDistTable:
                if dictDistTable[node][1]==sender:
                    dictDistTable[node]=[float('inf'),'']
                    for senders in dictOtherNode:
                        if dictDistTable[node][0]>dictOtherNode[senders][node]+current_neighbor[senders]:
                            dictDistTable[node]=[dictOtherNode[senders][node]+current_neighbor[senders],senders]
            flag=1




#######################deal with update################
    if not flag:
        for node in receivedDistanceVector:
            if node!=thisClientID:
                if node not in dictDistTable:
                    dictDistTable[node]=[receivedDistanceVector[node]+receivedDistanceVector[thisClientID], sender]
                elif dictDistTable[node][0]>receivedDistanceVector[node]+receivedDistanceVector[thisClientID] or dictDistTable[node][1]==sender:
                    dictDistTable[node]=[receivedDistanceVector[node]+receivedDistanceVector[thisClientID],sender]
            if node in current_neighbor:
                if current_neighbor[node]<dictDistTable[node][0]:
                    dictDistTable[node]=[current_neighbor[node],node]
    if unUpdatedDistanceVector!=dictDistTable:
        sendRouteDistance(socket_UDP_send,thisClient)
        currenttime=strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print 'Updated at '+ currenttime+' caused by information from neighbor %s.'%sender

def initDeadTimer(socket_UDP_send,thisClient):
    for nodeID in dictDistTable:
        ip,port=nodeID.split(':')
        dictCloseTimeOut[nodeID]=threading.Timer(4*TIMEOUT,nodeClose,(ip,int(port),socket_UDP_send,thisClient))
        dictCloseTimeOut[nodeID].daemon = True
        dictCloseTimeOut[nodeID].start()

if __name__ == '__main__':
    thisClient, TIMEOUT=Input()
     #Initialize UDP socket
    socket_UDP_rcv, socket_UDP_send=initSocket()
    TimeOut = threading.Timer(TIMEOUT, sendRouteDistance, (socket_UDP_send,thisClient))
    TimeOut.daemon = True
    TimeOut.start()
    sendRouteDistance(socket_UDP_send,thisClient)
    initDeadTimer(socket_UDP_send,thisClient)
    showRT()
    while True:
        try:
            socket_list=[sys.stdin,socket_UDP_rcv]
            read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
        except KeyboardInterrupt:
            sys.exit()
        for selection in read_sockets:
            if selection == socket_list[0]:
                input_process(sys.stdin.readline(),socket_UDP_send,thisClient)
                time.sleep(1)
            else:
                receivedDistanceVector=socket_UDP_rcv.recv(2048)

                sender, receivedDistanceVector=reloadDistanceVector(receivedDistanceVector)
                update(sender,receivedDistanceVector,thisClient,socket_UDP_send)
