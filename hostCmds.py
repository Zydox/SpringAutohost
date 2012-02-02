# -*- coding: ISO-8859-1 -*-
import hostCmdsBattle
import hostCmdsSpecial
import hostCmdsLadderbot
import hostCmdsDownload
import hostCmdsUsers
from doxFunctions import *


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
		
	
	def HandleInput (self, Source, Command, Data, User, ReturnSuccess = False):
		self.Debug ('DEBUG', 'HandleInput::' + str (Source) + '::' + str (Command) + '::' + str (Data))
		try:
			if self.HostCmdsBattle.Commands.has_key (Command):
				Return = self.HostCmdsBattle.HandleInput (Command, Data)
			elif self.HostCmdsSpecial.Commands.has_key (Command):
				Return = self.HostCmdsSpecial.HandleInput (Command, Data, User)
			elif self.HostCmdsLadderbot.Commands.has_key (Command):
				Return = self.HostCmdsLadderbot.HandleInput (Command, Data)
			elif self.HostCmdsDownload.Commands.has_key (Command):
				Return = self.HostCmdsDownload.HandleInput (Command, Data)
			elif self.HostCmdsUsers.Commands.has_key (Command):
				Return = self.HostCmdsUsers.HandleInput (Command, Data, User)
			elif self.Host.GroupConfig['Alias'].has_key (Command):
				if len (self.Host.GroupConfig['Alias'][Command]) == 1:
					Command = self.Host.GroupConfig['Alias'][Command][0]
					for iArg in range (0, len (Data)):
						Command = Command.replace ('%' + str (iArg + 1), Data[iArg])
					Cmd = doxReturnValue (Command, ' ')
					Input = Command[len (Cmd) + 1:]
					Input = doxExtractInput (Input, self.Commands[Cmd][0])
					if Input[0]:
						return (self.HandleInput (Source, Cmd, Input[1], User))
					else:
						Return = [False, 'Alias command failed::' + Input[1]]
				else:
					Return = [True, []]
					for Command in self.Host.GroupConfig['Alias'][Command]:
						for iArg in range (0, len (Data)):
							Command = Command.replace ('%' + str (iArg + 1), Data[iArg])
						Cmd = doxReturnValue (Command, ' ')
						Input = Command[len (Cmd) + 1:]
						Input = doxExtractInput (Input, self.Commands[Cmd][0])
						if Input[0]:
							Result = self.HandleInput (Source, Cmd, Input[1], User, True)
							if not Result[0]:
								Return[0] = False
							if isinstance (Result[1], list):
								for Line in Result[1]:
									Return[1].append (Line)
							else:
								Return[1].append (Result[1])
						else:
							Return[0] = False
							Return[1].append ('Alias command failed::' + Input[1])
							break
					Return[1].append ('Alias command completed')
			else:
				Return = [False, 'Unknown command type']
		except Exception as Error:
			self.Debug ('ERROR', 'Failed with error: ' + str (Error), 1)
			Return = [False, 'Internal failure (crashed)']
		
		if ReturnSuccess:
			return (Return)
		if Return and len (Return) > 1:
			if not Return[0]:
				print 'FAILED...'
				print Return[1]
				print '...'
			return (Return[1])
	
	
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
