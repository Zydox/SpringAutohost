# -*- coding: ISO-8859-1 -*-
import os
import subprocess
import threading
import time
import socket
from tempfile import NamedTemporaryFile as TmpFile

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
		#ScriptURI = str (self.Server.Config['TempPath']) + 'Script.txt'
		#using a uniquely named tmp file here to avoid clashes from multiple spawns
		Script = TmpFile(prefix='Script.txt_')
		self.GenerateBattleScript (Script)
		#reopening the file is not guaranteed to work on win
		if self.Headless:
			self.SpringPID = subprocess.Popen([self.Server.Config['PathSpringHeadless'], ScriptURI]) 
		else:
			self.SpringPID = subprocess.Popen([self.Server.Config['PathSpringDedicated'], ScriptURI]) 
		
		self.SpringUDP = SpringUDP (self, self.Debug)
		self.SpringUDP.start ()
		self.Host.HostCmds.Notifications ('BATTLE_STARTED')
		
		return (True)
	
	
	def SpringStop (self, Reason = 'UNKNOWN', Message = ''):
		#UDP_SERVER_QUIT
		self.Debug ('Spring::Stop (' + Reason + '::' + Message + ')')
		try:
			self.SpringUDP.Terminate (Message)
			self.SpringUDP.join()
			self.SpringPID.kill()
			self.Lobby.BattleStop ()
			return (True)
		except:
			return (False)
	
	
	def SpringTalk (self, UDP_Command):
		self.Debug ('Spring::SpringTalk=' + str (UDP_Command))
		try:
			self.SpringUDP.Talk (UDP_Command)
		except:
			return (False)

	
<<<<<<< HEAD
	def GenerateBattleScript (self, FilePath):
		self.Debug ('Spring::GenerateBattleScript::' + str (FilePath))
		Battle = self.Lobby.Battles[self.Lobby.BattleID]
		
		self.Headless = 0
		for User in Battle['Users']:
			if not User == self.Lobby.User and self.Lobby.BattleUsers[User]['AI'] and self.Lobby.BattleUsers[User]['AIOwner'] == self.Lobby.User:
				self.Headless = 1
		
		FP = open (FilePath, 'w')
=======
	def GenerateBattleScript (self, FP):
		self.Debug ('Spring::GenerateBattleScript::' + FP.name)
		self.Headless = 1
		
		Battle = self.Lobby.Battles[self.Lobby.BattleID]
>>>>>>> origin/zydox
		FP.write ('[GAME]\n')
		FP.write ('{\n')
		FP.write ('\tMapname=' + str (Battle['Map']) + ';\n')
		FP.write ('\tMaphash=' + str (self.Server.Maps[Battle['Map']]['Hash']) + ';\n')
		FP.write ('\t[modoptions]\n')
		FP.write ('\t{\n')
		for iOpt in self.Server.Mods[Battle['Mod']]['Options']:
			FP.write ('\t\t' + str (self.Server.Mods[Battle['Mod']]['Options'][iOpt]['Key']) + '=' + str (self.Server.Mods[Battle['Mod']]['Options'][iOpt]['Default']) + ';\n')
			if self.Server.Mods[Battle['Mod']]['Options'][iOpt]['Key'] == 'minspeed':
				self.HeadlessSpeed[0] = self.Server.Mods[Battle['Mod']]['Options'][iOpt]['Default']
			if self.Server.Mods[Battle['Mod']]['Options'][iOpt]['Key'] == 'maxspeed':
				self.HeadlessSpeed[1] = self.Server.Mods[Battle['Mod']]['Options'][iOpt]['Default']
		FP.write ('\t}\n')
		FP.write ('\tStartPosType=2;\n')
		FP.write ('\tGameType=' + str (Battle['Mod']) + ';\n')
		FP.write ('\tModHash=' + str (self.Server.Mods[Battle['Mod']]['Hash']) + ';\n')
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
#			FP.write ('\t\tcountryCode=' + str (self.Lobby.Users[User]['Country']) + ';\n')
#			FP.write ('\t\tRank=' + str (self.Lobby.Users[User]['Rank']) + ';\n')
			FP.write ('\t\tPassword=2DD5A5ED;\n')
			FP.write ('\t\tSpectator=1;\n')
#			FP.write ('\t\tTeam=' + str (Teams[self.Lobby.BattleUsers[User]['Team']]) + ';\n')
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
#					FP.write ('\t\tcountryCode=' + str (self.Lobby.Users[User]['Country']) + ';\n')
					FP.write ('\t\tShortName=' + str (self.Lobby.BattleUsers[User]['AIDLL']) + ';\n')
#					FP.write ('\t\tPassword=' + str (self.Lobby.BattleUsers[User]['Password']) + ';\n')
#					FP.write ('\t\tSpectator=' + str (self.Lobby.BattleUsers[User]['Spectator']) + ';\n')
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
#				print (User + '\t' + str (self.Lobby.BattleUsers[User]))
#				if not Teams.has_key (self.Lobby.BattleUsers[User]['Team']) and self.Lobby.BattleUsers[User]['Spectator'] == 0:
#					Teams[self.Lobby.BattleUsers[User]['Team']] = {
#						'Leader':iP,
#						'Ally':self.Lobby.BattleUsers[User]['Ally'],
#						'Color':self.Lobby.BattleUsers[User]['Color'],
#						'Side':self.Lobby.BattleUsers[User]['Side'],
#						'Handicap':self.Lobby.BattleUsers[User]['Handicap'],
#					}

		print (AIs)
		print (Teams)
		print (Allys)
		
#		iT = 0
		FP.write ('\tNumTeams=' + str (len (Teams)) + ';\n')
		
		for User in Battle['Users']:
			if User != self.Lobby.User and (self.Lobby.BattleUsers[User]['Spectator'] == 0 or self.Lobby.BattleUsers[User]['AI']):
				if not Allys.has_key (self.Lobby.BattleUsers[User]['Ally']):
					Allys[self.Lobby.BattleUsers[User]['Ally']] = iA
					iA = iA + 1
#				Color = str (round (int (self.Lobby.BattleUsers[User]['Color'][4:6], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][2:4], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][0:2], 16) / 255.0, 5))

				FP.write ('\t[TEAM' + str (Teams[self.Lobby.BattleUsers[User]['Team']]) + ']\n')
				FP.write ('\t{\n')
				if self.Lobby.BattleUsers[User]['AI']:
					FP.write ('\t\tTeamLeader=0;\n')
#					FP.write ('\t\tTeamLeader=' + str (AIs[User]) + ';\n')
				else:
					FP.write ('\t\tTeamLeader=' + str (Players[User]) + ';\n')
				FP.write ('\t\tAllyTeam=' + str (Allys[self.Lobby.BattleUsers[User]['Ally']]) + ';\n')
				FP.write ('\t\tRgbColor=' + str (round (int (self.Lobby.BattleUsers[User]['Color'][4:6], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][2:4], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][0:2], 16) / 255.0, 5)) + ';\n')
				FP.write ('\t\tSide=' + str (self.Server.Mods[Battle['Mod']]['Sides'][self.Lobby.BattleUsers[User]['Side']]) + ';\n')
				FP.write ('\t\tHandicap=' + str (self.Lobby.BattleUsers[User]['Handicap']) + ';\n')
				FP.write ('\t}\n')
				

#		for Team in Teams:
#			if not Allys.has_key (Teams[Team]['Ally']):
#				Allys[Teams[Team]['Ally']] = iA
#				iA = iA + 1
#			FP.write ('\t[TEAM' + str (iT) + ']\n')
#			FP.write ('\t{\n')
#			FP.write ('\t\tTeamLeader=' + str (Teams[Team]['Leader']) + ';\n')
#			FP.write ('\t\tAllyTeam=' + str (Allys[Teams[Team]['Ally']]) + ';\n')
#			FP.write ('\t\tRgbColor=' + str (Teams[Team]['Color']) + ';\n')
#			FP.write ('\t\tSide=' + str (Teams[Team]['Side']) + ';\n')
#			FP.write ('\t\tHandicap=' + str (Teams[Team]['Handicap']) + ';\n')
#			FP.write ('\t}\n')
#			iT = iT + 1

#		iA = 0
		FP.write ('\tNumAllyTeams=' + str (len (Allys)) + ';\n')
		for Ally in Allys:
			FP.write ('\t[ALLYTEAM' + str (Allys[Ally]) + ']\n')
			FP.write ('\t{\n')
			FP.write ('\t\tNumAllies=0;\n')
			FP.write ('\t}\n')
#			iA = iA + 1

		FP.write ('\tNumRestrictions=0;\n')
		FP.write ('\t[MAPOPTIONS]\n')
		FP.write ('\t{\n')
#		alt=1;
#		fog=0;
#		wc=0;
		FP.write ('\t}\n')
		FP.write ('}\n')
		#since FP is a tempfile object closing it would delete it atm
		#FP.close ()


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
				if ord (Data[0]) == 1:
					self.Spring.SpringStop ('UDP_SERVER_QUIT', 'Spring sent SERVER_QUIT')
				if ord (Data[0]) == 2:
					if self.Spring.Headless:
						self.Talk ('/setminspeed 1')
						self.Talk ('/setmaxspeed 1')
						self.Talk ('/setminspeed ' + str (self.Spring.HeadlessSpeed[0]))
						self.Talk ('/setmaxspeed ' + str (self.Spring.HeadlessSpeed[1]))
				if ord (Data[0]) == 3:
					self.Spring.Lobby.BattleSay ('Battle ended', 1)
				if ord (Data[0]) == 10:
					self.SpringUsers[Data[1]] = {'Alias':Data[2:], 'Ready':0, 'Alive':0}
				if ord (Data[0]) == 11:
					del (self.SpringUsers[Data[1]])
				if ord (Data[0]) == 12:
					self.SpringUsers[Data[1]]['Ready'] = 1
					self.SpringUsers[Data[1]]['Alive'] = 1
				if ord (Data[0]) == 14:
					self.SpringUsers[Data[1]]['Alive'] = 0
				
				if not ord (Data[0]) == 20 and not ord (Data[0]) == 60:
					try:
						self.Debug ('UDP::' + str (ord (Data[0])) + '::' + str (ord (Data[1])) + '::' + str (Data[2:]))
					except:
						try:
							self.Debug ('UDP::' + str (ord (Data[0])) + '::' + str (ord (Data[1])))
						except:
							self.Debug ('UDP::' + str (ord (Data[0])))
				
				if ord (Data[0]) == 13:
					if ord (Data[2]) == 252:
						if self.Spring.Lobby.BattleID and self.Spring.Lobby.Battles[self.Spring.Lobby.BattleID]['PassthoughSpringAllyToBattleLobby']:
							self.Spring.Lobby.BattleSay ('<' + self.SpringUsers[Data[1]]['Alias'] + '> Ally: ' + str (Data[3:]))
					if ord (Data[2]) == 253:
						if self.Spring.Lobby.BattleID and self.Spring.Lobby.Battles[self.Spring.Lobby.BattleID]['PassthoughSpringSpecToBattleLobby']:
							self.Spring.Lobby.BattleSay ('<' + self.SpringUsers[Data[1]]['Alias'] + '> Spec: ' + str (Data[3:]))
					if ord (Data[2]) == 254:
						if self.Spring.Lobby.BattleID and self.Spring.Lobby.Battles[self.Spring.Lobby.BattleID]['PassthoughSpringNormalToBattleLobby']:
							self.Spring.Lobby.BattleSay ('<' + self.SpringUsers[Data[1]]['Alias'] + '> ' + str (Data[3:]))
				try:
					if ord (Data[0]) == 10:
						print '10::' + str (ord (Data[1])) + '::' + str (ord (Data[2])) + '::' + str (Data[3:])
					if ord (Data[0]) == 11:
						print '11::' + str (ord (Data[1])) + '::' + str (ord (Data[2])) + '::' + str (Data[3:])
					if ord (Data[0]) == 12:
						print '12::' + str (ord (Data[1])) + '::' + str (ord (Data[2])) + '::' + str (Data[3:])
					if ord (Data[0]) == 14:
						print '14::' + str (ord (Data[1])) + '::' + str (ord (Data[2])) + '::' + str (Data[3:])
				except:
					i = 1
	
	
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
		self.Debug ('Talk::' + str (Message))
		self.Socket.sendto (str (Message), self.ServerAddr)
	
	
	def Terminate (self, Message = ''):
		self.Debug ('SpringUDP terminate (' + str (Message) + ')')
		self.Active = 0
