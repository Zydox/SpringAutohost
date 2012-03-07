# -*- coding: ISO-8859-1 -*-
import os
import inspect
import time
import traceback
import sys
import threading

class Debug:
	def __init__ (self):
		i = 1
		self.LogFile = None
		self.LogStore = 1
		self.LogHistory = []
	
	
	def Debug (self, Level, Info = '', CaptureCrash = 0):
		frame = inspect.currentframe ()
		filename = os.path.basename (frame.f_back.f_code.co_filename)
		fileline = frame.f_back.f_lineno
		function = frame.f_back.f_code.co_name
		LogLine = time.strftime ('%Y%m%d %H:%M:%S') + '\t' + threading.current_thread().name + '\t' + str (time.clock ()) + '\t' + Level + '\t' + filename + '\t' + function + '\t' + str (Info) 
		if self.LogStore:
			self.LogHistory.append (LogLine)
		elif self.LogFile:
			self.WriteLogToFile (LogLine)
		else:
			print (LogLine)
		if CaptureCrash:
			self.CaptureCrash ()
	
	
	def WriteLogToFile (self, Line):
		file = open (self.LogFile, 'a')
		file.write (Line + '\n')
		file.close ()
	
	
	def SetFile (self, LogFile):
		self.LogFile = LogFile
		file = open (self.LogFile, 'w')
		file.close ()
		self.Debug ('INFO', 'Log file set')
		self.LogStore = 0
		for Line in self.LogHistory:
			self.WriteLogToFile (Line)
		self.LogHistory = []
	
	
	def CaptureCrash (self):
		for Entry in traceback.format_exception_only (sys.exc_type, sys.exc_value):
			self.Debug ('CRASH', 'Exception: ' + str (Entry))
		for Entry in traceback.format_tb (sys.exc_info ()[2]):
			self.Debug ('CRASH', 'Trace: ' + str (Entry))
