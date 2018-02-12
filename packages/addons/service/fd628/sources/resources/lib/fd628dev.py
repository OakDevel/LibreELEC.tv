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
import struct
from fd628utils import *

class fd628Dev:
	def __init__(self):
		self._fd628 = None
		import ioctl
		import ctypes
		size = ctypes.sizeof(ctypes.c_int(0))
		self._FD628_IOC_MAGIC = ord('M')
		self._FD628_IOC_SMODE = ioctl.IOW(self._FD628_IOC_MAGIC,  1, size)
		self._FD628_IOC_GMODE = ioctl.IOR(self._FD628_IOC_MAGIC,  2, size)
		self._FD628_IOC_SBRIGHT = ioctl.IOW(self._FD628_IOC_MAGIC,  3, size)
		self._FD628_IOC_GBRIGHT = ioctl.IOR(self._FD628_IOC_MAGIC,  4, size)
		self._FD628_IOC_POWER = ioctl.IOW(self._FD628_IOC_MAGIC,  5, size)
		self._FD628_IOC_GVER = ioctl.IOR(self._FD628_IOC_MAGIC, 6, size)
		self._FD628_IOC_STATUS_LED = ioctl.IOW(self._FD628_IOC_MAGIC, 7, size)
		self._FD628_IOC_GDISPLAY_TYPE = ioctl.IOR(self._FD628_IOC_MAGIC, 8, size)
		self._FD628_IOC_SDISPLAY_TYPE = ioctl.IOW(self._FD628_IOC_MAGIC, 9, size)
		self._FD628_IOC_SCHARS_ORDER = ioctl.IOW(self._FD628_IOC_MAGIC, 10, 7)
		self._FD628_IOC_MAXNR = 11

	def __enter__(self):
		try:
			self._fd628 = os.open('/dev/fd628_dev', os.O_RDWR)
		except Exception as inst:
			self._fd628 = None
			kodiLogError(inst)
		return self

	def __exit__(self, type, value, traceback):
		if (self._fd628 != None):
			os.close(self._fd628)
		self._fd628 = None

	def enableDisplay(self, value):
		if (value):
			self.__writeIntFD628(self._FD628_IOC_POWER, 1)
			brightness = self.getBrightness()
			if (brightness != None):
				self.setBrightness(brightness)
		else:
			self.__writeIntFD628(self._FD628_IOC_POWER, 0)

	def getBrightness(self):
		return self.__readFD628(self._FD628_IOC_GBRIGHT)

	def setBrightness(self, value):
		self.__writeIntFD628(self._FD628_IOC_SBRIGHT, value)

	def getDisplayType(self):
		return self.__readFD628(self._FD628_IOC_GDISPLAY_TYPE)

	def setDisplayType(self, value):
		self.__writeIntFD628(self._FD628_IOC_SDISPLAY_TYPE, value)

	def setCharacterOrder(self, value):
		import array
		arr = array.array('B', [value[0], value[1], value[2], value[3], value[4], value[5], value[6]])
		self.__writeFD628(self._FD628_IOC_SCHARS_ORDER, arr, True)

	def __readFD628(self, request):
		ret = None
		if (self._fd628 != None):
			try:
				import fcntl
				pack = struct.pack('i', 0)
				value = fcntl.ioctl(self._fd628, request, pack)
				ret = struct.unpack('i', value)[0]
			except Exception as inst:
				kodiLogError(inst)
		kodiLogNotice('__readFD628: value = {0}'.format(ret))
		return ret

	def __writeIntFD628(self, request, value):
		self.__writeFD628(request, value)

	def __writeFD628(self, request, value, isBuf = False):
		if (self._fd628 != None):
			try:
				import fcntl
				if not (isBuf):
					value = struct.pack('i', value)
				kodiLogNotice('__writeFD628: value = {0}'.format(repr(value)))
				fcntl.ioctl(self._fd628, request, value)
			except Exception as inst:
				kodiLogError(inst)
