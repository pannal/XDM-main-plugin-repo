# Author: panni <panni@fragstore.net>
# URL: https://github.com/pannal/XDM-pannal-plugin-repo/
#
# This file is part of a XDM plugin.
#
# XDM plugin.
# Copyright (C) 2014  panni
#
# This plugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

from xdm.plugins import *
from xdm.tasks import createGenericEvent

class ModifyName(SearchTermFilter):
    """
    This is the simplest of plugins. Allow the user to change the name of the element to search for in the indexer (e.g. group used wrong release name)
    """
    version = "0.1"
    identifier = 'de.pannal.element.name'
    screenName = 'Modify Name To Look For'
    addMediaTypeOptions = "runFor"
    single = True
    elementConfig = {
        'look_for_instead': '',
        'look_for_that_exclusively': False
    }

    elementConfig_meta = {
        'look_for_that_exclusively': 'Only look for the given name and not for the ones found before.',
    }

    config_meta = {'plugin_desc': "This enables your to look for a different name than detected by the provider's returned name (e.g. if the release was named wrongly and you know it, change this for a single element)"}

    def compare(self, element, terms):
        self.e.getConfigsFor(element) #this will load all the elements configs

        lookForInstead = self.e.getConfig("look_for_instead", element).value
        onlyLookForThat = self.e.getConfig("look_for_that_exclusively", element).value

        lookFor = terms
        if len(lookForInstead):
            lookFor = [lookForInstead] + terms if not onlyLookForThat else [lookForInstead]
            message = "Searching additionally%s for %s (%s)." \
                      % (" (exclusively)" if onlyLookForThat else "", lookForInstead, ", ".join(lookFor))

            log.info(message)
            createGenericEvent(element, "filter", message)

        return lookFor

