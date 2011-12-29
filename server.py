#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import handleCFG
import debug
import host
import time
import springUnitsync

#
#	Server
#		Debug - debug
#		HandleCFG - handleCFG
#		SpringUnitsync - springUnitsync
#			SpringCompile - springCompile
#		Hosts = host {}
#			Lobby - lobby
#				Ping - lobby
#			HostCmds - hostCmds
#			Spring - spring
#				SpringUDP - spring
#			-UserRoles [User]
#

class Server:
	def __init__ (self):
		self.ClassDebug = debug.Debug ()
		self.Debug = self.ClassDebug.Debug
		self.Debug ("Initiate")
		self.HandleCFG = handleCFG.HandleCFG (self)
		self.ClassDebug.SetFile ('/tmp/Debug.log')
		self.SpringUnitsync = springUnitsync.SpringUnitsync (self)
		
		self.Hosts = {}
		
		self.Start ()
		
	
	def Start (self):
		self.Debug ("Start server")
		for Group in self.Config['Groups'].keys ():
			self.SpawnHost (Group)
	
	
	def SpawnHost (self, Group = None, Account = None):
		self.Debug ("Spawn Host (" + str (Group) + "/" + str (Account) + ")")
		
		if Group:
			GroupRange = [Group]
		else:
			GroupRange = self.Config['Groups'].keys ()
		
		if Account:
			AccountRange = [Account]
		else:
			AccountRange = []
			for Group in GroupRange:
				for Account in self.Config['GroupUsers'][Group].keys ():
					AccountRange.append (Account)
		AccountRange.sort ()
		
		for Group in GroupRange:
			if self.Config['Groups'].has_key (Group):
				for Account in AccountRange:
					if self.Config['GroupUsers'][Group].has_key (Account):
						Config = self.Config['Groups'][Group]
						for Key in Config.keys ():
							if self.Config['GroupUsers'][Group][Account].has_key (Key):
								Config[Key] = self.Config['GroupUsers'][Group][Account][Key]
						self.Hosts[Account] = host.Host (Account, self, Config, self.Config['GroupUsers'][Group][Account])
						self.Hosts[Account].start ()
						break	# only spawn one host for each group
	
	
	def RemoveHost (self, Account):
		self.Debug ()
		del (self.Hosts[Account])
	
	
	def Terminate (self):
		self.Debug ()
		for Host in self.Hosts.keys ():
			self.Hosts[Host].Terminate ()

S = Server ()