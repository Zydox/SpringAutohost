# -*- coding: ISO-8859-1 -*-
import time
import math
from operator import itemgetter
import operator
import random


class HostCmdsBattleBalance:
	def __init__ (self, ClassHostCmdsBattle, ClassServer, ClassHost):
		self.HostCmdsBattle = ClassHostCmdsBattle
		self.Server = ClassServer
		self.Host = ClassHost
		self.Debug = ClassServer.Debug
		self.Lobby = ClassHost.Lobby
		self.DebugBalanceFunction = None
	
	
	def Refresh (self):
		if self.Lobby.BattleID:
			self.Battle = self.Lobby.Battles[self.Host.Lobby.BattleID]
			self.BattleUsers = self.Lobby.BattleUsers
		else:
			self.Battle = {}
			self.BattleUsers = {}
			self.Debug ('WARNING', 'self.Host.Lobby.BattleID doesn\'t exist')
		
		self.Teams = self.Host.Battle['Teams']
		self.Players = 0
		self.TeamRank = {}
		self.TeamPlayers = {}
		self.PlayerList = {}
		self.Balance = []
		self.Data = {
			'TotalRank':0,
			'OptimalTeamRank':0,
			'OptimalTeamPlayers':0,
		}
	
	
	def LogicBalance (self):
		self.Debug ('INFO')
		self.Refresh ()
		
		for iTeam in range (0, self.Teams):
			self.TeamRank[iTeam] = 0
			self.TeamPlayers[iTeam] = 0
		for User in self.BattleUsers:
			if self.BattleUsers[User]['AI']:
				self.PlayerList[User] = 1
			elif self.BattleUsers[User].has_key ('Spectator') and not self.BattleUsers[User]['Spectator']:
				self.PlayerList[User] = self.Lobby.Users[User]['Rank']
		self.Players = len (self.PlayerList)
		for User in self.PlayerList:
			self.Data['TotalRank'] = self.Data['TotalRank'] + self.PlayerList[User]
		self.Data['OptimalTeamRank'] = int (math.floor (self.Data['TotalRank'] / float (self.Teams)))
		self.Data['OptimalTeamPlayers'] = int (math.floor (self.Players / float (self.Teams)))
		
		self.BalanceClans ()
		self.BalanceTeams ()
		self.BalancePlayers ()
		
		if self.DebugBalanceFunction:
			self.DebugBalanceFunction (self.Balance)
		else:
			for Balance in self.Balance:
				self.HostCmdsBattle.Logic.LogicForceTeam (Balance[0], Balance[1])
		
		return ([True, 'Balancing...'])
	
	
	def BalanceClans (self):
		if not self.Players / float (self.Teams) > 1:
			return (True)
		Clans = {}
		for User in self.PlayerList:
			for Clan in User.split (']'):
				if Clan[0:1] == '[':
					if not Clans.has_key (Clan[1:]):
						Clans[Clan[1:]] = [User]
					else:
						Clans[Clan[1:]].append (User)
		for Clan in Clans.keys ():
			if len (Clans[Clan]) == 1:
				del (Clans[Clan])
		if len (Clans) == 0:
			return (True)
		
		for Clan in Clans.keys ():
			Players = len (Clans[Clan])
			Ranks = 0
			for User in Clans[Clan]:
				Ranks += self.PlayerList[User]
			if Players <= self.Data['OptimalTeamPlayers']:
				Team = self.GetBestTeam (Players, Ranks)
				self.TeamPlayers[Team] += Players
				self.TeamRank[Team] += Ranks
				for User in Clans[Clan]:
					del (self.PlayerList[User])
					self.Balance.append ([User, Team + 1])
	
	
	def BalanceTeams (self, IncludeEmptyTeams = 0):
		for Team in self.TeamPlayers.keys ():
			if (self.TeamPlayers[Team] or IncludeEmptyTeams) and self.TeamPlayers[Team] < self.Data['OptimalTeamPlayers']:
				NeededPlayers = self.Data['OptimalTeamPlayers'] - self.TeamPlayers[Team]
				NeededRank = self.Data['OptimalTeamRank'] - self.TeamRank[Team]
				Players = self.BalanceGetPlayers (NeededPlayers, NeededRank)
				for User in Players:
					self.TeamPlayers[Team] += 1
					self.TeamRank[Team] += self.PlayerList[User]
					self.Balance.append ([User, Team + 1])
					del (self.PlayerList[User])
	
	
	def BalanceGetPlayers (self, GetPlayers, GetRank):
		Best = GetRank
		BestUsers = []
		for iRand in range (0, 100):
			random.seed()
			Players = self.PlayerList.keys ()
			iPlayers = GetPlayers
			Users = []
			Rank = 0
			while iPlayers > 0:
				User = Players.pop (random.randint( 0,len (Players) - 1))
				iPlayers -= 1
				Users.append (User)
				Rank += self.PlayerList[User]
			if Rank == GetRank:
				Best = 0
				BestUsers = Users[:]
				break
			elif abs (GetRank - Rank) < Best:
				Best = abs (GetRank - Rank)
				BestUsers = Users[:]		
		return (BestUsers)
	
	
	def BalancePlayers (self):
		if len (self.PlayerList) == 0:
			return (True)
		self.BalanceTeams (1)
	
	
	def GetBestTeam (self, Players, Rank):
		Teams = {}
		for Team in self.TeamPlayers:
			Teams[Team] = 0
			"""	If a bunch of players are beeing placed and the searched team has no players,
					it gets a bonus value of 100k...
			"""
			if not self.TeamPlayers[Team] and Players > 1:
				Teams[Team] += 100000
			
			if self.TeamPlayers[Team] + Players == self.Data['OptimalTeamPlayers']:
				Teams[Team] += 10000
			elif self.TeamPlayers[Team] + Players < self.Data['OptimalTeamPlayers']:
				Teams[Team] += 1000
			else:
				Teams[Team] += 100
		
		for Team in self.TeamRank:
			if self.TeamRank[Team] + Rank == self.Data['OptimalTeamRank'] and self.TeamPlayers[Team] + Players == self.Data['OptimalTeamPlayers']:
				Teams[Team] += 1000
			elif self.TeamRank[Team] + Players < self.Data['OptimalTeamRank']:
				Teams[Team] += 100
			else:
				Teams[Team] += 10
			
			# Give bonus to the team with the loest rank
			Teams[Team] -= self.TeamRank[Team]
		return (sorted(Teams.items(), key=itemgetter(1), reverse=True)[0][0])
