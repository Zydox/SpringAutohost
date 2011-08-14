# -*- coding: ISO-8859-1 -*-

class HostCmdsBattleLogic:
	def __init__ (self, ClassHostCmdsBattle, ClassServer, ClassHost):
		self.HostCmdsBattle = ClassHostCmdsBattle
		self.Server = ClassServer
		self.Host = ClassHost
		self.Debug = ClassServer.Debug
		self.Lobby = ClassHost.Lobby
		
	
	def Refresh (self):
		self.Battle = self.Host.Lobby.Battles[self.Host.Lobby.BattleID]
		self.BattleUsers = self.Host.Lobby.BattleUsers
	
	
	def LogicRing (self, User =''):
		self.Refresh ()
		if User:
			self.Host.Lobby.BattleRing (User)
			return ('Ringing "' + str (User) + '"')
		else:
			for User in self.BattleUsers:
				if self.BattleUsers[User]['Spectator'] == 0 and self.BattleUsers[User]['Ready'] == 0:
					self.Host.Lobby.BattleRing (User)
			return ('Ringing all unready users')
	
	
	def LogicAddBot (self, Team, Ally, Bot, Side, Color):
		self.Refresh ()
		Version = 0
		AI_ID = 0
		for AI in self.Server.Mods[self.Battle['Mod']]['AI']:
			if self.Server.Mods[self.Battle['Mod']]['AI'][AI]['shortName'] == Bot:
				if not self.Server.Mods[self.Battle['Mod']]['AI'][AI].has_key ('version') or Version < self.Server.Mods[self.Battle['Mod']]['AI'][AI]['version']:
					if self.Server.Mods[self.Battle['Mod']]['AI'][AI].has_key ('version'):
						Version = float (self.Server.Mods[self.Battle['Mod']]['AI'][AI]['version'])
						Name = self.Server.Mods[self.Battle['Mod']]['AI'][AI]['name']
						if Version:
							Name = Name + ' (v. ' + str (Version) + ')'
						AI_ID = AI
		if AI_ID:
			AI_Data = self.Server.Mods[self.Battle['Mod']]['AI'][AI_ID]
			self.Lobby.Send ('ADDBOT BOT' + str (Team) + ' ' + str (self.LogicFunctionBattleStatus (0, Team, Ally, 0, 0, 0, Side)) + ' 255 ' + AI_Data['shortName'])
			#ADDBOT 730 Bot [CN]Zydox 68 200 E323AI
			#ADDBOT BATTLE_ID name owner battlestatus teamcolor {AIDLL}
			return (Name)
		return ('No AI found with that name')
	
	
	def LogicInfo (self):
		self.Refresh ()
		Return = ['Battle information']
		for Alias in self.BattleUsers:
			if not Alias == self.Host.Lobby.User:
				User = self.BattleUsers[Alias]
				try:
					R = str (self.Host.Spring.SpringUDP.IsReady (Alias))
					A = str (self.Host.Spring.SpringUDP.IsAlive (Alias))
				except:
					R = 'N/A'
					A = 'N/A'
				Return.append (Alias + '   ' + 'A:' + A + '   R:' + R)
		return (Return)
	
	
	def LogicFunctionBattleStatus (self, Ready, Team, Ally, Spec, Hcp, Sync, Side):
		Status = 0
		
		if Ready:	Status = Status + 2
		Tmp = self.Lobby.dec2bin (int (Team) - 1, 4)
		if Tmp[0]:	Status = Status + 4
		if Tmp[1]:	Status = Status + 8
		if Tmp[2]:	Status = Status + 16
		if Tmp[3]:	Status = Status + 32
		Tmp = self.Lobby.dec2bin (int (Ally) - 1, 4)
		if Tmp[0]:	Status = Status + 64
		if Tmp[1]:	Status = Status + 128
		if Tmp[2]:	Status = Status + 256
		if Tmp[3]:	Status = Status + 512
		if Spec:	Status = Status + 1024
		Tmp = self.Lobby.dec2bin (int (Hcp), 7)
		if Tmp[0]:	Status = Status + 2048
		if Tmp[1]:	Status = Status + 4096
		if Tmp[2]:	Status = Status + 8192
		if Tmp[3]:	Status = Status + 16384
		if Tmp[4]:	Status = Status + 32768
		if Tmp[5]:	Status = Status + 65536
		if Tmp[6]:	Status = Status + 131072
		#262144
		#524288
		#1048576
		#2097152
		if Sync == 1:	Status = Status + 4194304
		elif Sync == 2:	Status = Status + 8388608
		if Side == 'CORE':	iSide = 1
		else:	iSide = 0
		Tmp = self.Lobby.dec2bin (int (iSide), 4)
		if Tmp[0]:	Status = Status + 16777216
		if Tmp[1]:	Status = Status + 33554432
		if Tmp[2]:	Status = Status + 67108864
		if Tmp[3]:	Status = Status + 134217728
		
#b0 = undefined (reserved for future use) 
#b1 = ready (0=not ready, 1=ready) 
#b2..b5 = team no. (from 0 to 15. b2 is LSB, b5 is MSB) 
#b6..b9 = ally team no. (from 0 to 15. b6 is LSB, b9 is MSB) 
#b10 = mode (0 = spectator, 1 = normal player) 
#b11..b17 = handicap (7-bit number. Must be in range 0..100). Note: Only host can change handicap values of the players in the battle (with HANDICAP command). These 7 bits are always ignored in this command. They can only be changed using HANDICAP command. 
#b18..b21 = reserved for future use (with pre 0.71 versions these bits were used for team color index) 
#b22..b23 = sync status (0 = unknown, 1 = synced, 2 = unsynced) 
#b24..b27 = side (e.g.: arm, core, tll, ... Side index can be between 0 and 15, inclusive) 
#b28..b31 = undefined (reserved for future use) 
		Return = []
		Return.append ('Team::' + str (self.Lobby.dec2bin (int (Team) - 1, 4)))
		Return.append ('Status::' + str (Status))
		return (Status)
		return (Return)
