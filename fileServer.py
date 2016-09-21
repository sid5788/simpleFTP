import os
import sys
import socket
import utils
import random
from thread import *

SERV_PORT = 7735
SERV_HOST = ''
BUF = ''
last_recvd_seq = 0

def probLoss(prob):
        #generate random probability of error
        loss_chance = float(random.random())
        #print "Loss Chance: Probability"
        #print str(loss_chance)+':'+str(prob)
        if (loss_chance < prob):
           return 1
        else:
           return 0

def sendAck(seq_no,addr):
        #sends ACK for received packet
        send_soc = utils.init_create_socket()
        pkt = utils.create_ack(seq_no)
        send_soc.sendto(pkt,addr)
        #print "------------------------>"
        #print "Sending ACK"+str(seq_no)+"------------------------>"
        #print "------------------------>"
        send_soc.close()
        
def checkError(recvd_data,msg_type,chk_sum,seq_no, prob):
        global last_recvd_seq
        error = 0
        #Check if msg_type is for data message
        if (msg_type != '\x55\x55'):
            #print "------------------------>"
            #print 'Error pkt: '+str(seq_no)
            #print 'Message type is not data'
            #print "------------------------>"
            return 1
        #compute checksum on the recvd packet return 1 if checksum wrong
        check_sum=utils.frombits(bin(utils.create_checksum(recvd_data))).zfill(2)
        if(check_sum != chk_sum):
            #print "------------------------>"
            #print 'Error pkt: '+str(seq_no)
            #print "CheckSums don't match. Recalculated CheckSum:"
            #print check_sum
            #print "------------------------>"
            return 2
        #check Sequence number of recvd packet is in order error = 1 of seq num wrong
        if (seq_no != (last_recvd_seq+1)):
            #print "------------------------>"
            #print 'Error pkt: '+str(seq_no)
            #print 'Sequence number out of order.Last recvd Seq:'+str(last_recvd_seq)+'SeqNo:'+str(seq_no)
            #print "------------------------>"
            return 3
        #check probability of error
        error = probLoss(prob) 
        if (error == 1):
            #print "------------------------>"
            print "Packet Loss, sequence number = "+str(seq_no)
            #print 'Error pkt: '+str(seq_no)
            #print 'Probability Error'
            #print "------------------------>"
            return 4
        return error

def extractData(data):
    recvd_data_list = list(data)
    seq_no = int(''.join(recvd_data_list[0:4]))
    #print '--------------------------------------------------'
    #print 'Sequence No:'
    #print seq_no
    chk_sum = ''.join(recvd_data_list[4:6])
    #print 'CheckSum:'
    #print chk_sum
    msg_type = ''.join(recvd_data_list[6:8])
    #print 'Message Type:'
    #print msg_type
    recvd_data = ''.join(recvd_data_list[8:])
    #print 'Recvd Data:'
    #print recvd_data
    return recvd_data,msg_type,chk_sum,seq_no
    
def write_file(fd, data):
        #read from buffer and write to file
        os.write(fd, data)

def recv_data(udp_soc, port, output_file, prob):
        global BUF, last_recvd_seq
        #print "Inside Received Data"
        #Receive the first packet to get the length of data
        data,addr = udp_soc.recvfrom(1000)
        #print "Received Data"
        recvd_data,msg_type,chk_sum,seq_no = extractData(data)
        MSS = int(recvd_data)
        sendAck(seq_no,addr)
        #Remove the file if already exists
        os.system('rm -fr '+output_file)
        fd = os.open(output_file, os.O_RDWR|os.O_CREAT)
        while 1:
	    #reads packet from socket
            data,addr = udp_soc.recvfrom(MSS+64)
            #check that data is received from the correct address
            recvd_data = 'Address:'+str(addr)+' Data Received:'+str(data)
            #print recvd_data
            #Extract data from received message
            recvd_data,msg_type,chk_sum,seq_no = extractData(data)
            
            #compute checksum and in sequence reception
            error = checkError(recvd_data,msg_type,chk_sum,seq_no,prob)
            if (error == 0):
                #If no error in received packet detected
                last_recvd_seq = seq_no
            
                #Check for end of file transfer
                if (str(recvd_data) == "1010TransferComplete1010"):
                    #Acknowledge received packet
                    sendAck(seq_no,addr)
                    break
                #Write to buffer
                BUF = BUF+recvd_data
                #print "\n Current Buffer:"+BUF
                #Write to file (temp)
                #print "--------------------------------|||||\nWrite to File Seq No:"+str(seq_no)+" Data:"+recvd_data
                write_file(fd,recvd_data)
                #Acknowledge received packet
                sendAck(seq_no,addr)
            #else:
                #Error in received packet detected
                #print error
 
def main():
        #Get the command line arguments
        if len(sys.argv) != 4:
                print "fileServer.py <port no> <filename> <probability>"
                sys.exit()
        port = 0
        output_file = ''
        prob=0.0
        port = int(sys.argv[1])
        output_file = sys.argv[2]
        prob = float(sys.argv[3])
        # bind a socket to hostname and port
        udp_soc = utils.init_bind_socket(SERV_HOST,port)
        #Start Receiving data in main thread
        recv_data(udp_soc,port,output_file,prob)
        #Start a thread to start reading from buffer and write to file
        
        #Close socket
        udp_soc.close()

if __name__ == "__main__":
        main()
