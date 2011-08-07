# -*- coding: ISO-8859-1 -*-

class HostCmdsBattle:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('HostCmdsBattle Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc
			'map':[['*'], 'Source', '!map <map name>', 'Changes the map to <map name>'],
			'maps':[[], 'PM', '!maps', 'Return a list with all the available maps'],
			'start':[[], 'Source', '!start', 'Starts the battle if possible'],
			'stop':[[], 'Source', '!stop', 'Stops the battle'],
			'lock':[['OB'], 'Source', '!lock [0/1]', 'Locks/unlocks the battle'],
			'kick':[['V'], 'Source', '!kick <user>', 'Kicks <user> from the battle'],
			'ring':[['OV'], 'Source', '!ring [<user>]', 'Rings a specific user or all unready users'],
			'addbox':[['I', 'I', 'I', 'I', 'I'], 'Source', '!addbox <> <> <> <> <>', 'Adds a startbox'],
			'udp':[['*'], 'Source', '!udp <command>', 'Sends a command to the spring server'],
			'forcestart':[[], 'Source', '!forcestart', 'Force start the battle'],
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
		

	def HandleInput (self, Command, Data):
		self.Debug ('HandleInput::' + str (Command) + '::' + str (Data))
		
		if (Command == "map"):
			if (self.Server.Maps.has_key (Data[0])):
				self.Host.Lobby.BattleMap (Data[0])
				return ('Map changed to ' + str (Data[0]))
			else:
				return ('Map "' + str (Data[0]) + '" not found')
		elif Command == 'maps':
			Return = []
			for Map in self.Server.Maps:
				Return.append (Map)
			Return.sort ()
			return (Return)
		elif (Command == "start"):
#			ScriptURI = str (self.Server.Config['TempPath']) + 'Script.txt'
#			self.Host.Spring.GenerateBattleScript (ScriptURI)
#			self.SpringPID = subprocess.Popen([self.Server.Config['SpringExec'], ScriptURI]) 
			self.Host.Spring.SpringStart ()
			self.Host.Lobby.BattleStart ()
			return ('Battle started')
		elif (Command == "stop"):
			Return = self.Host.Spring.SpringStop ()
			self.Host.Lobby.BattleStop ()
			return (Return)
		elif (Command == "lock"):
			if len (Data) == 1:
				Lock = Data[0]
			else:
				Lock = {0:1, 1:0}[self.Host.Lobby.Battles[self.Host.Lobby.BattleID]['Locked']]
			self.Host.Lobby.BattleLock (Lock)
			if Lock:
				return ('Battle locked')		
			else:
				return ('Battle unlocked')		
		elif (Command == 'kick'):
			self.Host.Spring.SpringTalk ('/kick ' + Data[0])
			if self.Host.Lobby.Users.has_key (Data[0]):
				self.Host.Lobby.BattleKick (Data[0])
				return ('User kicked')
			else:
				return ('Can\'t find the user')

		elif Command == 'ring':
			if len (Data) == 1:
				self.Host.Lobby.BattleRing (Data[0])
				return ('Ringing "' + str (Data[0]) + '"')
			else:
				for User in self.Host.Lobby.BattleUsers:
					if self.Host.Lobby.BattleUsers[User]['Spectator'] == 0 and self.Host.Lobby.BattleUsers[User]['Ready'] == 0:
						self.Host.Lobby.BattleRing (User)
				return ('Ringing all unready users')
		elif (Command == 'addbox'):
			self.Host.Lobby.BattleAddBox (Data[0] - 1, Data[1], Data[2], Data[3], Data[4])
			return ('Box added')
		elif Command == 'udp':
			self.Host.Spring.SpringTalk (Data[0])
		elif Command == 'forcestart':
			self.Host.Spring.SpringTalk ('/forcestart')
			return ('Battle started')