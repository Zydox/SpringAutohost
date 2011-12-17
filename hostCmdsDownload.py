# -*- coding: ISO-8859-1 -*-
#import os, time, datetime
#import inspect
from xmlrpclib import ServerProxy
import urllib
import hashlib
import os


class HostCmdsDownload:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
#		self.Debug ('Ladderbot Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc
			'downloadsearch':[['*'], 'PM', '!downloadsearch <mod>', 'Searches for the specified file'],
			'downloadmod':[['*'], 'PM', '!downloadmod <mod>', 'Downloads the specified mod'],
			'downloadmap':[['*'], 'PM', '!downloadmap <map>', 'Downloads the specified map'],
			'addspectator':[[], 'Source', '!addspectator', 'abma?'],
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
		self.XMLRPC_Init ()
	

	def HandleInput (self, Command, Data):
		self.Debug ('HandleInput::' + str (Command) + '::' + str (Data))
		
		if Command == 'downloadsearch':
			Results = self.XMLRPC_Proxy.springfiles.search ({"logical" : "or", "tag" : Data[0], "filename" : Data[0], "springname" : Data[0], "torrent" : True, "nosensitive":True})
			if Results:
				Return = ['Found matcher (top 10 max):']
				for Result in Results:
					Return.append ('* ' + str (Result['springname']) + ' (' + str (Result['filename']) + ')')
				return (Return)
			else:
				return ('No matches found for "' + str (Data[0]) + '".')
		elif Command == 'downloadmod':
			Result = self.XMLRPC_Proxy.springfiles.search ({"logical" : "or", "tag" : Data[0], "filename" : Data[0], "springname" : Data[0], "torrent" : True})
			if not Result:
				return ('No match found for "' + str (Data[0]) + '".')
			if not len (Result) == 1:
				return ('To many matches found for "' + str (Data[0]) + '", only one match is allowed.')
			else:
				if self.DownloadFile (Result[0], 'Mod'):
					return ('Downloaded the mod "' + str (Result[0]['springname']) + '".')
				else:
					return ('Download failed for the mod "' + str (Data[0]) + '".')
		elif Command == 'downloadmap':
			Result = self.XMLRPC_Proxy.springfiles.search ({"logical" : "or", "tag" : Data[0], "filename" : Data[0], "springname" : Data[0], "torrent" : True})
			if not Result:
				return ('No match found for "' + str (Data[0]) + '".')
			if not len (Result) == 1:
				return ('To many matches found for "' + str (Data[0]) + '", only one match is allowed.')
			else:
				if self.DownloadFile (Result[0], 'Map'):
					return ('Downloaded the map "' + str (Result[0]['springname']) + '".')
				else:
					return ('Download failed for the map "' + str (Data[0]) + '".')
		elif Command == 'addspectator':
			return ('This Is AMBA!!!!!!')
		
		return (Data[0])
	
	
	def StringPad (self, String, Length, Char = '0'):
		while len (String) < Length:
			String = String + str (Char)
		return (String)
	
	
	def XMLRPC_Init (self):
		self.Debug ()
		self.XMLRPC_Proxy = ServerProxy ('http://api.springfiles.com/xmlrpc.php')
	
	
	def DownloadFile (self, Result, Type):
		self.Debug ()
		OK = 0
		FilePath = self.Server.Config['General']['Path' + str (Type) + 's'] + Result['filename']
		if self.DownloadFileVerify (FilePath, 'Local', Result):
			return (True)
		
		if (Type == 'Map' and Result['category'] == 'map') or (Type == 'Mod' and Result['category'] == 'game'):
			for Mirror in Result['mirrors']:
				self.Debug ('Download:' + str (Mirror))
				urllib.urlretrieve (Mirror, FilePath)
				if self.DownloadFileVerify (FilePath, Mirror, Result):
					if self.Server.SpringUnitsync.Load (self.Host.SpringVersion):
						return (True)
					else:
						self.Debug ('Unitsync re-load failed')
	
	
	def DownloadFileVerify (self, FilePath, Mirror, Result):
		if os.path.exists (FilePath) and int (os.path.getsize (FilePath)) == int (Result['size']):
			if hashlib.md5 (file (FilePath, 'r').read ()).hexdigest () == Result['md5']:
				return (True)
			else:
				self.Debug ('Download failed (MD5):' + str (Mirror))
		else:
			self.Debug ('Download failed (size):' + str (Mirror))
