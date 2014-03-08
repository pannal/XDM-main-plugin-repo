# Author: panni <panni@fragstore.net>
# URL: https://github.com/pannal/XDM-pannal-plugin-repo/
#
# This file is part of a XDM plugin.
# based on de.lad1337.simple.mover and de.lad1337.movie.simplemover
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
from xdm import helper
import time
import os
import shutil

class AdvancedMover(PostProcessor):
    """
    more or less advanced moving postprocessor
    """
    # fix locations
    identifier = 'de.pannal.advancedmover'
    version = "0.11"
    _config = {
                'copy': False,
                'skip_sample': False,
                "replace_space_with": " ",
                'final_path': "",
                "rename_folders_to_element": False,
                "rename_files_to_element": False,
                'delete_empty_folders_after_move': False,
                'delete_folder_after_move': True,
                'allowed_extensions': {
                        "options": sorted([".avi", ".mkv", ".iso", ".mp4", ".m4v", ".mp3", ".flac",
                                    ".aac", ".nfo", ".png", ".gif", ".bmp", ".jpg", ".sfv", ".zip",
                                    ".rar", ".7z", ".tar", ".tar.gz", ".tar.bz", ".tar.bz2", ".srt",
                                    ".txt", ".exe", ".apk", ".obb"]),
                        "selected": [".avi", ".mkv"],
                        "use_checkboxes": True,
                        "required": True,
                    }
    }
    screenName = 'Advanced Mover'
    config_meta = {'plugin_desc': 'This will move all the files with the given extensions from the path that is given to the path specified.',
                   'replace_space_with': {'desc': 'All spaces for the final file will be replaced with this.'},
                   'copy': {'desc': 'If this is on the Folder will be copied instead of moved.'},
                   'skip_sample': {'desc': 'Skip sample files (mostly movies/TV)'},
                   'delete_empty_folders_after_move': {'desc': "Delete possibly empty folders in the original location including the location itself if empty after moving?"},
                   'delete_folder_after_move': {'desc': "Delete non-empty folders in the original location including the location itself after moving?"},
                   'rename_folders_to_element': {'desc': "Rename target folders to the element/download name"},
                   'rename_files_to_element': {'desc': "Rename target files to the element/download name"},
                   }
    addMediaTypeOptions = "runFor"
    #useConfigsForElementsAs = 'Enable'
    _allowed_extensions = ()
    _selected_extensions = ()

    def __init__(self, instance='Default'):
        PostProcessor.__init__(self, instance=instance)
        # update allowed_extensions if plugin defaults were updated
        if self.c.allowed_extensions.options != self._config["allowed_extensions"]["options"]:
            opts = self._config["allowed_extensions"]
            opts.update(self.c.allowed_extensions.selected)
            self.c.allowed_extensions = opts

        self._allowed_extensions = tuple(self.c.allowed_extensions.options)
        self._allowed_extensions_selected = tuple(self.c.allowed_extensions.selected)

        # delete_folder_after_move overrides delete_empty_folders_after_move
        self.c.delete_empty_folders_after_move = False if self.c.delete_folder_after_move else self.c.delete_empty_folders_after_move

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
                if len(filenames):
                    processLogger("I can see the files %s" % filenames)
                    for filename in filenames:
                        if filename.endswith(self._allowed_extensions_selected):
                            if self.c.skip_sample and 'sample' in filename.lower():
                                processLogger("Skipping sample: %s" % filename)
                                continue
                            curImage = os.path.join(root, filename)
                            allFileLocations.append(curImage)
                            processLogger("Found file: %s" % curImage)
            if not allFileLocations:
                processLogger("No files found!")
                #return (False, processLog[0])
        else:
            allFileLocations = [filePath]

        success = True
        dest = None
        if allFileLocations:
            processLogger("Possibly renaming and moving Files")
            allFileLocations.sort()
            for index, curFile in enumerate(allFileLocations):
                processLogger("Processing file: %s" % curFile)
                try:
                    extension = os.path.splitext(curFile)[1]
                    folderName = element.getName() if self.c.rename_folders_to_element else os.path.basename(os.path.dirname(curFile))
                    fileNameBase = element.getName() if self.c.rename_files_to_element else os.path.splitext(os.path.basename(curFile))[0]
                    newFileName = fixName(fileNameBase + extension, self.c.replace_space_with)
                    processLogger("New Filename shall be: %s" % newFileName)

                    destFolder = os.path.join(destPath, fixName(folderName, self.c.replace_space_with))
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
                    processLogger("Unable to rename and move File: %s. Please process manually" % curFile)
                    processLogger("given ERROR: %s" % msg)
                    success = False

        if not self.c.copy:
            if self.c.delete_empty_folders_after_move:
                for root, dirs, files in os.walk(filePath, topdown=False):
                    for name in dirs:
                        fname = os.path.join(root, name)
                        if not os.listdir(fname): #to check wither the dir is empty
                            os.removedirs(fname)
                            processLogger("removed empty folder %s" % fname)
                if not os.listdir(filePath):
                    os.removedirs(filePath)
                    processLogger("removed empty folder %s" % filePath)

            if self.c.delete_folder_after_move:
                shutil.rmtree(filePath)
                processLogger("removed %s completely" % filePath)


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
