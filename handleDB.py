# -*- coding: ISO-8859-1 -*-
from sqlalchemy import create_engine

class HandleDB:
	def __init__ (self, ClassServer):
		self.Server = ClassServer
		self.Debug = self.Server.Debug
		
		self.Type = 'MySQL'
		self.Config = {}
		self.SetConfig ()
		self.Start ()

		
	
	def Start (self):
		self.Connect ()
#		print 'Hai'
		
#		self.StoreBoxes ('BA', 'Comet Catcher Redux', 2, 2, '0 10 10 190 190\n1 10 10 100 100')
		
#		D = self.Query ('SELECT * FROM MapSettings')
#		print D
#		for L in D:
#			print L['Boxes']
#		print D[0][0]
		
	
	def StoreBoxes (self, Group, Map, Teams, StartPosType, Boxes):
		GroupID = self.GetGroupID (Group)
		MapID = self.GetMapID (Map)
		self.Query ("REPLACE INTO MapSettings SET MapID='" + str (MapID) + "', GroupID='" + str (GroupID) + "', Teams='" + str (Teams) + "', StartPosType='" + str (StartPosType) + "', Boxes='" + str (Boxes) + "'")
	
	
	def LoadBoxes (self, Group, Map, Teams, StartPosType):
		Result = self.Query ("SELECT MapSettings.Boxes FROM MapSettings LEFT JOIN Maps ON MapSettings.MapID=Maps.ID LEFT JOIN Groups ON MapSettings.GroupID=Groups.ID WHERE Maps.MapName='" + str (Map) + "' AND Groups.GroupName='" + str (Group) + "' AND MapSettings.Teams='" + str (Teams) + "' AND MapSettings.StartPosType='" + str (StartPosType) + "'", 'Value')
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
		self.Debug ()
		if self.Type == 'MySQL':
			self.Config = {
				'Host':self.Server.Config['General']['SQL_Host'],
				'Port':self.Server.Config['General']['SQL_Port'],
				'User':self.Server.Config['General']['SQL_User'],
				'Password':self.Server.Config['General']['SQL_Password'],
				'Database':self.Server.Config['General']['SQL_Database'],
			}
	
	
	def Query (self, Query, ReturnType = 'Array'):
		self.Debug (Query)
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
			elif ReturnType == 'Array':
				Return = []
				for ResultRow in Result:
					Row = {}
					for Field in ResultRow.keys ():
						Row[Field] = ResultRow[Field]
#					print Row.keys ()
					Return.append (Row)
		except:
			pass
		return (Return)

	
	def Connect (self):
		self.Debug ()
		self.Disconnect ()
		if self.Type == 'MySQL':
			self.Engine = create_engine ('mysql://' + str (self.Config['User']) + ':' + str (self.Config['Password']) + '@' + str (self.Config['Host']) + ':' + str (self.Config['Port']) + '/' + str (self.Config['Database']), encoding="utf-8", echo=False, pool_recycle=True)


	def Disconnect (self):
		self.Debug ()
		try:
			self.Engine.close ()
			self.Debug ('(' + str (self.thread) + ') Closed SQL connection.')
		except:
			pass