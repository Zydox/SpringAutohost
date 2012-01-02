# -*- coding: ISO-8859-1 -*-
from sqlalchemy import create_engine

class HandleDB:
	def __init__ (self, ClassServer):
		self.Server = ClassServer
		self.Debug = self.Server.Debug
		self.Cache = {}
		
		self.Type = 'MySQL'
		self.Config = {}
		self.SetConfig ()
		self.Start ()

		
	
	def Start (self):
		self.Connect ()
	
	
	def StoreBoxes (self, Group, Map, Teams, StartPosType, Boxes):
		GroupID = self.GetGroupID (Group)
		MapID = self.GetMapID (Map)
		self.Query ("REPLACE INTO MapSettings SET MapID='" + str (MapID) + "', GroupID='" + str (GroupID) + "', Teams='" + str (Teams) + "', StartPosType='" + str (StartPosType) + "', Boxes='" + str (Boxes) + "'")
	
	
	def LoadBoxes (self, Group, Map, Teams, StartPosType):
		Result = self.Query ("SELECT MapSettings.Boxes FROM MapSettings LEFT JOIN Maps ON MapSettings.MapID=Maps.ID LEFT JOIN Groups ON MapSettings.GroupID=Groups.ID WHERE Maps.MapName='" + str (Map) + "' AND Groups.GroupName='" + str (Group) + "' AND MapSettings.Teams='" + str (Teams) + "' AND MapSettings.StartPosType='" + str (StartPosType) + "'", 'Value')
		return (Result)
	
	
	def StoreSmurf (self, SpringID, User, IP, Country, CPU):
#		print ''
		SpringID = self.GetValueID ('SpringID', SpringID)
		UserID = self.GetValueID ('User', User)
		CountryID = self.GetValueID ('Country', Country)
		CPUID = self.GetValueID ('CPU', CPU)
		
		Insert = 0
		Result = self.Query ("SELECT ID, FirstSeen FROM Smurfs WHERE SpringID='" + str (SpringID) + "' AND UserID='" + str (UserID) + "' AND CountryID='" + str (CountryID) + "' AND CPUID='" + str (CPUID) + "' ORDER BY FirstSeen DESC LIMIT 0,1", '1D')
		if Result:
#			print 'EXISTING'
			Result2 = self.Query ("SELECT MAX(FirstSeen) FROM Smurfs WHERE SpringID='" + str (SpringID) + "'", 'Value')
			if Result2 == Result['FirstSeen']:
#				print 'UPDATED'
				self.Query ("UPDATE Smurfs SET LastSeen=UNIX_TIMESTAMP() WHERE ID='" + str (Result['ID']) + "'")
			else:
				Insert = 1
		else:
			Insert = 1
		if Insert:
#			print 'INSERT'
			self.Query ("INSERT INTO Smurfs SET SpringID='" + str (SpringID) + "', UserID='" + str (UserID) + "', CountryID='" + str (CountryID) + "', CPUID='" + str (CPUID) + "', FirstSeen=UNIX_TIMESTAMP(), LastSeen=UNIX_TIMESTAMP()")

		if IP:
#			print 'IP FOUND'
			if not Result:
				Result = self.Query ("SELECT ID FROM Smurfs WHERE SpringID='" + str (SpringID) + "' AND UserID='" + str (UserID) + "' AND CountryID='" + str (CountryID) + "' AND CPUID='" + str (CPUID) + "' ORDER BY FirstSeen DESC LIMIT 0,1", '1D')
			
			IPID = self.GetValueID ('IP', IP)
			SmurfID = Result['ID']
			Insert = 0
			Result3 = self.Query ("SELECT ID, FirstSeen FROM SmurfIPs WHERE SmurfID='" + str (SmurfID) + "' AND IPID='" + str (IPID) + "' ORDER BY FirstSeen DESC LIMIT 0,1", '1D')
			if Result3:
#				print 'EXISTING IP'
				Result4 = self.Query ("SELECT MAX(FirstSeen) FROM SmurfIPs WHERE SmurfID='" + str (SmurfID) + "'", 'Value')
				if Result4 == Result3['FirstSeen']:
#					print 'UPDATED IP'
					self.Query ("UPDATE SmurfIPs SET LastSeen=UNIX_TIMESTAMP() WHERE ID='" + str (Result3['ID']) + "'")
				else:
					Insert = 1
			else:
				Insert = 1
			
			if Insert:
#				print 'INSERT IP'
				self.Query ("INSERT INTO SmurfIPs SET SmurfID='" + str (SmurfID) + "', IPID='" + str (IPID) + "', FirstSeen=UNIX_TIMESTAMP(), LastSeen=UNIX_TIMESTAMP()")
	
	
	def GetValueID (self, Type, Value):
		if self.Cache.has_key (Type):
			if self.Cache[Type].has_key (Value):
				return (self.Cache[Type][Value])
		else:
			self.Cache[Type] = {}
			ResultCache = self.Query ("SELECT ID, Value FROM TableValues WHERE Type='" + str (Type) + "'", '2D')
			for Row in ResultCache:
				self.Cache[Type][str (Row['Value'])] = str (Row['ID'])
			if self.Cache[Type].has_key (Value):
				return (self.Cache[Type][Value])
		
		
		if not Value:
			return (0)
		Result = self.Query ("SELECT ID FROM TableValues WHERE Type='" + str (Type) + "' AND Value='" + str (Value) + "'", 'Value')
		if not Result:
			Result = self.Query ("INSERT INTO TableValues SET Type='" + str (Type) + "', Value='" + str (Value) + "'")
			return (self.GetValueID (Type, Value))
		self.Cache[Type][Value] = Result
		return (Result)
	
	
	def GetGroupID (self, Group):
		Result = self.Query ('SELECT ID FROM Groups WHERE GroupName=\'' + str (Group) + '\'', 'Value')
		if not Result:
			Result = self.Query ('INSERT INTO Groups SET GroupName=\'' + str (Group) + '\'')
			return (self.GetGroupID (Group))
		return (Result)
	
	
	def GetMapID (self, Map):
		Result = self.Query ('SELECT ID FROM Maps WHERE MapName=\'' + str (Map) + '\'', 'Value')
		if not Result:
			Result = self.Query ('INSERT INTO Maps SET MapName=\'' + str (Map) + '\'')
			return (self.GetMapID (Map))
		return (Result)
	
	
	def SetConfig (self):
		self.Debug ('INFO')
		if self.Type == 'MySQL':
			self.Config = {
				'Host':self.Server.Config['General']['SQL_Host'],
				'Port':self.Server.Config['General']['SQL_Port'],
				'User':self.Server.Config['General']['SQL_User'],
				'Password':self.Server.Config['General']['SQL_Password'],
				'Database':self.Server.Config['General']['SQL_Database'],
			}
	
	
	def Query (self, Query, ReturnType = '2D'):
		self.Debug ('DEBUG', Query)
		Result = self.Engine.execute (Query)
#		print ''
#		print ReturnType
#		print Result
#		print Result.keys ()
#		if Result.has_key ('ID'):
#			print '===' + str (Result['ID'])
		
#		print '==============='
		Return = None
		try:
			if ReturnType == 'Value':
				K = Result.keys ()
#				print K
#				print K[0]
				for R in Result:
					Return = R[0]
#				print '--------------'
#				print Return
			elif ReturnType == '2D' or ReturnType == '1D':
				Return = []
				for ResultRow in Result:
					Row = {}
					for Field in ResultRow.keys ():
						Row[Field] = ResultRow[Field]
#					print Row.keys ()
					Return.append (Row)
				if ReturnType == '1D':
					Return = Return[0]
		except:
			pass
		return (Return)

	
	def Connect (self):
		self.Debug ('INFO')
		self.Disconnect ()
		if self.Type == 'MySQL':
			self.Engine = create_engine ('mysql://' + str (self.Config['User']) + ':' + str (self.Config['Password']) + '@' + str (self.Config['Host']) + ':' + str (self.Config['Port']) + '/' + str (self.Config['Database']), encoding="utf-8", echo=False, pool_recycle=True)


	def Disconnect (self):
		self.Debug ('INFO')
		try:
			self.Engine.close ()
			self.Debug ('INFO', '(' + str (self.thread) + ') Closed SQL connection.')
		except:
			pass