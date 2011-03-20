# -*- coding: ISO-8859-1 -*-
import localconfig

class LoadCFG:
	def __init__ (self, Class):
		self.Server = Class
		self.Debug = Class.Debug
		self.LoadCFG ()
	
	
	def LoadCFG (self):
		self.Debug ("Load CFG")
		self.Server.Config = localconfig.Server
		
		self.Server.Groups = {
			'BA_Tourney':{
				'Mod':'Balanced Annihilation V7.19',
				'Map':'Comet Catcher Redux',
				'ChannelsReport':[['tourney'], ['cn']],
				'Accounts':[ ['TourneyBot%d'%i,'machine', 8460+i] for i in range(5) ]
			},
			'teh':{
				'Mod':'Balanced Annihilation V7.19',
				'Map':'Comet Catcher Redux',
				'ChannelsReport':[['infolog']],
				'Accounts':[
					['TourneyBot','DoxiePooh', 8468],
				]
			},
		}
		self.IP = localconfig.IP
		
		self.Server.AccessCommands = {
			'code':['owner', 'admin'],
			'udp':['owner'],
			'start':['owner', 'admin', '%BattlePlayer%'],
			'kick':['owner', 'admin', 'operator'],
			'ring':['admin', 'operator', '%BattlePlayer%', '%GamePlayer%'],
		}
		self.Server.AccessRoles = {
			'owner':{
				'[CN]Zydox':1,
				'_koshi_':1,
				'BrainDamage':1,
			},
			'admin':{
				'[CN]Zydox':1,
				'_koshi_':1,
				'BrainDamage':1,
			},
			'operator':{
			},
		}
