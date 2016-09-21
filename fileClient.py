import sys
import socket
import os
import utils
import time
import threading
import signal
from thread import *

SERV_HOST = ''
SERV_PORT = 7735
LOGGING = 1
fileName = "SampleFile"
timeout_timer=1
#transfer window size
N = 4
#MSS
MSS = 1000
#File Segments list
fileList = []
sent_index = -1
ack_index = -1
window_limit = 0
udp_soc = utils.init_create_socket() 
host = ''
port = 0
lock = threading.RLock()

def resend_pkts(signum, f):
    global ack_index
    global window_limit
    global fileList
    global host
    global port

    resent_seq_no = ack_index+1
    #print 'reset alarm:Resending_pkts:'+str(resent_seq_no)+'to'+str(window_limit)
    lock.acquire()
    #print '------------\nlock acquired in Resend Pkts\n--------------'
    signal.alarm(0)
    signal.setitimer(signal.ITIMER_REAL, timeout_timer)
    while ((resent_seq_no<=window_limit)and(resent_seq_no<=(len(fileList)-1))):
        msg = fileList[resent_seq_no]
        pkt = utils.create_message(resent_seq_no,msg)
        udp_soc.sendto(pkt, (host, port))
        print 'Timeout, sequence number = '+str(resent_seq_no)
        #print resent_seq_no
        resent_seq_no+=1
    lock.release()
    #print '------------\nlock released in Resend Pkts\n--------------'

def transferFile(udp_soc,host,port):
        global fileList
        global N
        global sent_index
        global ack_index
        global window_limit
        window_limit= N-1
        seq_no=-1
        
        length = len(fileList)
        while 1:
            #print "Ack Index:"+str(ack_index)
            if (ack_index == length-1):
                break
            '''
            time.sleep(0)
            if ((window_limit - sent_index) == N):
                lock.acquire()
                
                signal.alarm(0)
                signal.setitimer(signal.ITIMER_REAL, timeout_timer)
                lock.release()
            '''
            while ((sent_index<window_limit)and(sent_index<(len(fileList)-1))):
                lock.acquire()
                #print '------------\nlock acquired in transfer file\n--------------'
                signal.alarm(0)
                signal.setitimer(signal.ITIMER_REAL, timeout_timer)
                sent_index+=1
                seq_no+=1
                msg = fileList[sent_index]
                pkt = utils.create_message(seq_no,msg)
                #print 'Sending Msg:'+str(seq_no)+"\n------------------------"
                udp_soc.sendto(pkt, (host, port))
                #print 'Sent_pkts:'+str(sent_index)+' Window Limit:'+str(window_limit)+'\nxxxxxxxxxxxxxxxx'
                lock.release()
                #print '------------\nlock released in transfer file\n--------------'
                time.sleep(0)

def  readFile(sampleFile, length):
        global fileList
        try:
            fd = open(sampleFile,'r+')
        except:
            sys.exit('Unable to open file!')
        
        msg = str(MSS)
        fileList.append(msg)
        while (msg):
            msg = fd.read(length) 
            fileList.append(msg)
        
        msg = "1010TransferComplete1010"
        fileList.append(msg)

#Listen to incoming ACKs
def recvAcks(udp_soc):
        global ack_index
        global fileList
        global window_limit
        global N
        global sent_index
        last_index = len(fileList)-1
        #print "ACK Thread Started: last_index:"+str(last_index)+'\n-------------------------'
        while (ack_index < last_index):
            recvd_ack,addr = udp_soc.recvfrom(100)
            #print "Received Ack:"
            #print recvd_ack
            seq_no = int(''.join(list(recvd_ack)[0:4]))
            #print "Seq No Ackd:"
            #print recvd_ack
            #print "------------------------------------"
            if (seq_no > ack_index and seq_no <= window_limit):
                ack_index = seq_no
                if(ack_index == window_limit):
                    #lock.acquire()
                    lock.acquire()
                    #print '------------\nlock acquired in recvAcks\n--------------'
                    #signal.alarm(0)
                    window_limit= window_limit+N
                    #print 'Disable Alarms:Window Ackd!! Ack Index:'+str(ack_index)+" Sent Index:"+str(sent_index)+" New Window Limit:"+str(window_limit)+'\n---------------------'
                    lock.release()
                    #print '------------\nlock released in recvAcks\n--------------'
                  
def main():
        global N
        global MSS
        global host
        global port
        if len(sys.argv) != 6:
                print "Usage: fileClient.py <Server_Name> <port no> <file name> <windowsize> <MSS>"
                sys.exit()
        #open a socket
        host = sys.argv[1]
        port = int(sys.argv[2])
        sample_file = sys.argv[3]
        N = int(sys.argv[4])
        MSS = int(sys.argv[5])
        signal.signal(signal.SIGALRM, resend_pkts)
        #Read from file and put in buffer
        readFile(sample_file, MSS)
        #Thread to listen to incoming ACKs
        t = threading.Thread(target=recvAcks, args=(udp_soc,))
        t.start()
        #connect to server and sends messages read from buffer
        transferFile(udp_soc,host,port)
        t.join()
        #Close udp socket
        udp_soc.close()

if __name__ == "__main__":
    main()
