# -*- coding: ISO-8859-1 -*-
import time
from doxFunctions import *

class hostCmdsVoting:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('INFO', 'hostCmdsVoting Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc, 4 = Category (if available), 5 = Extended help (if available)
			'vote':[['V', 'O*'], 'Source', '!vote', 'Starts a vote', 'Voting'],
			'endvote':[[], 'Source', '!endvote', 'Ends voting', 'Voting'],
		}
		self.Votes = {}
		self.VoteCommand = None
		self.VoteTimeStart = 0
		self.VoteConfig = {
				'TimeLimit':60,
				'SuccessCriteria':[	# Expired, Min % Yes, Max % No
						[0, 51, 49],
						[1, 40, 10],
						[1, 30, 0]
				]
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
	
	
	def HandleInput (self, Command, Data, User, Source):
		self.Debug ('DEBUG', 'HandleInput::' + str (Command) + '::' + str (Data))
		
		if Command == 'vote':
			print '***'
			print Data
			Voted = 0
			if len (Data) == 1 and Data[0] == '1' or Data[0] == 'y' or Data[0] == 'yes':
				if self.VoteCommand:
					Voted = True
					self.Votes[User] = True
					self.LogicFunctionCheckResult ()
				else:
					return ([False, 'Nothing to vote on'])
			elif len (Data) == 1 and Data[0] == '0' or Data[0] == 'n' or Data[0] == 'no':
				if self.VoteCommand:
					Voted = True
					self.Votes[User] = False
					self.LogicFunctionCheckResult ()
				else:
					return ([False, 'Nothing to vote on'])
			elif self.VoteCommand:
				return ([False, 'Vote already in progress'])
			elif self.HostCmds.Commands.has_key (Data[0]):
				if len (Data) == 1:
					Data.append ('')
				Input = doxExtractInput (Data[1], self.HostCmds.Commands[Data[0]][0])
				if Input[0]:
					if Data[1]:
						Cmd = Data[0] + ' ' + Data[1]
					else:
						Cmd = Data[0]
					if self.LogicFunctionInitVote (Data[0], Input[1], Source, User):
						return ([True, 'Vote started for "' + Cmd + '"'])
					else:
						return ([False, 'Can\'t start a vote for "' + Cmd + '"'])
				else:
					return ([True, 'Vote command not correct'])
			else:
				return ([False, 'Command not found'])
			if Voted:
				return ([True, 'Voted (' + str (Data[0]) + ')'])
			
			return ([True, 'Vote started'])
		elif Command == 'endvote':
			self.LogicFunctionResetVotes ()
			return ([True, 'Vote aborted'])
	
	
	def LogicFunctionResetVotes (self):
		self.Votes = {}
		self.VoteCommand = None
		self.VoteTimeStart = 0
	
	
	def LogicFunctionInitVote (self, Command, Data, Source, User):
		self.VoteCommand = [Command, Data, Source, User]
		self.VoteTimeStart = time.time ()
		if len (self.LogicFunctionListValidVoters ()) < 1:
			self.LogicFunctionResetVotes ()
			return (False)
		return (True)
	
	
	def LogicFunctionCheckResult (self, Expired = False):
		VotesYes = 0
		VotesNo = 0
		Voters = self.LogicFunctionListValidVoters ()
		Votes = len (Voters)
		for User in Voters.keys ():
			if self.Votes.has_key (User):
				if self.Votes[User]:
					VotesYes += 1
				else:
					VotesNo += 1
		VotesYesP = VotesYes / Votes * 100
		VotesNoP = VotesNo / Votes * 100
		print 'Check result'
		print Voters
		print self.Votes
		print VotesYes
		print VotesYesP
		print VotesNo
		print VotesNoP
		Success = False
		Completed = False
		for SuccessCriteria in self.VoteConfig['SuccessCriteria']:
			if (Expired or not SuccessCriteria[0]) and SuccessCriteria[1] <= VotesYesP and SuccessCriteria[2] > VotesNoP:
				Success = True
				Completed = True
				break
			elif (Expired or not SuccessCriteria[0]) and SuccessCriteria[1] > VotesYesP and SuccessCriteria[2] <= VotesNoP:
				Completed = True
				break
		print '___'
		print Completed
		print Success
		print '...'
		if Success:
			print 'Excec command:'
			print self.VoteCommand
			print self.Host.HostCmds.HandleInput (self.VoteCommand[2], self.VoteCommand[0], self.VoteCommand[1], self.VoteCommand[3], True)
		if Completed:
			self.LogicFunctionResetVotes ()
	
	
	def LogicFunctionListValidVoters (self):
		Return = {}
		Allowed = self.Host.ListAccess (self.VoteCommand[0], True)
		for User in self.Host.Lobby.BattleUsers.keys ():
			if not User == self.Host.Lobby.User and self.Host.CheckAccess (Allowed, User):
				Return[User] = 1
		return (Return)
