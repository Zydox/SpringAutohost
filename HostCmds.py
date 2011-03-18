# -*- coding: ISO-8859-1 -*-
import HostCmdsBattle
import HostCmdsSpecial
import HostCmdsLadderbot

class HostCmds:
	def __init__ (self, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('HostCmds Init')
		self.Host = ClassHost
		self.Commands = {}
		self.HostCmdsBattle = HostCmdsBattle.HostCmdsBattle (self, ClassServer, ClassHost)
		self.HostCmdsSpecial = HostCmdsSpecial.HostCmdsSpecial (self, ClassServer, ClassHost)
		self.HostCmdsLadderbot = HostCmdsLadderbot.HostCmdsLadderbot (self, ClassServer, ClassHost)

	def HandleInput (self, Source, Command, Data):
		self.Debug ('HandleInput::' + str (Source) + '::' + str (Command) + '::' + str (Data))
		
		
		
		if (self.HostCmdsBattle.Commands.has_key (Command)):
			return (self.HostCmdsBattle.HandleInput (Command, Data))
		elif (self.HostCmdsSpecial.Commands.has_key (Command)):
			return (self.HostCmdsSpecial.HandleInput (Command, Data))
		elif (self.HostCmdsLadderbot.Commands.has_key (Command)):
			return (self.HostCmdsLadderbot.HandleInput (Command, Data))
		else:
			return ('Unknown command type')