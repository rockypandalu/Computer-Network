__author__ = 'rocky'
import sys, socket, struct, time, datetime
#Global variables
Max_Seg_Size=576
exp_seq=0       #Expect received data
buffer_data={}  #a dict record the data in buffer

#Stroe received data and deal with making ACK
class ReceiveFile:
#Store input arguments
    def __init__(self, filename, listening_port,sender_IP,sender_port,log_filename):
        self.write_to_filename=filename
        self.listening_port=int(listening_port)
        self.sender_IP=sender_IP
        self.sender_port=int(sender_port)
        self.log_filename=log_filename

#pack data in to ACK chunk
    def make_ACK(self, FIN,received_data):
        ACK = struct.pack('HHIIIHH',self.listening_port, self.sender_port, received_data.sequence_num, exp_seq, FIN,received_data.checksum,received_data.Urge_data_pointer)
        return ACK

#send the ACK packet by TCP
    def sendACK(self,FIN,socket_TCP,received_data):
        ACK=self.make_ACK(FIN,received_data)
        self.log_send_ACK(received_data,FIN)
        socket_TCP.send(ACK)

#Write the ACK chunk data into a log file
    def log_send_ACK(self,received_data,FIN):
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        log='ACK      '+timestamp+', source: '+str(self.listening_port)+', destination '+str(self.sender_port)+', sequence number: '+str(received_data.sequence_num)+', expected ACK number: '+str(received_data.ACK_num)+', FIN: '+str(FIN)+'\n'
        if self.log_filename=='stdout':
            print log
        else:
            write_file(self.log_filename,log)

#Store the input arguments
class UnPackedFile:
    def __init__(self, source,destination,sequence_num,ACK_num,FIN,checksum, Urge_data_pointer,chunk_data):
        self.source=source
        self.destination=destination
        self.sequence_num=sequence_num
        self.ACK_num=ACK_num
        self.FIN=FIN
        self.checksum=checksum
        self.Urge_data_pointer=Urge_data_pointer
        self.chunk_data=chunk_data


#Deal with input
def system_input():
    if len(sys.argv)==6:
       receiver=ReceiveFile(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
    else:
        print 'Input format Error!\n Please use the format'
        print 'python receiver.py <filename> <listening_port> <sender_IP> <sender_port> <log_filename>'
        sys.exit()
    return receiver

#Used for checksum calculation
def wraparound_add(a,b):

        c=a+b
        if c<=0xffff:
            return c
        else:
            return c-0xffff

#Calculate checksum and test whether the received data is correct
def checksum_justify(chunk, checksum_received):
    checksum=0
    for i in range(0,len(chunk),2):
            if i==len(chunk)-1:
                checksum=wraparound_add(checksum,ord(chunk[i]))
            else:
                bit_16=ord(chunk[i])+(ord(chunk[i+1]) << 8)
                checksum=wraparound_add(bit_16,checksum)
    if checksum+checksum_received==0xffff:
        return True
    else:
        return False

#Deal with each received chunk
def received_chunk_process(receiver,received_data,socket_TCP):
    global exp_seq,buffer_data
    data_to_checksum=str(received_data.source)+str(received_data.destination)+str(received_data.sequence_num)+str(received_data.ACK_num)+str(received_data.FIN)+str(received_data.Urge_data_pointer)+received_data.chunk_data
    if received_data.FIN==0:
        if checksum_justify(data_to_checksum,received_data.checksum):
            if received_data.sequence_num==exp_seq:
                #Data in this level is the normal, in sequence and correct data, which is valuable
                #Extra function: buffer on receiver side
                #Check whether there is any data in buffer
                if len(buffer_data)==0:
                    #if there is no data in buffer, directly write the received file and change the expected number to the next one
                    write_file(receiver.write_to_filename,received_data.chunk_data)
                    exp_seq=exp_seq+Max_Seg_Size
                else:
                    #If there is any data in buffer, consider the relationship between the received data and data in buffer
                    for pointer_buffer_data in sorted(buffer_data):
                        if pointer_buffer_data>exp_seq+Max_Seg_Size:
                            #The received data can not fill the gap between the expected data and buffer data
                            break
                        else:
                            #The received data can fill some gap between the expected data and buffer data
                            exp_seq=pointer_buffer_data
                    exp_seq=exp_seq+Max_Seg_Size
                    buffer_data_copy=buffer_data.copy()
                    has_write_received_data=0
                    #print the data in buffer which has small value than current expected value
                    for del_item in sorted(buffer_data_copy):
                        if received_data.sequence_num<del_item and has_write_received_data==0:
                            write_file(receiver.write_to_filename,received_data.chunk_data)
                            has_write_received_data=1
                        if exp_seq>del_item:
                            #in_sequence_data.append(buffer_data[del_item])
                            write_file(receiver.write_to_filename,buffer_data[del_item])
                            del buffer_data[del_item]
                receiver.sendACK(0,socket_TCP,received_data)
            #Received data out of order but no corrupt, they should be stored in buffer
            elif received_data.sequence_num>exp_seq:
                receiver.sendACK(0,socket_TCP,received_data)
                buffer_data[received_data.sequence_num]=received_data.chunk_data
                #buffer_data=sorted(buffer_data)
            else:
                receiver.sendACK(0,socket_TCP,received_data)
            #RECEIVED data with corruption
        else:
            receiver.sendACK(0,socket_TCP,received_data)
    #deal with last chunk
    else:
        if received_data.sequence_num>exp_seq:
            receiver.sendACK(0,socket_TCP,received_data)
        else:
            if not buffer_data:
                for data in buffer_data:
                    write_file(receiver.write_to_filename,data)
            write_file(receiver.write_to_filename,received_data.chunk_data)
            receiver.sendACK(1,socket_TCP,received_data)
            return 0
    return 1
#write file
def write_file(filename, received_data):
    File = open(filename,'a')
    File.write(received_data)
    File.close()
#write the log file
def write_log(receiver, received_data):
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    log='Received '+timestamp+', source: '+str(received_data.source)+', destination: '+str(received_data.destination)+', sequence number: '+str(received_data.sequence_num)+', ACK number: '+str(received_data.ACK_num)+', FIN: '+str(received_data.FIN)+', checksum: '+str(received_data.checksum)+'\n'
    if receiver.log_filename=='stdout':
        print log
    else:
        write_file(receiver.log_filename,log)



#Main function
if __name__ == '__main__':
    receiver=system_input()
    #Initial documents and clear existed documents
    File=open(receiver.write_to_filename,'wt')
    File.close()
    File=open(receiver.log_filename,'wt')
    File.close()
    #build UDP socket
    socket_UDP=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    HOST_UDP=''
    PORT_UDP=receiver.listening_port

    try:
        socket_UDP.bind((HOST_UDP, PORT_UDP))
    except socket.error , msg:
        print 'Fail to bind. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
    print 'Receiver bind successful'

     #start a TCP
    try:
        socket_TCP=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print 'Failed to create TCP socket. Error code: '
        sys.exit()
    print 'TCP socket Created'
    #Connect to sender
    socket_TCP.connect((receiver.sender_IP,receiver.sender_port))
    socket_TCP.send('hello')
    unpack_length_try=range((Max_Seg_Size+1))
    unpack_length_try.reverse()
    run=1
    #Iterally receive chunk and send ACK until received a FIN flag
    while run:
        chunk_received=socket_UDP.recvfrom(596)
        for chunk_data_length in unpack_length_try:
            try:
                received_data=struct.unpack('HHIIIHH%ds'%chunk_data_length,chunk_received[0])
                break
            except:
                pass
        unpacked_data=UnPackedFile(received_data[0],received_data[1],received_data[2],received_data[3],received_data[4],received_data[5],received_data[6],received_data[7])
        write_log(receiver,unpacked_data)
        run=received_chunk_process(receiver,unpacked_data,socket_TCP)
    print 'Delivery completed successfully'

