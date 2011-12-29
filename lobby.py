# -*- coding: ISO-8859-1 -*-
import threading
import time
import socket
import hashlib, base64, binascii
import random
import sys

class Lobby (threading.Thread):
	def __init__ (self, FunctionCallbackDebug, FunctionCallbackChat, FunctionCallbackEvent, LoginInfo):
		threading.Thread.__init__ (self)
		self.Debug = FunctionCallbackDebug
		self.CallbackChat = FunctionCallbackChat
		self.CallbackEvent = FunctionCallbackEvent
		self.User = None
		self.Passwd = None
		self.BattlePort = None
		self.HostIP = None
		self.HostPort = None
		self.IP = None
		self.SetLoginInfo (LoginInfo)
		self.ClassPing = None	# Ping class
		self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.Active = 0
		self.LoggedIn = 0
		self.AllowReConnect = 1
		self.LoggedInQueue = []
		
		self.Users = {}
		self.Battles = {}
		self.BattleUsers = {}
		self.BattleID = 0
		self.Channels = {}
		
		# I = Int, F = Float, V = String, S = Sentence, BXX = BitMask XX chars
		self.Commands = {
			'TASServer':['V', 'V', 'I', 'I'],
			'ACCEPTED':['V'],
			'MOTD':['S'],				# Ignore
			'LOGININFOEND':[],			# Ignore
			'PONG':[],					# Ignore
			'ADDUSER':['V', 'V', 'I', 'I'],
			'REMOVEUSER':['V'],
			'CLIENTSTATUS':['V', 'B7'],
			'BATTLEOPENED':['I', 'I', 'I', 'V', 'V', 'I', 'I', 'I', 'I', 'I', 'S', 'S', 'S'],
			'JOINEDBATTLE':['I', 'V', 'V'],
			'LEFTBATTLE':['I', 'V'],
			'BATTLECLOSED':['I'],
			'UPDATEBATTLEINFO':['I', 'I', 'I', 'I', 'S'],
			'SAIDPRIVATE':['V', 'S'],
			'SAIDPRIVATEEX':['V', 'S'],
			'SAYPRIVATE':['V', '*'],	# Ignore ECHO reply...
			'SAID':['V', 'V', 'S'],
			'SAIDEX':['V', 'V', 'S'],
			'SAIDBATTLE':['V', 'S'],
			'SAIDBATTLEEX':['V', 'S'],
			'REQUESTBATTLESTATUS':[],
			'JOINBATTLEREQUEST':['V', 'V'],
			'CLIENTBATTLESTATUS':['V', 'B32', 'I'],
			'OPENBATTLE':['I'],
			'JOIN':['V'],
			'CLIENTS':['V', 'S'],
			'JOINED':['V', 'V'],
			'LEFT':['V', 'V'],
			'ADDBOT':['I', 'V', 'V', 'B32', 'I', 'S'],
			'REMOVEBOT':['I', 'V'],
			'DENIED':['S'],
			'UPDATEBOT':['I', 'V', 'B32', 'I'],
			'SERVERMSG':['S'],
		}
	
	
	def run (self):
		self.Debug ('Lobby start')
		self.Connect ()
		RawData = ''
		while self.Active:
			Info = {"Time":int (time.time ()), "Loops":0}
			Data = ""
			while self.Active:
				Data = self.Socket.recv (1)
				if Data:
					RawData = RawData + Data
					Lines = RawData.split ("\n")
					if len (Lines) > 1:
						RawData = Lines[1]
						self.HandleCommand (Lines[0])
				else:
					if Info["Time"] == int (time.time ()):
						Info["Loops"] = Info["Loops"] + 1
						if Info["Loops"] > 10:
							self.ReConnect ()
					else:
						Info = {"Time":int (time.time ()), "Loops":0}
					print "*** No data :/"
		self.Debug ('Lobby run finnished')
	
	
	def SetLoginInfo (self, LoginInfo):
		self.Debug ()
		if LoginInfo.has_key ('Login'):
			self.User = LoginInfo['Login']
		if LoginInfo.has_key ('Password'):
			self.Passwd = LoginInfo['Password']
		if LoginInfo.has_key ('Port'):
			self.BattlePort = LoginInfo['Port']
		if LoginInfo.has_key ('LobbyHost'):
			self.HostIP = LoginInfo['LobbyHost']
		if LoginInfo.has_key ('LobbyPort'):
			self.HostPort = LoginInfo['LobbyPort']
	
	
	def HandleCommand (self, RawData):
#		self.Debug ('Command::' + str (Command))
		Command = self.ReturnValue (RawData, ' ')
		Data = RawData[len (Command) + 1:]
		if self.Commands.has_key (Command):
			Arg = []
			try:
				for Field in self.Commands[Command]:
					RawArg = ''
					if Field == 'I':
						NewArg = int (self.ReturnValue (Data, ' '))
					if Field == 'F':
						NewArg = float (self.ReturnValue (Data, ' '))
					elif Field == 'V':
						NewArg = str (self.ReturnValue (Data, ' '))
					elif Field[0:1] == 'B':
						RawArg = self.ReturnValue (Data, ' ')
						NewArg = self.dec2bin (RawArg, int (Field[1:]))
					elif Field == 'S':
						NewArg = self.ReturnValue (Data, '\t')
					elif Field == '*':
						NewArg = Data
					try:
						Arg.append (NewArg)
						if len (RawArg) > 0:
								NewArg = RawArg
						Data = Data[len (str (NewArg)) + 1:]
					except:
						print '\n\nCOMMAND FAILED\n\n'
			except:
				self.Debug ('WrongFormatedCommand::' + str (RawData))
				print '\n\nCOMMAND FAILED'
				print RawData
				print '\n'
				return (None)
		else:
			self.Debug ('UnknownCommand::' + str (RawData))

		if Command == "TASServer":
			self.Login ()
		elif Command == "ACCEPTED":
			self.SetLoggedIn ()
		elif Command == 'LOGININFOEND' or Command == 'PONG' or Command == 'MOTD':
			pass
		elif Command == "ADDUSER":
			if not self.Users.has_key (Arg[1]):
				self.Users[Arg[0]] = {
					'User':Arg[0],
					'Country':Arg[1],
					'CPU':Arg[2],
					'ID':Arg[3],
					'InGame':0,
					'Away':0,
					'Rank':0,
					'Moderator':0,
					'Bot':0,
					'InBattle':0,
				}
			else:
				self.Debug ('ERROR::User exsits' + str (RawData))
		elif Command == "REMOVEUSER":
			if self.Users.has_key (Arg[0]):
				del (self.Users[Arg[0]])
			else:
				self.Debug ('ERROR::User doesn\'t exist::' + str (RawData))
		elif Command == "CLIENTSTATUS":
			if self.Users.has_key (Arg[0]):
				self.Users[Arg[0]]["InGame"] = Arg[1][0]
				self.Users[Arg[0]]["Away"] = Arg[1][1]
				self.Users[Arg[0]]['Rank'] = Arg[1][4] * 4 + Arg[1][3] * 2 + Arg[1][2]
				self.Users[Arg[0]]['Moderator'] = Arg[1][5]
				self.Users[Arg[0]]['Bot'] = Arg[1][6]
			else:
				self.Debug ('ERROR::User doesn\'t exsits::' + str (RawData))
		elif Command == 'BATTLEOPENED':
			if not self.Battles.has_key (Arg[0]):
				self.Battles[Arg[0]] = {
					'ID':Arg[0],
					'Type':{0:'B', 1:'R'}[Arg[1]],
					'Nat':Arg[2],
					'Founder':Arg[3],
					'IP':Arg[4],
					'Port':Arg[5],
					'MaxPlayers':Arg[6],
					'Passworded':Arg[7],
					'MinRank':Arg[8],
					'MapHash':Arg[9],
					'Map':Arg[10],
					'Title':Arg[11],
					'Mod':Arg[12],
					'Users':[Arg[3]],
					'Spectators':0,
					'Players':0,
					'Locked':0,
				}
				self.Users[Arg[3]]['InBattle'] = Arg[0]
				self.SmurfDetection (Arg[3], Arg[4])
			else:
				self.Debug ('ERROR::Battle exsits::' + str (RawData))
		elif Command == 'OPENBATTLE':
			self.BattleID = Arg[0]
			self.Users[self.User]['InBattle'] = Arg[0]
			self.BattleUsers[self.User] = {
				'Spectator':1,
				'Password':'Humbug',
				'Team':None,
				'Ally':None,
				'Side':None,
				'Color':'000000',
				'Handicap':None,
				'Synced':1,
				'AI':0,
				'AIOwner':None,
				'AIDLL':None,
			}
		elif Command == 'JOINEDBATTLE':
			if self.Battles.has_key (Arg[0]):
				self.Battles[Arg[0]]['Users'].append (Arg[1])
				self.Battles[Arg[0]]['Players'] = len (self.Battles[Arg[0]]['Users']) - self.Battles[Arg[0]]['Spectators']
				if Arg[0] == self.BattleID:
					self.BattleUsers[Arg[1]] = {
						'Password':Arg[2],
						'AI':0,
						'AIOwner':None,
						'AIDLL':None,
					}
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
			if self.Users.has_key (Arg[1]):
				self.Users[Arg[1]]['InBattle'] = Arg[0]
			else:
				self.Debug ('ERROR::User doesn\'t exsits::' + str (RawData))
		elif Command == "LEFTBATTLE":
			if (self.Battles.has_key (Arg[0])):
				self.Battles[Arg[0]]['Users'].remove (Arg[1])
				self.Battles[Arg[0]]['Players'] = len (self.Battles[Arg[0]]['Users']) - self.Battles[Arg[0]]['Spectators']
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
			if self.Users.has_key (Arg[1]):
				self.Users[Arg[1]]['InBattle'] = 0
			else:
				self.Debug ('ERROR::User doesn\'t exsits::' + str (RawData))
		elif Command == "BATTLECLOSED":
			if self.Battles.has_key (Arg[0]):
				del (self.Battles[Arg[0]])
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
		elif Command == 'UPDATEBATTLEINFO':
			if self.Battles.has_key (Arg[0]):
				self.Battles[Arg[0]]['Spectators'] = Arg[1]
				self.Battles[Arg[0]]['Players'] = len (self.Battles[Arg[0]]['Users']) - Arg[1]
				self.Battles[Arg[0]]['Locked'] = Arg[2]
				self.Battles[Arg[0]]['MapHash'] = Arg[3]
				self.Battles[Arg[0]]['Map'] = Arg[4]
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
		elif Command == 'SAIDPRIVATE' or Command == 'SAID' or Command == 'SAIDEX' or Command == 'SAIDBATTLE' or Command == 'SAIDBATTLEEX' or Command == 'SAIDPRIVATEEX':
			if Arg[0] != self.User:
				self.CallbackChat (Command, Arg)
		elif Command == 'REQUESTBATTLESTATUS':
			self.Send ('MYBATTLESTATUS 4194304 000000')
		elif Command == 'JOINBATTLEREQUEST':
			self.Send ('JOINBATTLEACCEPT ' + str (Arg[0]))
			self.SmurfDetection (Arg[0], Arg[1])
		elif Command == 'CLIENTBATTLESTATUS':
			self.BattleUsers[Arg[0]]['Ready'] = int (Arg[1][1])
			self.BattleUsers[Arg[0]]['Team'] = int (Arg[1][5]) * 8 + int (Arg[1][4]) * 4 + int (Arg[1][3]) * 2 + int (Arg[1][2])
			self.BattleUsers[Arg[0]]['Ally'] = int (Arg[1][9]) * 8 + int (Arg[1][8]) * 4 + int (Arg[1][7]) * 2 + int (Arg[1][6])
			self.BattleUsers[Arg[0]]['Spectator'] = {0:1, 1:0}[int (Arg[1][10])]
			self.BattleUsers[Arg[0]]['Handicap'] = int (Arg[1][17]) * 64 + int (Arg[1][16]) * 32 + int (Arg[1][15]) * 16 + int (Arg[1][14]) * 8 + int (Arg[1][13]) * 4 + int (Arg[1][12]) * 2 + int (Arg[1][11])
			self.BattleUsers[Arg[0]]['Synced'] = int (Arg[1][23]) * 2 + int (Arg[1][22])
			self.BattleUsers[Arg[0]]['Side'] = int (Arg[1][27]) * 8 + int (Arg[1][26]) * 4 + int (Arg[1][25]) * 2 + int (Arg[1][24])
			self.BattleUsers[Arg[0]]['Color'] = self.ToHexColor (Arg[2])
		elif Command == 'JOIN':
			self.Channels[Arg[0]] = {'Users':{}}
		elif Command == 'CLIENTS':
			for User in Arg[1].split (' '):
				self.Channels[Arg[0]]['Users'][User] = User
		elif Command == 'JOINED':
			self.Channels[Arg[0]]['Users'][Arg[1]] = Arg[1]
		elif Command == 'LEFT':
			del (self.Channels[Arg[0]]['Users'][Arg[1]])
		elif Command == 'ADDBOT':
			if Arg[0] == self.BattleID:
				self.Battles[Arg[0]]['Users'].append (Arg[1])
				self.BattleUsers[Arg[1]] = {
					'AI':1,
					'AIOwner':Arg[2],
					'AIDLL':Arg[5],
					'Ready':int (Arg[3][1]),
					'Team':int (Arg[3][5]) * 8 + int (Arg[3][4]) * 4 + int (Arg[3][3]) * 2 + int (Arg[3][2]),
					'Ally':int (Arg[3][9]) * 8 + int (Arg[3][8]) * 4 + int (Arg[3][7]) * 2 + int (Arg[3][6]),
					'Spectator':{0:1, 1:0}[int (Arg[3][10])],
					'Handicap':int (Arg[3][17]) * 64 + int (Arg[3][16]) * 32 + int (Arg[3][15]) * 16 + int (Arg[3][14]) * 8 + int (Arg[3][13]) * 4 + int (Arg[3][12]) * 2 + int (Arg[3][11]),
					'Synced':int (Arg[3][23]) * 2 + int (Arg[3][22]),
					'Side':int (Arg[3][27]) * 8 + int (Arg[3][26]) * 4 + int (Arg[3][25]) * 2 + int (Arg[3][24]),
					'Color':self.ToHexColor (Arg[4]),
				}
		elif Command == 'REMOVEBOT':
			if self.Battles.has_key (Arg[0]):
				self.Battles[Arg[0]]['Users'].remove (Arg[1])
			else:
				self.Debug ('ERROR::Battle doesn\'t exsits::' + str (RawData))
		elif Command == 'DENIED':
			self.Debug ('DENIED::' + str (Arg[0]))
		elif Command == 'UPDATEBOT':
			if Arg[0] == self.BattleID:
				self.BattleUsers[Arg[1]]['Ready'] = int (Arg[2][1])
				self.BattleUsers[Arg[1]]['Team'] = int (Arg[2][5]) * 8 + int (Arg[2][4]) * 4 + int (Arg[2][3]) * 2 + int (Arg[2][2])
				self.BattleUsers[Arg[1]]['Ally'] = int (Arg[2][9]) * 8 + int (Arg[2][8]) * 4 + int (Arg[2][7]) * 2 + int (Arg[2][6])
				self.BattleUsers[Arg[1]]['Spectator'] = {0:1, 1:0}[int (Arg[2][10])]
				self.BattleUsers[Arg[1]]['Handicap'] = int (Arg[2][17]) * 64 + int (Arg[2][16]) * 32 + int (Arg[2][15]) * 16 + int (Arg[2][14]) * 8 + int (Arg[2][13]) * 4 + int (Arg[2][12]) * 2 + int (Arg[2][11])
				self.BattleUsers[Arg[1]]['Synced'] = int (Arg[2][23]) * 2 + int (Arg[2][22])
				self.BattleUsers[Arg[1]]['Side'] = int (Arg[2][27]) * 8 + int (Arg[2][26]) * 4 + int (Arg[2][25]) * 2 + int (Arg[2][24])
				self.BattleUsers[Arg[1]]['Color'] = self.ToHexColor (Arg[3])
		elif Command == 'SERVERMSG':
			if Arg[0][0:35] == 'You\'ve been kicked from server by <':
				self.AllowReConnect = 0
				print 'KICKED FROM SERVER'
				print Arg[0]
		
		
		if self.Commands.has_key (Command):
			self.CallbackEvent (Command, Arg)
	
	
	def Login (self):
		self.Debug ()
		self.Send ("LOGIN " + str (self.User) + " " + str (base64.b64encode (binascii.a2b_hex (hashlib.md5 (self.Passwd).hexdigest ()))) + " 0 " + str (self.IP) + " DoxBot\t\ta b sp", 1)
		
	
	def BattleOpen (self, Mod, ModHash, Map, MapHash, Title, MaxPlayers, MinRank = 0, Password = '*', Type = 0, Nat = 0):
		self.Send ("OPENBATTLE " + str (Type) + ' ' + str (Nat) + ' ' + str (Password) + ' ' + str (self.BattlePort) + ' ' + str (MaxPlayers) + ' ' + str (ModHash) + ' ' + str (MinRank) + ' ' + str (MapHash) + ' ' + str (Map) + '\t' + str (Title) + '\t' + str (Mod))
		
	
	def BattleClose (self):
		self.Send ('LEAVEBATTLE')
	
	
	def BattleMap (self, Map, MapHash):
		self.Battles[self.BattleID]['Map'] = Map
		self.Battles[self.BattleID]['MapHash'] = MapHash
		self.BattleUpdate ()
	
	
	def BattleSay (self, Message, Me = 0):
		if Me:
			self.Send ('SAYBATTLEEX ' + str (Message))
		else:
			self.Send ('SAYBATTLE ' + str (Message))
	
	
	def BattleStart (self):
		self.Send ('MYSTATUS 1')
	
	
	def BattleStop (self):
		self.Send ('MYSTATUS 0')
	
	
	def BattleLock (self, Lock):
		if self.Battles[self.BattleID]['Locked'] != Lock:
			self.Battles[self.BattleID]['Locked'] = Lock
			self.BattleUpdate ()
	
	
	def BattleUpdate (self):		
		self.Send ('UPDATEBATTLEINFO ' + str (self.Battles[self.BattleID]['Spectators']) + ' ' + str (self.Battles[self.BattleID]['Locked']) + ' ' + str (self.Battles[self.BattleID]['MapHash']) + ' ' + str (self.Battles[self.BattleID]['Map']))
	
	
	def BattleKick (self, User):
		self.Send ('KICKFROMBATTLE ' + str (User))
	
	
	def BattleAddAI (self, Command):
		self.Send (Command)
	
	
	def BattleKickAI (self, AI):
		self.Send ('REMOVEBOT ' + str (AI))
	
	
	def BattleForceID (self, User, ID):
		self.Send ('FORCETEAMNO ' + str (User) + ' ' + str (ID))
	
	
	def BattleForceTeam (self, User, Team):
		self.Send ('FORCEALLYNO ' + str (User) + ' ' + str (Team))
	
	
	def BattleRing (self, User):
		self.Send ('RING ' + str (User))
	
	
	def BattleAddBox (self, Ally, Left, Top, Right, Bottom):
		self.Send ('ADDSTARTRECT ' + str (Ally) + ' ' + str (Left) + ' ' + str (Top) + ' ' + str (Right) + ' ' + str (Bottom))
	
	
	def UserSay (self, User, Message):
		self.Send ('SAYPRIVATE ' + str (User) + ' ' + str (Message))
	
	
	def ChannelJoin (self, Channel, Password = ''):
		self.Send ('JOIN ' + str (Channel))
	
	
	def BattleUpdateAI (self, AI, BattleStatus, Color):
		self.Send ('UPDATEBOT ' + str (AI) + ' ' + str (BattleStatus) + ' ' + str (Color))
	
	
	def BattleHandicap (self, User, Handicap):
		self.Send ('HANDICAP ' + str (User) + ' ' + str (Handicap))
	
	
	def BattleUpdateScript (self, Tags):
		Script = ''
		for Tag in Tags:
			Script = Script + Tag[0] + '=' + str (Tag[1]) + '\t'
		self.Send ('SETSCRIPTTAGS ' + Script[0:-1])
	
	
	def Ping (self):
		self.Send ('PING')
	
	
	def Send (self, Command, Force = 0):
		if self.LoggedIn or Force == 1:
			self.Debug ("SEND::" + str (Command))
			self.Socket.send (Command + "\n")
		else:
			self.Debug ("SEND_QUEUE::" + str (Command))
			self.LoggedInQueue.append (Command)
	
	
	def Connect (self):
		self.Debug ()
		self.Socket.connect ((str (self.HostIP), int (self.HostPort)))
		self.Active = 1
		self.SetIP ()
		self.ClassPing = LobbyPing (self, self.Ping, self.Debug)
		self.Users = {}
		self.Battles = {}
		self.BattleUsers = {}
		self.BattleID = 0
		self.Channels = {}
	
	
	def Disconnect (self):
		self.Debug ()
		self.Active = 0
		self.Socket.shutdown (2)
		self.Socket.close ()
	
	
	def SetLoggedIn (self):
		self.Debug ()
		self.LoggedIn = 1
		if len (self.LoggedInQueue):
			for Command in self.LoggedInQueue:
				self.Send (Command)
			self.LoggedInQueue = []
		self.ClassPing.start ()
	
	
	def dec2bin (self, value, numdigits):
		val = int (value)
		digits = [0 for i in range (numdigits)]
		for i in range (numdigits):
			val, digits[i] = divmod (val, 2)
		return (digits)
	
	
	def ToHexColor (self, iColor):
		Color = "%X" % int (iColor)
		while (len (Color) < 6):
			Color = str (0) + Color
		Color = Color[4:6] + Color[2:4] + Color[0:2]
		return (Color)
	
	
	def ReturnValue (self, String, StopChar):
		if String.find (StopChar) != -1:
			return (String[0:String.find (StopChar)])
		return (String)
	
	
	def SmurfDetection (self, User, IP):
		Ignore = 1
#		self.Debug ('SMURF_DATA::' + User + '::' + IP)
	
	
	def SetIP (self):
		self.Debug ()
		try:
			self.IP = self.Socket.getsockname ()[0]
		except:
			try:
				self.IP = [IP for IP in socket.gethostbyname_ex (socket.gethostname ())[2] if not IP.startswith ("127.")][0]
			except:
				self.IP = '127.0.0.1'	#fallback
		self.Debug ('IP:' + str (self.IP))
	
	
	def Terminate (self):
		self.Debug ()
		self.AllowReConnect = 0
		self.ClassPing.Terminate ()
		self.Disconnect ()
	
	
	def ReConnect (self):
		self.Debug ()
		self.LoggedIn = 0
		self.Active = 0
		SleepTime = 1
		while not self.Active and self.AllowReConnect:
			self.Disconnect ()
			self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.Connect ()
			time.sleep (SleepTime)
			SleepTime = min (60, SleepTime + 2)


class LobbyPing (threading.Thread):
	def __init__ (self, ClassLobby, FunctionPing, FunctionDebug):
		threading.Thread.__init__ (self)
		self.Lobby = ClassLobby
		self.Ping = FunctionPing
		self.Debug = FunctionDebug
		self.SleepCounter = 0
		self.Active = 0
	
	
	def run (self):
		self.Debug ('Lobby Ping start')
		self.Active = 1
		self.SleepCounter = 0
		while self.Lobby.Active and self.Active:
			if self.SleepCounter == 25:
				self.SleepCounter = 0
				self.Ping ()
			self.SleepCounter = self.SleepCounter + 1
			time.sleep (1)
		self.Debug ('LobbyPing run finnished')
	
	
	def Terminate (self):
		self.Debug ()
		self.Active = 0