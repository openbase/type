#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

import yaml

# prefix used for schema references in an openAPI definition
referencePrefix = '#/components/schemas/'

def skipLine(line):
    """
    Skip lines which are not needed to parse a proto file.

    :return: True if the line can be skipped, otherwise False.
    """
    # skip empty lines
    if line == "":
        return True
    # skip lines with documentation
    if line.startswith('/') or line.startswith('*'):
        return True
    # skip definition of proto syntax version
    if line.startswith('syntax'):
        return True
    # skip package definition
    if line.startswith('package'):
        return True
    # skip imports
    if line.startswith('import'):
        return True
    # skip options
    if line.startswith('option '):
        return True
    return False

def addTypeToProp(fieldType, prop, internalSchemas={}):
    """
    Add an openAPI property type based on the fieldType defined in a proto definition.
    If the field type starts with an upper case then a reference is added, possible to an internal schema.
    If the field type contains a dot, everything from the first upper case latter in the field type is used as a reference.
    Else default types are tried to convert.

    :param fieldType: the protot field type to which an openAPI property type has to be found.
    :param prop: the property to which the openAPI type is added.
    :param internalSchemas: optionally internal schemas for the message dealt with. This is used to resolve references to internal messages/enums.
    :return: True if a property type or reference could be found, else False.
    """
    if fieldType[0].isupper():
        # correctly resolve references to internal messages/enums
        for internalSchema in internalSchemas:
            if internalSchema.split('.')[-1] == fieldType:
                prop['$ref'] = referencePrefix + internalSchema
                return prop
        prop['$ref'] = referencePrefix + fieldType
        return True

    if len(fieldType.split('.')) > 1:
        # build reference name from to first upper case character after a dot
        refName = ""
        for x in fieldType.split('.'):
            if len(x) == 0:
                continue
            if x[0].isupper():
                refName += x + '.'
        refName = refName[:-1]
        prop['$ref'] = '#/components/schemas/' + refName
        return True
    
    # translate default types
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
        # type could not be resolved
        return False

    return True

def protoToOpenAPISchemaRecursive(lines, schemas, basename): 
    """
    Recursively create a schema from lines read from a proto file.
    This method is recursive because proto messages can contain internal messages and enums.
    If this is the case the method will call itself recursively.

    :param lines: list of lines read from a proto file.
    :param schemas: dictionary of schemas to which the new definitions will be added.
    :param basename: basename respectively prefix which is added before the name of a schema.
                     This is used to prefix internal messages/enums with the name of the message containing it.
    :return: the filled schemas dictionary and the current procssing index. The return value should not be used
             because it deals with parameters only required for the recursion.
    """
    # create a new schema
    schema = {}
    # save the current name for the schema
    name = ""
    # index for the current line parsed
    i = 0;
    # iterate till end of file
    while (i < len(lines)):
        # get current line and remove whitespaces
        line = lines[i].strip()
        # increase index
        i += 1

        # if the line is irrelevant for parsing, continue the loop
        if skipLine(line):
            continue

        # closing curly brackets indicate that a message/enum definition has ended
        if line.startswith('}'):
            # return schemas and current index so that loop which recursively called this can resume at the correct location
            return schemas, i

        # test if line indicates an internal message/enum
        if name != "" and (line.startswith('message') or line.startswith('enum')):
            # name is already specified but there is a message/enum, so it is internal
            # recursively call this method but splice the lines to begin at the definition of the internal type
            _, processedLines = protoToOpenAPISchemaRecursive(lines[(i-1):len(lines)-1], schemas, basename=(name + '.'))
            # move the index of this iteration after the definition of the internal type
            i += processedLines
            continue

        # type is a message
        if line.startswith('message'):
            # set message flag
            isMessage = True
            # extract name
            name = basename + line.split(' ')[1]
            # create schema and add to schemas
            schemas[name] = schema
            schema['type'] = 'object'
            schema['properties'] = {}
            continue

        # type is an enum
        if line.startswith('enum'):
            # set message flag to false
            isMessage = False
            # extract name
            name = basename + line.split(' ')[1]
            # create schema for enum and add to schemas
            schemas[name] = schema
            schema['type'] = 'string'
            schema['enum'] = []
            continue

        # if item is an enum, parse lines as its values
        if not isMessage: 
            enumValue = line.split('=')[0].strip()
            # ignore values called unknown
            if enumValue == "UNKNOWN":
                continue
            else:
                schema['enum'].append(enumValue)
            continue

        # extract information for field
        split = line.split(' ')
        option = split[0]     # option is repeated, optional, ...
        fieldType = split[1]  # fieldType is string, uint64, reference to another type, ...
        fieldName = split[2]  # the name of the field

        # create a property for the field
        prop = {}
        # if the field option is repeated add the property as an array, else normally
        if option == "repeated":
            properties = schema['properties']
            properties[fieldName] = {}
            properties[fieldName]['type'] = 'array'
            properties[fieldName]['items'] = prop
        else:
            schema['properties'][fieldName] = prop
        
        # add property fields based on field type and print an error if it could not be done
        if not addTypeToProp(fieldType, prop, schemas):
            print('Could not parser fieldType[' + fieldType + '] into an openAPI property')
    return schemas, i
        

def protoToOpenAPISchema(protoFile): 
    """
    Create openAPI schemas from a proto file.
    For more details have a look at the method protoToOpenAPISchemaRecursive.

    :param protoFile: the proto file from which schemas are generated.
    :return: a dictionary with schemas referenced by their name.
    """
    schemas = {}
    with open(protoFile, 'r') as f:
        protoToOpenAPISchemaRecursive(f.readlines(), schemas, '')
    return schemas

def findReferencesRecursive(dictionary, referenceList):
    """
    Recursively traverse a dictionary and if there is a key called '$ref'
    remove the openAPI reference prefix and append it to the referenceList.

    :param dictionary: the dictionary which is recursively traversed.
    :param referenceList: the list to which references will be added.
    """
    # if parameter is not a dict there is nothing to add
    if type(dictionary) is not dict:
        return

    # it is a dict so iterate its key
    for key in dictionary:
        # key is a reference so append it 
        if key == '$ref':
            reference = dictionary[key].replace(referencePrefix, '')
            referenceList.append(reference)

        # value to key is another dict so traverse recursively into it
        if type(dictionary[key]) is dict:
            findReferencesRecursive(dictionary[key], referenceList)

        # value to key is a list so check each element of the list
        if type(dictionary[key]) is list:
            for item in dictionary[key]:
                findReferencesRecursive(item, referenceList)

def findReferences(dictionary):
    """
    Find all references defined in an openAPI schema.
    For more information have a look at the method findReferencesRecursive.

    :param dictionary: the dictionary for the schema to be checked.
    :return: a list with string for references made by the provided schema.
    """
    referenceList = []
    findReferencesRecursive(dictionary, referenceList)
    return referenceList

if __name__ == '__main__':
    # create argument parser
    parser = argparse.ArgumentParser(description='Tool for generating openAPI schemas definitions from protocol buffers.', \
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # add arguments
    parser.add_argument('-p', '--proto', default='.', type=str, help='proto file or directory. If a directory, it is recursively searched for proto files.')
    parser.add_argument('--openAPI', default='openAPI.yaml', type=str, help='openAPI definition file in yaml format to which the generated schemas will be added. If it does not exist it will be created.')
    parser.add_argument('--overwrite', action='store_true', help='flag determining if schemas should be overwritten if defined multiple times.')
    args = parser.parse_args() 

    # create dictionary for the openAPI definition
    dictionary = {}
    # if file specified by args exists, parse it into the dictionary
    if os.path.isfile(args.openAPI):
        with open(args.openAPI, 'r') as openAPIFile:
            try:
                dictionary = yaml.safe_load(openAPIFile)
            except yaml.YAMLError as error:
                print('Could not parse yaml file: ' + str(error))
                exit(1)

    # create or get components node
    if 'components' not in dictionary:
        components = {}
        dictionary['components'] = components
    else:
        components = dictionary['components']

    # create or get schemas node
    if 'schemas' not in components:
        schemas = {}
        components['schemas'] = schemas
    else:
        schemas = components['schemas']
     
    # create list of proto files to check, either from a single file or by checking the directory recursively
    if os.path.isdir(args.proto):
        files = Path(args.proto).glob('**/*.proto')
    else:
        files = [args.proto]

    # iterate over every proto file
    for filename in files:
        # create schema definitions for file
        schemasInFile = protoToOpenAPISchema(filename)
        # iterate over new schemas
        for schema in schemasInFile:
            # check if schema with name already exist and has changed
            # if overwrite is false print a warning
            if not args.overwrite and (schema in schemas) and (schemasInFile[schema] != schemas[schema]):
                print('Consider the overwrite option to always overwrite an existing schema!')
                print('Skip adding schema[' + schema + '] from file[' + str(filename) + ']:\n' + yaml.dump(schemasInFile[schema]))
                print('It differs from existing schema:\n' + yaml.dump(schemas[schema]))
                continue
            # add new schema
            schemas[schema] = schemasInFile[schema]

    # iterate over all schemas and validate that references are defined
    for schema in schemas:
        # retrieve references for schema
        references = findReferences(schemas[schema])
        for reference in references:
            # for every reference check if a schema exists, else print a warning
            if reference not in schemas:
                print('Could not find schema for reference[' + reference + ']')

    # write schemas to the openAPI definition file
    with open(args.openAPI, 'w') as openAPIFile:
        openAPIFile.write(yaml.dump(dictionary, default_flow_style=False))

