# -*- coding: ISO-8859-1 -*-
import os
import subprocess
import threading
import time
import socket


class Spring:
	def __init__ (self, ClassServer, ClassLobby):
		self.Debug = ClassServer.Debug
		self.Server = ClassServer
		self.Lobby = ClassLobby
		self.SpringAutoHostPort = 9000
		
	
	def SpringStart (self):
		self.Debug ('Spring::Start')
		ScriptURI = str (self.Server.Config['TempPath']) + 'Script.txt'
		self.GenerateBattleScript (ScriptURI)
		self.SpringPID = subprocess.Popen([self.Server.Config['SpringExec'], ScriptURI]) 
		
		self.SpringUDP = SpringUDP (self, self.Debug)
		self.SpringUDP.start ()
		
		return (True)
	
	
	def SpringStop (self):
		self.Debug ('Spring::Stop')
		self.SpringUDP.Terminate ()
		try:
			self.SpringUDP.join()
			self.SpringPID.kill()
			return (True)
		except:
			return (False)
	
	
	def SpringTalk (self, UDP_Command):
		self.SpringUDP.Talk (UDP_Command)

	
	def GenerateBattleScript (self, FilePath):
		self.Debug ('Spring::GenerateBattleScript::' + str (FilePath))
		
		Battle = self.Lobby.Battles[self.Lobby.BattleID]
		FP = open (FilePath, 'w')
		FP.write ('[GAME]\n')
		FP.write ('{\n')
		FP.write ('\tMapname=' + str (Battle['Map']) + ';\n')
		FP.write ('\tMaphash=' + str (self.Server.Maps[Battle['Map']]['Hash']) + ';\n')
		FP.write ('\t[modoptions]\n')
		FP.write ('\t{\n')
		for iOpt in self.Server.Mods[Battle['Mod']]['Options']:
			FP.write ('\t\t' + str (self.Server.Mods[Battle['Mod']]['Options'][iOpt]['Key']) + '=' + str (self.Server.Mods[Battle['Mod']]['Options'][iOpt]['Default']) + ';\n')
		FP.write ('\t}\n')
		FP.write ('\tStartPosType=2;\n')
		FP.write ('\tGameType=' + str (Battle['Mod']) + ';\n')
		FP.write ('\tModHash=' + str (self.Server.Mods[Battle['Mod']]['Hash']) + ';\n')
		FP.write ('\tHostIP=' + str (self.Lobby.IP) + ';\n')
		FP.write ('\tHostPort=' + str (self.Lobby.BattlePort) + ';\n')
		FP.write ('\tAutoHostName=' + str (self.Lobby.User) + ';\n')
		FP.write ('\tAutoHostCountryCode=' + str (self.Lobby.Users[self.Lobby.User]['Country']) + ';\n')
		FP.write ('\tAutoHostRank=' + str (self.Lobby.Users[self.Lobby.User]['Rank']) + ';\n')
		FP.write ('\tAutoHostAccountId=' + str (self.Lobby.Users[self.Lobby.User]['ID']) + ';\n')
		FP.write ('\tAutohostPort=' + str (self.SpringAutoHostPort) + ';\n')
		FP.write ('\tIsHost=1;\n')
		FP.write ('\tNumPlayers=' + str (len (Battle['Users']) - 1) + ';\n')

		iP = 0
		iT = 0
		iA = 0
		Teams = {}
		Allys = {}
		Players = {}
		for User in Battle['Users']:
			if (User != self.Lobby.User):
				if not Teams.has_key (self.Lobby.BattleUsers[User]['Team']):
					Teams[self.Lobby.BattleUsers[User]['Team']] = iT
					iT = iT + 1
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
#				print (User + '\t' + str (self.Lobby.BattleUsers[User]))
#				if not Teams.has_key (self.Lobby.BattleUsers[User]['Team']) and self.Lobby.BattleUsers[User]['Spectator'] == 0:
#					Teams[self.Lobby.BattleUsers[User]['Team']] = {
#						'Leader':iP,
#						'Ally':self.Lobby.BattleUsers[User]['Ally'],
#						'Color':self.Lobby.BattleUsers[User]['Color'],
#						'Side':self.Lobby.BattleUsers[User]['Side'],
#						'Handicap':self.Lobby.BattleUsers[User]['Handicap'],
#					}
				iP = iP + 1

		print (Teams)
		print (Allys)
		
#		iT = 0
		FP.write ('\tNumTeams=' + str (len (Teams)) + ';\n')
		
		for User in Battle['Users']:
			if (User != self.Lobby.User and self.Lobby.BattleUsers[User]['Spectator'] == 0):
				if not Allys.has_key (self.Lobby.BattleUsers[User]['Ally']):
					Allys[self.Lobby.BattleUsers[User]['Ally']] = iA
					iA = iA + 1
#				Color = str (round (int (self.Lobby.BattleUsers[User]['Color'][4:6], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][2:4], 16) / 255.0, 5)) + ' ' + str (round (int (self.Lobby.BattleUsers[User]['Color'][0:2], 16) / 255.0, 5))

				FP.write ('\t[TEAM' + str (Teams[self.Lobby.BattleUsers[User]['Team']]) + ']\n')
				FP.write ('\t{\n')
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
		FP.close ()


class SpringUDP (threading.Thread):
	def __init__ (self, ClassSpring, FunctionDebug):
		threading.Thread.__init__ (self)
		self.Spring = ClassSpring
		self.Debug = FunctionDebug
		self.Active = 1
		self.Socket = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
		self.Socket.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.ServerAddr = None
	
	
	def run (self):
		self.Debug ('SpringUDP start')
		self.Socket.bind ((str ('127.0.0.1'), int (self.Spring.SpringAutoHostPort)))
		while (self.Active):
			while (self.Active):
				Data, self.ServerAddr = self.Socket.recvfrom (8192)
				if (Data):
					self.Debug ('UDP::' + str (ord (Data[0])) + '::' + str (Data))
		self.Socket.shutdown(socket.SHUT_RDWR)
		self.Socket.close()
	
	
	def Talk (self, Message):
		self.Debug ('UDP_SEND::' + str (Message))
		self.Socket.sendto (str (Message), self.ServerAddr)
	
	
	def Terminate (self):
		self.Debug ('SpringUDP terminate')
		self.Active = 0