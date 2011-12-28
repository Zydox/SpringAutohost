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
		elif Event == 'LOGININFOEND':
			self.InitLoad = 0
		elif Event == 'CLIENTSTATUS' and self.Lobby.Users[Data[0]]['InBattle']:
			print ""
			print self.InitLoad
			print Event
			print Data
			print self.Lobby.Users[Data[0]]
			print self.Lobby.Battles[self.Lobby.Users[Data[0]]['InBattle']]


C = Collection ()