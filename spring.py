# -*- coding: ISO-8859-1 -*-
import os
import subprocess
import threading
import time
import socket
import sys


class Spring:
	def __init__ (self, ClassServer, ClassHost, ClassLobby):
		self.Debug = ClassServer.Debug
		self.Server = ClassServer
		self.Host = ClassHost
		self.Lobby = ClassLobby
		self.SpringAutoHostPort = 9000
		self.SpringUDP = None
		self.Headless = 0
		self.HeadlessSpeed = [1, 3]
	
	
	def SpringStart (self, Reason = 'UNKNOWN'):
		self.Debug ('Spring::Start (' + Reason + ')')
		ScriptURI = str (self.Server.Config['General']['PathTemp']) + 'Script.txt'
		self.GenerateBattleScript (ScriptURI)
		self.SpringPID = subprocess.Popen([self.Host.GetSpringBinary (self.Headless), ScriptURI]) 
		
		self.SpringUDP = SpringUDP (self, self.Debug)
		self.SpringUDP.start ()
		self.Host.HostCmds.Notifications ('BATTLE_STARTED')
		
		return (True)
	
	
	def SpringStop (self, Reason = 'UNKNOWN', Message = ''):
		self.Debug ('Spring::Stop (' + Reason + '::' + Message + ')')
		try:
			self.Debug (1)
			self.SpringUDP.Terminate (Message)
			self.Debug (2)
			self.SpringPID.terminate ()
			self.Debug (3)
			self.SpringPID.wait ()
			self.Debug (5)
#			self.SpringPID.kill ()
			self.Lobby.BattleStop ()
			self.Debug (6)
			return (True)
		except:
			self.Debug (7)
			return (False)
	
	
	def SpringTalk (self, UDP_Command):
		self.Debug ('Spring::SpringTalk=' + str (UDP_Command))
		try:
			self.SpringUDP.Talk (UDP_Command)
		except:
			return (False)

	
	def GenerateBattleScript (self, FilePath):
		self.Debug ('Spring::GenerateBattleScript::' + str (FilePath))
		Battle = self.Lobby.Battles[self.Lobby.BattleID]
		UnitsyncMod = self.Host.GetUnitsyncMod (Battle['Mod'])
		self.Headless = 0
		for User in Battle['Users']:
			if not User == self.Lobby.User and self.Lobby.BattleUsers[User]['AI'] and self.Lobby.BattleUsers[User]['AIOwner'] == self.Lobby.User:
				self.Headless = 1
		
		FP = open (FilePath, 'w')
		FP.write ('[GAME]\n')
		FP.write ('{\n')
		FP.write ('\tMapname=' + str (Battle['Map']) + ';\n')
		FP.write ('\tMaphash=' + str (Battle['MapHash']) + ';\n')
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
		FP.write ('\tGameType=' + str (Battle['Mod']) + ';\n')
		FP.write ('\tModHash=' + str (UnitsyncMod['Hash']) + ';\n')
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
			print self.Lobby.BattleUsers[User]
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
			FP.write ('\t[PLAYER' + str (iP) + ']\n')
			FP.write ('\t{\n')
			FP.write ('\t\tName=' + str (self.Lobby.User) + ';\n')
			FP.write ('\t\tPassword=2DD5A5ED;\n')
			FP.write ('\t\tSpectator=1;\n')
			FP.write ('\t}\n')
			iP = iP + 1
		
		for User in Battle['Users']:
			if User != self.Lobby.User:
				if not Teams.has_key (self.Lobby.BattleUsers[User]['Team']):
					Teams[self.Lobby.BattleUsers[User]['Team']] = iT
					iT = iT + 1
				
				if self.Lobby.BattleUsers[User]['AI']:
					AIs[User] = iAI
					FP.write ('\t[AI' + str (iAI) + ']\n')
					FP.write ('\t{\n')
					FP.write ('\t\tName=' + str (User) + ';\n')
					FP.write ('\t\tShortName=' + str (self.Lobby.BattleUsers[User]['AIDLL']) + ';\n')
					FP.write ('\t\tTeam=' + str (Teams[self.Lobby.BattleUsers[User]['Team']]) + ';\n')
					FP.write ('\t\tHost=0;\n')
					FP.write ('\t}\n')
					iAI = iAI + 1
				else:
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
					iP = iP + 1
		
#		print (AIs)
#		print (Teams)
#		print (Allys)
		
		FP.write ('\tNumTeams=' + str (len (Teams)) + ';\n')
		
		for User in Battle['Users']:
			if User != self.Lobby.User and (self.Lobby.BattleUsers[User]['Spectator'] == 0 or self.Lobby.BattleUsers[User]['AI']):
				if not Allys.has_key (self.Lobby.BattleUsers[User]['Ally']):
					Allys[self.Lobby.BattleUsers[User]['Ally']] = iA
					iA = iA + 1
				
				FP.write ('\t[TEAM' + str (Teams[self.Lobby.BattleUsers[User]['Team']]) + ']\n')
				FP.write ('\t{\n')
				if self.Lobby.BattleUsers[User]['AI']:
					FP.write ('\t\tTeamLeader=0;\n')
				else:
					FP.write ('\t\tTeamLeader=' + str (Players[User]) + ';\n')
				FP.write ('\t\tAllyTeam=' + str (Allys[self.Lobby.BattleUsers[User]['Ally']]) + ';\n')
				FP.write ('\t\tRgbColor=' + str (round (int (self.Lobby.BattleUsers[User]['Color'][4:6], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][2:4], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][0:2], 16) / 255.0, 5)) + ';\n')
				FP.write ('\t\tSide=' + str (UnitsyncMod['Sides'][self.Lobby.BattleUsers[User]['Side']]) + ';\n')
				FP.write ('\t\tHandicap=' + str (self.Lobby.BattleUsers[User]['Handicap']) + ';\n')
				FP.write ('\t}\n')
		
		FP.write ('\tNumAllyTeams=' + str (len (Allys)) + ';\n')
		for Ally in Allys:
			FP.write ('\t[ALLYTEAM' + str (Allys[Ally]) + ']\n')
			FP.write ('\t{\n')
			FP.write ('\t\tNumAllies=0;\n')
			FP.write ('\t}\n')
		
		FP.write ('\tNumRestrictions=0;\n')
		FP.write ('\t[MAPOPTIONS]\n')
		FP.write ('\t{\n')
		FP.write ('\t}\n')
		FP.write ('}\n')
		FP.close ()
	
	
	def Terminate (self):
		self.Debug ()
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
		self.SpringUsers = {}	# [ID] = {'Alias', 'Ready', 'Alive'}
		
	
	def run (self):
		self.Debug ('SpringUDP start')
		self.Socket.bind ((str ('127.0.0.1'), int (self.Spring.SpringAutoHostPort)))
		while self.Active:
			Data, self.ServerAddr = self.Socket.recvfrom (8192)
			if Data:
				if ord (Data[0]) == 1:	# Game stop
					self.Spring.SpringStop ('UDP_SERVER_QUIT', 'Spring sent SERVER_QUIT')
				if ord (Data[0]) == 2:	# Game start
					if self.Spring.Headless:
						self.Talk ('/setminspeed 1')
						self.Talk ('/setmaxspeed 1')
						self.Talk ('/setminspeed ' + str (self.Spring.HeadlessSpeed[0]))
						self.Talk ('/setmaxspeed ' + str (self.Spring.HeadlessSpeed[1]))
				if ord (Data[0]) == 3:	# Battle ended
					self.Spring.Lobby.BattleSay ('Battle ended', 1)
				if ord (Data[0]) == 10:	# User joined
					self.SpringUsers[Data[1]] = {'Alias':Data[2:], 'Ready':0, 'Alive':0}
				if ord (Data[0]) == 11:	# User left
					del (self.SpringUsers[Data[1]])
				if ord (Data[0]) == 12:	# User ready
					self.SpringUsers[Data[1]]['Ready'] = 1
					self.SpringUsers[Data[1]]['Alive'] = 1
				if ord (Data[0]) == 14:	# User died
					self.SpringUsers[Data[1]]['Alive'] = 0
				
				if not ord (Data[0]) == 20 and not ord (Data[0]) == 60:
					try:
						self.Debug ('UDP::' + str (ord (Data[0])) + '::' + str (ord (Data[1])) + '::' + str (Data[2:]))
					except:
						try:
							self.Debug ('UDP::' + str (ord (Data[0])) + '::' + str (ord (Data[1])))
						except:
							self.Debug ('UDP::' + str (ord (Data[0])))
				
				if ord (Data[0]) == 13:	# Battle chat
					if ord (Data[2]) == 252:	# Ally chat
						if self.Spring.Lobby.BattleID and self.Spring.Lobby.Battles[self.Spring.Lobby.BattleID]['PassthoughSpringAllyToBattleLobby']:
							self.Spring.Lobby.BattleSay ('<' + self.SpringUsers[Data[1]]['Alias'] + '> Ally: ' + str (Data[3:]))
					if ord (Data[2]) == 253:	# Spec chat
						if self.Spring.Lobby.BattleID and self.Spring.Lobby.Battles[self.Spring.Lobby.BattleID]['PassthoughSpringSpecToBattleLobby']:
							self.Spring.Lobby.BattleSay ('<' + self.SpringUsers[Data[1]]['Alias'] + '> Spec: ' + str (Data[3:]))
					if ord (Data[2]) == 254:	# Public chat
						if self.Spring.Lobby.BattleID and self.Spring.Lobby.Battles[self.Spring.Lobby.BattleID]['PassthoughSpringNormalToBattleLobby']:
							self.Spring.Lobby.BattleSay ('<' + self.SpringUsers[Data[1]]['Alias'] + '> ' + str (Data[3:]))
		self.Terminate ()
	
	
	def IsReady (self, SearchUser):
		self.Debug ('InReady::' + str (SearchUser))
		if len (self.SpringUsers):
			for User in self.SpringUsers:
				if self.SpringUsers[User]['Alias'] == SearchUser:
					return (self.SpringUsers[User]['Ready'])
	
	
	def IsAlive (self, SearchUser):
		self.Debug ('InAlive::' + str (SearchUser))
		if len (self.SpringUsers):
			for User in self.SpringUsers:
				if self.SpringUsers[User]['Alias'] == SearchUser:
					return (self.SpringUsers[User]['Alive'])
	
	
	def Talk (self, Message):
		self.Debug (str (Message))
		self.Socket.sendto (str (Message), self.ServerAddr)
	
	
	def Terminate (self, Message = ''):
		self.Debug (str (Message))
		self.Active = 0
		self.Talk ('/quit')
		try:
			self.Debug ('Terminate & close UDP socked')
			self.Socket.terminate (2)
			self.Socket.close ()
		except:
			self.Debug ('FAILED: Terminate & close UDP socked')
		self.Debug ('SystemExit')
		raise SystemExit ()
		self.Debug ('SystemExit OK')
		sys.exit ()
		self.Debug ('sys.exit ()')
