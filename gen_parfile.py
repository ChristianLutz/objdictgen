#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This file is part of CanFestival, a library implementing CanOpen Stack. 
#
#Copyright (C): Edouard TISSERANT, Francis DUPIN and Laurent BESSARD
#
#See COPYING file for copyrights details.
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


from types import ListType

# Currently there are three reasons why an entry will not be exported to the xml file.
# 1. considerSaveProperty is True and the save property itself is False
# 2. entry index is not between 0x1000 <= entryIndex <= 0x1029 or 0x2000 <= entryIndex <= 0x5FFF
# 3. entries with the name Compatibility Entry will not be exported
considerSaveProperty = True

# Function that write an EDS file after generate it's content
def WriteFile(filepath, content):
    # Open file in write mode
    cfile = open(filepath,"w")
    # Write content
    cfile.write(content)
    # Close file
    cfile.close()


# Function that generate the EDS file content for the current node in the manager
def GenerateFileContent(Node, filepath):
    global considerSaveProperty
    
    # Retreiving lists of indexes defined
    entries = Node.GetIndexes()
    parameters = []
    byteAddressOffset = 0
    
    # For each entryIndex, we generate the entryIndex section or sections if there is subindexes
    for entryIndex in entries:
        
        if 0x1000 <= entryIndex <= 0x1029:
            considerSaveProperty = False
        elif 0x2000 <= entryIndex <= 0x5FFF:
            considerSaveProperty = True
        else:
            # Ignore all other nodes
            continue
        
        values = Node.GetEntry(entryIndex, compute = False)
        
        # If there is only one value, it's a VAR entryIndex
        if type(values) != ListType:
            par, byteOffset = ExtractEntryInfos(Node, byteAddressOffset, entryIndex)
            parameters.append(par)
            byteAddressOffset += byteOffset
        else:
            for subIndex, value in enumerate(values): #DONT REMOVE VALUE, Otherwise this will fail.
                par, byteOffset = ExtractEntryInfos(Node, byteAddressOffset, entryIndex, subIndex)
                parameters.append(par)
                byteAddressOffset += byteOffset
                
    
    # Return File Content
    return ',\n'.join(filter(None, parameters))

def ExtractEntryInfos(Node, byteAddressOffset, entryIndex, subIndex=0):
    subentry_infos = Node.GetSubentryInfos(entryIndex, subIndex)
    param_infos = Node.GetParamsEntry(entryIndex, subIndex) #containing comment
    if (not considerSaveProperty) or param_infos["save"]:
        return ReadSubEntryInfosAndAddToXml(Node, byteAddressOffset, entryIndex, subentry_infos, param_infos, subIndex)
    return None, 0

def ReadSubEntryInfosAndAddToXml(Node, byteAddressOffset, entryIndex, subEntry, paramEntry, subindex):
    # If entry is not for the compatibility, generate informations for subindex
    if "name" in subEntry and subEntry["name"] != "Compatibility Entry":
        typeSize = GetType(Node, subEntry)
        entryComment = GetComment(paramEntry)
        
        return '{0x%.4X' %entryIndex + ', 0x%.2X' %subindex + ', %d' %byteAddressOffset + '}', typeSize
    return None, 0

def GetComment(paramEntry):
    entryComment = ""
    if "comment" in paramEntry:
        entryComment = paramEntry["comment"]
    return entryComment

def GetType(Node, subEntry):
    typeSize = 0
    if "type" in subEntry:
        #typeValue = "0x%4.4X"%subentry_infos["type"]
        typeInfo = Node.GetEntryInfos(subEntry["type"])
        typeSize = typeInfo["size"]/8
    return typeSize

# Function that generates EDS file from current node edited
def GenerateParameterFile(filepath, node):
    try:
        # Generate file content
        content = GenerateFileContent(node, filepath)
        # Write file
        WriteFile(filepath, content)
        return None
    except ValueError, message:
        return _("Unable to generate parameter file\n%s")%message

