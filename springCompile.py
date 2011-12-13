# -*- coding: ISO-8859-1 -*-
import os
import shutil
import subprocess
import time
import socket


class SpringCompile:
	def __init__ (self, ClassServer):
		self.Debug = ClassServer.Debug
		self.Debug ()
		self.Server = ClassServer
		self.BasePath = self.Server.Config['General']['PathSpringBuilds']
		self.BuildJobs = self.Server.Config['General']['SpringBuildJobs']
		self.Prefix = 'Version_'
		
	
	def GetSpringVersion (self, Version):
		VersionPath = self.Prefix + Version + ''
		self.Debug (str (Version) + '/' + str (VersionPath))
		Return = {}
		Path = self.BasePath + str (VersionPath)
		
		if not self.ExistsSpringVersion (Version):
			self.Debug ('Compile start')
			os.chdir (self.BasePath)
			if os.path.exists (self.BasePath + 'spring'):
				self.Debug ('Remove spring dir')
				shutil.rmtree (self.BasePath + 'spring')
			self.Debug ('GIT: Clone spring start')
			self.Exec ('/usr/bin/git clone git://github.com/spring/spring.git')
			self.Debug ('GIT: Clone spring finnished')
			os.chdir (self.BasePath + 'spring')
			self.Exec ('/usr/bin/git fetch origin')
			Result = self.Exec ('/usr/bin/git checkout -f ' + str (Version))
			if Result.find ('error: pathspec') != -1:
				self.Debug ('Checkout for "' + str (Version) + '" failed')
				self.Debug ('Compile terminated')
				return ('ERROR')
			if not os.path.exists (Path):
				os.mkdir (Path)
#			self.Exec ('git pull')
#			self.Exec ('git pull --rebase')
			self.Debug ('GIT: submodule sync')
			self.Exec ('git submodule sync')
			self.Exec ('git submodule update --init')
#			self.Exec ('git pull')
#			self.Exec ('git pull --rebase')
#			self.Exec ('cmake -DSPRING_DATADIR="' + str (Path) + '" -DCMAKE_INSTALL_PREFIX="" -DBINDIR=. -DLIBDIR=. -DMANDIR=. -DDOCDIR=doc -DDATADIR=. -DUSERDOCS_PLAIN=FALSE -DUSERDOCS_HTML=FALSE -DNO_SOUND=TRUE -DHEADLESS_SYSTEM=TRUE -DCMAKE_BUILD_TYPE=DEBUG2')
#			BuildPath = self.BasePath + 'spring/' + str (Version)
#			if not os.path.exists (BuildPath):
#				os.mkdir (BuildPath)
#			os.chdir (BuildPath)
#			self.Exec ('pwd')
#			self.Exec ('cmake -DSPRING_DATADIR="' + str (Path) + '" -DCMAKE_INSTALL_PREFIX="" -DBINDIR=. -DLIBDIR=. -DMANDIR=. -DDOCDIR=doc -DDATADIR=. -DUSERDOCS_PLAIN=FALSE -DUSERDOCS_HTML=FALSE -DNO_SOUND=TRUE -DHEADLESS_SYSTEM=TRUE ../')
			self.Exec ('cmake -DSPRING_DATADIR="' + str (Path) + '" -DCMAKE_INSTALL_PREFIX="" -DBINDIR=. -DLIBDIR=. -DMANDIR=. -DDOCDIR=doc -DDATADIR=. -DUSERDOCS_PLAIN=FALSE -DUSERDOCS_HTML=FALSE -DNO_SOUND=TRUE -DHEADLESS_SYSTEM=TRUE')
			self.Debug ('Make spring-dedicated')
			self.Exec ('make -j' + str (self.BuildJobs) + ' spring-dedicated')
			self.Exec ('make install-spring-dedicated DESTDIR="' + str (Path) + '"')
			self.Debug ('Make spring-headless')
			self.Exec ('make -j' + str (self.BuildJobs) + ' spring-headless')
			self.Exec ('make install-spring-headless DESTDIR="' + str (Path) + '"')
			self.Debug ('Compile end')
			Return['Path'] = Path
		else:
			self.Debug ('Version compiled')
			Return['Path'] = Path
		return (Return)
	
	
	def ExistsSpringVersion (self, Version):
		Path = self.BasePath + str (self.Prefix) + str (Version)
		if os.path.exists (Path) and os.path.exists (Path + '/libunitsync.so') and os.path.exists (Path + '/spring-headless') and os.path.exists (Path + '/spring-dedicated'):
			return (True)
		return (False)
		
	
	def Exec (self, Command):
		op = subprocess.Popen([Command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
		Result = op.communicate ()[0]
		print ''
		print '###============================================================'
		print str (Command)
		print '==============================================================='
		print Result
		print '============================================================###'
		return (Result)