#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import hostCmdsBattleBalance
import hostCmdsBattleLogic
import lobby

class Testing:
	def __init__ (self):
		self.Lobby = lobby.Lobby (self.Debug, self.Debug, self.Debug, self.Debug, {})
		self.Balance = hostCmdsBattleBalance.HostCmdsBattleBalance (self, self.Lobby, self)
		self.Logic = hostCmdsBattleLogic.HostCmdsBattleLogic (self, self.Lobby, self)
		self.Balance.DebugBalanceFunction = self.DisplayBalance
		self.Battle = {'Teams':0}
		self.Lobby.BattleID = 1
		self.Lobby.Battles = {self.Lobby.BattleID:{}}
		self.SetData ()
		self.Balance.LogicBalance ()
	
	
	def Debug (self, i = '', i2 = '', i3 = ''):
		pass
	
	
	def SetData (self):
		Players = {'[SNTT]lfing': 6, 'DeadnightWarrior': 5, '[CoW]HermuldSuuri': 6, 'ismo': 5, 'KipZonderKop': 3, 'NTG': 6}
		Players = {'[SNTT]lfing': 6, '[CoW]HermuldSuuri': 6, 'ismo': 5, 'NTG': 6, 'DeadnightWarrior': 5}
		Players = {'[SNTT]lfing': 6, 'DeadnightWarrior': 5, '[ONE]MotionLine': 5, 'Masta_Ali': 6, 'ismo': 5, 'NTG': 6}
#		Players = {'[CN]Zydox': 6, '[CN]Plato': 4, '[tN]Ray': 6, '[AG]Abma': 5}
		Players = {'Player1':1, 'Player2':6, 'Player3':6, 'Player4':6, 'Player5':7, 'Player7':7}
		Teams = 2
		
		self.Battle['Teams'] = Teams
		self.Lobby.BattlePlayers = {}
		for User in Players:
			self.Lobby.BattleUsers[User] = {'Rank':int (Players[User]), 'AI':0, 'Spectator':0, 'Ally':-1}
			self.Lobby.Users[User] = {'Rank':int (Players[User]), 'AI':0, 'Spectator':0, 'Ally':-1}
	
	
	def DisplayBalance (self, Balance):
		Teams = {}
		TeamRank = {}
		for User in Balance:
			if not Teams.has_key (User[1]):
				Teams[User[1]] = []
				TeamRank[User[1]] = 0
			Teams[User[1]].append (User[0])
			Teams[User[1]].sort ()
			TeamRank[User[1]] += self.Lobby.Users[User[0]]['Rank']
		
		for Team in Teams.keys ():
			print '#=Team[ ' + str (Team) + ' ]=Rank[ ' + str (TeamRank[Team]) + ' ]==========================#'
			for User in Teams[Team]:
				print '* ' + User + '\t' + str (self.Lobby.Users[User]['Rank'])

T = Testing ()