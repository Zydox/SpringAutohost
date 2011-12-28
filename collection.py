#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import handleCFG
import time
import lobby


class Collection:
	def __init__ (self):
		self.Debug ("Initiate")
		self.HandleCFG = handleCFG.HandleCFG (self)
		self.Start ()
	
	
	def Debug (self, Info = '', Info2 = ''):
		pass
	
	
	def Start (self):
		self.Debug ()
		self.Lobby = lobby.Lobby (self.Debug, self.Debug, self.Event, self.Config['General'])
		self.Lobby.start ()
	
	
	def Event (self, Event, Data):
		print ""
		print Event
		print Data


C = Collection ()