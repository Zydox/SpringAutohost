# -*- coding: ISO-8859-1 -*-
import localconfig
import ConfigParser 
import tasbot
from tasbot.customlog import Log
 
class LoadCFG:
	def __init__ (self, Class):
		self.Server = Class
		self.Debug = Class.Debug
		self.LoadCFG ()
	
	def LoadCFG (self):
		self.Debug ("Load CFG")
		try:
			self.Server.Config = localconfig.Server
		except:
			Log.Error('using default server config')
			self.Server.Config = {
				'LobbyServer':{'Host':'springrts.com', 'Port':8200},
				'MainAccount':'[pyah]Master',
				'UnitsyncPath':'/usr/lib/libunitsync.so',
				'SpringExec':'/usr/bin/spring-dedicated'
			}
		try:
			self.Server.Groups = localconfig.Groups
		except:
			Log.Error('using default server config')
			self.Server.Groups = {
				'pyah':{
					'Mod':'Evolution RTS - v1.5',
					'Map':'Comet Catcher Redux',
					'ChannelsReport':[['autohostdev']],
					'Accounts':[('[pyah]Host_01','PASSWORD',0)]
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
