# -*- coding: ISO-8859-1 -*-
import sys

class HandleCFG:
	def __init__ (self, Class):
		self.Server = Class
		self.Debug = Class.Debug
		self.LoadCFG ()
	
	
	def LoadCFG (self):
		self.Debug ("Load CFG")
		self.Server.Config = {'General':{}, 'Groups':{}, 'GroupUsers':{}}
		if len (sys.argv) < 2:
			print 'Missing config file (python server.py <conf file1> <font file2> ...)'
			sys.exit ()
		
		for File in sys.argv[1:]:
			self.LoadFile (File)
#		print self.Server.Config
#		sys.exit ()
		
		self.Server.AccessCommands = {
			'code':['owner', 'admin'],
			'udp':['owner'],
			'start':['owner', 'admin', '%BattlePlayer%'],
			'kick':['owner', 'admin', 'operator'],
			'ring':['admin', 'operator', '%BattlePlayer%', '%GamePlayer%'],
			'forcestart':['owner', 'admin'],
		}
		self.Server.AccessRoles = {
			'owner':{
				'[CN]Zydox':1,
			},
			'admin':{
				'[CN]Zydox':1,
				'[Fx]Droid':1,
				'BrainDamage':1,
			},
			'operator':{
			},
		}
	
	def LoadFile (self, File):
		self.Debug ("Load file: " + File)
		Type = ''
		UserID = ''
		GroupID = ''
		FP = open (File, "r")
		for Line in FP:
			Line = Line.strip ()
			if Line and not Line[0] == '#':
				if Line[0:9] == '[GENERAL]':
					Type = 'General'
					GroupID = UserID = ''
				elif Line[0:7] == '[GROUP=' and Line[-1] == ']':
					Type = 'Group'
					GroupID = Line[7:-1].strip ()
					UserID = ''
				elif Line[0:6] == '[USER=' and Line[-1] == ']':
					Type = 'User'
					UserID = Line[6:-1].strip ()
					if not self.Server.Config['GroupUsers'].has_key (GroupID):
						self.Server.Config['GroupUsers'][GroupID] = {}
					if not self.Server.Config['GroupUsers'][GroupID].has_key (UserID):
						self.Server.Config['GroupUsers'][GroupID][UserID] = {'Account':UserID}
				elif Line.index ('='):
					Var = Line[0:Line.index ('='):].strip ()
					Value = Line[Line.index ('=') + 1:].strip ()
					print '::' + Type + '::' + str (GroupID) + '::' + str (UserID) + '::' + Var + '==' + Value
					if Type == 'General':
						self.Server.Config['General'][Var] = Value
					elif Type == 'Group':
						if not self.Server.Config['Groups'].has_key (GroupID):
							self.Server.Config['Groups'][GroupID] = {}
						self.Server.Config['Groups'][GroupID][Var] = Value
					elif Type == 'User':
						self.Server.Config['GroupUsers'][GroupID][UserID][Var] = Value
		FP.close ()