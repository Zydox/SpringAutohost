# -*- coding: ISO-8859-1 -*-
import os, time, datetime
import inspect

class HostCmdsSpecial:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('HostCmdsSpecial Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc
			'code':[[], 'Source', '!code', 'Displays the bots code files, bytes and last modified'],
			'help':[[], 'PM', '!help', 'Displays help'],
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
	

	def HandleInput (self, Command, Data):
		self.Debug ('HandleInput::' + str (Command) + '::' + str (Data))
		
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
			return (Return)
		elif Command == 'help':
			Return = []
			for Command in self.HostCmds.Commands:
				Return.append (self.HostCmds.Commands[Command][2] + '   ' + self.HostCmds.Commands[Command][3])
			return (Return)
			
	
	def StringPad (self, String, Length, Char = '0'):
		while len (String) < Length:
			String = String + str (Char)
		return (String)