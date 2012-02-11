# -*- coding: ISO-8859-1 -*-
import os
import sys

class HandleCFG:
	def __init__ (self, Class, CheckCFG = 1):
		self.Server = Class
		self.Debug = Class.Debug
		self.Files = []
		self.LoadCFG (CheckCFG)
	
	
	def LoadCFG (self, CheckCFG, ReLoad = 0):
		self.Debug ('INFO')
		self.Server.Config = {'General':{}, 'Groups':{}, 'GroupUsers':{}}
		self.Server.AccessCommands = {}
		self.Server.AccessRoles = {}
		
		if len (sys.argv) < 2:
			print 'Missing config file (python server.py <conf file1> <font file2> ...)'
			sys.exit ()
		
		if ReLoad:
			for File in self.Files:
				self.LoadFile (File)
		else:
			for File in sys.argv[1:]:
				self.Files.append (os.getcwd () + '/' + File)
				self.LoadFile (File)
		if CheckCFG:
			self.CheckBaseConfig ()
#		print self.Server.Config
#		sys.exit ()
	
	
	def LoadFile (self, File):
		self.Debug ('INFO', 'Load file: ' + File)
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
					if not self.Server.Config['Groups'].has_key (GroupID):
						self.Server.Config['Groups'][GroupID] = {}
				elif Line[0:6] == '[USER=' and Line[-1] == ']':
					Type = 'User'
					UserID = Line[6:-1].strip ()
					if not self.Server.Config['GroupUsers'].has_key (GroupID):
						self.Server.Config['GroupUsers'][GroupID] = {}
					if not self.Server.Config['GroupUsers'][GroupID].has_key (UserID):
						self.Server.Config['GroupUsers'][GroupID][UserID] = {'ID':UserID}
				elif Line[0:7] == '[EVENT_' and Line[-1] == ']':
					Event = Line[7:Line.index ('=')]
					if not self.Server.Config['Groups'][GroupID].has_key ('Events'):
						self.Server.Config['Groups'][GroupID]['Events'] = {}
					if not self.Server.Config['Groups'][GroupID]['Events'].has_key (Event):
						self.Server.Config['Groups'][GroupID]['Events'][Event] = []
					self.Server.Config['Groups'][GroupID]['Events'][Event].append (Line[Line.index ('=') + 1:-1])
				elif Line[0:7] == '[ALIAS=' and Line[-1] == ']':
					Type = 'Alias'
					Alias = Line[7:-1].strip ()
					if not self.Server.Config['Groups'][GroupID].has_key ('Alias'):
						self.Server.Config['Groups'][GroupID]['Alias'] = {}
					if not self.Server.Config['Groups'][GroupID]['Alias'].has_key (Alias):
						self.Server.Config['Groups'][GroupID]['Alias'][Alias] = []
				elif Line[0:17] == '[ACCESS_COMMANDS]':
					Type = 'AccessCommand'
				elif Line[0:15] == '[ACCESS_GROUPS]':
					Type = 'AccessGroup'
				elif '=' in Line:
					Var = Line[0:Line.index ('='):].strip ()
					Value = Line[Line.index ('=') + 1:].strip ()
					if 'Path' in Var:
						Value = Value.replace ('~', os.environ['HOME'])
#					print '::' + Type + '::' + str (GroupID) + '::' + str (UserID) + '::' + Var + '==' + Value
					try:
						Temp = int (Value)
						if str (Temp) == Value:
							Value = int (Value)
					except:
						pass
					
					if Type == 'General':
						self.Server.Config['General'][Var] = Value
					elif Type == 'Group':
						self.Server.Config['Groups'][GroupID][Var] = Value
					elif Type == 'User':
						self.Server.Config['GroupUsers'][GroupID][UserID][Var] = Value
					elif Type == 'AccessCommand':
						if not self.Server.AccessCommands.has_key (GroupID):
							self.Server.AccessCommands[GroupID] = {}
						Value = Value.split ('|')
						self.Server.AccessCommands[GroupID][Var] = []
						for iType in range (0, len (Value)):
							self.Server.AccessCommands[GroupID][Var].append (Value[iType].split (','))
					elif Type == 'AccessGroup':
						if not self.Server.AccessRoles.has_key (GroupID):
							self.Server.AccessRoles[GroupID] = {}
						self.Server.AccessRoles[GroupID][Var] = {}
						for User in Value.split (','):
							self.Server.AccessRoles[GroupID][Var][User.strip ()] = 1
				elif Line and Type == 'Alias':
					self.Server.Config['Groups'][GroupID]['Alias'][Alias].append (Line)
					
		FP.close ()
	
	
	def CheckBaseConfig (self):
		# Check for cmake, make, gcc, gcc-c++
		self.Debug ('INFO')
		Errors = []
		Paths = [
			'PathSpringBuilds',
			'PathTemp',
			'PathMods',
			'PathMaps'
		]
		
		for Path in Paths:
			if not self.Server.Config['General'].has_key (Path):
				Errors.append ('The path for "' + Path + '" is missing')
			elif not os.path.exists (self.Server.Config['General'][Path]):
				Errors.append ('The path for "' + Path + '" (' + self.Server.Config['General'][Path] + ') is missing')
			else:
				FilePath = self.Server.Config['General'][Path] + '___WRITE_TEST_FILE___.DELETE'
				try:
					File = open (FilePath, 'w')
					File.close ()
					os.remove (FilePath)
				except:
					Errors.append ('The path for "' + Path + '" (' + self.Server.Config['General'][Path] + ') is not writable')
		
		if Errors:
			self.Debug ('ERROR', 'Config errors found, please correct before trying to start again')
			print 'Config errors found, please correct before trying to start again'
			for Error in Errors:
				print '* ' + Error
				self.Debug ('ERROR', Error)
			sys.exit ()
