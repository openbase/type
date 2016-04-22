#!/usr/bin/python
import logging
import sys
import glob
import os
import os.path
import re
import xml.dom.minidom
import optparse

logger = logging.getLogger("RSTcodeCheck")

# TODOS
# - checkstyle-compatible output
# check for enum names

# checks

class Check(object):

    def __init__(self, fileContents, fileLines, fileNameFromRoot, errorHandler):
        self.fileContents = fileContents
        self.fileLines = fileLines
        self.fileNameFromRoot = fileNameFromRoot
        self.errorHandler = errorHandler

        # generate the name of the primary message from file name
        fileName = os.path.basename(self.fileNameFromRoot)
        assert(fileName[-6:] == ".proto")
        self.primaryMessageNameFromFileName = fileName[:-6]


    def check(self):
        raise NotImplementedError()

class CheckPackageMatchFolder(Check):

    packageRegEx = re.compile("package (.+);")

    def check(self):
        declaredPackages = self.packageRegEx.findall(self.fileContents)

        if len(declaredPackages) == 0:
            self.errorHandler.addError(description="No package declared.")
            return
        elif len(declaredPackages) > 1:
            self.errorHandler.addError(description="Multiple packages declared. Only one is allowed.")
            return

        packagePathParts = declaredPackages[0].split('.')

        # split the file path into a list of components
        fileNameParts = []
        remainingPath = self.fileNameFromRoot
        while True:
            (remainingPath, tail) = os.path.split(remainingPath)
            if len(tail) == 0:
                break;
            fileNameParts = [tail] + fileNameParts
        fileNameParts = fileNameParts[:-1]

        if packagePathParts != fileNameParts:
            self.errorHandler.addError(description="Declared package %s does not match file name and location" % declaredPackages[0])
            
            
        #check whether package is starting with rstexperimental to avoid collisions with official RST
        packageEnforcedStart = "rst"
        if packagePathParts[0] != packageEnforcedStart:
            self.errorHandler.addError(description="Declared package %s does not start with %s. This is not allowed in this project." % (declaredPackages[0], packageEnforcedStart))

class CheckJavaOuterClassname(Check):

    outerClassnameRegEx = re.compile('option( +)java_outer_classname( +)=( +)"(.+)";')

    def check(self):
        declaredOuterClassnames = self.outerClassnameRegEx.findall(self.fileContents)

        if len(declaredOuterClassnames) == 0:
            self.errorHandler.addError(description="No java_outer_classname definition found")
            return
        if len(declaredOuterClassnames) > 1:
            self.errorHandler.addError(description="Multiple java_outer_classname definition found")
            return

        outerClassname = declaredOuterClassnames[0]

        # first check the actual classname against the file name
        expectedName = self.primaryMessageNameFromFileName + "Type"
        if outerClassname[3] != expectedName:
            self.errorHandler.addError(description="Declared java_outer_classname '%s' does not match expected '%s'" % (outerClassname[3], expectedName))

        # now check white spaces
        for i in range(3):
            if len(outerClassname[i]) != 1:
                self.errorHandler.addError(description="Too many spaces in java_outer_classname definition.")

class CheckMessageMatchesFileName(Check):

    messageRegEx = re.compile("message (\w+) {")

    def check(self):

        declaredMessages = self.messageRegEx.findall(self.fileContents)

        for msg in declaredMessages:
            if msg == self.primaryMessageNameFromFileName:
                return

        self.errorHandler.addError(description="No declared message name (found %s) matches the primary message name %s defined through the file name" % (declaredMessages, self.primaryMessageNameFromFileName))

class CheckVariableNames(Check):

    variableRegEx = re.compile('(required|optional|repeated)( +)(\w+)( +)(\w+)( +)=( +)(\d+);');

    def check(self):
        declaredVariables = self.variableRegEx.findall(self.fileContents)

        for decl in declaredVariables:
            name = decl[4]
            if name.lower() != name:
                self.errorHandler.addError(description="Variable name '%s' does not meet a_test_variable style of coding with lower-case names and underscore separation." % name)

class CheckImportsAbsolute(Check):

    importRegEx = re.compile('import "(\S+)";');

    def check(self):

        declaredImports = self.importRegEx.findall(self.fileContents)

        for imp in declaredImports:

            if imp[-6:] != ".proto":
                self.errorHandler.addError(description="Import '%s' must import a file ending with .proto" % imp)

            if imp[:3] != "rst":
                self.errorHandler.addError(description="Imports must be absolute starting with 'rst/' from one of the protocol roots. Import '%s' violates this rule." % imp)

class CheckIndentation(Check):

    lineStartRegEx = re.compile("^( +)(\\*){0,1}")

    def check(self):

        for (lineNumber, line) in enumerate(self.fileLines):
            if '\t' in line:
                self.errorHandler.addError(line=lineNumber, description="Indentation with tabs")

            match = self.lineStartRegEx.match(line)
            if match and (len(match.group(1)) % 4 != 0) and (match.group(2) is None):
                self.errorHandler.addError(line=lineNumber,
                                           description=("Indentation depth %i is not a multiple of 4."
                                                        % len(match.group(1))))

class CheckNewlineAtEof(Check):

    def check(self):
        if self.fileContents[-1] != "\n":
            self.errorHandler.addError(line=len(self.fileLines), description="Missing newline at EOF.")

class CheckTrailingSpaces(Check):

    trailingRegEx = re.compile("(\s*)$")

    def check(self):

        for lineNumber in range(1, len(self.fileLines) + 1):
            line = self.fileLines[lineNumber - 1]
            spaces = self.trailingRegEx.findall(line)
            for space in spaces:
                if len(space) > 0:
                    self.errorHandler.addError(line=lineNumber, description="Line has trailing spaces")

class CheckBlockCommentIndents(Check):

    indentRegEx = re.compile("^(\s*)\\*.*$")

    def check(self):

        for lineNumber in range(1, len(self.fileLines) + 1):
            line = self.fileLines[lineNumber - 1]
            spaces = self.indentRegEx.findall(line)
            for space in spaces:
                if len(space) % 4 != 1:
                    self.errorHandler.addError(line=lineNumber, description="Block comment continuations must be aligned with leading asterisk.")

class CheckPackageDeclarationFirst(Check):

    def check(self):

        if self.fileLines[0][:len("package")] != "package":
            self.errorHandler.addError(description="Package declaration required on first line")

class CheckNoSpaceBeforeFileSettings(Check):

    keywordsRegEx = re.compile('^(\s*)(package|option|import)\s+')

    def check(self):

        for lineNumber in range(1, len(self.fileLines) + 1):
            line = self.fileLines[lineNumber - 1]

            keywordSpaces = self.keywordsRegEx.findall(line)
            for space in keywordSpaces:
                if len(space[0]) > 0:
                    self.errorHandler.addError(line=lineNumber, description="No space before file-level keywords allowed.")

class CheckLeftCurlyBraces(Check):

    braceRegEx = re.compile('^(\s*)\\{')

    def check(self):

        for lineNumber in range(1, len(self.fileLines) + 1):
            line = self.fileLines[lineNumber - 1]

            newlineBraces = self.braceRegEx.findall(line)
            if len(newlineBraces) > 0:
                self.errorHandler.addError(line=lineNumber, description="Left curly braces must be on the same line with the introductory statement.")

class CheckRightCurlyBraces(Check):

    braceRegEx = re.compile('^(.*)\\}')

    def check(self):

        for lineNumber in range(1, len(self.fileLines) + 1):
            line = self.fileLines[lineNumber - 1]

            rightBraces = self.braceRegEx.findall(line)
            for brace in rightBraces:
                if re.match('^\s*$', brace) == None:
                    self.errorHandler.addError(line=lineNumber, description="Right curly braces must be on a new empty line.")

class CheckAnnotations(Check):

    annotationRegEx = re.compile('^\s*//@')

    def check(self):

        for lineNumber in range(1, len(self.fileLines) + 1):
            line = self.fileLines[lineNumber - 1]

            annotations = self.annotationRegEx.findall(line)
            for annotation in annotations:
                self.errorHandler.addError(line=lineNumber, description="Write annotation comments with a space (e.g. '// @ANNOTATION' instead of '//@ANNOTATION'.")

# utility stuff

def getProtoFilesRecursive(folder):

    logger.info("Analyzing folder %s for proto files", folder)

    protoFiles = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f[-6:] == ".proto":
                protoFiles.append(root + os.path.sep + f)
    logger.debug("Found files: %s", protoFiles)

    return protoFiles

class FileErrorHandler(object):
    def __init__(self, fileName, parent):
        self.__fileName = fileName
        self.__parent = parent

    def addError(self, line=None, description=None):
        print("[ERROR] %s(%s): %s" % (self.__fileName, line, description))
        self.__parent.countError()
        
    def done(self):
        pass

class ErrorHandler(object):
    def __init__(self):
        self.__count = 0;
          
    def errorCount(self):
        return self.__count
      
    def countError(self):
        self.__count  += 1
      
    def createFileErrorHandler(self, fileName):
        return FileErrorHandler(fileName, self)

    def done(self):
        pass

class CheckstyleXmlFileErrorHandler(FileErrorHandler):
    def __init__(self, fileName, document, checkstyleElement):
        self.__fileName = fileName
        self.__document = document
        self.__fileElement = document.createElement("file")
        self.__fileElement.setAttribute("name", fileName)
        checkstyleElement.appendChild(self.__fileElement)

    def addError(self, line=0, description=None):
        print("[ERROR] %s(%s): %s" % (self.__fileName, line, description))
        errorElement = self.__document.createElement("error")
        errorElement.setAttribute("line", str(line))
        errorElement.setAttribute("message", description)
        errorElement.setAttribute("source", "RST check")
        errorElement.setAttribute("severity", "error")
        self.__fileElement.appendChild(errorElement)

    def done(self):
        pass

class CheckstyleXmlErrorHandler(ErrorHandler):

    def __init__(self, fileName):
        self.__fileName = fileName
        self.__document = xml.dom.minidom.Document()
        self.__checkstyleElement = self.__document.createElement("checkstyle")
        self.__document.appendChild(self.__checkstyleElement)
        self.__checkstyleElement.setAttribute("version", "5.5")

    def createFileErrorHandler(self, fileName):
        return CheckstyleXmlFileErrorHandler(fileName, self.__document, self.__checkstyleElement)

    def done(self):
        #print(self.__document.toprettyxml())
        f = open(self.__fileName, 'w')
        f.write(self.__document.toprettyxml())
        f.close()

def checkFile(file, root, errorHandler, additionalCheckClasses=[]):

    f = open(file, 'r')
    contents = f.read()
    f.close()

    lines = contents.splitlines()
    relPath = os.path.relpath(file, root)

    fileErrorHandler = errorHandler.createFileErrorHandler(file)
    def executeCheck(checkClass):
        checkClass(contents, lines, relPath, fileErrorHandler).check();

    executeCheck(CheckPackageMatchFolder)
    executeCheck(CheckJavaOuterClassname)
    executeCheck(CheckMessageMatchesFileName)
    executeCheck(CheckVariableNames)
    executeCheck(CheckImportsAbsolute)
    executeCheck(CheckIndentation)
    executeCheck(CheckNewlineAtEof)
    executeCheck(CheckTrailingSpaces)
    executeCheck(CheckBlockCommentIndents)
    executeCheck(CheckPackageDeclarationFirst)
    executeCheck(CheckNoSpaceBeforeFileSettings)
    executeCheck(CheckLeftCurlyBraces)
    executeCheck(CheckRightCurlyBraces)
    executeCheck(CheckAnnotations)

    for check in additionalCheckClasses:
        executeCheck(check)

    fileErrorHandler.done()

def checkFilesInFolder(folder, errorHandler, additionalCheckClasses=[]):

    logger.info("Checking all files in folder %s", folder)

    protoFiles = getProtoFilesRecursive(folder)
    for f in protoFiles:
        if not os.path.split(f)[-1].startswith('__'):
            checkFile(f, folder, errorHandler, additionalCheckClasses)

def checkFilesInMultipleRoots(rootFolder, errorHandler, exclude=[]):

    logger.info("Searching for RST roots in %s", rootFolder)

    rootCandidates = os.listdir(rootFolder)
    roots = []
    for candidate in rootCandidates:
        if os.path.isdir(os.path.join(rootFolder, candidate)) and candidate != ".svn" and not candidate in exclude:
            roots.append(os.path.join(rootFolder, candidate))

    logger.info("Found RST roots %s", roots)

    for root in roots:
        checkFilesInFolder(os.path.abspath(root), errorHandler)

if __name__ == '__main__':


    parser = optparse.OptionParser()
    parser.add_option("-o", "--output", dest="filename", default="./rst-checks.xml",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-f", "--format",
                      dest="format", default="plain",
                      help="Format to use for reporting errors", metavar="(plain|xml)")
    parser.add_option("-r", "--root", dest="root", default="../proto",
                      help="Different RST roots like stable and sandbox are located here", metavar="DIR")
    parser.add_option("-d", "--debug", dest="debug", default=False, action="store_true",
                      help="Provide debug output")
    parser.add_option("-e", "--deprecated", dest="deprecated", default=False,
                      action="store_true",
                      help="Include the deprecated domain")

    (options, args) = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    # decide on output
    errorHandler = ErrorHandler()
    if options.format == "xml":
        errorHandler = CheckstyleXmlErrorHandler(options.filename)

    exclude = ['deprecated']
    if options.deprecated:
        exclude = []
    checkFilesInMultipleRoots(options.root, errorHandler,
                              exclude=exclude)

    errorHandler.done()
    sys.exit(-1 if errorHandler.errorCount() else 0);
