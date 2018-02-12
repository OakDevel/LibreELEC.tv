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

import xbmcaddon
import os
import fd628states
import fd628dev
import fd628settings
from fd628utils import *

addon = xbmcaddon.Addon(id='service.fd628')

class fd628Monitor(xbmc.Monitor):
	def __init__(self):
		super(fd628Monitor, self).__init__()
		self._settingsChangedCallback = None

	def setSettingsChangedCallback(self, callbackObject):
		self._settingsChangedCallback = callbackObject

	def onSettingsChanged(self):
		kodiLog('Enter fd628Monitor.onSettingsChanged')
		if (self._settingsChangedCallback != None):
			self._settingsChangedCallback.onSettingsChanged()

class fd628Addon():
	def __init__(self, monitor):
		self._fd628 = fd628dev.fd628Dev()
		self._states = []
		self._monitor = monitor
		self._monitor.setSettingsChangedCallback(self)
		self._settings = fd628settings.fd628Settings()

	def run(self):
		firstLoop = True
		while not self._monitor.abortRequested():
			if self._monitor.waitForAbort(0.5):
				break
			vfdon = '/sys/class/leds/fd628_dev/led_on'
			vfdoff = '/sys/class/leds/fd628_dev/led_off'
			if (not os.path.isfile(vfdon) or not os.path.isfile(vfdoff)):
				firstLoop = True
				continue
			if (firstLoop):
				self.onSettingsChanged()
				firstLoop = False
			ledon = []
			ledoff = []
			for state in self._states:
				state.update()
				if (state.hasChanged()):
					if (state.getValue()):
						ledon.append(state.getLedName())
					else:
						ledoff.append(state.getLedName())
			self.__writeFile(vfdon, ledon)
			self.__writeFile(vfdoff, ledoff)
		self.__cleanUp()

	def __cleanUp(self):
		self.__turnOffIndicators()
		self._monitor = None

	def __turnOffIndicators(self):
		ledoff = []
		vfdoff = '/sys/class/leds/fd628_dev/led_off'
		for state in self._states:
			ledoff.append(state.getLedName())
		self.__writeFile(vfdoff, ledoff)

	def __writeFile(self, path, values):
		if (os.path.isfile(path)):
			with open(path, "wb") as vfd:
				for j in values:
					vfd.write(j)
					vfd.flush()

	def onSettingsChanged(self):
		kodiLog('Enter fd628Addon.onSettingsChanged')
		self._settings.readValues()
		self.__createStates()
		self._fd628.enableDisplay(self._settings.isDisplayOn())
		if (self._settings.isDisplayOn()):
			self._fd628.setBrightness(self._settings.getBrightness())
			if (self._settings.isAdvancedSettings()):
				self._fd628.setDisplayType(self._settings.getDisplayType())
				self._fd628.setCharacterOrder(self._settings.getCharacterIndexes())
		kodiLog('isDisplayOn = {0}'.format(self._settings.isDisplayOn()))
		kodiLog('getBrightness = {0}'.format(self._settings.getBrightness()))
		kodiLog('isAdvancedSettings = {0}'.format(self._settings.isAdvancedSettings()))
		kodiLog('getDisplayType = {0}'.format(self._settings.getDisplayType()))
		kodiLog('getCharacterIndexex = {0}'.format(self._settings.getCharacterIndexes()))

	def __createStates(self):
		settingsWindows = ['settings', 'systeminfo', 'systemsettings', 'servicesettings', 'pvrsettings', \
		'playersettings', 'mediasettings', 'interfacesettings', 'profiles', 'skinsettings', 'videossettings', \
		'musicsettings', 'appearancesettings', 'picturessettings', 'weathersettings', 'gamesettings', \
		'service-LibreELEC-Settings-mainWindow.xml', 'service-LibreELEC-Settings-wizard.xml', \
		'service-LibreELEC-Settings-getPasskey.xml']
		appsWindows = ['addonbrowser', 'addonsettings', 'addoninformation', 'addon', 'programs']
		self.__turnOffIndicators()
		states = []
		states.append(fd628states.fd628CondVisibility('play', 'Player.Playing'))
		states.append(fd628states.fd628CondVisibility('pause', 'Player.Paused'))
		states.append(fd628states.fd628FileContains('hdmi', '/sys/class/amhdmitx/amhdmitx0/hpd_state', ['1']))
		states.append(fd628states.fd628FileContains('cvbs', '/sys/class/display/mode', ['cvbs']))
		states.append(fd628states.fd628FileContains('eth', '/sys/class/net/eth0/operstate', ['up', 'unknown']))
		states.append(fd628states.fd628FileContains('wifi', '/sys/class/net/wlan0/operstate', ['up']))
		states.append(fd628states.fd628WindowChecker('setup', settingsWindows))
		states.append(fd628states.fd628WindowChecker('apps', appsWindows))
		states.append(fd628states.fd628ExtStorageChecker('usb', '/dev/sd'))
		states.append(fd628states.fd628ExtStorageChecker('sd', '/dev/mmcblk'))
		if (self._settings.isStorageIndicator()):
			for state in states:
				if (state.getLedName() == self._settings.getStorageIndicatorIcon()):
					states.remove(state)
					break
			states.append(fd628states.fd628ExtStorageCount(self._settings.getStorageIndicatorIcon(), None, 'rw'))
			kodiLog('Active states: ' + str([str(state) for state in states]))
		self._states = states

monitor = fd628Monitor()
fd628 = fd628Addon(monitor)
kodiLog('Service start.')
fd628.run()
kodiLog('Service stop.')
