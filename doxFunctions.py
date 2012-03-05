# -*- coding: ISO-8859-1 -*-
import re
import time
import math
import string 
import random 
import subprocess
import shlex


def doxReMatch (Pattern, Text):
    match = re.search (Pattern, Text)
    if match:
        return (match.group(0))
    return (None)


def doxTime ():
    return (int (math.floor (time.time ())))


def doxExtractInput (Data, Fields):
	Failed = None
	Return = []
	for Field in Fields:
		NewArg = ''
		if Field == '*' or (Field == 'O*' and len (Data) > 0):
			NewArg = Data
			if Field == '*' and len (NewArg) < 1:
				Failed = 'Missing data'
		elif Field == 'I' or (Field == 'OI' and len (Data) > 0):
			try:
				NewArg = int (doxReturnValue (Data, ' '))
			except:
				Failed = 'INT field not numeric'
		elif Field == 'V' or (Field == 'OV' and len (Data) > 0):
			NewArg = doxReturnValue (Data, ' ')
			if Field == 'V' and len (NewArg) < 1:
				Failed ='Missing variable'
		elif Field[0] == 'V' and len (Field) > 1:
			try:
				NewArg = doxReturnValue (Data, ' ')
				if len (NewArg) != int (Field[1:]):
					Failed = 'Variable not the correct length'
			except:
				NewArg = 'Faulty variable'
		elif Field == 'B' or (Field == 'OB' and len (Data) > 0):
			try:
				NewArg = int (doxReturnValue (Data, ' '))
				if NewArg != 0 and NewArg != 1:
					Failed = 'BOOL field not 0 or 1'
			except:
				Failed = 'BOOL CONVERSION FAILED'
		elif len (Data) == 0 and (Field == 'OI' or Field == 'OV' or Field == 'OB' or Field == 'O*'):
			NewArg = ''
		else:
			Failed = 'UNKNOWN INPUT TYPE::' + str (Field)
		if len (str (NewArg)) > 0:
			Return.append (NewArg)
			Data = Data[len (str (NewArg)) + 1:]
	if Failed:
		Return = [False, Failed]
	else:
		Return = [True, Return]
	return (Return)
	

def doxReturnValue (String, StopChar, Reverse = False):
	if String.find (StopChar) != -1:
		if Reverse:
			return (String[String.find (StopChar) + 1:])
		else:
			return (String[0:String.find (StopChar)])
	return (String)


def doxIfIntToInt (Value):
	try:
		Temp = int (Value)
		if str (Temp) == Value:
			Value = int (Value)
	except:
		pass
	return (Value)


def doxUniqID ():
	return (str (doxTime ()) + ''.join (random.choice (string.ascii_lowercase) for x in range(22)))


def doxExec (Command):
	PID = subprocess.Popen (shlex.split (Command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	Lines = []
	while 1:
		Line1 = PID.stdout.readline ().rstrip ()
#		Line2 = PID.stderr.readline ().rstrip ()
		Line2 = ''
		if len (Lines) > 100 or (len (Line1) == 0 and len (Line2) == 0):
			break
		else:
			if len (Line1):
				Lines.append (Line1)
			if len (Line2):
				Lines.append (Line2)
	return (Lines)
