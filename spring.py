# -*- coding: ISO-8859-1 -*-
import os
import subprocess
import threading
import time
import socket
import sys
import math
from doxFunctions import *

class Spring:
	def __init__ (self, ClassServer, ClassHost, ClassLobby, UDPPort):
		self.Debug = ClassServer.Debug
		self.Server = ClassServer
		self.Host = ClassHost
		self.Lobby = ClassLobby
		self.SpringAutoHostPort = UDPPort
		self.SpringUDP = None
		self.SpringPID = None
		self.SpringOutput = None
		self.SpringError = None
		self.Headless = 0
		self.HeadlessSpeed = [1, 3]
		self.Debug ('INFO', 'UDP Port:' + str (self.SpringAutoHostPort))
		self.Game = {}
	
	
	def SpringEvent (self, Event, Data = ''):
		self.Debug ('INFO', str (Event) + '::' + str (Data))
		if Event == 'USER_CHAT_ALLY':
			if self.Lobby.BattleID and self.Host.GroupConfig['PassthoughSpringAllyToBattleLobby']:
				self.Lobby.BattleSay ('<' + str (Data[0]) + '> Ally: ' + str (Data[1]))
		elif Event == 'USER_CHAT_SPEC':
			if self.Lobby.BattleID and self.Host.GroupConfig['PassthoughSpringSpecToBattleLobby']:
				self.Lobby.BattleSay ('<' + str (Data[0]) + '> Spec: ' + str (Data[1]))
		elif Event == 'USER_CHAT_PUBLIC':
			self.Host.HandleInput ('BATTLE_PUBLIC', Data[1], Data[0])
			if self.Lobby.BattleID and self.Host.GroupConfig['PassthoughSpringNormalToBattleLobby']:
				self.Lobby.BattleSay ('<' + str (Data[0]) + '> ' + str (Data[1]))
		elif Event == 'BATTLE_STARTED':
			self.Host.HostCmds.Notifications ('BATTLE_STARTED')
		elif Event == 'BATTLE_SCRIPT_CREATED':
			self.Game = Data
			self.Game['TimeCreated'] = doxTime ()
			self.Game['Deaths'] = []
		elif Event == 'GAME_START':
			self.Game['TimeStart'] = doxTime ()
		elif Event == 'GAME_END':
			self.Game['TimeEnd'] = doxTime ()
			self.Server.HandleDB.StoreBattle (self.Lobby.Users[self.Lobby.User]['ID'], self.Host.GroupConfig['ConfigGroupRank'], self.Game['Game'], self.Game['Map'], self.Game['TimeCreated'], self.Game['GameID'], self.Game)
		elif Event == 'USER_DIED':
			self.Game['Deaths'].append ([Data, doxTime ()])
		elif Event == 'GAMEOUTPUT_GAMEID':
			self.Game['GameID'] = Data
			
	
	
	def UserIsPlaying (self, User):
		if self.SpringUDP and self.SpringUDP.Active:
			return (self.SpringUDP.IsPlaying (User))
	
	
	def UserIsSpectating (self, User):
		if self.SpringUDP and self.SpringUDP.Active:
			return (self.SpringUDP.IsSpectating (User))
		return (False)
	
	
	def SpringStart (self, Reason = 'UNKNOWN'):
		self.Debug ('INFO', 'Spring::Start (' + Reason + ')')
		
		ScriptURI = str (self.Server.Config['General']['PathTemp']) + 'Script.txt'
		self.GenerateBattleScript (ScriptURI)
		self.SpringPID = subprocess.Popen([self.Host.GetSpringBinary (self.Headless), ScriptURI], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.SpringEvent ('BATTLE_STARTED')
		self.SpringOutput = SpringOutput (self, self.Debug)
		self.SpringOutput.start ()
		self.SpringError = SpringError (self, self.Debug)
		self.SpringError.start ()
		self.SpringUDP = SpringUDP (self, self.Debug)
		self.SpringUDP.start ()
		
		return (True)
	
	
	def SpringStop (self, Reason = 'UNKNOWN', Message = ''):
		self.Debug ('INFO', 'Spring::Stop (' + Reason + '::' + Message + ')')
		if self.SpringUDP:
			try:
				self.SpringUDP.Terminate (Message)
			except Exception as Error:
				self.Debug('WARNING', 'Error killing SpringUDP: ' + str (Error))
		
		if self.SpringPID:
			try:
				self.SpringPID.terminate ()
				if self.SpringPID.wait () == None:
					self.SpringPID.kill ()
				self.SpringPID = None
			except Exception as Error:
				self.Debug('ERROR', 'Error killing Spring: ' + str (Error))
		
		if self.SpringOutput:
			try:
				self.SpringOutput.Terminate (Message)
			except Exception as Error:
				self.Debug('ERROR', 'Error killing SpringOutput: ' + str (Error))
		
		if self.SpringError:
			try:
				self.SpringError.Terminate (Message)
			except Exception as Error:
				self.Debug('ERROR', 'Error killing SpringError: ' + str (Error))
		
		self.Lobby.BattleStop ()
		return (True)
	
	
	def SpringTalk (self, UDP_Command):
		self.Debug ('INFO', 'Spring::SpringTalk=' + str (UDP_Command))
		try:
			self.SpringUDP.Talk (UDP_Command)
		except:
			return (False)
	
	
	def GenerateBattleScript (self, FilePath):
		self.Debug ('INFO', 'Spring::GenerateBattleScript::' + str (FilePath))
		Battle = self.Lobby.Battles[self.Lobby.BattleID]
		UnitsyncMod = self.Host.GetUnitsyncMod (Battle['Mod'])
		self.Headless = 0
		for User in Battle['Users']:
			if not User == self.Lobby.User and self.Lobby.BattleUsers[User]['AI'] and self.Lobby.BattleUsers[User]['AIOwner'] == self.Lobby.User:
				self.Headless = 1
		Return = {}
		
		FP = open (FilePath, 'w')
		FP.write ('[GAME]\n')
		FP.write ('{\n')
		FP.write ('\tMapname=' + str (Battle['Map']) + ';\n')
		Return['Map'] = Battle['Map']
		FP.write ('\t[modoptions]\n')
		FP.write ('\t{\n')
		if self.Host.Battle.has_key ('ModOptions'):
			for Key in self.Host.Battle['ModOptions'].keys ():
				FP.write ('\t\t' + str (Key) + '=' + str (self.Host.Battle['ModOptions'][Key]) + ';\n')
				if Key == 'minspeed':
					self.HeadlessSpeed[0] = self.Host.Battle['ModOptions'][Key]
				if Key == 'maxspeed':
					self.HeadlessSpeed[1] = self.Host.Battle['ModOptions'][Key]
		FP.write ('\t}\n')
		FP.write ('\tStartPosType=' + str (self.Host.Battle['StartPosType']) + ';\n')
		Return['StartPosType'] = str (self.Host.Battle['StartPosType'])
		Return['Game'] = str (Battle['Mod'])
		FP.write ('\tGameType=' + str (Battle['Mod']) + ';\n')
		FP.write ('\tHostIP=' + str (self.Lobby.IP) + ';\n')
		FP.write ('\tHostPort=' + str (self.Lobby.BattlePort) + ';\n')
		if self.Headless:
			FP.write ('\tMyPlayerName=' + str (self.Lobby.User) + ';\n')
			FP.write ('\tAutohostPort=' + str (self.SpringAutoHostPort) + ';\n')
			FP.write ('\tIsHost=1;\n')
			iP = 1
		else:
			FP.write ('\tAutoHostName=' + str (self.Lobby.User) + ';\n')
			FP.write ('\tAutoHostCountryCode=' + str (self.Lobby.Users[self.Lobby.User]['Country']) + ';\n')
			FP.write ('\tAutoHostRank=' + str (self.Lobby.Users[self.Lobby.User]['Rank']) + ';\n')
			FP.write ('\tAutoHostAccountId=' + str (self.Lobby.Users[self.Lobby.User]['ID']) + ';\n')
			FP.write ('\tAutohostPort=' + str (self.SpringAutoHostPort) + ';\n')
			FP.write ('\tIsHost=1;\n')
			iP = 0
		
		for User in Battle['Users']:
			if not User == self.Lobby.User and not self.Lobby.BattleUsers[User]['AI']:
				iP = iP + 1
		FP.write ('\tNumPlayers=' + str (iP) + ';\n')
		
		iP = 0
		iT = 0
		iA = 0
		iAI = 0
		Teams = {}
		Allys = {}
		Players = {}
		AIs = {}
		
		if self.Headless:
			Players[self.Lobby.User] = iP
			FP.write ('\t[PLAYER' + str (iP) + ']\n')
			FP.write ('\t{\n')
			FP.write ('\t\tName=' + str (self.Lobby.User) + ';\n')
			FP.write ('\t\tPassword=2DD5A5ED;\n')
			FP.write ('\t\tSpectator=1;\n')
			FP.write ('\t}\n')
			iP = iP + 1
		
		Return['Teams'] = {}
		for User in Battle['Users']:
			if User != self.Lobby.User:
				if not Teams.has_key (self.Lobby.BattleUsers[User]['Team']):
					Teams[self.Lobby.BattleUsers[User]['Team']] = iT
					Return['Teams'][iT] = []
					iT = iT + 1
				
				if not self.Lobby.BattleUsers[User]['AI']:
					Players[User] = iP
					FP.write ('\t[PLAYER' + str (iP) + ']\n')
					FP.write ('\t{\n')
					FP.write ('\t\tName=' + str (User) + ';\n')
					FP.write ('\t\tcountryCode=' + str (self.Lobby.Users[User]['Country']) + ';\n')
					FP.write ('\t\tRank=' + str (self.Lobby.Users[User]['Rank']) + ';\n')
					FP.write ('\t\tPassword=' + str (self.Lobby.BattleUsers[User]['Password']) + ';\n')
					FP.write ('\t\tSpectator=' + str (self.Lobby.BattleUsers[User]['Spectator']) + ';\n')
					FP.write ('\t\tTeam=' + str (Teams[self.Lobby.BattleUsers[User]['Team']]) + ';\n')
					FP.write ('\t}\n')
					Return['Teams'][Teams[self.Lobby.BattleUsers[User]['Team']]].append ([User, self.Lobby.BattleUsers[User]['Spectator'], self.Lobby.Users[User]['ID'], self.Lobby.Users[User]['Rank']])
					iP = iP + 1
		
		for User in Battle['Users']:
			if User != self.Lobby.User:
				if self.Lobby.BattleUsers[User]['AI']:
					AIs[User] = iAI
					FP.write ('\t[AI' + str (iAI) + ']\n')
					FP.write ('\t{\n')
					FP.write ('\t\tName=' + str (User) + ';\n')
					FP.write ('\t\tShortName=' + str (self.Lobby.BattleUsers[User]['AIDLL']) + ';\n')
					FP.write ('\t\tTeam=' + str (Teams[self.Lobby.BattleUsers[User]['Team']]) + ';\n')
					FP.write ('\t\tHost=' + str (Players[self.Lobby.BattleUsers[User]['AIOwner']]) + ';\n')
					FP.write ('\t}\n')
					Return['Teams'][Teams[self.Lobby.BattleUsers[User]['Team']]].append ([User, 0, 'AI', self.Lobby.BattleUsers[User]['AIDLL'], Players[self.Lobby.BattleUsers[User]['AIOwner']]])
					iAI = iAI + 1
		
		FP.write ('\tNumTeams=' + str (len (Teams)) + ';\n')
		
		Return['Allies'] = {}
		for User in Battle['Users']:
			if User != self.Lobby.User and (self.Lobby.BattleUsers[User]['Spectator'] == 0 or self.Lobby.BattleUsers[User]['AI']):
				if not Allys.has_key (self.Lobby.BattleUsers[User]['Ally']):
					Allys[self.Lobby.BattleUsers[User]['Ally']] = iA
					Return['Allies'][iA] = []
					iA = iA + 1
				
				FP.write ('\t[TEAM' + str (Teams[self.Lobby.BattleUsers[User]['Team']]) + ']\n')
				FP.write ('\t{\n')
				if self.Lobby.BattleUsers[User]['AI']:
					FP.write ('\t\tTeamLeader=0;\n')
				else:
					FP.write ('\t\tTeamLeader=' + str (Players[User]) + ';\n')
				FP.write ('\t\tAllyTeam=' + str (Allys[self.Lobby.BattleUsers[User]['Ally']]) + ';\n')
				FP.write ('\t\tRgbColor=' + str (round (int (self.Lobby.BattleUsers[User]['Color'][0:2], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][2:4], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][4:6], 16) / 255.0, 5)) + ';\n')
				FP.write ('\t\tSide=' + str (UnitsyncMod['Sides'][self.Lobby.BattleUsers[User]['Side']]) + ';\n')
				FP.write ('\t\tHandicap=' + str (self.Lobby.BattleUsers[User]['Handicap']) + ';\n')
				FP.write ('\t}\n')
				Return['Allies'][Allys[self.Lobby.BattleUsers[User]['Ally']]].append ([Teams[self.Lobby.BattleUsers[User]['Team']], UnitsyncMod['Sides'][self.Lobby.BattleUsers[User]['Side']], self.Lobby.BattleUsers[User]['Handicap'], self.Lobby.BattleUsers[User]['Color']])
		for Ally in Battle['Boxes'].keys ():
			if not Allys.has_key (Ally):
				Allys[Ally] = iA
				iA+= 1
		
		FP.write ('\tNumAllyTeams=' + str (len (Allys)) + ';\n')
		for Ally in Allys:
			FP.write ('\t[ALLYTEAM' + str (Allys[Ally]) + ']\n')
			FP.write ('\t{\n')
			FP.write ('\t\tNumAllies=0;\n')
			if str (self.Host.Battle['StartPosType']) == '2' and Battle['Boxes'].has_key (Ally):
				FP.write ('\t\tStartRectLeft=' + str (round (float (Battle['Boxes'][Ally][0]) / 200, 2)) + ';\n')
				FP.write ('\t\tStartRectTop=' + str (round (float (Battle['Boxes'][Ally][1]) / 200, 2)) + ';\n')
				FP.write ('\t\tStartRectRight=' + str (round (float (Battle['Boxes'][Ally][2]) / 200, 2)) + ';\n')
				FP.write ('\t\tStartRectBottom=' + str (round (float (Battle['Boxes'][Ally][3]) / 200, 2)) + ';\n')
			FP.write ('\t}\n')
		
		if len (Battle['DisabledUnits']) > 0:
			FP.write ('\tNumRestrictions=' + str (len (Battle['DisabledUnits'])) + ';\n')
			iUnit = 0
			FP.write ('\t[RESTRICT]\n')
			FP.write ('\t{\n')
			for Unit in Battle['DisabledUnits'].keys ():
				FP.write ('\t\tUnit' + str (iUnit) + '=' + str (Unit) + ';\n')
				FP.write ('\t\tLimit' + str (iUnit) + '=0;\n')
				iUnit += 1
			FP.write ('\t}\n')
		else:
			FP.write ('\tNumRestrictions=0;\n')
		
		FP.write ('\t[MAPOPTIONS]\n')
		FP.write ('\t{\n')
		if self.Host.Battle.has_key ('MapOptions'):
			for Key in self.Host.Battle['MapOptions'].keys ():
				FP.write ('\t\t' + str (Key) + '=' + str (self.Host.Battle['MapOptions'][Key]) + ';\n')
		FP.write ('\t}\n')
		FP.write ('}\n')
		FP.close ()
		self.SpringEvent ('BATTLE_SCRIPT_CREATED', Return)
	
	
	def Terminate (self):
		self.Debug ('INFO')
		self.SpringStop ('Terminate')


class SpringUDP (threading.Thread): 
	def __init__ (self, ClassSpring, FunctionDebug):
		threading.Thread.__init__ (self)
		self.Spring = ClassSpring
		self.Debug = FunctionDebug
		self.Active = 1
		self.Socket = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
		self.Socket.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.ServerAddr = None
		self.SpringUsers = {}	# [ID] = Alias
		self.Users = {}			# [Alias] = {'Ready', 'Alive', 'InGame'}
	
	
	def run (self):
		self.Debug ('INFO', 'SpringUDP start')
		self.Socket.bind ((str ('127.0.0.1'), int (self.Spring.SpringAutoHostPort)))
		self.Socket.settimeout (1)
		while self.Active:
			try:
				Data, self.ServerAddr = self.Socket.recvfrom (8192)
			except socket.timeout:
				continue
			if Data:
				try:
					if ord (Data[0]) == 1:	# Game stop
						self.Spring.SpringEvent ('SERVER_QUIT')
						self.Spring.SpringStop ('UDP_SERVER_QUIT', 'Spring sent SERVER_QUIT')
					elif ord (Data[0]) == 2:	# Game start
						if self.Spring.Headless:
							self.Talk ('/setminspeed 1')
							self.Talk ('/setmaxspeed 1')
							self.Talk ('/setminspeed ' + str (self.Spring.HeadlessSpeed[0]))
							self.Talk ('/setmaxspeed ' + str (self.Spring.HeadlessSpeed[1]))
						for User in self.Users.keys ():
							if self.Users[User]['Alive']:
								self.Users[User]['Playing'] = 1
						self.Spring.SpringEvent ('GAME_START')
					elif ord (Data[0]) == 3:	# Battle ended
						self.Spring.Lobby.BattleSay ('Battle ended', 1)
						for User in self.Users.keys ():
							self.Users[User]['Playing'] = 0
						self.Spring.SpringEvent ('GAME_END')
					elif ord (Data[0]) == 4:	# Information
						self.Spring.SpringEvent ('INFORMATION', Data[1:])
						Info = Data[1:].split (' ')
						if Info[0] == 'Player' and Info[2] == 'finished':
							if not self.Users.has_key (Info[1]):
								self.Users[Info[1]] = {'Ready':0, 'Playing':0, 'Alive':0, 'InGame':1}
							self.Users[Info[1]]['Alive'] = 1
							self.Spring.SpringEvent ('PLAYER_JOINED', Info[1])
						elif Info[0] == 'Spectator' and Info[2] == 'finished':
							self.Spring.SpringEvent ('SPECTATOR_JOINED', Info[1])
							if not self.Users.has_key (Info[1]):
								self.Users[Info[1]] = {'Ready':0, 'Playing':0, 'Alive':0, 'InGame':1}
					elif ord (Data[0]) == 10:	# User joined
						self.Spring.SpringEvent ('USER_JOINED', Data[2:])
						self.SpringUsers[Data[1]] = Data[2:]
						self.Users[self.GetUserFromID (Data[1])]['InGame'] = 1
					elif ord (Data[0]) == 11:	# User left
						self.Spring.SpringEvent ('USER_LEFT', self.GetUserFromID (Data[1]))
						self.Users[self.GetUserFromID (Data[1])]['InGame'] = 0
					elif ord (Data[0]) == 12:	# User ready
						self.Spring.SpringEvent ('USER_READY', self.GetUserFromID (Data[1]))
						self.Users[self.GetUserFromID (Data[1])]['Ready'] = 1
						self.Users[self.GetUserFromID (Data[1])]['Alive'] = 1
					elif ord (Data[0]) == 13:	# Battle chat
						if ord (Data[2]) == 252:	# Ally chat
							self.Spring.SpringEvent ('USER_CHAT_ALLY', [self.GetUserFromID (Data[1]), str (Data[3:])])
						if ord (Data[2]) == 253:	# Spec chat
							self.Spring.SpringEvent ('USER_CHAT_SPEC', [self.GetUserFromID (Data[1]), str (Data[3:])])
						if ord (Data[2]) == 254:	# Public chat
							self.Spring.SpringEvent ('USER_CHAT_PUBLIC', [self.GetUserFromID (Data[1]), str (Data[3:])])
					elif ord (Data[0]) == 14:	# User died
						self.Spring.SpringEvent ('USER_DIED', self.GetUserFromID (Data[1]))
						self.Users[self.GetUserFromID (Data[1])]['Alive'] = 0
					else:
						if not ord (Data[0]) == 20 and not ord (Data[0]) == 60:
							try:
								self.Debug ('WARNING', 'UNKNOWN_UDP::' + str (ord (Data[0])) + '::' + str (ord (Data[1])) + '::' + str (Data[2:]))
							except:
								try:
									self.Debug ('WARNING', 'UNKNOWN_UDP::' + str (ord (Data[0])) + '::' + str (ord (Data[1])))
								except:
									self.Debug ('WARNING', 'UNKNOWN_UDP::' + str (ord (Data[0])))
				except Exception as Error:
					self.Debug ('ERROR', 'CRASH::' + str (ord (Data[0])) + ' => ' + str (Error))
		self.Debug ('INFO', 'UDP run finnsihed')
	
	
	def GetUserFromID (self, ID):
		if self.SpringUsers.has_key (ID):
			return (self.SpringUsers[ID])
		self.Debug ('ERROR', 'No user found for "' + str (ord (ID)) + '"')
	
	
	def IsReady (self, User):
		self.Debug ('INFO', 'InReady::' + str (User))
		if self.Users.has_key (User):
			return (self.Users[User]['Ready'])
		return (False)
	
	
	def IsAlive (self, SearchUser):
		self.Debug ('INFO', 'InAlive::' + str (User))
		if self.Users.has_key (User):
			return (self.Users[User]['Alive'])
		return (False)
	
	
	def IsSpectating (self, User):
		self.Debug ('INFO', 'IsSpectating::' + str (User))
		if self.Users.has_key (User) and self.Users[User]['InGame'] and not self.Users[User]['Playing']:
			return (True)
		return (False)
	
	
	def IsPlaying (self, User):
		self.Debug ('INFO', 'IsPlaying::' + str (User))
		if self.Users.has_key (User) and self.Users[User]['InGame'] and self.Users[User]['Playing']:
			return (True)
		return (False)
	
	
	def AddUser (self, User, Password):
		self.Debug ('INFO', 'User:' + str (User) + ', Passwd:' + str (Password))
		self.Talk ('/ADDUSER ' + str (User) + ' ' + str (Password))
	
	
	def Talk (self, Message, Try = 0):
		self.Debug ('INFO', str (Message))
		if self.Active:
			try:
				self.Socket.sendto (str (Message), self.ServerAddr)
			except:
				self.Debug ('ERROR', 'Socked send failed (try: ' + str (Try) + ')')
				if Try < 10:
					time.sleep (0.05)
					self.Talk (Message, Try + 1)
				else:	
					self.Spring.SpringStop ('UDP_TALK_FAIED', 'SpringUDP lost connection to spring')
	
	
	def Terminate (self, Message = ''):
		self.Debug ('INFO', str (Message))
		self.Active = 0
		self.Talk ('/QUIT')
		try:
			self.Debug ('INFO', 'Close UDP socked')
			self.Socket.close ()
		except:
			self.Debug ('ERROR', 'FAILED: Close UDP socked')


class SpringOutput (threading.Thread):
	def __init__ (self, ClassSpring, FunctionDebug):
		threading.Thread.__init__ (self)
		self.Spring = ClassSpring
		self.Debug = FunctionDebug
		self.Active = 1
		self.PID = self.Spring.SpringPID
	
	
	def run (self):
		self.Debug ('INFO', 'SpringOutput start')
		while self.Active:
			Line = self.PID.stdout.readline ()
			if Line:
				self.Debug ('DEBUG_GAME', Line)
				if 'GameID:' in Line:
					self.Spring.SpringEvent ('GAMEOUTPUT_GAMEID', doxReMatch ('[a-fA-F0-9]{32}', Line))
			else:
				self.Active = 0
	
	
	def Terminate (self, Message = ''):
		self.Debug ('INFO', str (Message))
		self.Active = 0


class SpringError (threading.Thread):
	def __init__ (self, ClassSpring, FunctionDebug):
		threading.Thread.__init__ (self)
		self.Spring = ClassSpring
		self.Debug = FunctionDebug
		self.Active = 1
		self.PID = self.Spring.SpringPID
	
	
	def run (self):
		self.Debug ('INFO', 'SpringError start')
		while self.Active:
			Line = self.PID.stderr.readline ()
			if Line:
				self.Debug ('DEBUG_GAME_ERROR', Line)
			else:
				self.Active = 0
	
	
	def Terminate (self, Message = ''):
		self.Debug ('INFO', str (Message))
		self.Active = 0
