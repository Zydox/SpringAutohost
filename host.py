# -*- coding: ISO-8859-1 -*-
import threading
import time
import sys
import re
import lobby
import hostCmds
import spring


class Host (threading.Thread):
	def __init__ (self, ID, Group, ClassServer, GroupConfig, AccountConfig):
		threading.Thread.__init__ (self)
		self.ID = ID
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('INFO', 'Host Init')
		self.Group = Group
		self.GroupConfig = GroupConfig
		self.LogicTest = self.Server.LogicTest
		self.SpringVersion = self.GetSpringVersion ()
		self.Lobby = lobby.Lobby (self.Debug, self.HandleInput, self.HandleEvent, self.HandleLocalEvent, dict (AccountConfig, **{'LobbyHost':ClassServer.Config['General']['LobbyHost'], 'LobbyPort':ClassServer.Config['General']['LobbyPort']}))
		self.HostCmds = hostCmds.HostCmds (ClassServer, self)
		self.Spring = spring.Spring (ClassServer, self, self.Lobby, AccountConfig['UDPPort'])
		self.UserRoles = {}		# [User][Role] = 1
		self.Battle = {
			'Mod':self.GroupConfig['Mod'],
			'Map':self.GroupConfig['Map'],
			'BattleDescription':self.GroupConfig['BattleDescription'],
			'StartPosType':None,
			'MapOptions':{},
			'ModOptions':{},
			'Teams':2,
		}
		
	
	def run (self):
		self.Debug ('INFO', 'Start host')
		if not self.LogicTest:
			self.Lobby.start ()
			if len (self.GroupConfig['LobbyChannels']) > 0:
				for Channel in self.GroupConfig['LobbyChannels'].split (','):
					self.Lobby.ChannelJoin (Channel)
		self.SetDefaultMod ()
		self.HostCmds.HostCmdsBattle.Logic.LogicFunctionBattleLoadDefaults ()
		self.Debug ('INFO', 'Run finnished')
	
	
	def HandleEvent (self, Event, Data):
		self.Debug ('DEBUG', 'HandleEvent::' + str (Event) + '::' + str (Data))
		if Event == 'DENIED':
			self.Terminate ('LOGIN_DENIED::' + str (Data[0]))
		
		if self.GroupConfig.has_key ('Events') and self.GroupConfig['Events'].has_key (Event):
			for Command in self.GroupConfig['Events'][Event]:
				self.HandleInput ('INTERNAL', '!' + Command)
		
		if Event == 'OPENBATTLE':	# Load the default settings for a battle
			self.HostCmds.HostCmdsBattle.Logic.LogicFunctionBattleUpdateScript ()
	
	
	def HandleLocalEvent (self, Event, Data):
		self.Debug ('DEBUG', Event + str (Data))
		if Event == 'SMURF_DETECTION':
			self.Server.HandleDB.StoreSmurf (Data[0], Data[1], Data[2], Data[3], Data[4])
		elif Event == 'USER_JOINED_BATTLE':
			if self.Spring.SpringUDP and self.Spring.SpringUDP.Active:
				self.Spring.SpringUDP.AddUser (Data[0], Data[1])
		elif Event == 'USER_LEFT_BATTLE':
			pass
		else:
			print ''
			print Event
			print Data
	
	
	def HandleInput (self, Source, Data, User = None):
		self.Debug ('DEBUG', 'HandleInput::' + str (Source) + '::' + str (Data))
		
		Input = {'Raw':Source + ' ' + ' '.join (Data), 'Reference':None}
		if Source == 'SAIDPRIVATE':
			Input['Source'] = 'PM'
			Input['Return'] = 'PM'
			Input['User'] = Data[0]
			Input['Reference'] = Data[0]
			Input['Input'] = Data[1]
		elif Source == 'SAIDBATTLE':
			Input['Source'] = 'Battle'
			Input['Return'] = 'BattleMe'
			Input['User'] = Data[0]
			Input['Reference'] = Data[0]
			Input['Input'] = Data[1]
			if self.Lobby.BattleID and self.GroupConfig['PassthoughBattleLobbyToSpring']:
				self.Spring.SpringTalk ('<' + Input['User'] + '> ' + Input['Input'])
		elif Source == 'INTERNAL':
			Input['Source'] = 'Battle'
			Input['Return'] = 'BattleMe'
			Input['User'] = User
			Input['Reference'] = ''
			Input['Input'] = Data
		elif Source == 'INTERAL_RETURN':
			Input['Source'] = 'PM'
			Input['Return'] = 'Return'
			Input['User'] = User
			Input['Reference'] = ''
			Input['Input'] = Data
		elif Source == 'BATTLE_PUBLIC':
			Input['Source'] = 'GameBattle'
			Input['Return'] = 'BattleMe'
			Input['User'] = User
			Input['Reference'] = User
			Input['Input'] = Data
		elif Source == 'SAIDBATTLEEX':
			Input['Source'] = 'BattleMe'
			Input['Return'] = 'BattleMe'
			Input['User'] = Data[0]
			Input['Reference'] = Data[0]
			Input['Input'] = self.ConvertSuggestion (Data[1])
		elif Source == 'INTERNAL_ALIAS_BATTLE':
			Input['Source'] = 'Battle'
			Input['Return'] = 'BattleMe'
			Input['User'] = User
			Input['Reference'] = User
			Input['Input'] = Data
		elif Source == 'INTERNAL_ALIAS_PM':
			Input['Source'] = 'PM'
			Input['Return'] = 'PM'
			Input['User'] = User
			Input['Reference'] = User
			Input['Input'] = Data
		
		if len (Input) > 2:
			if self.Lobby.ReturnValue (Input['Input'], ' ')[0:1] == '!':
				Input['Command'] = self.Lobby.ReturnValue (Input['Input'], ' ')[1:]
				Input['RawData'] = Input['Input'][len (Input['Command']) + 2:]
				Input['Data'] = []
				
				if self.HostCmds.Commands.has_key (Input['Command']):
					Data = Input['RawData']
					Failed = 0
					if Source == 'INTERAL_RETURN':
						Input['Return'] = 'Return'
					elif self.HostCmds.Commands[Input['Command']][1] == 'Source':
						if Input['Source'] == 'Battle':
							Input['Return'] = 'BattleMe'
						else:
							Input['Return'] = Input['Source']
					else:
						Input['Return'] = self.HostCmds.Commands[Input['Command']][1]
					
					for Field in self.HostCmds.Commands[Input['Command']][0]:
						NewArg = ''
						if Field == '*' or (Field == 'O*' and len (Data) > 0):
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
						elif Field[0] == 'V' and len (Field) > 1:
							try:
								NewArg = self.Lobby.ReturnValue (Data, ' ')
								if len (NewArg) != int (Field[1:]):
									Failed = 'Variable not the correct length'
							except:
								NewArg = 'Faulty variable'
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
						Input['Message'] = 'ERROR:' + str (Field) + '::' + Failed
					elif len (Data) > 0:
						Input['Message'] = 'TO MUCH DATA/BAD DATA'
					else:
						Input = self.HandleAccess (Input, Source)
				else:
					Input['Message'] = ['UNKNOWN COMMAND ("' + str (Input['Command']) + '")', 'Use !help to list the available commands']
					Input['Return'] = 'PM'
			else:
				Input['Message'] = ''	# Everything which doesn't start with ! ?
			
			if Input['Return'] == 'Return':
				return (Input['Message'])
			
			self.ReturnInput (Input)
	
	
	def HandleAccess (self, Input, Source = ''):
		self.Debug ('DEBUG', 'HandleAccess::' + str (Input['User']) + '::' + str (Input['Command']))
		OK = 0
		if Source == 'INTERNAL' or Source == 'INTERAL_RETURN':
			OK = 1
		elif self.Server.AccessCommands[self.Group].has_key (Input['Command']):
			for Group in self.Server.AccessCommands[self.Group][Input['Command']]:
				if Group == '%BattlePlayer%':
					if self.Lobby.BattleUsers.has_key (Input['User']) and self.Lobby.BattleUsers[Input['User']]['Spectator'] == 0:
						OK = 1
				elif Group == '%BattleSpectator%':
					if self.Lobby.BattleUsers.has_key (Input['User']) and self.Lobby.BattleUsers[Input['User']]['Spectator'] == 1:
						OK = 1
				elif Group == '%GamePlayer%':
					OK = self.Spring.UserIsPlaying (Input['User'])
				elif Group == '%GameSpectator%':
					OK = self.Spring.UserIsSpectating (Input['User'])
				elif self.Server.AccessRoles[self.Group].has_key (Group):
					if self.Server.AccessRoles[self.Group][Group].has_key (Input['User']):
						OK = 1
				if OK:
					break
		else:
			self.Debug ('INFO', 'HandleAccess::NO_AUTH_CHECK::' + str (Input['Command']))
			OK = 1
		
		if Source == 'INTERNAL_AUTH_CHECK':
			return (OK)
		
		self.Debug ('DEBUG', 'HandleAccessResult::' + str (Input['User']) + '::' + str (Input['Command']) + '==' + str (OK))
		if OK:
			Input['Message'] = self.HostCmds.HandleInput (Input['Source'], Input['Command'], Input['Data'], Input['User'])
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
		
		if Messages and len (Messages) > 0:
			for Message in Messages:
				if Message and len (Message) > 0:
					if Data['Return'] == 'PM':
						self.Lobby.UserSay (Data['Reference'], Message)
					elif Data['Return'] == 'Battle':
						self.Lobby.BattleSay (Message, 0)
					elif Data['Return'] == 'BattleMe':
						self.Lobby.BattleSay (Message, 1)
					elif Data['Return'] == 'GameBattle':
						self.Spring.SpringTalk (Message)
	
	
	def ConvertSuggestion (self, Data):
		Info = Data.split (' ')
		if Info[0] == 'suggests':
			if Info[1] == 'that':
				if Info[3] == 'changes' and Info[4] == 'to' and Info[5] == 'ally':
					Data = '!team ' + Info[2] + ' ' + re.sub ('\D', '', Info[6])
				elif Info[3] == 'changes' and Info[4] == 'to' and Info[5] == 'team':
					Data = '!id ' + Info[2] + ' ' + re.sub ('\D', '', Info[6])
				elif Info[3] == 'becomes' and Info[4] == 'a' and Info[5] == 'spectator.':
					Data = '!spec ' + Info[2]
			else:
				Data = '!map ' + Data[9:]
		elif Info[0] == 'thinks' and Info[2] == 'should':
			if Info[3] == 'leave.':
				Data = '!kick ' + Info[1]
			elif Info[3] == 'get' and Info[4] == 'a' and Info[6] == 'resource' and Info[7] == 'bonus':
				Data = '!hcp ' + Info[1] + ' ' + re.sub ('\D', '', Info[5])
		elif Info[0] == 'sugests' and Info[1] == 'that' and Info[3] == 'changes' and Info[4] == 'colour.':
			Data = '!fixcolor ' + Info[2]
		return (Data)
	
	
	def GetSpringVersion (self):
		if self.GroupConfig.has_key ('SpringBuild') and self.GroupConfig['SpringBuild']:
			Version = self.GroupConfig['SpringBuild']
		elif  self.Server.Config['General'].has_key ('SpringBuildDefault'):
			Version = self.Server.Config['General']['SpringBuildDefault']
		else:
			Version = 'Default'
		self.Debug ('INFO', Version)
		return (Version)
	
	
	def GetUnitsyncMod (self, Mod = None):
		if not Mod:
			Mod = self.Battle['Mod']
		if self.Server.SpringUnitsync.Mods.has_key (self.SpringVersion):
			if self.Server.SpringUnitsync.Mods[self.SpringVersion].has_key (Mod):
				return (self.Server.SpringUnitsync.Mods[self.SpringVersion][Mod])
			elif Mod == '#KEYS#':
				return (self.Server.SpringUnitsync.Mods[self.SpringVersion].keys ())
	
	
	def GetUnitsyncMap (self, Map = None):
		if not Map:
			Map = self.Battle['Map']
		if self.Server.SpringUnitsync.Maps.has_key (self.SpringVersion):
			if self.Server.SpringUnitsync.Maps[self.SpringVersion].has_key (Map):
				return (self.Server.SpringUnitsync.Maps[self.SpringVersion][Map])
			elif Map == '#KEYS#':
				return (self.Server.SpringUnitsync.Maps[self.SpringVersion].keys ())
	
	
	def GetSpringBinary (self, Headless = 0):
		self.Debug ('INFO')
		if self.Server.Config['General'].has_key ('PathSpringBuilds'):
			Spring = self.Server.Config['General']['PathSpringBuilds'] + 'Version_' + str (self.SpringVersion)
		
			if Headless:
				Spring = Spring + '/spring-headless'
			else:
				Spring = Spring + '/spring-dedicated'
		self.Debug ('INFO', Spring)
		return (Spring)
	
	
	def SetDefaultMod (self):
		self.Debug ('INFO', 'Mod::' + str (self.Battle['Mod']))
		pattern = re.compile(self.Battle['Mod'])
		List = []
		for Mod in self.Server.SpringUnitsync.Mods[self.SpringVersion].keys ():
			if pattern.match (Mod):
				List.append (Mod)
		if len (List) > 0:
			List.sort (reverse=True)
			self.Battle['Mod'] = List[0]
			self.Debug ('INFO', 'Mod::' + str (self.Battle['Mod']))
		else:
			self.Debug ('WARNING', 'No default mod found')
	
	
	def Terminate (self, Reason = '', Info = ''):
		self.Debug ('INFO', str (Reason) + '::' + str (Info))
		self.Spring.Terminate ()
		self.Lobby.Terminate ()
		self.Server.RemoveHost (self.ID)