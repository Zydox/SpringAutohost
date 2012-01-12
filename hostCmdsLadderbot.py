# -*- coding: ISO-8859-1 -*-
import os, time, datetime
import inspect

class HostCmdsLadderbot:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('INFO', 'Ladderbot Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc, 4 = Category (if available), 5 = Extended help (if available)
			'ladderbot':[['*'], 'Source', '!ladderbot <command>', 'Accepts commands from the LadderBot to set up specific battles'],
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
	

	def HandleInput (self, Command, Data):
		self.Debug ('DEBUG', 'HandleInput::' + str (Command) + '::' + str (Data))
		return (Data[0])
	
	
	def StringPad (self, String, Length, Char = '0'):
		while len (String) < Length:
			String = String + str (Char)
		return (String)