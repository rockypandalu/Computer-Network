__author__ = 'rocky'
import os,struct,sys,socket,time,thread,datetime
#Global variables used to transfer value between threads
Estimated_RTT=0.2  #initial estimated RTT
Sample_RTT=0       #RTT of package in current round
alpha=0.125
beta=0.25
DevRTT=0.2         #Derivation of RTT
Time_out_interval=1#Initial timeout value
Current_ACK=0      #The largest ACK sequence received by sender
Sending_Seq=0      #The sequence that being sent
Max_Seg_Size=576   #data size of each packet
window_base=0      #base of window
list_has_retransmitted=[]#record the sequence of package which has been retransmitted
dict_time_out_counter={} #Record when package is recently be sent
flag_pause_rec_thread=0  #Pause the receiver thread for ACK, avoid clash between threads
finish_state=0           #Status of finish
total_send=0#The number of packets sent (including retransmit)
duplicate_ACK=0#The number of duplicate ACK received
flag_retransmit_caused_by_dup_ACK=-1#changed from receiver thread, ask sender thread to retransmit package and achieve fast retransmittion
class SendFile:
    chunk_data_total=[]
    #Store input value from terminal
    def __init__(self, filename, remote_IP, remote_port, ack_port_number, log_filename, window_size):
        self.filename=filename
        self.remote_IP=remote_IP
        self.remote_port=int(remote_port)
        self.ack_port_number=int(ack_port_number)
        self.log_file=log_filename
        self.window_size=int(window_size)

    #read data and divide them into chunks with specific length
    def make_chunk_data(self):
        try:
            data=open(self.filename)
        except:
            print 'Fail to open the file'
        while len(self.chunk_data_total) < os.stat(self.filename).st_size/Max_Seg_Size:
            chunk_data=data.read(Max_Seg_Size)
            self.chunk_data_total.append(chunk_data)
        self.chunk_data_total.append(data.read(os.stat(self.filename).st_size % Max_Seg_Size))

        data.close()

    #provide headers to chunk
    def make_chunk(self, sequence_num):
        sequence_packet=sequence_num/Max_Seg_Size
        #print 'sequence_packet'
        #print sequence_packet

        if sequence_packet==len(self.chunk_data_total)-1:
            FIN=1
        else:
            FIN=0
        chunk_data=self.chunk_data_total[sequence_packet]
        source=self.ack_port_number
        destination=self.remote_port
        Urge_data_pointer=0
        ACK_num=sequence_num+len(chunk_data)
        chunk_str=str(source)+str(destination)+str(sequence_num)+str(ACK_num)+str(FIN)+str(Urge_data_pointer)+chunk_data
        checksum=self.make_checksum(chunk_str)
        chunk=struct.pack('HHIIIHH%ds'%len(chunk_data), source, destination, sequence_num, ACK_num, FIN, checksum, Urge_data_pointer, chunk_data)
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        log='Sent '+timestamp+', source: '+str(source)+', destination: '+str(destination)+', sequence number: '+str(sequence_num)+', ACK number: '+str(ACK_num)+', FIN: '+str(FIN)+', checksum: '+str(checksum)+', Estimated RTT: '+str(Estimated_RTT)+'\n'
        if self.log_file=='stdout':
            print log
        else:
            #write logfile
            File=open(self.log_file,'a')
            File.write(log)
            File.close()
        return [chunk,FIN]

    #Used for calculate check sum
    def wraparound_add(self,a,b):
        c=a+b
        if c<=0xffff:
            return c
        else:
            return c-0xffff

    #Calculate checksum using the same method as lecture slide
    def make_checksum(self,chunk):
        checksum=0
        for i in range(0,len(chunk),2):
            if i==len(chunk)-1:
                checksum=self.wraparound_add(checksum,ord(chunk[i]))
            else:
                bit_16=ord(chunk[i])+(ord(chunk[i+1]) << 8)
                checksum=self.wraparound_add(bit_16,checksum)
        return ~checksum & 0xffff

#Deal with input data and store them in class SendFile
def system_input():
    if len(sys.argv)==7:
       sender=SendFile(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6])
    elif len(sys.argv)==6:
        sender=SendFile(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],1)
    else:
        print 'Input format Error!\n Please use the format \n python sender.py <filename> <remote_IP> <remote_port> <ack_port_num> <log_filename> <window_size>'
        print 'or python sender.py <filename> <remote_IP> <remote_port> <ack_port_num> <log_filename>'
        sys.exit()
    return sender

#print the received ACK in a log file
def log_recv_ACK(sender,received_data):
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    log='ACK  '+timestamp+', source: '+str(received_data[0])+', destination: '+str(received_data[1])+', sequence number: '+str(received_data[2])+', expected number: '+str(received_data[3])+', FIN: '+str(received_data[4])+'\n'
    if sender.log_file=='stdout':
        print log
    else:
        File=open(sender.log_file,'a')
        File.write(log)
        File.close()

#Because of cumulative ACK, when received a large ACK, update the dictionary and delete the old value
def del_dict_time_out_counter(ACK_seq):
    global dict_time_out_counter, list_has_retransmitted
    dict_time_out_counter_copy=dict_time_out_counter.copy()
    for seq in dict_time_out_counter_copy:
        if seq<ACK_seq:
            del dict_time_out_counter[seq]
    for seq in list_has_retransmitted:
        if seq<ACK_seq:
            list_has_retransmitted.remove(seq)

#Find key in a dictionary from value
def find_dict_key_from_value(dict,value):
    for key in dict:
        if dict[key]==value:
            return key

# Extra function, print the progress the transmission has done
def progress(ACK, total_package):
    rate=float(ACK)/float(total_package)*100
    print '\rSent %d%%' % rate,
    sys.stdout.flush()

#Receiver Thread
#1. Receive the ACK
#2. unpack ACK
#3. do operation when the received ACK has a sequence number > current largest ACK number
#4. If duplicated ACK is received by 3 times, request send thread to retransmit the package
def recv_ACK(conn,addr,sender,socket_UDP):
    global Current_ACK, Estimated_RTT,Sample_RTT,duplicate_ACK,finish_state,dict_time_out_counter,DevRTT,list_has_retransmitted,Time_out_interval,flag_retransmit_caused_by_dup_ACK
    total_seq=os.stat(sender.filename).st_size
    while 1:
        ACK=conn.recv(20)
        received_ACK=struct.unpack('HHIIIHH',ACK)
        log_recv_ACK(sender,received_ACK)
        if received_ACK[4]==1:
            print '\rSent 100%'
            finish_state=2
            break
        if received_ACK[3]>Current_ACK:
            progress(received_ACK[3],total_seq)
            duplicate_ACK=0
            Current_ACK=received_ACK[3]
            if not received_ACK[2] in dict_time_out_counter:
                time.sleep(0.007)
            #update time out interval and RTT for non retransmitted data
            elif received_ACK[3] not in list_has_retransmitted:
                Sample_RTT=time.time()-dict_time_out_counter[received_ACK[2]]
                Estimated_RTT=Estimated_RTT*(1-alpha)+alpha*Sample_RTT
                DevRTT=(1-beta)*DevRTT+beta*abs(Sample_RTT-Estimated_RTT)
                Time_out_interval=Estimated_RTT+DevRTT
            while flag_pause_rec_thread==1:
                time.sleep(0.0001)
            del_dict_time_out_counter(received_ACK[3])
        else:
            duplicate_ACK+=1
            if duplicate_ACK>2:
                flag_retransmit_caused_by_dup_ACK=received_ACK[3]



#Main function
if __name__ == '__main__':
    #input arguments
    sender=system_input()
    File=open(sender.log_file,'wt')
    File.close()
    print sender.ack_port_number
    sender.make_chunk_data()
    #Initialize UDP socket
    try:
         socket_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        print 'Failed to create UDP socket.'
        sys.exit()

     #start a TCP
    try:
        socket_TCP=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print 'Failed to create TCP socket.'
        sys.exit()
    socket_TCP.bind(('', sender.ack_port_number))
    socket_TCP.listen(10)
    print 'Socket listening'
    #built TCP connection
    conn, addr=socket_TCP.accept()
    test=conn.recv(1024)
    thread.start_new_thread(recv_ACK,(conn,addr,sender,socket_UDP))
    FIN=0
    #time.sleep(3)
    #Send thread
    while not FIN:
        while Sending_Seq<=(window_base+sender.window_size*Max_Seg_Size):
            [chunk,FIN]=sender.make_chunk(Sending_Seq)

            socket_UDP.sendto(chunk, (sender.remote_IP, sender.remote_port))
            total_send+=1
            if not Sending_Seq in dict_time_out_counter:
                dict_time_out_counter[Sending_Seq]=time.time()
            if FIN:
                finish_state=1
                break
            Sending_Seq+=Max_Seg_Size
        flag_pause_rec_thread=1

        if flag_retransmit_caused_by_dup_ACK>0:
            if flag_retransmit_caused_by_dup_ACK not in list_has_retransmitted:
                list_has_retransmitted.append(flag_retransmit_caused_by_dup_ACK)
            [chunk,FIN]=sender.make_chunk(flag_retransmit_caused_by_dup_ACK)
            socket_UDP.sendto(chunk, (sender.remote_IP, sender.remote_port))
            dict_time_out_counter[flag_retransmit_caused_by_dup_ACK]=time.time()
            total_send+=1
            duplicate_ACK=0
            flag_retransmit_caused_by_dup_ACK=-1

        if len(dict_time_out_counter)!=0:
            timer_set=min(dict_time_out_counter.values())
            time_out=timer_set+Time_out_interval
            if time.time()>time_out:
            #TIme out
                key=find_dict_key_from_value(dict_time_out_counter,timer_set)
                if key not in list_has_retransmitted:
                    list_has_retransmitted.append(key)
                [chunk,FIN]=sender.make_chunk(key)
                socket_UDP.sendto(chunk, (sender.remote_IP, sender.remote_port))
                dict_time_out_counter[key]=time.time()
                total_send+=1
        flag_pause_rec_thread=0
        window_base=Current_ACK
    while finish_state!=2:
        flag_pause_rec_thread=1
        if len(dict_time_out_counter)!=0:
            timer_set=min(dict_time_out_counter.values())
            time_out=timer_set+Time_out_interval
            if time.time()>time_out:
            #TIme out
                key=find_dict_key_from_value(dict_time_out_counter,timer_set)
                if key not in list_has_retransmitted:
                    list_has_retransmitted.append(key)
                [chunk,FIN]=sender.make_chunk(key)
                socket_UDP.sendto(chunk, (sender.remote_IP, sender.remote_port))
                dict_time_out_counter[key]=time.time()
                total_send+=1
        flag_pause_rec_thread=0
        time.sleep(Estimated_RTT)
    Num_retransmit=total_send-len(sender.chunk_data_total)
    print 'Delivery completed successfully'
    print 'Total bytes sent (without retransmission)= '+str(os.stat(sender.filename).st_size)
    print 'Segments sent (without retransmission)= '+str(len(sender.chunk_data_total))
    print 'Segments retransmitted = '+str(Num_retransmit)
    original_data=open(sender.filename).read()
    generated_data=open('file.txt').read()
    if original_data==generated_data:
         print 'good'