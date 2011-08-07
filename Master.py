# -*- coding: ISO-8859-1 -*-
import Lobby
import threading
import time


class Master (threading.Thread):
	def __init__ (self, ClassServer):
		threading.Thread.__init__ (self)
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('Master Init')
		self.Lobby = Lobby.Lobby (ClassServer, self.HandleInput, self.HandleEvent, ClassServer.Config['MainAccount'])
	
	
	def run (self):
		self.Debug ('Start master')
		self.Lobby.start ()
	
	
	def HandleEvent (self, Event, Data):
		self.Debug ('HandleEvent::' + str (Event) + '::' + str (Data))
	
	
	def HandleInput (self, Source, Data):
		self.Debug ('HandleCommand::' + str (Source) + '::' + str (Data))
		
		
		if (Source == 'SAIDPRIVATE'):
			Command = Data[1].split (' ')
			if (Command[0] == '!Host' and len (Command) == 2):
				if (self.Server.Groups.has_key (Command[1])):
					Result = self.SpawnHost (Command[1])
					if (Result['OK']):
						self.Lobby.Send ("SAYPRIVATE " + Data[0] + " Hosting " + Command[1] + " (" + str (Result['Host']) + ")")
					else:
						self.Lobby.Send ("SAYPRIVATE " + Data[0] + " No Host available for " + Command[1])
				else:
					self.Lobby.Send ("SAYPRIVATE " + Data[0] + " Unknown group")
			if (Command[0] == '!User' and len (Command) == 2):
				if (self.Lobby.Users.has_key (Command[1])):
					self.Lobby.Send ("SAYPRIVATE " + Data[0] + " " + str (self.Lobby.Users[Command[1]]))
					
	
	
	def SpawnHost (self, Group):
		Return = {'OK':0}
		if (self.Server.Groups.has_key (Group)):
			Setup = self.Server.Groups[Group]
			if (len (Setup['Accounts']) > 0):
				for Host in Setup['Accounts']:
					if (not self.Lobby.Users.has_key (Host[0]) or self.Lobby.Users[Host[0]]['InBattle'] == 0):
						Return['OK'] = 1
						Return['Host'] = Host[0]
						self.Server.SpawnHost (Group, Host)
						break
		return (Return)