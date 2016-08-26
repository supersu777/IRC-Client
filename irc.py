#IRC Client via terminal
#Author: RedFoX
#FA2AS
#License: Free

#IRC Commands:
#PASS <secret-passwd> -->not optional
#to login:
#NICK <nickname>\r\nUSER <username> <hostname> <servername> :<realname>
#for ping:
#PING :abcdef
#PONG :abcdef
#to join a channel:
#JOIN #<channel>
#to send a msg:
#PRIVMSG #<channel>|#<nick> :<message>
#to left:
#QUIT :<optional-quit-msg>

#import module
import sys,time,select
from socket import *


class irc:
	host="irc.quakenet.org"#irc.freenode.org
	nick="bandits"
	user="rabbid"
	server="IRC_Server"
	realname="unknown"
	
	login_msg="NICK %s\r\nUSER %s %s %s :%s\r\n"%(nick,user,host,server,realname)
	
	
	def __init__(self):
		self.joined=False
		
		self.port=6667
		self.buffer=8192
		self.sock=socket(AF_INET,SOCK_STREAM)
		connected=self.establish()
		if connected:
			print "[ <> ] Connected to %s:%d"%(self.host,self.port)
			#start irc client
			self.start()
			
	def establish(self):
		try:
			print "[ ~ ] Connecting to %s:%d"%(self.host,self.port)
			self.sock=create_connection((self.host,self.port))
			return True
		except Exception as e:
			print "[ ! ] Failed connecting to %s:%d"%(self.host,self.port)
			print "Error msg:",e
			print "Retrying..."
			#indicate a gap
			time.sleep(0.01)
			self.establish()
	def onrecv(self):
		self.readbuffer=""
		timeout=2
		self.sock.setblocking(0)
		total_data=[];
		data='';
		begin=time.time()
		#recv
		while 1:
			if total_data and time.time()-begin >=timeout: break
			#if you got no data at all, wait a littlelonger, twice the timeout
			elif time.time()-begin > timeout*2: break
			#recv something
			try:
				data=self.sock.recv(self.buffer)
				if data:
					total_data.append(data)
					#change the beginning time for measurement
					begin=time.time()
				else:
					#sleep for sometime to indicate a gap
					time.sleep(0.01)
			except: pass
		#join all parts to make final string
		self.readbuffer+= ''.join(total_data)
		return self.readbuffer
	def send(self,data):
		self.sock.send(data)
		
	def enter_nick(self):
		sys.stdout.write( "[ ? ] Please enter a new nick: ")
		new_nick=raw_input()
		if new_nick:
			self.login_msg=self.login_msg.replace("%s"%self.nick,new_nick)
			self.nick=new_nick
			print "[ * ] Use new nick: %s"%new_nick
			print "[ * ] Retrying..."
			self.send(self.login_msg)
		else:
			print "[ ! ] You must enter a new nick"
			self.enter_nick()
			
	def login(self):
		signing=True
		self.is_success=False
		self.send(self.login_msg)
		#print "sent:",[self.login_msg]
		print "[ # ] Login with nick name: %s"%self.nick
		while signing:
			login_success=[":%s MODE %s :+i"%(self.nick,self.nick)]#,"NOTICE AUTH :*** No ident response"]
			nick_already_exists="%s :Nickname is already in use."%self.nick
			nick_is_registered="%s :This nickname is registered"%self.nick
			freenode_login_success=":%s MODE %s :+i"%(self.nick,self.nick)
			quakenet_login_success="NOTICE AUTH :*** No ident response"
			registered="NICK :%s"%self.nick
			banned="%s :You are banned from this server- Please do not spam users or channels"%self.nick
			data=self.recv()
			if data:
				print data
				for sukses in login_success:
				
					if nick_already_exists in data:
						print "[ ! ] Login failed! Nickname %s is already in use."%self.nick
					
						self.enter_nick()
						break
						
					elif nick_is_registered in data:
						print "[ ! ] Login failed! Nickname %s is registered."%self.nick
						self.enter_nick()
						break
						
					elif sukses in data :
						"""self.send(self.login_msg)
						data=self.recv()"""
						
						self.is_success=True
						
						signing=False
						break
					elif banned in data:
						print "[ !!! ] You have been banned!";
						exit()
					elif "timed out" in data:
						print "[ ! ] Remote closed connection";
						exit()
					elif "%s :You may not reregister"%self.nick in data:
						
						signing=False
						break
					elif "PING :" in data:
						self.ping_msg=data.split("PING :",1)[1]
						self.pong_to(self.ping_msg)
						self.is_success=True
						signing=False;
						break
						

	def ui(self):
		timeout=120 #server will send PING msg to client if they do not send anything after 258 seconds
		sys.stdout.write("command: ")
		sys.stdout.flush()
		i, o, e = select.select([sys.stdin],[],[],timeout)
		if i:
			self.cmd=sys.stdin.readline().strip()
			cmd=self.cmd.startswith
			try:
				#print self.joined
				if self.joined and cmd("/")==False:
					self.cmd="/msg #%s :%s"%(self.channel,self.cmd)#"PRIVMSG #%s :%s"%(self.channel,self.cmd)
				command=self.cmd.split("/",1)[1].split(" ",1)[0]
				
			except Exception as e:
				command=self.cmd
			print "[ $ ] Command:",command
			if command=="join":#cmd("/join "):
				try:
					self.cmd=self.cmd.split("#",1)[1]#self.cmd[6:]
					self.join_to()
				except Exception as e:
					#print [self.cmd]
					if not self.cmd:
						print "[ ! ] You must enter channel name to join."
			elif command=="msg":#cmd("/msg "):
				try:
					self.at=self.cmd.split("#",1)[1].split(" ",1)[0]
					try:
						self.cmd=self.cmd.split(":",1)[1]#self.cmd[5:]
						self.msg_to()
					except IndexError as e:
						print "[ ! ] You must enter a message to send it to %s."%self.at
				except IndexError as e:
					print "[ ! ] You must enter channel name or nick name to send a message."
			else:
				#print "is joined:", self.joined
				
				self.send(self.cmd+"\r\n")
				data=self.recv()
				print data
				if ":Closing Link:" in data:
					print "[ ! ] Server disconnected"
					exit()
		else:
			#if user was not enter anything then ping the server :)
			print "You said nothing in %d seconds!"%timeout
			self.ping_to()
			
		
	def msg_to(self):
		message=self.cmd
		msg="PRIVMSG #%s :%s\r\n"%(self.at,message) 
		self.send(msg)
		print "[ > ] msg to: %s"%self.at
		print "[ # ] msg: %s"%message
		data=self.recv()
		print [data]
		
	def join_to(self):
		#self.joined=False
		self.channel=self.cmd
		print "[ ~ ] Joining to %s channel..."%self.channel
		join="JOIN #%s\r\n"%self.channel
		self.send(join)
		data= self.onrecv()
		if data:
			print data
			#print "NICK:",self.nick
			#print "CHANNEL:",self.channel
			if "%s #%s :End of /NAMES list."%(self.nick,self.channel) in data:
				print "[ * ] Joined to %s"%self.channel;
				self.joined=True
			elif "%s #%s :Cannot join channel (+i) - you must be invited"%(self.nick,self.channel) in data:
				print "[ ! ] Cannot join to channel: %s"%self.channel
			
				
	
	def ping_to(self,msg=None):
		if not msg:
			msg="PING :123456\r\n"
		else:
			msg="PING :%s"%msg
		print repr(msg)
		self.send(msg)
		data=self.recv()
		print data
	def pong_to(self,msg):
		msg="PONG :%s"%msg
		print repr(msg)
		self.send(msg)
		data=self.recv()
		print data
			
	def start(self):
		#initialize
		send=self.send; self.send=send
		recv=self.onrecv; self.recv=recv
		
		#login
		print "[ ~ ] Signing in with nick %s , user: %s , to hostname: %s and server name: %s with realname: %s"%(self.nick,self.user,self.host,self.server,self.realname)
		#loop for login :)
		self.login()
		if self.is_success:
			print "[ * ] Login success!"
		"""
		COMMAND:
			/join #channel
			/msg #channel|nickname
		"""
		while 1:
			#start user interface
			self.ui()
			
try:
	irc()
except KeyboardInterrupt:
	print "\nexit..."
	exit()
