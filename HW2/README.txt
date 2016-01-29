1.
a. Documentation
The project implements a simplified TCP-like transport layer protocol, with pipeline Go Back N principle, to send a file from sender to receiver realiably. It can recover form in­-network packet loss, packet corruption, packet duplication and packet reordering and should be able cope with dynamic network delays.

Please see usage scenario about how to run the code.

###################################################################################################################################

b. Usage Scenario

(1) Run proxy: ./newudpl -i127.0.0.1:* -o127.0.0.1:20000 -p5000:6000 -L7 -B5 -O9

(2) START sender BEFORE start receiver: python Sender.py hamlet.txt 127.0.0.1 5000 20001 logfile_sender.txt 10

(3) START receiver: python Receiver.py file.txt 20000 127.0.0.1 20001 logfile_receiver.txt

Result: 

Sender side: 
Socket listening
Sent 100%
Delivery completed successfully
Total bytes sent (without retransmission)= 191733
Segments sent (without retransmission)= 333
Segments retransmitted = 411

Receiver side:
Receiver bind successful
TCP socket Created
Delivery completed successfully

Sender log file: 
Sent 2015-11-08 01:15:56, source: 20001, destination: 5000, sequence number: 5184, ACK number: 5760, FIN: 0, checksum: 25550, Estimated RTT: 0.2
Sent 2015-11-08 01:15:56, source: 20001, destination: 5000, sequence number: 5760, ACK number: 6336, FIN: 0, checksum: 46884, Estimated RTT: 0.2
ACK  2015-11-08 01:15:56, source: 20000, destination: 20001, sequence number: 0, expected number: 576, FIN: 0
Sent 2015-11-08 01:15:56, source: 20001, destination: 5000, sequence number: 6336, ACK number: 6912, FIN: 0, checksum: 28580, Estimated RTT: 0.178129631281

Receiver log file: 
Received 2015-11-08 01:15:56, source: 20001, destination: 5000, sequence number: 4032, ACK number: 4608, FIN: 0, checksum: 22442
ACK      2015-11-08 01:15:56, source: 20000, destination 20001, sequence number: 4032, expected ACK number: 4608, FIN: 0


NOTE: when running the proxy, a delay can be added by -d 0.1
      if the last digit in sender argument (in this scenario is 10) is not entered, take the window size as 1
      if the log file name position is inputted the ‘stdout’, all log headers will be printed out in terminal.

################################################################################################################################

2. 
a. TCP Segment Structure
I managed to follow the 20 byte TCP header format.
For the segment structure of data sent by sender, as shown in figure below, it has 5 lines and in total 20 bytes of headers. They are 16 bit of Source port number and destination port number, 32 bit of sequence number, acknowledgement number and FIN flag. In the last line of header, there are 16 bit of Checksum and 16 bit of Urgent pointer.

—————————————————————————————————————————————————————
|                    32 bit                          |
—————————————————————————————————————————————————————
|Source port# (16 bit)  | Destination port# (16 bit) |
—————————————————————————————————————————————————————
|             Sequence Number (32 bit)               |
—————————————————————————————————————————————————————
|           Acknowledgment Number (32 bit)           |
—————————————————————————————————————————————————————
|                   FIN 32bit                        |
—————————————————————————————————————————————————————
|     Checksum(16 bit)    |  Urgent pointer (16 bit) |
—————————————————————————————————————————————————————
|            Application data (576 Bytes)            |
|                                                    |

—————————————————————————————————————————————————————
For ACK sent by receiver has the similar as the header of the segment sent by sender.

—————————————————————————————————————————————————————
|                    32 bit                          |
—————————————————————————————————————————————————————
|Source port# (16 bit)  | Destination port# (16 bit) |
—————————————————————————————————————————————————————
|             Sequence Number (32 bit)               |
—————————————————————————————————————————————————————
|           Acknowledgment Number (32 bit)           |
—————————————————————————————————————————————————————
|                   FIN 32bit                        |
—————————————————————————————————————————————————————
|     Checksum(16 bit)    |  Urgent pointer (16 bit) |
—————————————————————————————————————————————————————

####################################################################################################################################

b. The States Typically Visited by a Sender and Receiver

Sender:
The sender has 2 threads namely sending thread and receiving thread.

Before the 2 thread start, I firstly build a UDP socket to send segments and a TCP socket to receive ACK from receiver and accept the TCP connection.

State for sending thread:

The sending thread is based on the pipeline algorithm. Thus there will be a window in sending process. I take 2 pointers in the pipeline algorithm: base is the first segment in the current window (the last segment of window can be expressed by base) and seq of largest segment sent is the largest sequence of segment the sender has sent (no matter whether if is received by receiver).

|(base)        (seq of largest segment sent)                     |
——————————————————————————————————————————————————————————————————


1. Send all data between seq of largest segment sent and the last segment (only includes the last segment edge). 

2. Pause the receiver thread in case of threading class.

3. Do fast retransmission. If the receiver thread tells the sender thread there is a ACK number that has been received for over 3 times, the sender thread will directly resend the segment with sequence number equal to ACK number (this is always the base segment) without waiting for timeout.

4. Deal with time out. Look for all segments that has been sent but did not receive an ACK, if one of them is time out, Resend the timeout segment.

5. Start the receiver thread again.

6. Check whether the FIN=1 flag is sent, if no ——> go back to step 1. Else resend data which has not confirmed to be received by ACK until receive the ACK with FIN==1.

Listening thread:
1. Receive the 20 byte ACK form receiver and unpack it.

2. If the received ACK number is larger than the base sequence number, update window.
   Else record the received ACK as the duplicate ACK and ask for retransmission when duplicated ACK greater than 3.
   THEN, go back to step 1.

*************************************************************************************************************************************

Receiver:
The receiver contains a buffer to record all not in sequence segments to improve the transmutation efficiency. Because there are too many states in the receiver side, I will mainly focus on who the receiver work.

1. receive data from sender and unpack data.

2. for normal transmutation (FIN==0, no corruption and in sequence), detect the condition of segments in buffer
   if there is no buffer or the buffer cannot fill the gap——>print current segment and expected ACK number move to the next segment.
   if the buffer gap can be filled, move the expected ACK number to the next segment with the buffer gap can not be filled and print the received segment as well as all buffer segments with sequence number < expected number. (for example: if segment # 4,5,7 is in the buffer, the segment #3 is received, the next expect ACK number is 6. and segment 3,4,5 should be printed)
   THEN send the ACK with the expected sequence number.

3. for corruption situation, send ACK with the current expected sequence number.

4. for not in sequence, if the sequence is larger than current expected sequence number, put received segment in buffer and send ACK with current expected sequence number. if sequence number < current expected sequence number, just send an ACK with current expected sequence number.

5. for FIN=1, do the similar thing as step 2,3,4, but send FIN=1 when receive a segment with FIN = 1 and no buffer exist.


###################################################################################################################################

c. the loss recovery mechanism

Fast retransmission: sender retransmit base segment when receive duplicated ACK for more than 3 times.

Time out: if no ACK or ACK with larger sequence number has been received, the segment with sequence number=ACK number will be resent when time out. 

###################################################################################################################################

d. Additional Features

Sending progress display: on the sender side, the program can calculate the ratio of file that has been sent and print it out in terminal. Like: Sent: 45%

Buffer on receiver side: the receiver side can record all non-corrupt but in sequence segments, so the sender no longer need to retransmit segment in buffer. This can improve the efficiency.

Fast retransmission: when the sender receive 3 duplicated ACKs it will retransmit the segment with the sequence number same as the duplicated ACK to save transmission time.

###################################################################################################################################

e. Statement about RTT calculation
   The estimated RTT is updated only when the ACK of the segment is received without retransmission. By this, I make sure the RTT I used to calculate estimated RTT can reflect the time of one RTT.

###################################################################################################################################

g. test version
   The program has been tested on MAC with python 2.7.10 and 2.6.9.
