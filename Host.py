# -*- coding: ISO-8859-1 -*-
import Lobby
import threading
import time
import HostCmds
import Spring


class Host (threading.Thread):
	def __init__ (self, ClassServer, Group, HostAccount):
		threading.Thread.__init__ (self)
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('Host Init')
		self.Lobby = Lobby.Lobby (ClassServer, self.HandleInput, self.HandleEvent, HostAccount)
		self.Group = Group
		self.HostCmds = HostCmds.HostCmds (ClassServer, self)
		self.Spring = Spring.Spring (ClassServer, self.Lobby)
		self.UserRoles = {}		# [User][Role] = 1
		
	
	def run (self):
		self.Debug ('Start host')
		self.Lobby.start ()
		if len (self.Server.Groups[self.Group]['ChannelsReport']) > 0:
			for Channel in self.Server.Groups[self.Group]['ChannelsReport']:
				self.Lobby.ChannelJoin (Channel[0])
		
		self.HostBattle ()
	
	
	def HandleEvent (self, Event, Data):
#		self.Debug ('HandleEvent::' + str (Event) + '::' + str (Data))
		if Event == 'ADDUSER' or Event == 'REMOVEUSER' or Event == 'CLIENTBATTLESTATUS':
			self.SetAccessRoles (Data[0])
		elif (Event == 'JOINEDBATTLE' or Event == 'LEFTBATTLE' or Event == 'LEFTBATTLE') and Data[0] == self.Lobby.BattleID:
			self.SetAccessRoles (Data[1])
		
	
	def HandleInput (self, Source, Data):
		self.Debug ('HandleInput::' + str (Source) + '::' + str (Data))
		
		Input = {'Raw':Source + ' ' + ' '.join (Data), 'Reference':None}
		if (Source == 'SAIDPRIVATE'):
			Input['Source'] = 'PM'
			Input['Return'] = 'PM'
			Input['User'] = Data[0]
			Input['Reference'] = Data[0]
			Input['Input'] = Data[1]
		elif (Source == 'SAIDBATTLE'):
			Input['Source'] = 'Battle'
			Input['Return'] = 'BattleMe'
			Input['User'] = Data[0]
			Input['Reference'] = Data[0]
			Input['Input'] = Data[1]
		
		if (len (Input) > 2):
			if self.Lobby.ReturnValue (Input['Input'], ' ')[0:1] == '!':
				Input['Command'] = self.Lobby.ReturnValue (Input['Input'], ' ')[1:]
				Input['RawData'] = Input['Input'][len (Input['Command']) + 2:]
				Input['Data'] = []
			
				if self.HostCmds.Commands.has_key (Input['Command']):
					Data = Input['RawData']
					Failed = 0
					for Field in self.HostCmds.Commands[Input['Command']][0]:
						NewArg = ''
						if self.HostCmds.Commands[Input['Command']][1] == 'Source':
							Input['Return'] = Input['Source']
						else:
							Input['Return'] = self.HostCmds.Commands[Input['Command']][1]
						if (Field == '*' or (Field == 'O*' and len (Data) > 0)):
							NewArg = Data
							if Field == '*' and len (NewArg) < 1:
								Failed = 'Missing data'
						elif Field == 'I' or (Field == 'OI' and len (Data) > 0):
							try:
								NewArg = int (self.Lobby.ReturnValue (Data, ' '))
							except:
								Failed = 'INT field not numeric'
						elif Field == 'V' or (Field == 'OV' and len (Data) > 0):
							NewArg = self.Lobby.ReturnValue (Data, ' ')
							if Field == 'V' and len (NewArg) < 1:
								Failed ='Missing variable'
						elif Field == 'B' or (Field == 'OB' and len (Data) > 0):
							try:
								NewArg = int (self.Lobby.ReturnValue (Data, ' '))
								if NewArg != 0 and NewArg != 1:
									Failed = 'BOOL field not 0 or 1'
							except:
								Failed = 'BOOL CONVERSION FAILED'
						elif len (Data) == 0 and (Field == 'OI' or Field == 'OV' or Field == 'OB' or Field == 'O*'):
							NewArg = ''
						else:
							Failed = 'UNKNOWN INPUT TYPE::' + str (Field)
						if len (str (NewArg)) > 0:
							Input['Data'].append (NewArg)
							Data = Data[len (str (NewArg)) + 1:]
					
					if Failed:
						Input['Message'] = Failed
					elif len (Data) > 0:
						Input['Message'] = 'TO MUCH DATA/BAD DATA'
					else:
						Input = self.HandleAccess (Input)
				else:
					Input['Message'] = ['UNKNOWN COMMAND ("' + str (Input['Command']) + '")', 'Use !help to list the available commands']
					Input['Return'] = 'PM'
			else:
				Input['Message'] = ''	# Everything which doesn't start with ! ?
			
			self.ReturnInput (Input)
			print (Input)
	
	
	def HandleAccess (self, Input):
		OK = 0
		if self.Server.AccessCommands.has_key (Input['Command']):
			if self.UserRoles.has_key (Input['User']):
				for Role in self.Server.AccessCommands[Input['Command']]:
					if self.UserRoles[Input['User']].has_key (Role):
						OK = 1
		else:
			self.Debug ('HandleAccess::NO_AUTH_CHECK::' + str (Input['Command']))
			OK = 1
		
		if OK:
			Input['Message'] = self.HostCmds.HandleInput (Input['Source'], Input['Command'], Input['Data'])
		else:
			Input['Message'] = 'Missing auth for command "' + str (Input['Command']) + '"'
			Input['Return'] = 'PM'
		return (Input)

	
	
	def ReturnInput (self, Data):
		Messages = []
		if isinstance (Data['Message'], str):
			Messages = [Data['Message']]
		elif isinstance (Data['Message'], list):
			Messages = Data['Message']
		
		if len (Messages) > 0:
			for Message in Messages:
				if len (Message) > 0:
					if Data['Return'] == 'PM':
						self.Lobby.UserSay (Data['Reference'], Message)
					elif Data['Return'] == 'Battle':
						self.Lobby.BattleSay (Message, 0)
					elif Data['Return'] == 'BattleMe':
						self.Lobby.BattleSay (Message, 1)
	
	
	# Function which is called when a users access roles should be re-calculated
	def SetAccessRoles (self, User):
#		self.Debug ('SetAccessRoles::' + str (User))
		if self.UserRoles.has_key (User):
			self.UserRoles[User] = {}
		
		if self.Lobby.Users.has_key (User) and not User == self.Lobby.User:
			for Role in self.Server.AccessRoles:
				if self.Server.AccessRoles[Role].has_key (User):
					if self.UserRoles.has_key (User):
						self.UserRoles[User][Role] = 1
					else:
						self.UserRoles[User] = {Role:1}
			if self.Lobby.BattleUsers.has_key (User) and self.Lobby.BattleUsers[User].has_key ('Spectator'):
				if self.Lobby.BattleUsers[User]['Spectator']:
					self.UserRoles[User]['%BattleSpectator%'] = 1
				else:
					self.UserRoles[User]['%BattlePlayer%'] = 1
			
		if self.UserRoles.has_key (User):
			print ('USER WITH ACCESS ROLES (' + str (User) + ')')
			print (self.UserRoles[User])
			print (self.UserRoles)
	
	
	def HostBattle (self):
		self.Debug ("Host battle")
		Mod = self.Server.Groups[self.Group]['Mod']
		Map = self.Server.Groups[self.Group]['Map']
		self.Lobby.BattleOpen (Mod, Map, 'Test', 16)
	

	def Debug (self, Message):
		print (Message)