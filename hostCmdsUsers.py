# -*- coding: ISO-8859-1 -*-

class HostCmdsUsers:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('INFO', 'HostCmdsUsers Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc, 4 = Category (if available), 5 = Extended help (if available)
			'searchuser':[['V'], 'PM', '!searchuser <map name>', 'Searches for a user', 'DB query functions'],
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
	
	
	def HandleInput (self, Command, Data, User):
		self.Debug ('DEBUG', 'HandleInput::' + str (Command) + '::' + str (Data))
		
		if Command == 'searchuser':
			Data = self.Server.HandleDB.SearchUser  (Data[0])
			if Data:
				return (Data['User'] + ' => ' + str (Data['LastSeen']))
			return ('No user found')
