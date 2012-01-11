# -*- coding: ISO-8859-1 -*-
import time
from decimal import *


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
		else:
			self.Battle = {}
			self.BattleUsers = {}
			self.Debug ('WARNING', 'self.Host.Lobby.BattleID doesn\'t exist')
	
	
	def LogicOpenBattle (self):
		Mod = self.Host.Battle['Mod']
		Map = self.Host.Battle['Map']
		UnitsyncMod = self.Host.GetUnitsyncMod (Mod)
		if not UnitsyncMod:
			return ('Mod doesn\'t exist')
		UnitsyncMap = self.Host.GetUnitsyncMap (Map)
		if not UnitsyncMap:
			return ('Map doesn\'t exist')
		Desc = self.Host.Battle['BattleDescription']
		if self.Server.Config['General']['SpringBuildDefault'] != self.Host.SpringVersion:
			Desc = 'Dev build:' + str (self.Host.SpringVersion) + ', ' + Desc
		self.Lobby.BattleOpen (Mod,  UnitsyncMod['Hash'], Map, UnitsyncMap['Hash'], Desc, 16)
		self.Lobby.BattleEnableUnitsAll ()
	
	
	def LogicCloseBattle (self):
		self.Lobby.BattleClose ()
	
	
	def LogicRing (self, User =''):
		self.Refresh ()
		if User:
			Match = self.LogicFunctionSearchMatch (User, self.BattleUsers.keys ())
			if self.BattleUsers.has_key (Match):
				self.Host.Lobby.BattleRing (Match)
				return ('Ringing "' + str (Match) + '"')
			else:
				return ('No user found')
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
		Mod = self.Host.GetUnitsyncMod (self.Battle['Mod'])
		
		SideOK = 0
		for iSide in Mod['Sides'].keys ():
			if Mod['Sides'][iSide] == Side:
				SideOK = 1
		if not SideOK:
			return ('Side "' + str (Side) + '" doesn\'t exist')
		
		for AI in Mod['AI']:
			if Mod['AI'][AI]['shortName'] == Bot:
				if not Mod['AI'][AI].has_key ('version') or Version < Mod['AI'][AI]['version']:
					if Mod['AI'][AI].has_key ('version'):
						try:
							Version = float (Mod['AI'][AI]['version'])
						except:
							Version = None
						Name = Mod['AI'][AI]['name']
						if Version:
							Name = Name + ' (v. ' + str (Version) + ')'
						AI_ID = AI
		if AI_ID:
			AI_Data = Mod['AI'][AI_ID]
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
	
	
	def LogicKickBots (self):
		self.Refresh ()
		Return = []
		for User in self.Battle['Users']:
			if self.Host.Lobby.BattleUsers.has_key (User):
				if self.Host.Lobby.BattleUsers[User]['AI']:
					self.Host.Lobby.BattleKickAI (User)
					self.Host.Spring.SpringTalk ('/kick ' + User)
					Return.append ('AI "' + User + '" kicked')
		if Return:
			return (Return)
	
	
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
				self.Lobby.BattleUpdateAI (AI, self.LogicFunctionBattleStatus (0, ID, self.BattleUsers[AI]['Ally'], 0, self.BattleUsers[AI]['Handicap'], 0, self.BattleUsers[AI]['Side']), self.LogicFunctionBattleColor (self.BattleUsers[AI]['Color']))
				if ID < 15:
					ID = ID + 1
		return ('IDs fixed')
	
	
	def LogicForceTeam (self, User, Team):
		self.Refresh ()
		if Team < 1 or Team > 16:
			return ('Team has to be between 1 to 16')
		if self.BattleUsers.has_key (User):
			Team -= 1
			if self.BattleUsers[User]['Ally'] != Team:
				self.Lobby.BattleForceTeam (User, Team)
			return ('Team changed')
		else:
			return ('User not found')
	
	
	def LogicForceID (self, User, ID):
		self.Refresh ()
		if ID < 1 or ID > 16:
			return ('ID has to be between 1 to 16')
		if self.BattleUsers.has_key (User):
			ID -= 1
			if self.BattleUsers[User]['Team'] != ID:
				self.Lobby.BattleForceID (User, ID)
			return ('ID changed')
		else:
			return ('User not found')
	
	
	def LogicForceColor (self, User, Color):
		self.Refresh ()
		if not len (Color) == 6 or Color.upper().strip ('0123456789ABCDEF'):
			return ('Color was not a Hex RGB color')
		if self.BattleUsers.has_key (User):
			self.Lobby.BattleForceColor (User, self.LogicFunctionBattleColor (Color))
			return ('Color changed')
		else:
			return ('User not found')
	
	
	def LogicChangeMap (self, Map):
		self.Refresh ()
		Match = self.LogicFunctionSearchMatch (Map, self.Host.GetUnitsyncMap ('#KEYS#'))
		if Match:
			UnitsyncMap = self.Host.GetUnitsyncMap (Match)
			if UnitsyncMap:
				self.Host.Battle['Map'] = Match
				self.Host.Lobby.BattleMap (Match, UnitsyncMap['Hash'])
				self.LogicFunctionMapLoadDefaults ()
				self.LogicFunctionLoadBoxes ()
				return ('Map changed to ' + str (Match))
		else:
			Matches = self.LogicFunctionSearchMatch (Map, self.Host.GetUnitsyncMap ('#KEYS#'), 1)
			if Matches:
				Return = ['Multiple maps found, listing the 10 first:']
				for Map in Matches:
					Return.append (Map)
					if len (Return) == 11:
						break
				return (Return)
		return ('Map "' + str (Map) + '" not found')
	
	
	def LogicListMaps (self):
		Return = []
		Maps = self.Host.GetUnitsyncMap ('#KEYS#')
		for Map in Maps:
			Return.append (Map)
		Return.sort ()
		Return = ['Maps:'] + Return
		return (Return)
	
	
	def LogicListMods (self):
		Return = []
		Mods = self.Host.GetUnitsyncMod ('#KEYS#')
		for Mod in Mods:
			Return.append (Mod)
		Return.sort ()
		Return = ['Mods:'] + Return
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
	
	
	def LogicSetModOption (self, Option, Value = None):
		self.Debug ('INFO', str (Option) + '=>' + str (Value))
		if not self.Host.Lobby.BattleID:
			return ('No battle is open')
		Mod = self.Host.GetUnitsyncMod (self.Host.Lobby.Battles[self.Host.Lobby.BattleID]['Mod'])
		if not Mod.has_key ('Options'):
			return ('This mod has no options')
		elif not Mod['Options'].has_key (Option):
			Return = ['Valid ModOptions are:']
			for Key in Mod['Options'].keys ():
				Return.append (Key + ' - ' + Mod['Options'][Key]['Title'])
			return (Return)
		elif Value == None:
			return (self.LogicFunctionOptionValueValid (Mod['Options'][Option], Value, 1))
		else:
			Result = self.LogicFunctionOptionValueValid (Mod['Options'][Option], Value)
			if Result['OK']:
				self.Debug ('DEBUG', str (Value) + ' => ' + str (Result['Value']))
				self.Host.Battle['ModOptions'][Option] = Result['Value']
				self.LogicFunctionBattleUpdateScript ()
				return ('OK')
			else:
				return (self.LogicFunctionOptionValueValid (Mod['Options'][Option], Value, 1))
	
	
	def LogicSetMapOption (self, Option, Value = None):
		self.Debug ('INFO', str (Option) + '=>' + str (Value))
		if not self.Host.Lobby.BattleID:
			return ('No battle is open')
		Map = self.Host.GetUnitsyncMap (self.Host.Lobby.Battles[self.Host.Lobby.BattleID]['Map'])
		if not Map.has_key ('Options'):
			return ('This map has no options')
		elif not Map['Options'].has_key (Option):
			Return = ['Valid MapOptions are:']
			for Key in Map['Options'].keys ():
				Return.append (Key + ' - ' + Map['Options'][Key]['Title'])
			return (Return)
		elif Value == None:
			return (self.LogicFunctionOptionValueValid (Map['Options'][Option], Value, 1))
		else:
			Result = self.LogicFunctionOptionValueValid (Map['Options'][Option], Value)
			if Result['OK']:
				self.Debug ('DEBUG', str (Value) + ' => ' + str (Result['Value']))
				self.Host.Battle['MapOptions'][Option] = Result['Value']
				self.LogicFunctionBattleUpdateScript ()
				return ('OK')
			else:
				return (self.LogicFunctionOptionValueValid (Map['Options'][Option], Value, 1))
	
	
	def LogicSetStartPos (self, StartPos):
		self.Debug ('INFO', StartPos)
		if StartPos < 4:
			self.Host.Battle['StartPosType'] = StartPos
			self.LogicFunctionBattleUpdateScript ()
			self.LogicFunctionLoadBoxes ()
			return ('StartPos set')
		else:
			return ('StartPos must be between 0 and 3')
	
	
	def LogicStartBattle (self, ForceStart = 0):
		self.Debug ('INFO')
		self.Refresh ()
		
		if not ForceStart:
			for User in self.BattleUsers:
				if not self.BattleUsers[User]['Ready'] and not self.BattleUsers[User]['Spectator']:
					return ('Not all users are ready yet')
		
		Locked = self.Lobby.Battles[self.Lobby.BattleID]['Locked']
		self.Lobby.BattleLock (1)
		self.Lobby.BattleSay ('Preparing to start the battle...', 1)
		time.sleep (1)
		
		if self.Host.Spring.SpringStart ():
			self.Lobby.BattleStart ()
			self.Lobby.BattleLock (Locked)
			return ('Battle started')
		else:
			self.Lobby.BattleLock (Locked)
			return ('Battle failed to start')
	
	
	def LogicSetHandicap (self, User, Hcp):
		self.Debug ('INFO', 'User:' + str (User) + ', Hcp:' + str (Hcp))
		if self.Host.Lobby.BattleUsers.has_key (User):
			if Hcp >= 0 and Hcp <= 100:
				if self.BattleUsers[User]['AI']:
					self.Lobby.BattleUpdateAI (User, self.LogicFunctionBattleStatus (0, self.BattleUsers[User]['Team'], self.BattleUsers[User]['Ally'], 0, int (Hcp), 0, self.BattleUsers[User]['Side']), self.LogicFunctionBattleColor (self.BattleUsers[User]['Color']))
				else:
					self.Lobby.BattleHandicap (User, Hcp)
			else:
				return ('Handicap must be in the range of 0 - 100')
		else:
			return ('User "' + str (User) + '" is not in this battle')
	
	
	def LogicReHostWithMod (self, Mod):
		self.Refresh ()
		if self.Battle['Mod'] == Mod:
			return ('"' + str (Mod) + '" is already hosted')
		else:
			if not self.Host.GetUnitsyncMod (Mod):
				return ('"' + str (Mod) + '" doesn\'t exist on this host')
			else:
				self.Host.Battle['Mod'] = Mod
				self.LogicCloseBattle ()
				self.LogicOpenBattle ()
				self.LogicFunctionLoadBoxes ()
				return ('OK')
	
	
	def LogicAddBox (self, Left, Top, Right, Bottom, Team = -1):
		self.Refresh ()
		if Left > 100 or Top > 100 or Right > 100 or Bottom > 100 or Left < 0 or Top < 0 or Right < 0 or Bottom < 0:
			return ('Box values must be between 0 and 100')
		elif Team < -1 or Team == 0 or Team > 16:
			return ('Team must be between 1 and 16')
		
		if Team == -1:
			for iTeam in range (0, 15):
				if not self.Battle['Boxes'].has_key (iTeam):
					Team = iTeam
					break
			if Team == -1:
				return ('No team is free, please specify which should be replaced')
		else:
			Team = Team - 1
		
		if self.Battle['Boxes'].has_key (Team):
			self.LogicRemoveBox (Team + 1)
		self.Lobby.BattleAddBox (Team, Left * 2, Top * 2, Right * 2, Bottom * 2)
		return ('Box added')
	
	
	def LogicSplitBox (self, Type, Size, ClearBoxes = 0):
		if Type != 'h' and Type != 'v' and Type != 'c1' and Type != 'c2' and Type != 'c' and Type != 's':
			return ('The box type wasn\'t of a valid type')
		if Size < 1 or Size > 100:
			return ('Size must be between 1 and 100')
		if ClearBoxes:
			self.LogicRemoveBoxes ()
		if Type == 'h':
			self.LogicAddBox (0, 0, Size, 100, 1)
			self.LogicAddBox (100 - Size, 0, 100, 100, 2)
		elif Type == 'v':
			self.LogicAddBox (0, 0, 100, Size, 1)
			self.LogicAddBox (0, 100 - Size, 100, 100, 2)
		elif Type =='c1':
			self.LogicAddBox (100 - Size, 0, 100, Size, 1)
			self.LogicAddBox (0, 100 - Size, Size, 100, 2)
		elif Type == 'c2':
			self.LogicAddBox (0, 0, Size, Size, 1)
			self.LogicAddBox (100 - Size, 100 - Size, 100, 100, 2)
		elif Type == 'c':
			self.LogicAddBox (0, 0, Size, Size, 1)
			self.LogicAddBox (100 - Size, 100 - Size, 100, 100, 2)
			self.LogicAddBox (100 - Size, 0, 100, Size, 3)
			self.LogicAddBox (0, 100 - Size, Size, 100, 4)
		elif Type == 's':
			self.LogicAddBox (0, 0, Size, 100, 1)
			self.LogicAddBox (100 - Size, 0, 100, 100, 2)
			self.LogicAddBox (0, 0, 100, Size, 3)
			self.LogicAddBox (0, 100 - Size, 100, 100, 4)
		return ('Boxes added')
	
	
	def LogicClearBox (self, Box):
		if Box < 0 or Box > 16:
			return ('Box has to be between 0 and 16')
		elif Box:
			self.LogicRemoveBox (Box)
			return ('Box cleared')
		else:
			self.LogicRemoveBoxes ()
			return ('Boxes cleared')
	
	
	def LogicRemoveBox (self, Team):
		self.Lobby.BattleRemoveBox (Team - 1)
	
	
	def LogicRemoveBoxes (self):
		self.Refresh ()
		if self.Battle.has_key ('Boxes'):
			for Team in self.Battle['Boxes'].keys ():
				self.Lobby.BattleRemoveBox (Team)
	
	
	def LogicSaveBoxes (self):
		self.Refresh ()
		if self.Host.Battle['StartPosType'] != 2:
			return ('Can only save boxes for "Choose in game"')
		
		Boxes = []
		for Team in self.Battle['Boxes'].keys ():
			Boxes.append (str (Team) + ' ' + str (self.Battle['Boxes'][Team][0]) + ' ' + str (self.Battle['Boxes'][Team][1]) + ' ' + str (self.Battle['Boxes'][Team][2]) + ' ' + str (self.Battle['Boxes'][Team][3]))
		if len (Boxes) > 0:
			Boxes = '\n'.join (Boxes)
			self.Server.HandleDB.StoreBoxes (self.Host.Group, self.Battle['Map'], self.Host.Battle['Teams'], self.Host.Battle['StartPosType'], Boxes)
			return ('Saved')
		else:
			return ('No boxes to save')
	
	
	def LogicLoadPreset (self, Preset = 'Default'):
		Config = self.Server.HandleDB.LoadPreset (self.Host.Group, Preset)
		if Config:
			for Command in Config.split ('\n'):
				self.Host.HandleInput ('INTERNAL', '!' + Command.strip ())
			return ('Preset loaded')
		else:
			return ('No preset found for "' + str (Preset) + '"')
	
	
	def LogicSavePreset (self, Preset):
		self.Refresh ()
		Config = ['map ' + self.Battle['Map'], 'teams ' + str (self.Host.Battle['Teams'])]
		Mod = self.Host.GetUnitsyncMod (self.Battle['Mod'])
		for ModKey in Mod['Options'].keys ():
			if self.Host.Battle['ModOptions'].has_key (ModKey):
				if str (Mod['Options'][ModKey]['Default']) != str (self.Host.Battle['ModOptions'][ModKey]):
					Config.append ('modoption ' + str (ModKey) + ' ' + str (self.Host.Battle['ModOptions'][ModKey]))
		self.Server.HandleDB.StorePreset (self.Host.Group, Preset, '\n'.join (Config))
		return ('Saved')
	
	
	def LogicSetTeams (self, Teams):
		if Teams > 16 or Teams < 2:
			return ('Teams has to be between 2 and 16')
		self.Host.Battle['Teams'] = Teams
		self.HostCmdsBattle.Balance.LogicBalance ()
		return ('OK')
	
	
	def LogicDisableUnit (self, SearchUnit):
		self.Refresh ()
		Mod = self.Host.GetUnitsyncMod ()
		
		Units = {}
		for Unit in Mod['Units'].keys ():
			Units[Unit] = Unit + ' - ' + Mod['Units'][Unit]
		
		Match = self.LogicFunctionSearchMatch (SearchUnit, Units)
		if Match:
			if Mod['Units'].has_key (Match):
				self.Lobby.BattleDisableUnits (Match)
				return ('"' + Match + '" has been disabled')
		else:
			Matches = self.LogicFunctionSearchMatch (SearchUnit, Units, 1, 0)
			if Matches:
				Matches = ['Available units:'] + Matches
				return (Matches)
		return ('No match found')
	
	
	def LogicEnableUnitsAll (self):
		self.Lobby.BattleEnableUnitsAll ()
		return ('All units enabled')
	
	
	def LogicFunctionSearchMatch (self, Search, List, ListMatches = 0, DictReturnKeys = 1):
		self.Debug ('INFO', 'Search: ' + str (Search))
		Matches = []
		if isinstance(List, list):
			for Match in List:
				if Search.lower () in Match.lower ():
					if Search == Match and not ListMatches:
						self.Debug ('INFO', 'Perfect match:' + str (Search))
						return (Search)
					else:
						Matches.append (Match)
		elif isinstance(List, dict):
			for Match in List:
				if Search.lower () in List[Match].lower ():
					if Search == Match and not ListMatches:
						self.Debug ('INFO', 'Perfect match:' + str (Search))
						return (Search)
					elif DictReturnKeys:
						Matches.append (Match)
					else:
						Matches.append (List[Match])
		if len (Matches) == 1:
			self.Debug ('INFO', 'Found:' + str (Matches[0]))
			return (Matches[0])
		elif len (Matches) and ListMatches:
			return (Matches)
		return (False)
	
	
	def LogicFunctionLoadBoxes (self):
		self.Debug ('INFO')
		if self.Host.Battle['StartPosType'] == 2:
			self.Refresh ()
			Boxes = self.Server.HandleDB.LoadBoxes (self.Host.Group, self.Battle['Map'], self.Host.Battle['Teams'], self.Host.Battle['StartPosType'])
			if Boxes:
				self.LogicRemoveBoxes ()
				for Box in Boxes.split ('\n'):
					Box = Box.split (' ')
					self.LogicAddBox (int (Box[1]) / 2, int (Box[2]) / 2, int (Box[3]) / 2, int (Box[4]) / 2, int (Box[0]) + 1)
		else:
			self.LogicRemoveBoxes ()
	
	
	def LogicFunctionOptionValueValid (self, Option, Value, Help = 0):
		Return = {'OK':0}
		if Option['Type'] == 'Select':
			if Option['Options'].has_key (Value):
				Return = {'OK':1, 'Value':Value}
			if Help == 1:
				Return = ['Valid keys for "' + str (Option['Title']) + '" are :']
				for Key in Option['Options']:
					Return.append (str (Key) + ' - ' + str (Option['Options'][Key]))
		elif Option['Type'] == 'Numeric':
			try:
				getcontext().prec = 6
				Value = float (Value)
				self.Debug ('DEBUG', Value)
				self.Debug ('DEBUG', Value >= Option['Min'])
				self.Debug ('DEBUG', Value <= Option['Max'])
				self.Debug ('DEBUG', not Value % Option['Step'])
				self.Debug ('DEBUG', Decimal ((Value / Option['Step']) % 1))
				if Value >= Option['Min'] and Value <= Option['Max'] and Decimal ((Value / Option['Step']) % 1) == 0:
					if int (Value) == Value:
						Value = int (Value)
					Return = {'OK':1, 'Value':Value}
			except:
				self.Debug ('ERROR', 'CRASH')
			if Help == 1:
				Return = 'Valid values are between ' + str (Option['Min']) + ' to ' + str (Option['Max']) + ' with a stepping of ' + str (Option['Step'])
		elif Option['Type'] == 'Boolean':
			try:
				Value = int (Value)
				if Value == 1 or Value == 0:
					Return = {'OK':1, 'Value':Value}
			except:
				pass
			if Help == 1:
				Return = 'Valid values for "' + str (Option['Title']) + '" are 0 or 1'
		return (Return)
	
	
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
		
		Mod = self.Host.GetUnitsyncMod ()
		SideOK = -1
		for iSide in Mod['Sides'].keys ():
			if Mod['Sides'][iSide] == Side:
				SideOK = iSide
		if SideOK == -1:
			SideOK = int (Side)
		Tmp = self.Lobby.dec2bin (int (SideOK), 4)
		if Tmp[0]:	Status = Status + 16777216
		if Tmp[1]:	Status = Status + 33554432
		if Tmp[2]:	Status = Status + 67108864
		if Tmp[3]:	Status = Status + 134217728
		
		return (Status)
	
	
	def LogicFunctionBattleColor (self, HexColor):
		Color = int (HexColor[4:6] + HexColor[2:4] + HexColor[0:2], 16)
		return (Color)
	
	
	def LogicFunctionBattleUpdateScript (self):
		self.Debug ('INFO')
		self.Refresh ()
		Tags = []
		if not self.Battle['ScriptTags'].has_key ('game/startpostype') or self.Battle['ScriptTags']['game/startpostype'] != str (self.Host.Battle['StartPosType']):
			Tags.append (['game/startpostype', self.Host.Battle['StartPosType']])
		if self.Host.Lobby.BattleID and self.Host.Battle.has_key ('ModOptions'):
			for Key in self.Host.Battle['ModOptions'].keys ():
				Value = self.Host.Battle['ModOptions'][Key]
				try:
					if int (Value) == Value:
						Value = int (Value)
					Tag = ['game/modoptions/' + str (Key).lower (), str (Value)]
				except:
					Tag = ['game/modoptions/' + str (Key).lower (), str (Value)]
				if not self.Battle['ScriptTags'].has_key (Tag[0]) or self.Battle['ScriptTags'][Tag[0]] != Tag[1]:
					Tags.append (Tag)
		if self.Host.Lobby.BattleID and self.Host.Battle.has_key ('MapOptions'):
			for Key in self.Host.Battle['MapOptions'].keys ():
				Value = self.Host.Battle['MapOptions'][Key]
				try:
					if int (Value) == Value:
						Value = int (Value)
					Tag = ['game/mapoptions/' + str (Key).lower (), str (Value)]
				except:
					Tag = ['game/mapoptions/' + str (Key).lower (), str (Value)]
				if not self.Battle['ScriptTags'].has_key (Tag[0]) or self.Battle['ScriptTags'][Tag[0]] != Tag[1]:
					Tags.append (Tag)
		if len (Tags) > 0:
			self.Lobby.BattleUpdateScript (Tags)
	
	
	def LogicFunctionBattleLoadDefaults (self):
		self.Debug ('INFO')
		if self.Host.Lobby.BattleID:
			Mod = self.Host.GetUnitsyncMod (self.Host.Lobby.Battles[self.Host.Lobby.BattleID]['Mod'])
		else:
			Mod = self.Host.GetUnitsyncMod (self.Host.Battle['Mod'])
		if Mod and len (Mod['Options']):
			for Key in Mod['Options'].keys ():
				if not self.Host.Battle['ModOptions'].has_key (Key):
					self.Host.Battle['ModOptions'][Key] = Mod['Options'][Key]['Default']
		try:
			if not self.Host.Battle.has_key ('StartPosType') or not int (self.Host.Battle['StartPosType']) == self.Host.Battle['StartPosType']:
				self.Host.Battle['StartPosType'] = 1
		except:
			self.Host.Battle['StartPosType'] = 1
		self.LogicFunctionMapLoadDefaults ()
	
	
	def LogicFunctionMapLoadDefaults (self):
		self.Debug ('INFO')
		if self.Host.Lobby.BattleID:
			Map = self.Host.GetUnitsyncMap (self.Host.Lobby.Battles[self.Host.Lobby.BattleID]['Map'])
		else:
			Map = self.Host.GetUnitsyncMap (self.Host.Battle['Map'])
		self.Host.Battle['MapOptions'] = {}
		if Map and Map.has_key ('Options'):
			for Key in Map['Options'].keys ():
				if not self.Host.Battle['MapOptions'].has_key (Key):
					self.Host.Battle['MapOptions'][Key] = Map['Options'][Key]['Default']