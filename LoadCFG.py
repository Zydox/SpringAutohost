# -*- coding: ISO-8859-1 -*-
class LoadCFG:
	def __init__ (self, Class):
		self.Server = Class
		self.Debug = Class.Debug
		self.LoadCFG ()
	
	
	def LoadCFG (self):
		self.Debug ("Load CFG")
		self.Server.Config = {
			'LobbyServer':{'Host':'taspringmaster.clan-sy.com', 'Port':8200},
			'MainAccount':['TourneyBot', 'DoxiePooh', 0],
			'UnitsyncPath':'/usr/local/lib/libunitsync.so',
			'SpringExec':'/usr/local/bin/spring-dedicated',
			'TempPath':'/tmp/',
		}
		
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
				'Mod':'Balanced Annihilation V7.19',
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