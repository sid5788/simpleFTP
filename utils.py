import socket

LOGGING = 1
chk_sum_bits = ['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0']

def tobits(s):
    result = []
    for c in s:
        bits = bin(ord(c))[2:]
        bits = '00000000'[len(bits):] + bits
        result.extend([int(b) for b in bits])
    return result

def frombits(bits):
    chars = []
    for b in range(len(bits) / 8):
        byte = bits[b*8:(b+1)*8]
        chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
    return ''.join(chars)

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def create_checksum(msg):
    s = 0
    length = len(msg)
    if (length%2 != 0):
        msg+='\x00'
    for i in range(0, length, 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff

def init_create_socket():
	#create UDP socket
	try:
		udp_soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error, error_msg:
		print "Socket creation failed. "+str(error_msg[0])+": "+error_msg[1]
		sys.exit()

        return udp_soc

def init_bind_socket(host,port):
        #create UDP socket
        udp_soc = init_create_socket()
	#Bind socket to all interface on known port 
	try:
		udp_soc.bind((host,port))
	except socket.error, error_msg:
		print "Binding failed. "+str(error_msg[0])+": "+error_msg[1]
		sys.exit()
	#listen for peers
	return udp_soc
'''
Data Message format:
Header:
32 bit: Sequence number
16 bit: CheckSum
16 bit: 0101010101010101

Data:
(MSS-32-16-16 bits)
'''

#def init_chksum():
#       chk_sum = frombits(chk_sum_bits)
#       print "Initial CheckSum:"
#       print chk_sum
#       return chk_sum

def create_message(seq_no,data):
        chk_sum = create_checksum(data)
        chk_sum_list = frombits(bin(chk_sum)).zfill(2)
        #print "CheckSum:"
        #print chk_sum_list
        msg_type_bits = ['0','1','0','1','0','1','0','1','0','1','0','1','0','1','0','1']
        msg_type = (frombits(msg_type_bits)).zfill(2)
        #print "Sent Data:"
        #print data
        seq_no_list = tobits(str(seq_no).zfill(4))
        seq_no_msg = frombits(seq_no_list)
	msg = seq_no_msg+chk_sum_list+msg_type+data
	return msg


'''
ACK Message Format:
Header:
32 bit: Sequence number
16 bit: 0s
16 bit: 1010101010101010
'''
def create_ack(seq_no):
        msg_type_bits = ['1','0','1','0','1','0','1','0','1','0','1','0','1','0','1','0']
        msg_type = frombits(msg_type_bits)
        chk_sum = frombits(chk_sum_bits)
        seq_no_list = tobits(str(seq_no).zfill(4))
        seq_no_msg=frombits(seq_no_list)
        msg = seq_no_msg+chk_sum+msg_type
        return msg
'''
def send_data(soc,data):
	if LOGGING:
		print "sending msg..."
		print data
	data_str = str(data)
	header = str(len(data_str)).ljust(HEADER_LEN)
	msg_len = HEADER_LEN + len(data_str)
	while msg_len>0:
		send_len = soc.send(header+data_str)
		msg_len = msg_len - send_len

def recieve_data(soc):
	header = soc.recv(HEADER_LEN)
	data = ''
	if len(header)!=0:
		data_len = int(header)
		data = soc.recv(data_len)
	return data
'''

