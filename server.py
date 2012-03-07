#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import handleCFG, handleDB
import debug
import host
import time
import springUnitsync
from threading import RLock

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
		self.Debug ('INFO', 'Initiate')
		self.Lock = RLock ()
		self.LogicTest = 0
		self.HandleCFG = handleCFG.HandleCFG (self)
		self.ClassDebug.SetFile (self.Config['General']['FileDebugLog'])
		self.SpringUnitsync = springUnitsync.SpringUnitsync (self)
		self.HandleDB = handleDB.HandleDB (self)
		
		self.Hosts = {}
		
		self.Start ()
		
	
	def Start (self):
		self.Debug ('INFO', 'Start server')
		for Group in self.Config['Groups'].keys ():
			self.SpawnHost (Group)
	
	
	def GetMasterLock (self, ClassHost):
		self.Debug ('INFO', 'Request')
		self.Lock.acquire ()
		ClassHost.IsMaster = True
		self.Debug ('INFO', 'Received')
	
	
	def ReleaseMasterLock (self, ClassHost):
		self.Debug ('INFO', 'Release')
		try:
			self.Lock.release ()
			ClassHost.IsMaster = False
			self.Debug ('INFO', 'Released')
		except:
			self.Debug ('ERROR', 'Release failed', 1)
	
	
	def SpawnHost (self, Group = None, Account = None):
		self.Debug ('INFO', "Spawn Host (" + str (Group) + "/" + str (Account) + ")")
		
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
					if self.Config['GroupUsers'][Group].has_key (Account) and not self.Hosts.has_key (Account):
						Config = self.Config['Groups'][Group]
						for Key in Config.keys ():
							if self.Config['GroupUsers'][Group][Account].has_key (Key):
								Config[Key] = self.Config['GroupUsers'][Group][Account][Key]
						AccountKey = Group + '=' + str (Account)
						self.Hosts[AccountKey] = host.Host (AccountKey, Group, self, Config, self.Config['GroupUsers'][Group][Account])
						self.Hosts[AccountKey].start ()
						return ([True, 'Started ' + str (AccountKey)])
	
	
	def RemoveHost (self, Account):
		self.Debug ('INFO')
		del (self.Hosts[Account])
	
	
	def Terminate (self):
		self.Debug ('INFO')
		for Host in self.Hosts.keys ():
			self.Hosts[Host].Terminate ()

S = Server ()