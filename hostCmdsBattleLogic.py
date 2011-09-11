# -*- coding: ISO-8859-1 -*-

class HostCmdsBattleLogic:
	def __init__ (self, ClassHostCmdsBattle, ClassServer, ClassHost):
		self.HostCmdsBattle = ClassHostCmdsBattle
		self.Server = ClassServer
		self.Host = ClassHost
		self.Debug = ClassServer.Debug
		self.Lobby = ClassHost.Lobby
		
	
	def Refresh (self):
		if self.Host.Lobby.BattleID:
			self.Battle = self.Host.Lobby.Battles[self.Host.Lobby.BattleID]
			self.BattleUsers = self.Host.Lobby.BattleUsers
	
	
	def LogicOpenBattle (self):
		Mod = self.Host.GroupConfig['Mod']
		Map = self.Host.GroupConfig['Map']
		UnitsyncMod = self.Host.GetUnitsyncMod (Mod)
		if not UnitsyncMod:
			return ('Mod doesn\'t exist')
		UnitsyncMap = self.Host.GetUnitsyncMap (Map)
		if not UnitsyncMap:
			return ('Map doesn\'t exist')
		self.Lobby.BattleOpen (Mod,  UnitsyncMod['Hash'], Map, UnitsyncMap['Hash'], 'Test', 16)
	
	
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
	
	
	def LogicAddBot (self, Team, Ally, Side, Color, Bot):
		if not self.Host.Lobby.BattleID:
			return ('No battle open')
		self.Refresh ()
		Version = 0
		AI_ID = 0
		UnitsyncMod = self.Host.GetUnitsyncMod (self.Battle['Mod'])
		for AI in UnitsyncMod['AI']:
			if UnitsyncMod['AI'][AI]['shortName'] == Bot:
				if not UnitsyncMod['AI'][AI].has_key ('version') or Version < UnitsyncMod['AI'][AI]['version']:
					if UnitsyncMod['AI'][AI].has_key ('version'):
						print UnitsyncMod['AI'][AI]
						try:
							Version = float (UnitsyncMod['AI'][AI]['version'])
						except:
							Version = None
						Name = UnitsyncMod['AI'][AI]['name']
						if Version:
							Name = Name + ' (v. ' + str (Version) + ')'
						AI_ID = AI
		if AI_ID:
			AI_Data = UnitsyncMod['AI'][AI_ID]
			self.Lobby.BattleAddAI ('ADDBOT BOT' + str (Team) + ' ' + str (self.LogicFunctionBattleStatus (0, Team - 1, Ally - 1, 0, 0, 0, Side)) + ' ' + str (self.LogicFunctionBattleColor (Color)) + ' ' + AI_Data['shortName'])
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
	
	
	def LogicSpec (self, User):
		self.Refresh ()
		if self.BattleUsers.has_key (User):
			self.Lobby.Send ('FORCESPECTATORMODE ' + str (User))
			return ('User "' + str (User) + '" spectated')
		return ('User "' + str (User) + '" not found in battle')
	
	
	def LogicKick (self, User):
		self.Refresh ()
		self.Host.Spring.SpringTalk ('/kick ' + User)
		if self.Host.Lobby.BattleUsers.has_key (User):
			if self.Host.Lobby.BattleUsers[User]['AI']:
				self.Host.Lobby.BattleKickAI (User)
				return ('AI "'+ str (User) + '" kicked')
			else:
				self.Host.Lobby.BattleKick (User)
				return ('User "'+ str (User) + '" kicked')
		else:
			return ('Can\'t find the user "' + str (User) + '"')
	
	
	def LogicFixID (self):
		self.Refresh ()
		ID = 0
		AIs = []
		for User in self.BattleUsers:
			if not self.BattleUsers[User]['Spectator'] and not self.BattleUsers[User]['AI']:
				self.Lobby.BattleForceID (User, ID)
				if ID < 15:
					ID = ID + 1
			elif self.BattleUsers[User]['AI']:
				AIs.append (User)
		if len (AIs):
			for AI in AIs:
				self.Lobby.BattleUpdateAI (AI, self.LogicFunctionBattleStatus (0, ID, self.BattleUsers[AI]['Ally'], 0, 0, 0, self.BattleUsers[AI]['Side']), self.LogicFunctionBattleColor (self.BattleUsers[AI]['Color']))
				if ID < 15:
					ID = ID + 1
		return ('IDs fixed')
	
	
	def LogicChangeMap (self, Map):
		UnitsyncMap = self.Host.GetUnitsyncMap (Map)
		if UnitsyncMap:
			self.Host.Lobby.BattleMap (Map, UnitsyncMap['Hash'])
			return ('Map changed to ' + str (Map))
		else:
			return ('Map "' + str (Map) + '" not found')
	
	
	def LogicListMaps (self):
		Return = []
		UnitsyncMap = self.Host.GetUnitsyncMap ('#KEYS#')
		for Map in UnitsyncMap:
			Return.append (Map)
		Return.sort ()
		return (Return)
	
	
	def LogicSetSpringVersion (self, SpringVersion):
		if self.Server.SpringUnitsync.SpringCompile.ExistsSpringVersion (SpringVersion):
			Result = self.Server.SpringUnitsync.Load (SpringVersion)
			self.Host.SpringVersion = SpringVersion
			self.Lobby.BattleClose ()
			self.LogicOpenBattle ()
			return ('Spring "' + str (SpringVersion) + '" loaded')
		else:
			return ('Spring "' + str (SpringVersion) + '" not found (use !compile to add it)')
	
	
	def LogicBalance (self, Teams = 2, BalanceType = 'RANK'):
		self.Refresh ()
		TeamRank = {}
		PlayerRank = {}
		for iTeam in range (0, Teams):
			TeamRank[iTeam] = 0
		for User in self.BattleUsers:
			if self.BattleUsers[User]['AI']:
				PlayerRank[User] = 1
			elif not self.BattleUsers[User]['Spectator']:
				PlayerRank[User] = self.Lobby.Users[User]['Rank']
		print '==============================='
		print PlayerRank
		print TeamRank
		print '==============================='
		print ''
		
		return ('Testing')
	
	
	def LogicFunctionBattleStatus (self, Ready, Team, Ally, Spec, Hcp, Sync, Side):
		Status = 0
		if Ready:	Status = Status + 2
		Tmp = self.Lobby.dec2bin (int (Team), 4)
		if Tmp[0]:	Status = Status + 4
		if Tmp[1]:	Status = Status + 8
		if Tmp[2]:	Status = Status + 16
		if Tmp[3]:	Status = Status + 32
		Tmp = self.Lobby.dec2bin (int (Ally), 4)
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
		
		return (Status)


	def LogicFunctionBattleColor (self, HexColor):
		Color = int (HexColor[4:6] + HexColor[2:4] + HexColor[0:2], 16)
		return (Color)