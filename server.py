# -*- coding: ISO-8859-1 -*-
#!/usr/bin/env python
import handleCFG
import debug
import master
import host
import time
import unitsync

#
#	Server
#		Debug - debug
#		HandleCFG - handleCFG
#		Unitsync - unitsync
#		Master - master
#			Lobby - lobby
#				Ping - lobby
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
		
		self.Unitsync = unitsync.Unitsync (self.Config['General']['PathUnitsync'])
		self.Unitsync.Init (True, 1)
		self.LoadMaps ()
		self.LoadMods ()
		
#		self.Master = master.Master (self)
		self.Hosts = {}
		
		self.Start ()
		
	
	def Start (self):
		self.Debug ("Start server")
#		self.Master.start ()
#		self.SpawnHost (1, 1)
		self.SpawnHost ('BACD', 'TourneyBot')
		
	
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
		
		for Group in GroupRange:
			if self.Config['Groups'].has_key (Group):
				for Account in AccountRange:
					if self.Config['GroupUsers'][Group].has_key (Account):
						print self.Config['GroupUsers'][Group][Account]
						self.Hosts[Account] = host.Host (self, self.Config['Groups'][Group], self.Config['GroupUsers'][Group][Account])
						self.Hosts[Account].start ()
						break
		

	def LoadMaps (self):
		self.Debug ('Load maps')
		self.Maps = {}
		for iMap in range (0, self.Unitsync.GetMapCount ()):
			Map = self.Unitsync.GetMapName (iMap)
			self.Maps[Map] = {'Hash':self.SignInt (self.Unitsync.GetMapChecksum (iMap))}
			if self.Unitsync.GetMapOptionCount (Map):
				self.Maps[Map]['Options'] = {}
				for iOpt in range (0, self.Unitsync.GetMapOptionCount (Map)):
					self.Maps[Map]['Options'][iOpt] = self.LoadOption (iOpt)
					if len (self.Maps[Map]['Options'][iOpt]) == 0:
						del (self.Maps[Map]['Options'][iOpt])
	
	
	def LoadMods (self):
		self.Debug ('Load mods')
		self.Mods = {}
		for iMod in range (0, self.Unitsync.GetPrimaryModCount ()):
			self.Unitsync.Init (True, 1)
			self.Unitsync.AddAllArchives (self.Unitsync.GetPrimaryModArchive (iMod))
			Mod = self.Unitsync.GetPrimaryModName (iMod)
			self.Mods[Mod] = {
				'Hash':self.SignInt (self.Unitsync.GetPrimaryModChecksum (iMod)),
				'Title':self.Unitsync.GetPrimaryModName (iMod),
				'Sides':{},
				'Options':{},
				'AI':{},
			}
			if self.Unitsync.GetSideCount():
				for iSide in xrange (self.Unitsync.GetSideCount()):
					self.Mods[Mod]['Sides'][iSide] = self.Unitsync.GetSideName (iSide)
			if self.Unitsync.GetModOptionCount ():
				for iOpt in xrange (self.Unitsync.GetModOptionCount ()):
					self.Mods[Mod]['Options'][iOpt] = self.LoadOption (iOpt)
					if len (self.Mods[Mod]['Options'][iOpt]) == 0:
						del (self.Mods[Mod]['Options'][iOpt])
			if self.Unitsync.GetSkirmishAICount ():
				for iAI in range (0, self.Unitsync.GetSkirmishAICount ()):
					self.Mods[Mod]['AI'][iAI] = {}
					for iAII in range (0, self.Unitsync.GetSkirmishAIInfoCount (iAI)):
						self.Mods[Mod]['AI'][iAI][self.Unitsync.GetInfoKey (iAII)] = self.Unitsync.GetInfoValue (iAII)
	
	
	def LoadOption (self, iOpt):
		Data = {}
		if self.Unitsync.GetOptionType (iOpt) == 1:
			Data = {
				'Key':self.Unitsync.GetOptionKey (iOpt),
				'Title':self.Unitsync.GetOptionName (iOpt),
				'Type':'Boolean',
				'Default':self.Unitsync.GetOptionBoolDef (iOpt),
			}
		elif self.Unitsync.GetOptionType (iOpt) == 2:
			Data = {
				'Key':self.Unitsync.GetOptionKey (iOpt),
				'Title':self.Unitsync.GetOptionName (iOpt),
				'Type':'Select',
				'Default':self.Unitsync.GetOptionListDef (iOpt),
				'Options':{},
			}
			if self.Unitsync.GetOptionListCount (iOpt):
				for iItem in range (0, self.Unitsync.GetOptionListCount (iOpt)):
					Data['Options'][self.Unitsync.GetOptionListItemKey (iOpt, iItem)] = self.Unitsync.GetOptionListItemName (iOpt, iItem) + ' (' + self.Unitsync.GetOptionListItemDesc (iOpt, iItem) + ')'
		elif self.Unitsync.GetOptionType (iOpt) == 3:
			Data = {
				'Key':self.Unitsync.GetOptionKey (iOpt),
				'Title':self.Unitsync.GetOptionName (iOpt),
				'Type':'Numeric',
				'Default':self.Unitsync.GetOptionNumberDef (iOpt),
				'Min':self.Unitsync.GetOptionNumberMin (iOpt),
				'Max':self.Unitsync.GetOptionNumberMax (iOpt),
				'Step':self.Unitsync.GetOptionNumberStep (iOpt),
			}
		elif self.Unitsync.GetOptionType (iOpt) == 5:
			Ignore = 1
		else:
			self.Debug ('ERROR::Unkown options type (' + str (self.Unitsync.GetOptionType (iOpt)) + ')')
		return (Data)
	
	
	def SignInt (self, Int):
		if Int > 2147483648:
			Int = Int - 2147483648 * 2
		return (Int)

S = Server ()