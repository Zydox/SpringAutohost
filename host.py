# -*- coding: ISO-8859-1 -*-
import threading
import time
import sys
import re
import lobby
import hostCmds
import spring
from doxFunctions import *


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
		self.CommandThreads = {}
		self.CommandThreadID = 0
		self.CommandSeen = {}
		self.IsMaster = False
	
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
		
		# Gets and releases the Master lock for the Host thread...
		self.Server.GetMasterLock (self)
		while (self.IsMaster):
			time.sleep (1)
		self.Server.ReleaseMasterLock (self)
	
	
	def HandleEvent (self, Event, Data):
		self.Debug ('DEBUG', 'HandleEvent::' + str (Event) + '::' + str (Data))
		self.CommandSeen[Event] = 1
		if Event == 'DENIED':
			self.Terminate ('LOGIN_DENIED::' + str (Data[0]))
		
		if self.GroupConfig.has_key ('Events') and self.GroupConfig['Events'].has_key (Event):
			for Command in self.GroupConfig['Events'][Event]:
				self.HandleInput ('INTERNAL', '!' + Command)
		
		if Event == 'OPENBATTLE':	# Load the default settings for a battle
			self.HostCmds.HostCmdsBattle.Logic.LogicFunctionBattleUpdateScript ()
	
	
	def HandleLocalEvent (self, Event, Data):
		self.Debug ('DEBUG', Event + str (Data))
		if Event == 'SMURF_DETECTION_PUBLIC':
			if self.IsMaster:
				self.Server.HandleDB.StoreSmurf (Data[0], Data[1], Data[2], Data[3], Data[4])
		elif Event == 'SMURF_DETECTION_BATTLE':
			self.Server.HandleDB.StoreSmurf (Data[0], Data[1], Data[2], Data[3], Data[4])
		elif Event == 'USER_JOINED_BATTLE':
			if self.Spring.SpringUDP and self.Spring.SpringUDP.Active:
				self.Spring.SpringUDP.AddUser (Data[0], Data[1])
			self.HandleInput ('INTERNAL', '!sleepunsyncedmaplink ' + Data[0])
		elif Event == 'USER_LEFT_BATTLE':
			pass
		elif Event == 'BATTLE_MAP_CHANGED':
			self.HandleInput ('INTERNAL', '!sleepunsyncedmaplink')
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
		
		if len (Input) > 2:
			if self.Lobby.ReturnValue (Input['Input'], ' ')[0:1] == '!':
				self.CommandThreads[self.CommandThreadID] = HostCommand (self, self.Debug, self.CommandThreadID, Input, Source)
				self.CommandThreadID += 1
				self.HostCommandThreadCleanup ()
	
	
	def UserAccess (self, Command, User, Vote = False):
		VoteGroup = -1
		Groups = {}
		Return = False
		if self.Server.AccessCommands.has_key (self.Group) and self.Server.AccessCommands[self.Group].has_key (Command):
			if self.Lobby.BattleID and self.Lobby.Users[self.Lobby.User]['InGame']:
				if Vote:
					VoteGroup = 3
				else:
					VoteGroup = 2
			else:
				if Vote:
					VoteGroup = 1
				else:
					VoteGroup = 0
			if len (self.Server.AccessCommands[self.Group][Command]) == 4:
				for Group in self.Server.AccessCommands[self.Group][Command][VoteGroup]:
					Groups[Group] = True
			
			if Groups.has_key ('%BattlePlayer%') and self.Lobby.BattleUsers.has_key (User) and self.Lobby.BattleUsers[User]['Spectator'] == 0:
				Return = True
			elif Groups.has_key ('%BattleSpectator%') and self.Lobby.BattleUsers.has_key (User) and self.Lobby.BattleUsers[User]['Spectator'] == 1:
				Return = True
			elif Groups.has_key ('%GamePlayer%') and self.Spring.UserIsPlaying (User):
				Return = True
			elif Groups.has_key ('%GameSpectator%') and self.Spring.UserIsSpectating (User):
				Return = True
			elif self.Server.AccessUsers.has_key (self.Group) and self.Lobby.Users.has_key (User):
				for AccessLine in self.Server.AccessUsers[self.Group]:
					GroupOK = False
					for Group in AccessLine[5]:
						if Groups.has_key (Group):
							GroupOK = True
					if GroupOK:
						if AccessLine[0] == '*' or AccessLine[0] == self.Lobby.Users[User]['ID']:
							if AccessLine[1] == '*' or AccessLine[1] == User:
								if AccessLine[2] == '*' or AccessLine[2] == self.Lobby.Users[User]['Country']:
									if AccessLine[3] == '*' or AccessLine[3] == self.Lobby.Users[User]['Bot']:
										if AccessLine[4] == '*' or AccessLine[4] == self.Lobby.Users[User]['Moderator']:
											Return = True
											break
		else:
			Return = True
		print 'UserAccess::' + str (Command) + '::' + str (User) + '::' + str (Vote) + '::' + str (Return)
		return (Return)
	
	
	def HandleAccess (self, Input, Source = '', Vote = False):
		self.Debug ('DEBUG', 'HandleAccess::' + str (Input['User']) + '::' + str (Input['Command']) + '::' + str (Vote))
		OK = False
		if Source == 'INTERNAL' or Source == 'INTERAL_RETURN':
			OK = True
		else:
			OK = self.UserAccess (Input['Command'], Input['User'], Vote)
		
		if Source == 'INTERNAL_AUTH_CHECK':
			return (OK)
		elif not OK and not Vote:
			return (self.HandleAccess (Input, Source, True))
		
		self.Debug ('DEBUG', 'HandleAccessResult::' + str (Input['User']) + '::' + str (Input['Command']) + '==' + str (OK))
		if OK:
			if Vote:
				Input['Data'] = [Input['Command']] + Input['Data']
				Input['Command'] = 'vote'
			CommandReturn = self.HostCmds.HandleInput (Input['Source'], Input['Command'], Input['Data'], Input['User'], True)
			Input['CommandSuccess'] = CommandReturn[0]
			Input['Message'] = CommandReturn[1]
		else:
			Input['Message'] = 'Missing auth for command "' + str (Input['Command']) + '"'
			Input['Return'] = 'PM'
		return (Input)
	
	
	def ReturnInput (self, Data):
		# If Return is a list, the first option is for successfull command and the second for command failure
		if isinstance (Data['Return'], list) and len (Data['Return']) == 2 and Data.has_key ('CommandSuccess'):
			if Data['CommandSuccess']:
				Data['Return'] = Data['Return'][0]
			else:
				Data['Return'] = Data['Return'][1]
		
		Messages = []
		if isinstance (Data['Message'], str):
			Messages = [Data['Message']]
		elif isinstance (Data['Message'], list):
			Messages = Data['Message']
		
		if Data['Return'][-9:] == 'Requester':
			Data['Return'] = Data['Return'][0:-9]
			if Data.has_key ('User') and Data['User']:
				User = Data['User']
			else:
				User = '<Unknown>'
			Messages[0] = Messages[0] + ' (req: ' + User + ')'
		
		if Messages and len (Messages) > 0:
			for Message in Messages:
				if Message and len (Message) > 0:
					if Data['Return'] == 'PM':
						self.Lobby.UserSay (Data['Reference'], Message)
					elif Data['Return'] == 'Battle':
						self.Lobby.BattleSay (Message, 0)
						if Data['Source'] == 'PM':
							self.Lobby.UserSay (Data['Reference'], Message)
					elif Data['Return'] == 'BattleMe':
						self.Lobby.BattleSay (Message, 1)
						if Data['Source'] == 'PM':
							self.Lobby.UserSay (Data['Reference'], Message)
					elif Data['Return'] == 'GameBattle':
						self.Spring.SpringTalk (Message)
	
	
	def ConvertSuggestion (self, Data):
		Info = Data.split (' ')
		if len (Info) > 1 and Info[0] == 'suggests':
			if len (Info) > 1 and Info[1] == 'that':
				if len (Info) > 6 and Info[3] == 'changes' and Info[4] == 'to' and Info[5] == 'ally':
					Data = '!team ' + Info[2] + ' ' + re.sub ('\D', '', Info[6])
				elif len (Info) > 6 and Info[3] == 'changes' and Info[4] == 'to' and Info[5] == 'team':
					Data = '!id ' + Info[2] + ' ' + re.sub ('\D', '', Info[6])
				elif len (Info) > 5 and Info[3] == 'becomes' and Info[4] == 'a' and Info[5] == 'spectator.':
					Data = '!spec ' + Info[2]
			else:
				Data = '!map ' + Data[9:]
		elif len (Info) > 3 and Info[0] == 'thinks' and Info[2] == 'should':
			if Info[3] == 'leave.':
				Data = '!kick ' + Info[1]
			elif len (Info) > 7 and Info[3] == 'get' and Info[4] == 'a' and Info[6] == 'resource' and Info[7] == 'bonus':
				Data = '!hcp ' + Info[1] + ' ' + re.sub ('\D', '', Info[5])
		elif len (Info) > 4 and Info[0] == 'sugests' and Info[1] == 'that' and Info[3] == 'changes' and Info[4] == 'colour.':
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
		self.IsMaster = False
		self.Server.RemoveHost (self.ID)
	
	
	def HostCommandWait (self, LobbyEvent):
		self.Debug ('DEBUG', LobbyEvent)
		iSleep = 0
		self.CommandSeen[LobbyEvent] = 0
		while not self.CommandSeen[LobbyEvent]:
			iSleep += 1
			time.sleep (0.01)
			if iSleep == 1000:	# 10 seconds, breaking the wait...
				self.Debug ('WARNING', 'Breaking, timelimit excceded')
				return (False)
		return (True)
	
	
	def HostCommandThreadCleanup (self):
		for ThreadID in self.CommandThreads.keys ():
			if not self.CommandThreads[ThreadID].Active:
				del (self.CommandThreads[ThreadID])


class HostCommand (threading.Thread):
	def __init__ (self, ClassHost, FunctionDebug, CommandThreadID, Input, Source):
		threading.Thread.__init__ (self)
		self.Host = ClassHost
		self.Debug = FunctionDebug
		self.CommandThreadID = CommandThreadID
		self.Active = 1
		self.Input = Input
		self.Source = Source
		self.start ()
	
	
	def run (self):
		self.Debug ('INFO', 'HostCommand start')
		self.Handle (self.Input, self.Source)
		self.Debug ('INFO', 'HostCommand run finnished')
		self.Active = 0
	
	
	def Handle (self, Input, Source):
		Input['Command'] = doxReturnValue (Input['Input'], ' ')[1:]
		Input['RawData'] = Input['Input'][len (Input['Command']) + 2:]
		Input['Data'] = []
		
		if self.Host.HostCmds.Commands.has_key (Input['Command']):
			Data = Input['RawData']
			Failed = 0
			if Source == 'INTERAL_RETURN':
				Input['Return'] = 'Return'
			elif self.Host.HostCmds.Commands[Input['Command']][1] == 'Source':
				if Input['Source'] == 'Battle':
					Input['Return'] = 'BattleMe'
				elif Input['Source'] == 'BattleRequester':
					Input['Return'] = 'BattleMeRequester'
				else:
					Input['Return'] = Input['Source']
			else:
				Input['Return'] = self.Host.HostCmds.Commands[Input['Command']][1]
			
			Extracted = doxExtractInput (Input['RawData'], self.Host.HostCmds.Commands[Input['Command']][0])
			if not Extracted[0]:
				Input['Message'] = 'ERROR:' + str (Extracted[1])
			else:
				Input['Data'] = Extracted[1]
				Input = self.Host.HandleAccess (Input, Source)
		else:
			Input['Message'] = ['UNKNOWN COMMAND ("' + str (Input['Command']) + '")', 'Use !help to list the available commands']
			Input['Return'] = 'PM'
		
		self.Host.ReturnInput (Input)
