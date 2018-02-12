################################################################################
#      This file is part of LibreELEC - https://libreelec.tv
#      Copyright (C) 2018-present Team LibreELEC
#
#  LibreELEC is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  LibreELEC is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with LibreELEC.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import xbmc
import os

enableDebug = False

class fd628State(object):
	def __init__(self, ledName):
		self._value = False
		self._hasChanged = False
		self._ledName = ledName
		if (enableDebug):
			self._logName = '/storage/downloads/service.fd628/debug/{0}.log'.format(ledName)
			with open(self._logName, 'w') as f:
				pass

	def _getStr(self, className):
		return '{0} ({1})'.format(className, self._ledName)

	def update(self):
		raise NotImplementedError

	def getValue(self):
		return self._value

	def hasChanged(self):
		return self._hasChanged

	def getLedName(self):
		return self._ledName

	def _update(self, value):
		self._log('Enter _update\n')
		self._log('value = {0}\n'.format(value))
		if (value != self._value):
			self._log('Value changed\n')
			self._hasChanged = True
			self._value = value
		else:
			self._log('Value not changed\n')
			self._hasChanged = False

	def _log(self, s):
		if (enableDebug):
			with open(self._logName, 'a') as f:
				f.write(s)

class fd628CondVisibility(fd628State):
	def __init__(self, ledName, cmd):
		super(fd628CondVisibility, self).__init__(ledName)
		self._cmd = cmd

	def __str__(self):
		return self._getStr('fd628CondVisibility')

	def update(self):
		self._log('Enter update\n')
		value = xbmc.getCondVisibility(self._cmd)
		self._update(value)

class fd628FileContains(fd628State):
	def __init__(self, ledName, path, strings):
		super(fd628FileContains, self).__init__(ledName)
		self._path = path
		self._strings = strings

	def __str__(self):
		return self._getStr('fd628FileContains')

	def update(self):
		if (os.path.isfile(self._path)):
			with open(self._path, 'rb') as state:
				content = state.read()
			value = self.__checkContent(content)
			self._update(value)
		else:
			self._update(False)

	def __checkContent(self, content):
		ret = False
		for s in self._strings:
			if (s in content):
				ret = True
				break
		return ret

class fd628WindowChecker(fd628State):
	def __init__(self, ledName, windows):
		super(fd628WindowChecker, self).__init__(ledName)
		self._windows = windows

	def __str__(self):
		return self._getStr('fd628WindowChecker')

	def update(self):
		value = False
		for id in self._windows:
			if (xbmc.getCondVisibility('Window.IsVisible({0})'.format(id))):
				value = True
				break
		self._update(value)

class fd628ExtStorageChecker(fd628State):
	def __init__(self, ledName, path):
		super(fd628ExtStorageChecker, self).__init__(ledName)
		self._path = path

	def __str__(self):
		return self._getStr('fd628ExtStorageChecker')

	def update(self):
		value = False
		for folder, subs, files in os.walk('/dev/disk/by-uuid'):
			for filename in files:
				path = os.path.realpath(os.path.join(folder, filename))
				if (path.startswith(self._path)):
					value = True
					break
		self._update(value)

class fd628ExtStorageCount(fd628State):
	def __init__(self, ledName, paths, type):
		super(fd628ExtStorageCount, self).__init__(ledName)
		self._paths = paths
		self._readCount = [0] * len(self._paths)
		self._writeCount = [0] * len(self._paths)
		for i in range(len(self._paths)):
			values = self.__readStatus(self._paths[i])
			if (len(values) > 0):
				self._readCount[i] = values[0]
				self._writeCount[i] = values[1]
		self._read = False
		self._write = False
		if (type == 'r'):
			self._read = True
		elif (type == 'w'):
			self._write = True
		elif (type == 'rw'):
			self._read = True
			self._write = True
		else:
			raise Exception('\'type\' must be \'r\', \'w\' or \'rw\'.')

	def __str__(self):
		return self._getStr('fd628ExtStorageCount')
			
	def update(self):
		value = False
		for i in range(len(self._paths)):
			values = self.__readStatus(self._paths[i])
			if (len(values) > 0):
				if (self._read):
					value = value or self._readCount[i] != values[0]
				if (self._write):
					value = value or self._writeCount[i] != values[1]
				self._readCount[i] = values[0]
				self._writeCount[i] = values[1]
			else:
				self._readCount[i] = 0
				self._writeCount[i] = 0
		self._update(value)

	def __readStatus(self, path):
		if (os.path.isfile(path)):
			with open(path, 'rb') as status:
				values = status.read().split()
			return [values[2], values[6]]
		else:
			return []
