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


import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
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
    
    ET.register_namespace('ino',"http://www.inovel.de/XMLSchema")
    parentNode = ET.Element("{http://www.inovel.de/XMLSchema}IDS")
    deviceNode = ET.SubElement(parentNode, "{http://www.inovel.de/XMLSchema}Device")
    communicationParameterNode = ET.SubElement(deviceNode, "{http://www.inovel.de/XMLSchema}CommunicationParameter")
    processParameterNode = ET.SubElement(deviceNode, "{http://www.inovel.de/XMLSchema}ProcessParameter")
    
    # For each entryIndex, we generate the entryIndex section or sections if there is subindexes
    for entryIndex in entries:
        paraNode = processParameterNode
        if 0x1000 <= entryIndex <= 0x1029:
            paraNode = communicationParameterNode
            considerSaveProperty = False
        elif 0x2000 <= entryIndex <= 0x5FFF:
            paraNode = processParameterNode
            considerSaveProperty = True
        else:
            # Ignore all other nodes
            continue
        
        values = Node.GetEntry(entryIndex, compute = False)
        
        # If there is only one value, it's a VAR entryIndex
        if type(values) != ListType:
            ExtractEntryInfos(Node, paraNode, entryIndex)
        else:
            for subIndex, value in enumerate(values): #DONT REMOVE VALUE, Otherwise this will fail.
                ExtractEntryInfos(Node, paraNode, entryIndex, subIndex)
    
    # Return File Content
    return PrettyPrintNode(parentNode)

def ExtractEntryInfos(Node, paraNode, entryIndex, subIndex=0):
    subentry_infos = Node.GetSubentryInfos(entryIndex, subIndex)
    param_infos = Node.GetParamsEntry(entryIndex, subIndex) #containing comment
    if (not considerSaveProperty) or param_infos["save"]:
        ReadSubEntryInfosAndAddToXml(Node, paraNode, entryIndex, subentry_infos, param_infos, subIndex)

def ReadSubEntryInfosAndAddToXml(Node, parentNode, entryIndex, subEntry, paramEntry, subindex):
    # If entry is not for the compatibility, generate informations for subindex
    if "name" in subEntry and subEntry["name"] != "Compatibility Entry":
        typeSize, typeNumber = GetType(Node, subEntry)
        entryComment = GetComment(paramEntry)
        
        AddParameterItem(parentNode, entryIndex, subindex, 
                         subEntry["access"], subEntry["name"],
                         entryComment, typeSize, typeNumber)

def GetComment(paramEntry):
    entryComment = ""
    if "comment" in paramEntry:
        entryComment = paramEntry["comment"]
    return entryComment

def GetType(Node, subEntry):
    typeSize = "0"
    typeNumber = -1
    if "type" in subEntry:
        #typeValue = "0x%4.4X"%subentry_infos["type"]
        typeInfo = Node.GetEntryInfos(subEntry["type"])
        typeSize = "%d"%(typeInfo["size"]/8)
        typeNumber = GetTypeNumber(Node.GetTypeName(subEntry["type"]))
    return typeSize, typeNumber

def GetTypeNumber(typeName):
    if "INTEGER" in typeName:
        return 0
    elif "UNSIGNED" in typeName:
        return 3
    elif "STRING" in typeName:
        return 1
    else:
        return -1

def AddParameterItem(parentNode, index, subindex, access, description, comment, length, dtype):
    node = ET.SubElement(parentNode, "{http://www.inovel.de/XMLSchema}ParameterItem")
    CreateNodeWithValue(node, "{http://www.inovel.de/XMLSchema}Index", "0x%.4X"%index)
    CreateNodeWithValue(node, "{http://www.inovel.de/XMLSchema}Subindex", "0x%.2X"%subindex)
    CreateNodeWithValue(node, "{http://www.inovel.de/XMLSchema}Authority", access.upper())
    CreateNodeWithValue(node, "{http://www.inovel.de/XMLSchema}Security", access.upper())
    CreateNodeWithValue(node, "{http://www.inovel.de/XMLSchema}Description", description)
    CreateNodeWithValue(node, "{http://www.inovel.de/XMLSchema}Comment", comment)
    nodeDataType = ET.SubElement(node, "{http://www.inovel.de/XMLSchema}DataType")
    CreateNodeWithValue(nodeDataType, "{http://www.inovel.de/XMLSchema}Length", length)
    CreateNodeWithValue(nodeDataType, "{http://www.inovel.de/XMLSchema}Type", "%d"%dtype)
    

def CreateNodeWithValue(parentNode, elementName, elementValue):
    node = ET.SubElement(parentNode, elementName)
    node.text = elementValue
    return node

def PrettyPrintNode(node):
    rough_string = ET.tostring(node, encoding="UTF-8", method="xml") #
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")

# Function that generates EDS file from current node edited
def GenerateIDSFile(filepath, node):
    try:
        # Generate file content
        content = GenerateFileContent(node, filepath)
        # Write file
        WriteFile(filepath, content)
        return None
    except ValueError, message:
        return _("Unable to generate IDS file\n%s")%message

