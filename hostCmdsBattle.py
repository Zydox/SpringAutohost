# -*- coding: ISO-8859-1 -*-
import hostCmdsBattleLogic

class HostCmdsBattle:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('HostCmdsBattle Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Logic = hostCmdsBattleLogic.HostCmdsBattleLogic (self, ClassServer, ClassHost)
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc
			'map':[['*'], 'Source', '!map <map name>', 'Changes the map to <map name>'],
			'maps':[[], 'PM', '!maps', 'Return a list with all the available maps'],
			'start':[[], 'Source', '!start', 'Starts the battle if possible'],
			'stop':[[], 'Source', '!stop', 'Stops the battle'],
			'lock':[['OB'], 'Source', '!lock [0/1]', 'Locks/unlocks the battle'],
			'kick':[['V'], 'Source', '!kick <user>', 'Kicks <user> from the battle'],
			'ring':[['OV'], 'Source', '!ring [<user>]', 'Rings a specific user or all unready users'],
			'addbox':[['I', 'I', 'I', 'I', 'I'], 'Source', '!addbox <Team> <Left> <Top> <Right> <Bottom> (0-100)', 'Adds a startbox'],
			'udp':[['*'], 'Source', '!udp <command>', 'Sends a command to the spring server'],
			'forcestart':[[], 'Source', '!forcestart', 'Force start the battle'],
			'info':[[], 'PM', '!info', 'Returns the status of the current battle'],
			'addbot':[['I', 'I', 'V', 'V6', '*'], 'Source', '!addbot 1 1 CORE FFFFFF E323AI', 'Add a bot to the battle (Team, Ally, Side, Hex RGB Color, Bot)'],
			'spec':[['V'], 'Source', '!spec <User>', 'Spectates the specified user'],
			'fixid':[[], 'Source', '!fixid', 'Fix the player IDs'],
			'balance':[[], 'Battle', '!balance', 'Balances the battle users based on rank'],
			'openbattle':[[], 'Source', '!openbattle', 'Opens a battle'],
			'spring':[['V'], 'Source', '!spring <spring version>', 'Sets the spring version to the specified tag'],
			'modoption':[['V', '*'], 'Source', '!modoption <option> <value>', 'Sets a mod option'],
			'startpos':[['I'], 'Source', '!startpos <0-3>', 'Sets the start pos (0 Fixed, 1 Randon, 2 Choose in-game, 3 Choose now)'],
			'hcp':[['V', 'I'], 'Source', '!hcp <user> <hcp>', 'Sets the handicap for the specified user'],
			'mod':[['*'], 'Source', '!mod <mod>', 'Rehosts with the specified mod'],
			'saveboxes':[[], 'Source', '!saveboxes', 'Saves the current box setup'],
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
		

	def HandleInput (self, Command, Data):
		self.Debug ('HandleInput::' + str (Command) + '::' + str (Data))
		
		if Command == 'map':
			return (self.Logic.LogicChangeMap (Data[0]))
		elif Command == 'maps':
			return (self.Logic.LogicListMaps ())
		elif Command == 'start':
			return (self.Logic.LogicStartBattle ())
		elif Command == 'stop':
			Return = self.Host.Spring.SpringStop ()
			return (Return)
		elif Command == 'lock':
			if len (Data) == 1:
				Lock = Data[0]
			else:
				Lock = {0:1, 1:0}[self.Host.Lobby.Battles[self.Host.Lobby.BattleID]['Locked']]
			self.Host.Lobby.BattleLock (Lock)
			if Lock:
				return ('Battle locked')		
			else:
				return ('Battle unlocked')		
		elif Command == 'kick':
			return (self.Logic.LogicKick (Data[0]))
		elif Command == 'ring':
			if len (Data) == 1:
				return (self.Logic.LogicRing (Data[0]))
			else:
				return (self.Logic.LogicRing ())
		elif Command == 'addbox':
			return (self.Logic.LogicAddBox (Data[0], Data[1], Data[2], Data[3], Data[4]))
		elif Command == 'udp':
			self.Host.Spring.SpringTalk (Data[0])
		elif Command == 'forcestart':
			self.Host.Spring.SpringTalk ('/forcestart')
			return ('Battle started')
		elif Command == 'info':
			return (self.Logic.LogicInfo ())
		elif Command == 'addbot':
			return (self.Logic.LogicAddBot (Data[0], Data[1], Data[2], Data[3], Data[4]))
		elif Command == 'spec':
			return (self.Logic.LogicSpec (Data[0]))
		elif Command == 'fixid':
			return (self.Logic.LogicFixID ())
		elif Command == 'balance':
			return (self.Logic.LogicBalance ())
		elif Command == 'openbattle':
			return (self.Logic.LogicOpenBattle ())
		elif Command == 'spring':
			return (self.Logic.LogicSetSpringVersion (Data[0]))
		elif Command == 'modoption':
			return (self.Logic.LogicSetModOption (Data[0], Data[1]))
		elif Command == 'startpos':
			return (self.Logic.LogicSetStartPos (Data[0]))
		elif Command == 'hcp':
			return (self.Logic.LogicSetHandicap (Data[0], Data[1]))
		elif Command == 'mod':
			return (self.Logic.LogicReHostWithMod (Data[0]))
		elif Command == 'saveboxes':
			return (self.Logic.LogicSaveBoxes ())