# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM-main-plugin-repo/
#
# This file is part of a XDM plugin.
#
# XDM plugin.
# Copyright (C) 2013  Dennis Lutter
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
from xdm import helper
import time
import fnmatch
import os, sys
import re
import shutil
from os import path


class AdvancedMover(PostProcessor):
    identifier = 'de.pannal.advancedmover'
    version = "0.1"
    _config = {
                'copy': False,
                'skip_sample': False,
                "replace_space_with": " ",
                'final_path': "",
                "rename_folder_to_element": False,
                "rename_files_to_element": False,
                'allowed_extensions': {
                        "options": [".avi", ".mkv", ".iso", ".mp4", ".m4v", ".mp3", ".flac",
                                    ".aac", ".nfo", ".png", ".gif", ".bmp", ".jpg"],
                        "selected": [".avi", ".mkv"],
                    }
    }
    screenName = 'Advanced Mover'
    config_meta = {'plugin_desc': 'This will move all the files with the given extensions from the path that is given to the path specified.',
                   'replace_space_with': {'desc': 'All spaces for the final file will be replaced with this.'},
                   'copy': {'desc': 'If this is on the Folder will be copied instead of moved.'},
                   'skip_sample': {'desc': 'Skip sample files (mostly movies/TV)'},
                   }
    useConfigsForElementsAs = 'Path'

    def __init__(self, instance='Default'):
        for mtm in common.PM.getMediaTypeManager():
            prefix = self.useConfigsForElementsAs
            sufix = mtm.type
            h_name = '%s for %s' % (prefix, sufix)
            c_name = helper.replace_some('%s %s %s' % (mtm.name, prefix.lower(), sufix))
            self._config[c_name] = None
            self.config_meta[c_name] = {'human': h_name,
                                        'type': self.useConfigsForElementsAs.lower(),
                                        'mediaType': mtm.mt,
                                        'element': mtm.root}

        PostProcessor.__init__(self, instance=instance)

        self.extensions = self.c.allowed_extensions.selected

    def postProcessPath(self, element, filePath):
        destPath = self.c.final_path
        if not destPath:
            msg = "Destination path for %s is not set. Stopping PP." % element
            log.warning(msg)
            return (False, msg)
        # log of the whole process routine from here on except debug
        # this looks hacky: http://stackoverflow.com/questions/7935966/python-overwriting-variables-in-nested-functions
        processLog = [""]

        def processLogger(message):
            log.info(message)
            createdDate = time.strftime("%a %d %b %Y / %X", time.localtime()) + ": "
            processLog[0] = processLog[0] + createdDate + message + "\n"

        def fixName(name, replaceSpace):
            return helper.fileNameClean(name.replace(" ", replaceSpace))

        allFileLocations = []
        if os.path.isdir(filePath):
            processLogger("Starting file scan on %s" % filePath)
            for root, dirnames, filenames in os.walk(filePath):
                processLogger("I can see the files %s" % filenames)
                for filename in filenames:
                    if filename.endswith(self._allowed_extensions):
                        if self.c.skip_sample and 'sample' in filename.lower():
                            processLogger("Skipping sample: %s" % filename)
                            continue
                        curImage = os.path.join(root, filename)
                        allFileLocations.append(curImage)
                        processLogger("Found file: %s" % curImage)
            if not allFileLocations:
                processLogger("No files found!")
                return (False, processLog[0])
        else:
            allFileLocations = [filePath]

        processLogger("Possibly renaming and moving Files")
        success = True
        allFileLocations.sort()
        dest = None
        for index, curFile in enumerate(allFileLocations):
            processLogger("Processing file: %s" % curFile)
            try:
                extension = os.path.splitext(curFile)[1]
                folderName = element.getName() if self.c.rename_folder_to_element else os.path.basename(os.path.dirname(curFile))
                fileNameBase = element.getName() if self.c.rename_files_to_element else os.path.splitext(os.path.basename(curFile))[0]
                if len(allFileLocations) > 1:
                    newFileName = u"%s CD%s%s" % (fileNameBase, (index + 1), extension)
                else:
                    newFileName = fileNameBase + extension
                newFileName = fixName(newFileName, self.c.replace_space_with)
                processLogger("New Filename shall be: %s" % newFileName)

                destFolder = os.path.join(destPath, folderName, self.c.replace_space_with)
                if not os.path.isdir(destFolder):
                    os.mkdir(destFolder)
                dest = os.path.join(destFolder, newFileName)

                if self.c.copy:
                    msg = "Copying %s to %s" % (curFile, dest)
                    shutil.copytree(curFile, dest)
                else:
                    msg = "Moving %s to %s" % (curFile, dest)
                    shutil.move(curFile, dest)

            except Exception, msg:
                processLogger("Unable to rename and move Movie: %s. Please process manually" % curFile)
                processLogger("given ERROR: %s" % msg)
                success = False

        processLogger("File processing done")
        # write process log
        logFileName = fixName("%s.log" % element.getName(), self.c.replace_space_with)
        logFilePath = os.path.join(filePath, logFileName)
        try:
            # This tries to open an existing file but creates a new file if necessary.
            logfile = open(logFilePath, "a")
            try:
                logfile.write(processLog[0])
            finally:
                logfile.close()
        except IOError:
            pass

        return (success, dest, processLog[0])
