# -*- coding: ISO-8859-1 -*-
import os, time, datetime
import inspect
from collections import deque


class HostCmdsSpecial:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('INFO', 'HostCmdsSpecial Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc, 4 = Category (if available), 5 = Extended help (if available)
			'code':[[], 'PM', '!code', 'Displays the bots code files, bytes and last modified', 'Special'],
			'help':[['OV'], 'PM', '!help <optional term>', 'Displays help', 'Special', ['!help        displays all available commands', '!help he     displays all available commands containing "he"', '!help help   if a single match is found, a more detailed help is displayed (like this)']],
			'terminate':[[], 'PM', '!terminate', 'Shuts down the bot', 'Special'],
			'terminateall':[[], 'PM', '!terminateall', 'Shuts down all bots', 'Special'],
			'compile':[['V'], 'PM', '!compile <spring tag>', 'Compiles the provided spring version', 'Special'],
			'recompile':[['V'], 'PM', '!recompile <spring tag>', 'Re-compiles the provided spring version', 'Special'],
			'infolog':[[], 'PM', '!infolog', 'Returns the last 20 lines from the hosts infolog', 'Special'],
			'showconfig':[[], 'PM', '!showconfig', 'Returns the bot\'s config', 'Special'],
			'battlesay':[['*'], 'BattleMe', '!battlesay <text>', 'The bot says <text> in the battle room'],
			'battlesayme':[['*'], 'BattleMe', '!battlesayme <text>', 'The bot says /me <text> in the battle room'],
			'sleepsay':[['I', '*'], 'Source', '!sleepsay <sleep> <text>', 'Says <text> with a delay of <sleep> sec'],
			'reloadconfig':[[], 'Source', '!reloadconfig', 'Reloads the config files'],
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
	

	def HandleInput (self, Command, Data, User):
		self.Debug ('DEBUG', 'HandleInput::' + str (Command) + '::' + str (Data))
		
		if Command == 'code':
			Path = os.path.dirname (inspect.currentframe ().f_code.co_filename)
			Return = []
			Length = 0
			Size = 0
			LastChange = 99999999999
			Files = []
			for FileName in os.listdir (Path):
				if FileName[-3:] == '.py' and FileName != 'Unitsync.py':
					Length = max (Length, len (FileName))
					LastChange = min (LastChange, time.time() - os.path.getmtime (Path + '/' + FileName))
					Size = Size + os.path.getsize (Path + '/' + FileName)
					Files.append (FileName)
			for File in Files:
				Return.append (self.StringPad (File, Length, ' ') + '  ' + self.StringPad (str (os.path.getsize (Path + '/' + File)), 8, ' ') + '  ' + str (round ((time.time() - os.path.getmtime (Path + '/' + File)) / 3600, 1)) + " hours ago")
			Return.sort ()
			Return.append (self.StringPad ('Summary:', Length, ' ') + '  ' + self.StringPad (str (Size), 8, ' ') + '  ' + str (round (LastChange / 3600, 1)) + " hours ago")
			return ([True, Return])
		elif Command == 'help':
			Result = {}
			Matches = 0
			for Command in self.HostCmds.Commands:
				if not self.HostCmds.ActiveAlias.has_key (Command):		# Exclude all alias commands
					Line = self.HostCmds.Commands[Command][2] + '   ' + self.HostCmds.Commands[Command][3]
					if len (self.HostCmds.Commands[Command]) > 4:
						Category = self.HostCmds.Commands[Command][4]
					else:
						Category = '*'
					if not Result.has_key (Category):
						Result[Category] = []
					if len (Data) == 0:
						if self.Host.HandleAccess ({'Command':Command, 'User':User}, 'INTERNAL_AUTH_CHECK'):
							Result[Category].append (Line)
							Matches += 1
							Match = Command
					elif Data[0].lower () in Line.lower ():
						if self.Host.HandleAccess ({'Command':Command, 'User':User}, 'INTERNAL_AUTH_CHECK'):
							Result[Category].append (Line)
							Matches += 1
							Match = Command
			Return = []
			if Matches == 1:
				Return.append ('==[ !' + Match + ' ]==')
				Return.append (self.HostCmds.Commands[Match][2])
				Return.append (self.HostCmds.Commands[Match][3])
				if len (self.HostCmds.Commands[Match]) > 5:
					for Line in self.HostCmds.Commands[Match][5]:
						Return.append (' ' + Line)
			else:
				if len (Result) > 0:
					Categories = Result.keys ()
					Categories.sort ()
					for Category in Categories:
						if len (Result[Category]):
							if Category != '*':
								Return.append ('==[ ' + Category + ' ]==')
								Result[Category].sort ()
								Return = Return + Result[Category]
								Return.append (chr (160))		# No-break space char
					if Result.has_key ('*') and len (Result['*']):
						Return.append ('==[ Uncategorized ]==')
						Result['*'].sort ()
						Return = Return + Result['*']
				else:
					Return = 'No help was found for that command'
			return ([True, Return])
		elif Command == 'terminate':
			self.Host.Terminate ()
			return ([True, 'Terminated'])
		elif Command == 'terminateall':
			self.Server.Terminate ()
			return ([True, 'All hosts terminated'])
		elif Command == 'compile' or Command == 'recompile':
			self.Host.Lobby.BattleLock (1)
			self.Host.Lobby.BattleSay ('Battle locked, building spring "' + str (Data[0]) + '"...', 1)
			if Command == 'compile':
				Result = self.Server.SpringUnitsync.Load (Data[0])
			elif Command == 'recompile':
				Result = self.Server.SpringUnitsync.Load (Data[0], 1)
			if Result:
				Return = 'Spring "' + str (Data[0]) + '" compiled'
			else:
				Return = 'Spring "' + str (Data[0]) + '" compile failed'
			self.Host.Lobby.BattleSay ('Battle un-locked, build completed', 1)
			self.Host.Lobby.BattleLock (0)
			return ([True, Return])
		elif Command == 'infolog':
			try:
				File = open('/root/.spring/infolog.txt', 'r')
			except IOError as Error:
				self.Debug ('ERROR', 'File open failed: ' + str (Error))
				return ([False, 'Infolog read failed'])
			Return = deque ([])
			for Line in File:
				Return.append (Line)
				if len (Return) > 20:
					Return.popleft ()
			File.close ()
			return ([True, ['Last 20 lines of the infolog:'] + list (Return)])
		elif Command == 'showconfig':
			Return = []
			for Var in self.Host.GroupConfig.keys ():
				if not isinstance(self.Host.GroupConfig[Var], dict) and not isinstance(self.Host.GroupConfig[Var], list):
					Return.append (str (Var) + ' => ' + str (self.Host.GroupConfig[Var]))
			Return.sort ()
			return ([True, ['Autohost config:'] + Return])
		elif Command == 'battlesay':
			self.Host.Lobby.BattleSay (Data[0])
			return ([True, 'OK'])
		elif Command == 'battlesayme':
			self.Host.Lobby.BattleSay (Data[0], 1)
			return ([True, 'OK'])
		elif Command == 'sleepsay':
			time.sleep (Data[0])
			return ([True, Data[1]])
		elif Command == 'reloadconfig':
			self.Server.HandleCFG.LoadCFG (1, 1)
			return ([True, 'Config reloaded'])
	
	
	def StringPad (self, String, Length, Char = '0'):
		while len (String) < Length:
			String = String + str (Char)
		return (String)