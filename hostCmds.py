# -*- coding: ISO-8859-1 -*-
import hostCmdsBattle
import hostCmdsSpecial
import hostCmdsLadderbot
import hostCmdsDownload
import hostCmdsUsers

class HostCmds:
	def __init__ (self, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('INFO', 'HostCmds Init')
		self.Host = ClassHost
		self.Commands = {}
		self.ActiveAlias = {}
		self.HostCmdsBattle = hostCmdsBattle.HostCmdsBattle (self, ClassServer, ClassHost)
		self.HostCmdsSpecial = hostCmdsSpecial.HostCmdsSpecial (self, ClassServer, ClassHost)
		self.HostCmdsLadderbot = hostCmdsLadderbot.HostCmdsLadderbot (self, ClassServer, ClassHost)
		self.HostCmdsDownload = hostCmdsDownload.HostCmdsDownload (self, ClassServer, ClassHost)
		self.HostCmdsUsers = hostCmdsUsers.HostCmdsUsers (self, ClassServer, ClassHost)
		self.LoadAlias ()
		
	
	def HandleInput (self, Source, Command, Data, User):
		self.Debug ('DEBUG', 'HandleInput::' + str (Source) + '::' + str (Command) + '::' + str (Data))
		try:
			if self.HostCmdsBattle.Commands.has_key (Command):
				return (self.HostCmdsBattle.HandleInput (Command, Data))
			elif self.HostCmdsSpecial.Commands.has_key (Command):
				return (self.HostCmdsSpecial.HandleInput (Command, Data, User))
			elif self.HostCmdsLadderbot.Commands.has_key (Command):
				return (self.HostCmdsLadderbot.HandleInput (Command, Data))
			elif self.HostCmdsDownload.Commands.has_key (Command):
				return (self.HostCmdsDownload.HandleInput (Command, Data))
			elif self.HostCmdsUsers.Commands.has_key (Command):
				return (self.HostCmdsUsers.HandleInput (Command, Data, User))
			elif self.Host.GroupConfig['Alias'].has_key (Command):
				Return = []
				for Command in self.Host.GroupConfig['Alias'][Command]:
					for iArg in range (0, len (Data)):
						Command = Command.replace ('%' + str (iArg + 1), Data[iArg])
					Result = self.Host.HandleInput ('INTERAL_RETURN', '!' + Command)
					if isinstance (Result, list) :
						for Row in Result:
							Return.append (Row)
					else:
						Return.append (Result)
				Return.append ('Alias command completed')
				return (Return)
			else:
				return ('Unknown command type')
		except Exception as Error:
			self.Debug ('ERROR', 'Failed with error: ' + str (Error), 1)
			return ('Internal failure (crashed)')
	
	
	def LoadAlias (self):
		self.Debug ('INFO')
		if self.Host.GroupConfig.has_key ('Alias'):
			for Key in self.Host.GroupConfig['Alias'].keys ():
				iArgs = 0
				for Command in self.Host.GroupConfig['Alias'][Key]:
					if '%' in Command:
						for Arg in Command.split ('%')[1:]:
							if ' ' in Arg:
								Arg = Arg[0:Arg.index (' '):]
						try:
							iArgs = max (iArgs, int (Arg))
						except:
							continue
				Vars = []
				for iVar in range (0, iArgs):
					Vars.append ('V')
				self.Commands[Key] = [Vars, 'PM', '!' + Key, '!' + Key]
				self.ActiveAlias[Key] = 1
	
	
	def Notifications (self, Event):
		self.Debug ('INFO', 'Notifications::' + str (Event))
		if Event == 'BATTLE_ENDED':
			print '* Battle ended'
		elif Event == 'BATTLE_STARTED':
			print '* Battle started'
