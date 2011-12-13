# -*- coding: ISO-8859-1 -*-
import hostCmdsBattle
import hostCmdsSpecial
import hostCmdsLadderbot
import hostCmdsDownload

class HostCmds:
	def __init__ (self, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('HostCmds Init')
		self.Host = ClassHost
		self.Commands = {}
		self.HostCmdsBattle = hostCmdsBattle.HostCmdsBattle (self, ClassServer, ClassHost)
		self.HostCmdsSpecial = hostCmdsSpecial.HostCmdsSpecial (self, ClassServer, ClassHost)
		self.HostCmdsLadderbot = hostCmdsLadderbot.HostCmdsLadderbot (self, ClassServer, ClassHost)
		self.HostCmdsDownload = hostCmdsDownload.HostCmdsDownload (self, ClassServer, ClassHost)
		self.LoadAlias ()
		
	
	def HandleInput (self, Source, Command, Data):
		self.Debug ('HandleInput::' + str (Source) + '::' + str (Command) + '::' + str (Data))
		if self.HostCmdsBattle.Commands.has_key (Command):
			return (self.HostCmdsBattle.HandleInput (Command, Data))
		elif self.HostCmdsSpecial.Commands.has_key (Command):
			return (self.HostCmdsSpecial.HandleInput (Command, Data))
		elif self.HostCmdsLadderbot.Commands.has_key (Command):
			return (self.HostCmdsLadderbot.HandleInput (Command, Data))
		elif self.HostCmdsDownload.Commands.has_key (Command):
			return (self.HostCmdsDownload.HandleInput (Command, Data))
		elif self.Host.GroupConfig['Alias'].has_key (Command):
			Return = []
			for Command in self.Host.GroupConfig['Alias'][Command]:
				Return.append (self.Host.HandleInput ('INTERAL_RETURN', '!' + Command))
			Return.append ('Alias command completed')
			return (Return)
		else:
			return ('Unknown command type')
	
	
	def LoadAlias (self):
		self.Debug ()
		if self.Host.GroupConfig.has_key ('Alias'):
			for Key in self.Host.GroupConfig['Alias'].keys ():
				self.Commands[Key] = [[], 'PM', '!' + Key, '!' + Key]
	
	
	def Notifications (self, Event):
		self.Debug ('Notifications::' + str (Event))
		if Event == 'BATTLE_ENDED':
			print '* Battle ended'
		elif Event == 'BATTLE_STARTED':
			print '* Battle started'