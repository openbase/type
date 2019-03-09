from os.path import isdir, walk, join

# generates the python package identification files within the given source folder.

source_folder = "./openbase_type"
finit = '__init__.py'

def visitor(arg, dirname, fnames):
    fnames = [fname for fname in fnames if isdir(fname)]
    with open(join(dirname, finit), 'w') as file_: file_.write('')

walk(source_folder, visitor, None)
