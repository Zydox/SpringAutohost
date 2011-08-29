# -*- coding: ISO-8859-1 -*-
import sys

class HandleCFG:
	def __init__ (self, Class):
		self.Server = Class
		self.Debug = Class.Debug
		self.LoadCFG ()
	
	
	def LoadCFG (self):
		self.Debug ("Load CFG")
		self.Server.Config = {}
		if len (sys.argv) < 2:
			print 'Missing config file (python server.py <conf file1> <font file2> ...)'
			sys.exit ()
		
		for File in sys.argv[1:]:
			self.LoadFile (File)
#		print self.Server.Config
#		sys.exit ()
		
		self.Server.Groups = {
			'BA_Tourney':{
				'Mod':'Balanced Annihilation V7.19',
				'Map':'Comet Catcher Redux',
				'ChannelsReport':[['tourney'], ['cn']],
				'Accounts':[
					['TourneyBot1','machine', 8460],
					['TourneyBot2','machine', 8461],
					['TourneyBot3','machine', 8462],
					['TourneyBot4','machine', 8463],
					['TourneyBot5','machine', 8464],
					['TourneyBot6','machine', 8465],
					['TourneyBot7','machine', 8466],
					['TourneyBot8','machine', 8467],
				]
			},
			'teh':{
				'Mod':'Balanced Annihilation V7.50',
				'Map':'Comet Catcher Redux',
				'ChannelsReport':[['teh'], ['cn']],
				'Accounts':[
					['TourneyBot','DoxiePooh', 8468],
				]
			},
		}
		
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
		ConfigType = ''
		FP = open (File, "r")
		for Line in FP:
			Line = Line.strip ()
			if Line and not Line[0] == '#':
				if Line[0:8] == '[MASTER]':
					ConfigType = 'Master'
				elif Line[0:7] == '[SLAVE]':
					ConfigType = 'Slave'
				elif Line.index ('='):
					if ConfigType == 'Master':
						self.Server.Config[Line[0:Line.index ('='):]] = Line[Line.index ('=') + 1:]
		FP.close ()