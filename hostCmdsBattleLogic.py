# -*- coding: ISO-8859-1 -*-
import time
from decimal import *
import math
import random


class HostCmdsBattleLogic:
	def __init__ (self, ClassHostCmdsBattle, ClassServer, ClassHost):
		self.HostCmdsBattle = ClassHostCmdsBattle
		self.Server = ClassServer
		self.Host = ClassHost
		self.Debug = ClassServer.Debug
		self.Lobby = ClassHost.Lobby
		self.MapsRandom = {'Pos':0, 'List':{}}
	
	
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
			return ([False, 'Mod doesn\'t exist'])
		UnitsyncMap = self.Host.GetUnitsyncMap (Map)
		if not UnitsyncMap:
			return ([False, 'Map doesn\'t exist'])
		Desc = self.Host.Battle['BattleDescription']
		if self.Server.Config['General']['SpringBuildDefault'] != self.Host.SpringVersion:
			Desc = 'Dev build:' + str (self.Host.SpringVersion) + ', ' + Desc
		self.Lobby.BattleOpen (Mod,  UnitsyncMod['Hash'], Map, UnitsyncMap['Hash'], Desc, 16)
		self.Host.HostCommandWait ('OPENBATTLE')
		self.Lobby.BattleEnableUnitsAll ()
		return ([True, 'Battle opened'])
	
	
	def LogicCloseBattle (self):
		self.Lobby.BattleClose ()
		self.Host.HostCommandWait ('BATTLECLOSED')
		return ([True, 'Battle Closed'])
	
	
	def LogicRing (self, SearchUser = None):
		self.Refresh ()
		if SearchUser:
			User = self.LogicFunctionUserInBattle (SearchUser)
			if not User:
				return ([False, 'User "' + str (SearchUser) + '" is not in this battle'])
			self.Host.Lobby.BattleRing (User)
			return ([True, 'Ringing "' + str (User) + '"'])
		else:
			for User in self.BattleUsers:
				if self.BattleUsers[User]['Spectator'] == 0 and self.BattleUsers[User]['Ready'] == 0:
					self.Host.Lobby.BattleRing (User)
			return ([True, 'Ringing all unready users'])
	
	
	def LogicAddBot (self, Team, Ally, SearchSide, Color, Bot):
		if not self.Host.Lobby.BattleID:
			return ([False, 'No battle open'])
		self.Refresh ()
		Version = 0
		AI_ID = 0
		Mod = self.Host.GetUnitsyncMod (self.Battle['Mod'])
		
		Side = self.LogicFunctionSearchMatch (SearchSide, Mod['Sides'], 0, 0)
		if not Side:
			return ([False, 'Side "' + str (SearchSide) + '" doesn\'t exist'])
		
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
			self.Host.HostCommandWait ('ADDBOT')
			return ([True, Name])
		return ([False, 'No AI found with that name'])
	
	
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
		return ([True, Return])
	
	
	def LogicSpec (self, SearchUser):
		User = self.LogicFunctionUserInBattle (SearchUser)
		if not User:
			return ([False, 'User "' + str (SearchUser) + '" is not in this battle'])
		self.Lobby.Send ('FORCESPECTATORMODE ' + str (User))
		return ([True, 'User "' + str (User) + '" spectated'])
	
	
	def LogicKick (self, SearchUser):
		self.Refresh ()
		if self.Lobby.User.lower () == SearchUser.lower ():
			return ([False, 'Can\'t kick the host... use !terminate'])
		User = self.LogicFunctionUserInBattle (SearchUser)
		if not User:
			return ([False, 'User "' + str (SearchUser) + '" is not in this battle'])
		if self.Host.Lobby.BattleUsers[User]['AI']:
			self.Host.Lobby.BattleKickAI (User)
			self.Host.Spring.SpringTalk ('/kick ' + User)
			return ([True, 'AI "'+ str (User) + '" kicked'])
		else:
			self.Host.Lobby.BattleKick (User)
			self.Host.Spring.SpringTalk ('/kick ' + User)
			return ([True, 'User "'+ str (User) + '" kicked'])
	
	
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
			return ([True, Return])
		else:
			return ([True, 'No AI\'s in the battle'])
	
	
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
		return ([True, 'IDs fixed'])
	
	
	def LogicForceTeam (self, SearchUser, Team):
		self.Refresh ()
		if Team < 1 or Team > 16:
			return ([False, 'Team has to be between 1 to 16'])
		User = self.LogicFunctionUserInBattle (SearchUser)
		if not User:
			return ([False, 'User "' + str (SearchUser) + '" is not in this battle'])
		Team -= 1
		if self.BattleUsers[User]['Ally'] != Team:
			if self.BattleUsers[User]['AI']:
				self.Lobby.BattleUpdateAI (User, self.LogicFunctionBattleStatus (0, self.BattleUsers[User]['Team'], Team, 0, self.BattleUsers[User]['Handicap'], 0, self.BattleUsers[User]['Side']), self.LogicFunctionBattleColor (self.BattleUsers[User]['Color']))
			else:
				self.Lobby.BattleForceTeam (User, Team)
		return ([True, 'Team changed'])
	
	
	def LogicForceID (self, SearchUser, ID):
		self.Refresh ()
		if ID < 1 or ID > 16:
			return ([False, 'ID has to be between 1 to 16'])
		User = self.LogicFunctionUserInBattle (SearchUser)
		if not User:
			return ([False, 'User "' + str (SearchUser) + '" is not in this battle'])
		ID -= 1
		if self.BattleUsers[User]['Team'] != ID:
			if self.BattleUsers[User]['AI']:
				self.Lobby.BattleUpdateAI (User, self.LogicFunctionBattleStatus (0, ID, self.BattleUsers[User]['Ally'], 0, self.BattleUsers[User]['Handicap'], 0, self.BattleUsers[User]['Side']), self.LogicFunctionBattleColor (self.BattleUsers[User]['Color']))
			else:
				self.Lobby.BattleForceID (User, ID)
		return ([True, 'ID changed'])
	
	
	def LogicForceColor (self, SearchUser, Color):
		self.Refresh ()
		if not len (Color) == 6 or Color.upper ().strip ('0123456789ABCDEF'):
			return ([False, 'Color was not a Hex RGB color'])
		User = self.LogicFunctionUserInBattle (SearchUser)
		if not User:
			return ([False, 'User "' + str (SearchUser) + '" is not in this battle'])
		if not self.BattleUsers[User]['AI']:
			self.Lobby.BattleForceColor (User, self.LogicFunctionBattleColor (Color))
		else:
			self.Lobby.BattleUpdateAI (User, self.LogicFunctionBattleStatus (0, self.BattleUsers[User]['Team'], self.BattleUsers[User]['Ally'], 0, self.BattleUsers[User]['Handicap'], 0, self.BattleUsers[User]['Side']), self.LogicFunctionBattleColor (Color))
		return ([True, 'Color changed'])
	
	
	def LogicChangeMap (self, Map, Action = 'Fixed'):
		self.Refresh ()
		Pos = 0
		if Action == 'Reorder' or len (self.MapsRandom['List']) == 0:
			self.MapsRandom = {'Pos':0, 'List':{}}
			Maps = self.Host.GetUnitsyncMap ('#KEYS#')
			random.seed ()
			print Maps
			random.shuffle (Maps)
			iPos = 0
			print ''
			print Maps
			for Map in Maps:
				iPos += 1
				self.MapsRandom['List'][iPos] = Map
			if Action == 'Reorder':
				return ([True, 'Maps reordered'])
		if Action == 'Next':
			Pos = self.MapsRandom['Pos'] + 1
			if Pos > len (self.MapsRandom['List']):
				Pos = 1
		elif Action == 'Prev':
			Pos = self.MapsRandom['Pos'] - 1
			if Pos < 1:
				Pos = len (self.MapsRandom['List'])
		elif Action == 'Random':
			random.seed ()
			Pos = random.randint (1, len (self.MapsRandom['List']))
		elif Action == 'Fixed':
		  	Match = self.LogicFunctionSearchMatch (Map, self.Host.GetUnitsyncMap ('#KEYS#'))
			if Match:
				for MapID in self.MapsRandom['List'].keys ():
					if self.MapsRandom['List'][MapID] == Match:
						Pos = MapID
						break
			else:
				Matches = self.LogicFunctionSearchMatch (Map, self.Host.GetUnitsyncMap ('#KEYS#'), 1)
				if Matches:
					Return = ['Multiple maps found, listing the 10 first:']
					for Map in Matches:
						Return.append (Map)
						if len (Return) == 11:
							break
					return ([False, Return])
		
		if Pos:
			NewMap = self.MapsRandom['List'][Pos]
			UnitsyncMap = self.Host.GetUnitsyncMap (NewMap)
			if UnitsyncMap:
				self.MapsRandom['Pos'] = Pos
				self.Host.Battle['Map'] = NewMap
				self.Host.Lobby.BattleMap (NewMap, UnitsyncMap['Hash'])
				self.LogicFunctionMapLoadDefaults ()
				self.LogicFunctionLoadBoxes ()
				self.Host.HandleLocalEvent ('BATTLE_MAP_CHANGED', [NewMap])
				return ([True, 'Map changed to ' + str (NewMap)])
		else:
			return ([False, 'Map "' + str (Map) + '" not found'])
	
	
	def LogicListMaps (self, Search = None):
		Return = []
		if Search:
			Maps = self.LogicFunctionSearchMatch (Search, self.Host.GetUnitsyncMap ('#KEYS#'), 1)
		else:
			Maps = self.Host.GetUnitsyncMap ('#KEYS#')
		for Map in Maps:
			Return.append (Map)
		Return.sort ()
		Return = ['Maps:'] + Return
		return ([True, Return])
	
	
	def LogicListMods (self, Search = None):
		Return = []
		if Search:
			Mods = self.LogicFunctionSearchMatch (Search, self.Host.GetUnitsyncMod ('#KEYS#'), 1)
		else:
			Mods = self.Host.GetUnitsyncMod ('#KEYS#')
		for Mod in Mods:
			Return.append (Mod)
		Return.sort ()
		Return = ['Mods:'] + Return
		return ([True, Return])
	
	
	def LogicSetSpringVersion (self, SpringVersion):
		if self.Server.SpringUnitsync.SpringCompile.ExistsSpringVersion (SpringVersion):
			Result = self.Server.SpringUnitsync.Load (SpringVersion)
			self.Host.SpringVersion = SpringVersion
			self.Lobby.BattleClose ()
			self.LogicOpenBattle ()
			return ([True, 'Spring "' + str (SpringVersion) + '" loaded'])
		else:
			return ([False, 'Spring "' + str (SpringVersion) + '" not found (use !compile to add it)'])
	
	
	def LogicSetModOption (self, Option, Value = None):
		self.Debug ('INFO', str (Option) + '=>' + str (Value))
		if not self.Host.Lobby.BattleID:
			return ([False, 'No battle is open'])
		Mod = self.Host.GetUnitsyncMod (self.Host.Lobby.Battles[self.Host.Lobby.BattleID]['Mod'])
		if not Mod.has_key ('Options'):
			return ([True, 'This mod has no options'])
		elif not Mod['Options'].has_key (Option):
			Return = ['Valid ModOptions are:']
			for Key in Mod['Options'].keys ():
				Return.append (Key + ' - ' + Mod['Options'][Key]['Title'])
			return ([False, Return])
		elif Value == None:
			return ([False, self.LogicFunctionOptionValueValid (Mod['Options'][Option], Value, 1)])
		else:
			Result = self.LogicFunctionOptionValueValid (Mod['Options'][Option], Value)
			if Result['OK']:
				self.Debug ('DEBUG', str (Value) + ' => ' + str (Result['Value']))
				self.Host.Battle['ModOptions'][Option] = Result['Value']
				self.LogicFunctionBattleUpdateScript ()
				return ([True, 'OK'])
			else:
				return ([False, self.LogicFunctionOptionValueValid (Mod['Options'][Option], Value, 1)])
	
	
	def LogicSetMapOption (self, Option, Value = None):
		self.Debug ('INFO', str (Option) + '=>' + str (Value))
		if not self.Host.Lobby.BattleID:
			return ([False, 'No battle is open'])
		Map = self.Host.GetUnitsyncMap (self.Host.Lobby.Battles[self.Host.Lobby.BattleID]['Map'])
		if not Map.has_key ('Options'):
			return ([True, 'This map has no options'])
		elif not Map['Options'].has_key (Option):
			Return = ['Valid MapOptions are:']
			for Key in Map['Options'].keys ():
				Return.append (Key + ' - ' + Map['Options'][Key]['Title'])
			return ([False, Return])
		elif Value == None:
			return ([False, self.LogicFunctionOptionValueValid (Map['Options'][Option], Value, 1)])
		else:
			Result = self.LogicFunctionOptionValueValid (Map['Options'][Option], Value)
			if Result['OK']:
				self.Debug ('DEBUG', str (Value) + ' => ' + str (Result['Value']))
				self.Host.Battle['MapOptions'][Option] = Result['Value']
				self.LogicFunctionBattleUpdateScript ()
				return ([True, 'OK'])
			else:
				return ([False, self.LogicFunctionOptionValueValid (Map['Options'][Option], Value, 1)])
	
	
	def LogicSetStartPos (self, StartPos):
		self.Debug ('INFO', StartPos)
		if StartPos < 4:
			self.Host.Battle['StartPosType'] = StartPos
			self.LogicFunctionBattleUpdateScript ()
			self.LogicFunctionLoadBoxes ()
			return ([True, 'StartPos set'])
		else:
			return ([False, 'StartPos must be between 0 and 3'])
	
	
	def LogicStartBattle (self, ForceStart = 0):
		self.Debug ('INFO')
		self.Refresh ()
		self.LogicFixID ()
		
		if not ForceStart:
			for User in self.BattleUsers:
				if not self.BattleUsers[User]['Ready'] and not self.BattleUsers[User]['Spectator']:
					return ([False, 'Not all users are ready yet'])
		
		Locked = self.Lobby.Battles[self.Lobby.BattleID]['Locked']
		self.Lobby.BattleLock (1)
		self.Lobby.BattleSay ('Preparing to start the battle...', 1)
		time.sleep (1)
		
		if self.Host.Spring.SpringStart ():
			self.Lobby.BattleStart ()
			self.Host.HostCommandWait ('CLIENTSTATUS')
			self.Lobby.BattleLock (Locked)
			return ([True, 'Battle started'])
		else:
			self.Lobby.BattleLock (Locked)
			return ([False, 'Battle failed to start'])
	
	
	def LogicSetHandicap (self, SearchUser, Hcp):
		self.Debug ('INFO', 'User:' + str (SearchUser) + ', Hcp:' + str (Hcp))
		User = self.LogicFunctionUserInBattle (SearchUser)
		if not User:
			return ([False, 'User "' + str (SearchUser) + '" is not in this battle'])
		if Hcp >= 0 and Hcp <= 100:
			if self.BattleUsers[User]['AI']:
				self.Lobby.BattleUpdateAI (User, self.LogicFunctionBattleStatus (0, self.BattleUsers[User]['Team'], self.BattleUsers[User]['Ally'], 0, int (Hcp), 0, self.BattleUsers[User]['Side']), self.LogicFunctionBattleColor (self.BattleUsers[User]['Color']))
			else:
				self.Lobby.BattleHandicap (User, Hcp)
			return ([True, 'OK'])
		else:
			return ([False, 'Handicap must be in the range of 0 - 100'])
	
	
	def LogicReHostWithMod (self, Mod):
		self.Refresh ()
		
		Match = self.LogicFunctionSearchMatch (Mod, self.Host.GetUnitsyncMod ('#KEYS#'))
		if Match and self.Battle['Mod'] == Match:
			return ([True, '"' + str (Match) + '" is already hosted'])
		elif Match:
			self.Host.Battle['Mod'] = Match
			self.LogicCloseBattle ()
			self.LogicOpenBattle ()
			self.LogicFunctionLoadBoxes ()
			return ([True, 'Mod changed to "' + Match + '"'])
		else:
			Matches = self.LogicFunctionSearchMatch (Mod, self.Host.GetUnitsyncMod ('#KEYS#'), 1)
			if Matches:
				Return = ['Multiple mods found, listing the 10 first:']
				for Mod in Matches:
					Return.append (Mod)
					if len (Return) == 11:
						break
				return ([False, Return])
		return ([False, 'Mod "' + str (Mod) + '" not found'])
	
	
	def LogicAddBox (self, Left, Top, Right, Bottom, Team = -1):
		self.Refresh ()
		if Left > 100 or Top > 100 or Right > 100 or Bottom > 100 or Left < 0 or Top < 0 or Right < 0 or Bottom < 0:
			return ([False, 'Box values must be between 0 and 100'])
		elif Team < -1 or Team == 0 or Team > 16:
			return ([False, 'Team must be between 1 and 16'])
		
		if Team == -1:
			for iTeam in range (0, 15):
				if not self.Battle['Boxes'].has_key (iTeam):
					Team = iTeam
					break
			if Team == -1:
				return ([False, 'No team is free, please specify which should be replaced'])
		else:
			Team = Team - 1
		
		if self.Battle['Boxes'].has_key (Team):
			self.LogicRemoveBox (Team + 1)
		self.Lobby.BattleAddBox (Team, Left * 2, Top * 2, Right * 2, Bottom * 2)
		return ([True, 'Box added'])
	
	
	def LogicSplitBox (self, Type, Size, ClearBoxes = 0):
		self.LogicSetStartPos (2)
		if Type != 'h' and Type != 'v' and Type != 'c1' and Type != 'c2' and Type != 'c' and Type != 's':
			return ([False, 'The box type wasn\'t of a valid type'])
		if Size < 1 or Size > 100:
			return ([False, 'Size must be between 1 and 100'])
		if ClearBoxes:
			self.LogicRemoveBoxes ()
		if Type == 'v':
			self.LogicAddBox (0, 0, Size, 100, 1)
			self.LogicAddBox (100 - Size, 0, 100, 100, 2)
		elif Type == 'h':
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
		return ([True, 'Boxes added'])
	
	
	def LogicClearBox (self, Box):
		if Box < 0 or Box > 16:
			return ([False, 'Box has to be between 0 and 16'])
		elif Box:
			self.LogicRemoveBox (Box)
			return ([True, 'Box cleared'])
		else:
			self.LogicRemoveBoxes ()
			return ([True, 'Boxes cleared'])
	
	
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
			return ([False, 'Can only save boxes for "Choose in game"'])
		
		Boxes = []
		for Team in self.Battle['Boxes'].keys ():
			Boxes.append (str (Team) + ' ' + str (self.Battle['Boxes'][Team][0]) + ' ' + str (self.Battle['Boxes'][Team][1]) + ' ' + str (self.Battle['Boxes'][Team][2]) + ' ' + str (self.Battle['Boxes'][Team][3]))
		if len (Boxes) > 0:
			Boxes = '\n'.join (Boxes)
			self.Server.HandleDB.StoreBoxes (self.Host.Group, self.Battle['Map'], self.Host.Battle['Teams'], self.Host.Battle['StartPosType'], Boxes)
			return ([True, 'Saved'])
		else:
			return ([False, 'No boxes to save'])
	
	
	def LogicLoadPreset (self, Preset = 'Default'):
		Config = self.Server.HandleDB.LoadPreset (self.Host.Group, Preset)
		if Config:
			for Command in Config.split ('\n'):
				self.Host.HandleInput ('INTERNAL', '!' + Command.strip ())
			return ([True, 'Preset loaded'])
		else:
			return ([True, 'No preset found for "' + str (Preset) + '"'])
	
	
	def LogicSavePreset (self, Preset):
		self.Refresh ()
		Config = ['map ' + self.Battle['Map'], 'teams ' + str (self.Host.Battle['Teams'])]
		Mod = self.Host.GetUnitsyncMod (self.Battle['Mod'])
		for ModKey in Mod['Options'].keys ():
			if self.Host.Battle['ModOptions'].has_key (ModKey):
				if str (Mod['Options'][ModKey]['Default']) != str (self.Host.Battle['ModOptions'][ModKey]):
					Config.append ('modoption ' + str (ModKey) + ' ' + str (self.Host.Battle['ModOptions'][ModKey]))
		self.Server.HandleDB.StorePreset (self.Host.Group, Preset, '\n'.join (Config))
		return ([True, 'Saved'])
	
	
	def LogicSetTeams (self, Teams):
		if Teams > 16 or Teams < 2:
			return ([False, 'Teams has to be between 2 and 16'])
		self.Host.Battle['Teams'] = Teams
		self.HostCmdsBattle.Balance.LogicBalance ()
		return ([True, 'OK'])
	
	
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
				return ([True, '"' + Match + '" has been disabled'])
		else:
			Matches = self.LogicFunctionSearchMatch (SearchUnit, Units, 1, 0)
			if Matches:
				Matches = ['Available units:'] + Matches
				return ([False, Matches])
		return ([False, 'No match found'])
	
	
	def LogicEnableUnitsAll (self):
		self.Lobby.BattleEnableUnitsAll ()
		return ([True, 'All units enabled'])
	
	
	def LogicFixColors (self, ColorUser = None):
		self.Debug ('DEBUG', str (ColorUser))
		self.Refresh ()
		List = ['FF0000', '00FF00', '0000FF', '00FFFF', 'FF00FF', 'FFFF00', '000000', 'FFFFFF', '808080']
		
		''' Collect current colors '''
		CurrentList = {}
		for User in self.BattleUsers:
			if not self.BattleUsers[User]['Spectator'] or self.BattleUsers[User]['AI']:
				CurrentList[self.BattleUsers[User]['Team']] = self.Lobby.BattleUsers[User]['Color']
		
		if ColorUser:
			User = self.LogicFunctionUserInBattle (ColorUser)
			if not User:
				return ([False, 'User "' + str (ColorUser) + '" is not in this battle'])
			ColorUser = User
			for Diff in [400, 300, 200, 150, 100, 50, 10, 0]:
#				print 'DIFF::' + str (Diff)
				for Color in List:
					ColorOK = 1
					for Team in CurrentList.keys ():
						if Team != self.BattleUsers[ColorUser]['Team']:
#							print 'CNG::' + str (ColorUser) + '::' + str (Color) + '<>' + str (CurrentList[Team]) + '::' + str (self.LogicFunctionCompareColors (self.Lobby.BattleUsers[ColorUser]['Color'], Color))
							ColorDiff = self.LogicFunctionCompareColors (Color, CurrentList[Team])
							if ColorDiff <= Diff:
#								print '----Skip(BAD_EXISTING)'
								ColorOK = 0
					if ColorOK and Color != self.Lobby.BattleUsers[ColorUser]['Color']:
#						print '--CNG-CHANGE::' + ColorUser + '::' + Color
						self.Lobby.BattleUsers[ColorUser]['Color'] = Color
						return (self.LogicForceColor (ColorUser, Color))
		else:
			for User in self.BattleUsers:
				if not self.BattleUsers[User]['Spectator'] or self.BattleUsers[User]['AI']:
					for Team in CurrentList.keys ():
						if Team != self.BattleUsers[User]['Team']:
#							print 'CHK::' + User + '::' + str (self.LogicFunctionCompareColors (self.BattleUsers[User]['Color'], CurrentList[Team]))
							if self.LogicFunctionCompareColors (self.BattleUsers[User]['Color'], CurrentList[Team]) < 50:
#								print '--CHK-CHANGE'
								self.LogicFixColors (User)
			return ([True, 'Colors fixed'])
	
	
	def LogicSetBotSide (self, SearchUser, SearchSide):
		User = self.LogicFunctionUserInBattle (SearchUser)
		if not User:
			return ([False, 'User "' + str (SearchUser) + '" is not in this battle'])
		if self.BattleUsers[User]['AI']:
			Mod = self.Host.GetUnitsyncMod (self.Battle['Mod'])
		  	Side = self.LogicFunctionSearchMatch (SearchSide, Mod['Sides'], 0, 0)
		  	if not Side:
		  		return ([False, 'Side "' + str (SearchSide) + '" doesn\'t exist'])
			self.Lobby.BattleUpdateAI (User, self.LogicFunctionBattleStatus (0, self.BattleUsers[User]['Team'], self.BattleUsers[User]['Ally'], 0, self.BattleUsers[User]['Handicap'], 0, Side), self.LogicFunctionBattleColor (self.BattleUsers[User]['Color']))
			return ([True, 'OK'])
		else:
			return ([False, 'User "' + str (User) + '" is not a bot'])
	
	
	def LogicFunctionUserInBattle (self, User):
		if self.Lobby.BattleID:
			Match = self.LogicFunctionSearchMatch (User, self.Lobby.BattleUsers.keys ())
			if self.Lobby.BattleUsers.has_key (Match):
				return (Match)
		return (False)
	
	
	def LogicFunctionCompareColors (self, Color1, Color2):
		Diff = 0
		Diff += abs (int (Color1[4:6], 16) - int (Color2[4:6], 16))
		Diff += abs (int (Color1[2:4], 16) - int (Color2[2:4], 16))
		Diff += abs (int (Color1[0:2], 16) - int (Color2[0:2], 16))
		return (Diff)
	
	
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
			for Match in List.keys ():
				if Search.lower () in List[Match].lower ():
					if Search.lower () == List[Match].lower () and not ListMatches:
						self.Debug ('INFO', 'Perfect match:' + str (List[Match]))
						return (List[Match])
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
				if Value >= Option['Min'] and Value <= Option['Max'] and (Decimal ((Value / Option['Step'])) % 1 == 0 or Decimal ((Value / Option['Step'])) % 1 == 1):
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
		Mod = self.Host.GetUnitsyncMod (self.Host.Battle['Mod'])
		if Mod and Mod.has_key ('Options') and len (Mod['Options']):
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
		Map = self.Host.GetUnitsyncMap (self.Host.Battle['Map'])
		self.Host.Battle['MapOptions'] = {}
		if Map and Map.has_key ('Options') and len (Map['Options']):
			for Key in Map['Options'].keys ():
				if not self.Host.Battle['MapOptions'].has_key (Key):
					self.Host.Battle['MapOptions'][Key] = Map['Options'][Key]['Default']