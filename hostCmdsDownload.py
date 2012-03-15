# -*- coding: ISO-8859-1 -*-
from xmlrpclib import ServerProxy
import urllib
import hashlib
import os
import shutil
import string
from doxFunctions import *


class HostCmdsDownload:
	def __init__ (self, ClassHostCmds, ClassServer, ClassHost):
		self.Server = ClassServer
		self.Debug = ClassServer.Debug
		self.Debug ('INFO', 'HostCmdsDownload Init')
		self.Host = ClassHost
		self.HostCmds = ClassHostCmds
		self.Commands = {	# 0 = Field, 1 = Return to where (Source, PM, Battle), 2 = Ussage example, 3 = Usage desc, 4 = Category (if available), 5 = Extended help (if available)
			'downloadsearch':[['*'], 'PM', '!downloadsearch <mod>', 'Searches for the specified file'],
			'downloadmod':[['*'], 'PM', '!downloadmod <mod>', 'Downloads the specified mod'],
			'downloadmap':[['*'], 'PM', '!downloadmap <map>', 'Downloads the specified map'],
			'maplink':[[], 'Source', '!maplink', 'Provides the current maplink'],
			'modlink':[[], 'Source', '!modlink', 'Provides the current modlink'],
			'downloadrapidmod':[['*'], 'PM', '!downloadrapidmod <mod>', 'Downloads the specified mod'],
		}
		for Command in self.Commands:
			self.HostCmds.Commands[Command] = self.Commands[Command]
		self.XMLRPC_Init ()
	

	def HandleInput (self, Command, Data):
		self.Debug ('DEBUG', 'HandleInput::' + str (Command) + '::' + str (Data))
		
		if Command == 'downloadsearch':
			Results = self.XMLRPC_Proxy.springfiles.search ({"logical" : "or", "tag" : Data[0], "filename" : Data[0], "springname" : Data[0], "torrent" : True, "nosensitive":True})
			if Results:
				Return = ['Found matcher (top 10 max):']
				for Result in Results:
					Return.append ('* ' + str (Result['springname']) + ' (' + str (Result['filename']) + ')')
				return ([True, Return])
			else:
				return ([False, 'No matches found for "' + str (Data[0]) + '".'])
		elif Command == 'downloadmod':
			Result = self.XMLRPC_Proxy.springfiles.search ({"logical" : "or", "tag" : Data[0], "filename" : Data[0], "springname" : Data[0], "torrent" : True})
			if not Result:
				return ([False, 'No match found for "' + str (Data[0]) + '".'])
			if not len (Result) == 1:
				return ([False, 'To many matches found for "' + str (Data[0]) + '", only one match is allowed.'])
			else:
				if self.DownloadFile (Result[0], 'Mod'):
					return ([True, 'Downloaded the mod "' + str (Result[0]['springname']) + '".'])
				else:
					return ([False, 'Download failed for the mod "' + str (Data[0]) + '".'])
		elif Command == 'downloadmap':
			Result = self.XMLRPC_Proxy.springfiles.search ({"logical" : "or", "tag" : Data[0], "filename" : Data[0], "springname" : Data[0], "torrent" : True})
			if not Result:
				return ([False, 'No match found for "' + str (Data[0]) + '".'])
			if not len (Result) == 1:
				return ([False, 'To many matches found for "' + str (Data[0]) + '", only one match is allowed.'])
			else:
				if self.DownloadFile (Result[0], 'Map'):
					return ([True, 'Downloaded the map "' + str (Result[0]['springname']) + '".'])
				else:
					return ([False, 'Download failed for the map "' + str (Data[0]) + '".'])
		elif Command == 'maplink' or Command == 'modlink':
			if Command == 'maplink':
				Type = 'Map'
			else:
				Type = 'Mod'
			self.Debug ('INFO', Type + 'link:' + str (self.Host.Battle[Type]))
			Result = self.XMLRPC_Proxy.springfiles.search ({"logical" : "or", "tag" : self.Host.Battle[Type], "filename" : self.Host.Battle[Type], "springname" : self.Host.Battle[Type], "torrent" : True})
			
			if not Result or not len (Result) == 1 or not Result[0].has_key ('mirrors'):
				if not Result:
					self.Debug ('WARNING', 'Download link not found for ' + Type.lower ())
				elif not len (Result) == 1:
					self.Debug ('WARNING', 'Multiple download links found for ' + Type.lower () + ' (' + str (len (Result)) + ')')
				else:
					self.Debug ('WARNING', 'No mirror found')
				return ([False, 'No download link found for the current ' + Type.lower ()])
			else:
				for Mirror in Result[0]['mirrors']:
					return ([True, Type + ' download link: ' + str (Mirror).replace (' ', '%20')])
		elif Command == 'downloadrapidmod':
			WorkPath = self.Server.Config['General']['PathTemp'] + doxUniqID ()
			Command = self.Server.Config['General']['PathRapid'] + ' list-tags ' + Data[0]
			print Command
			Result = doxExec (Command)
			if len (Result) == 4 and Result[2] == 'Available tags:':
				Mod = Result[3][0:40].strip ()
			elif len (Result) > 4:
				return ([False, 'To many tags found, please try again'])
			else:
				return ([False, 'No match could be found'])
			
			self.Debug ('INFO', 'Rapid: make-sdd ' + Mod + ' to ' + WorkPath)
			Command = self.Server.Config['General']['PathRapid'] + ' make-sdd "' + Mod + '" ' + WorkPath
			print Command
			Result = doxExec (Command)
			if 'package ' + Mod.lower () + ' not known' in '\n'.join (Result).lower ():
				return ([False, 'Mod "' + Data[0] + '" not found'])
			elif not '====100%=====' in '\n'.join (Result):
				self.Debug ('INFO', 'Rapid: Removing ' + WorkPath)
				shutil.rmtree (WorkPath)
				self.Debug ('INFO', 'Rapid: Removed ' + WorkPath)
				return ([False, 'Mod "' + Data[0] + '" download failed'])
			
			ModName = Mod.lower ().replace ('version', '')
			for Pos in range (0, len (ModName)):
				if not ModName[Pos] in string.ascii_lowercase + string.digits + '._-':
					ModName = ModName.replace (ModName[Pos], '_')
			ModName = ModName.replace ('__', '_') + '.sd7'
			
			Command = self.Server.Config['General']['Path7Zip'] + ' a -t7z -ms=off "' + self.Server.Config['General']['PathMods'] + ModName + '" "' + WorkPath + '/*"'
			print Command
			self.Debug ('INFO', 'Rapid: 7Ziping to ' + self.Server.Config['General']['PathMods'] + ModName)
			Result = doxExec (Command)
			self.Debug ('INFO', 'Rapid: 7Ziped to ' + self.Server.Config['General']['PathMods'] + ModName)
			
			self.Debug ('INFO', 'Rapid: Removing ' + WorkPath)
			shutil.rmtree (WorkPath)
			self.Debug ('INFO', 'Rapid: Removed ' + WorkPath)
			
			if self.Server.SpringUnitsync.Load (self.Host.SpringVersion):
				return ([True, 'Downloaded mod ' + Mod])
			return ([False, 'Unitsync reload failed'])
	
	
	def StringPad (self, String, Length, Char = '0'):
		while len (String) < Length:
			String = String + str (Char)
		return (String)
	
	
	def XMLRPC_Init (self):
		self.Debug ('INFO')
		self.XMLRPC_Proxy = ServerProxy ('http://api.springfiles.com/xmlrpc.php')
	
	
	def DownloadFile (self, Result, Type):
		self.Debug ('INFO')
		OK = 0
		FilePath = self.Server.Config['General']['Path' + str (Type) + 's'] + Result['filename']
		if self.DownloadFileVerify (FilePath, 'Local', Result):
			return (True)
		
		if (Type == 'Map' and Result['category'] == 'map') or (Type == 'Mod' and Result['category'] == 'game'):
			for Mirror in Result['mirrors']:
				self.Debug ('INFO', 'Download:' + str (Mirror))
				urllib.urlretrieve (Mirror, FilePath)
				if self.DownloadFileVerify (FilePath, Mirror, Result):
					if self.Server.SpringUnitsync.Load (self.Host.SpringVersion):
						return (True)
					else:
						self.Debug ('ERROR', 'Unitsync re-load failed')
	
	
	def DownloadFileVerify (self, FilePath, Mirror, Result):
		if os.path.exists (FilePath) and int (os.path.getsize (FilePath)) == int (Result['size']):
			if hashlib.md5 (file (FilePath, 'r').read ()).hexdigest () == Result['md5']:
				return (True)
			else:
				self.Debug ('WARNING', 'Download failed (MD5):' + str (Mirror))
		else:
			self.Debug ('WARNING', 'Download failed (size):' + str (Mirror))
