import xbmc
import xbmcaddon

addonName = xbmcaddon.Addon(id='service.fd628').getAddonInfo('name')

def kodiLog(message, level = xbmc.LOGWARNING):
	xbmc.log(addonName + ' -> ' + str(message), level)

def kodiLogError(message):
	kodiLog(message, xbmc.LOGERROR)

def kodiLogWarning(message):
	kodiLog(message, xbmc.LOGNOTICE)

def kodiLogNotice(message):
	kodiLog(message, xbmc.LOGNOTICE)