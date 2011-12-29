#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import handleCFG
import time
import lobby


class Collection:
	def __init__ (self):
		self.Debug ("Initiate")
		self.HandleCFG = handleCFG.HandleCFG (self, 0)
		self.Start ()
		self.InitLoad = 0
		self.Battles = {}
	
	
	def Debug (self, Info = '', Info2 = ''):
		pass
	
	
	def Start (self):
		self.Debug ()
		self.Lobby = lobby.Lobby (self.Debug, self.Chat, self.Event, self.Config['General'])
		self.Lobby.start ()
	
	
	def Chat (self, Source, Data):
		if Source == 'SAIDPRIVATE':
			if Data[1] == '!terminate':
				print 'Terminated by ' + str (Data[0])
				self.Lobby.Terminate ()
	
	
	def Event (self, Event, Data):
		if Event == 'ACCEPTED':
			self.InitLoad = 1
			self.CollectionReset ()
		elif Event == 'LOGININFOEND':
			self.InitLoad = 0
			self.CollectionInit ()
		elif Event == 'CLIENTSTATUS' and self.Lobby.Users[Data[0]]['InBattle']:
			User = self.Lobby.Users[Data[0]]
			Battle = self.Lobby.Battles[User['InBattle']]
			
			if Battle['Founder'] == User['User']:
				if self.Battles.has_key (Battle['ID']):
					if self.Battles[Battle['ID']] != User['InGame']:
						if User['InGame'] == 0:
							self.CollectionBattleClose (Battle['ID'])
						else:
							self.CollectionBattleOpen (Battle)
				else:
					if User['InGame'] == 0:
						self.CollectionBattleClose (Battle['ID'])
					else:
						self.CollectionBattleOpen (Battle)
				self.Battles[Battle['ID']] = User['InGame']
	
	
	def CollectionReset (self):
		# Resets the cache...
		self.Battles = {}
	
	
	def CollectionInit (self):
		# Load all not closed battles from DB
		
		for BattleKey in self.Lobby.Battles:
			Battle = self.Lobby.Battles[BattleKey]
			# Update all battles which are open and remove from first array or add to the DB
			if self.Lobby.Users[Battle['Founder']]['InGame']:
				# Battle in game
				pass
			else:
				# Battle open but not in game
				pass
		
		# Update all remaining battles to closed
	
	
	def CollectionBattleOpen (self, Battle):
		if not self.InitLoad:
			# Called when a new battle begins
			print 'Battle start'
			pass
	
	
	def CollectionBattleClose (self, BattleID):
		if not self.InitLoad:
			# Called when a battle is closed
			print 'Battle stop'
			pass

C = Collection ()