###
# #%L
# Openbase Type Lib
# %%
# Copyright (C) 2018 - 2020 openbase.org
# %%
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Lesser Public License for more details.
# 
# You should have received a copy of the GNU General Lesser Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.html>.
# #L%
###
import glob, os
import shutil

print('test')
for filename in glob.iglob('org/' + '**/*.proto', recursive=True):
      print('process' + os.path.abspath(filename))
      tmpFileName = '/tmp/' + str(filename)

      ### create tmp folder
      os.makedirs(os.path.dirname(tmpFileName), exist_ok=True)

      java_package_name = os.path.dirname(filename).replace('/','.')
      java_class_name = os.path.basename(filename).replace('.proto','')

      option_java_package = 'option java_package = "' + java_package_name + '";\n'
      option_java_class = 'option java_outer_classname = "' + java_class_name + '";'

      #print('option_java_package['+ option_java_package+']')
      #print('option_java_class['+ option_java_class+']')
      print('tmp['+tmpFileName+']')

      with open(filename) as proto_file:
         with open(tmpFileName, 'w') as tmpFile:
            for line in proto_file.readlines():

               if "java_outer_classname" in line:
                     ### write package
                     tmpFile.write(option_java_package) 
                #     current_package = line.replace(
                #         "package ", "").replace(";\n", "")
                #     print('found package[' + current_package + ']')
                #     line = "package irre"

               tmpFile.write(line)
      # write back and cleanup
      ##if os.path.exists(tmp_repo_directory):
         #shutil.rmtree(tmp_repo_directory)
      shutil.move(tmpFileName, filename)
