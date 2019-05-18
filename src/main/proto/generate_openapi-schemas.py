#!/usr/bin/env python3

from pathlib import Path

import yaml

components={}
schemas = {}
components['schemas'] = schemas

def skipLine(line):
    if line == "":
        return True
    if line.startswith('/') or line.startswith('*'):
        return True
    if line.startswith('syntax'):
        return True
    if line.startswith('package'):
        return True
    if line.startswith('import'):
        return True
    if line.startswith('option '):
        return True
    return False

def protoToOpenAPISchema(filename):
    with open(filename) as f:
        schema = {}
        schema['properties'] = {}

        messageName = ""
        enum = False
        internalEnums = {}
        internalMessage = False
        internalMessages = {} 
        for line in f:
            line = line.strip()
            if skipLine(line):
                continue

            if line.startswith('message'):
                if messageName == "":
                    messageName = line.split(' ')[1]
                else:
                    internalMessage = True

                    internalMessageName = messageName + '.' + line.split(' ')[1]
                    internalMessages[line.split(' ')[1]] = internalMessageName

                    internalMessageSchema = {}
                    internalMessageSchema['type'] = 'object'
                    internalMessageSchema['properties'] = {}
                    schemas[internalMessageName] = internalMessageSchema
                continue

            if internalMessage:
                if line.startswith('}'):
                    internalMessage = False
                    continue

            if line.startswith('enum'):
                enum = True

                enumName = line.split(' ')[1]
                if enumName == 'State':
                    enumName = messageName + '.' + enumName
                internalEnums[line.split(' ')[1]] = enumName

                enumSchema = {}

                enumSchema['type'] = 'string'
                enumSchema['enum'] = []
                schemas[enumName] = enumSchema
                continue

            if enum:
                if line.startswith('}'):
                    enum = False
                else:
                    enumValue = line.split('=')[0].strip()
                    if enumValue == "UNKNOWN":
                        continue
                    else:
                        enumSchema['enum'].append(enumValue)
                continue

            if line.startswith('}'):
                continue

            split = line.split(' ')
            option = split[0]
            fieldType = split[1]
            fieldName = split[2]

            prop = {}
            if option == "repeated":
                if internalMessage:
                    properties = internalMessageSchema['properties']
                else:
                    properties = schema['properties']
                properties[fieldName] = {}
                properties[fieldName]['type'] = 'array'
                properties[fieldName]['items'] = prop
            else:
                if internalMessage:
                    internalMessageSchema['properties'][fieldName] = prop
                else:
                    schema['properties'][fieldName] = prop


            if fieldType in internalEnums:
                ref = "#/components/schemas/" + internalEnums[fieldType]
                prop['$ref'] = ref
                continue

            if fieldType in internalMessages:
                ref = "#components/schemas/" + internalMessages[fieldType]
                prop['$ref'] = ref
                continue

            if len(fieldType.split('.')) > 1:
                prop['$ref'] = '#/components/schemas/' + fieldType.split('.')[-1]
                continue

            if fieldType[0].isupper():
                prop['$ref'] = '#/components/schemas/' + fieldType
                continue

            if fieldType == 'string':
                prop['type'] = 'string'
            elif fieldType == 'bool':
                prop['type'] = 'boolean'
            elif fieldType == 'int64':
                prop['type'] = 'integer'
                prop['format'] = 'int64'
            elif fieldType == 'uint64':
                prop['type'] = 'integer'
                prop['format'] = 'int64'
            elif fieldType == 'double':
                prop['type'] = 'number'
                prop['format'] = 'double'
            elif fieldType == 'float':
                prop['type'] = 'number'
                prop['format'] = 'float'
            elif fieldType == 'int32':
                prop['type'] = 'integer'
                prop['format'] = 'int32'
            elif fieldType == 'uint32':
                prop['type'] = 'integer'
                prop['format'] = 'int32'
            elif fieldType == 'bytes':
                prop['type'] = 'string'
            else:
                print('Unexpected fieldType: ' + fieldType + " in " + str(filename) + " - " + line)

        schemas[messageName] = schema 

for filename in Path('openbase').glob('**/*.proto'):
    protoToOpenAPISchema(filename)

print(yaml.dump(components, default_flow_style=False))


