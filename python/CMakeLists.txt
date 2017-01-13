FIND_PACKAGE(PythonInterp)

# also check that setuptools is available
IF(PYTHONINTERP_FOUND AND ((NOT PYTHON_VERSION_MAJOR) OR (PYTHON_VERSION_MAJOR EQUAL 2)) AND NOT SETUPTOOLS_FOUND)
    MESSAGE(STATUS "Checking whether setuptools for python is available")
    EXECUTE_PROCESS(COMMAND ${PYTHON_EXECUTABLE} -c "import setuptools" RESULT_VARIABLE SETUPTOOLS_RESULT)
    IF(SETUPTOOLS_RESULT EQUAL 0)
        SET(SETUPTOOLS_FOUND TRUE CACHE BOOL "Indicates wether python can run setuptools" FORCE)
    ELSE()
        SET(SETUPTOOLS_FOUND FALSE CACHE BOOL "Indicates wether python can run setuptools")
    ENDIF()
    MESSAGE(STATUS "setuptools available: ${SETUPTOOLS_FOUND}")
ENDIF()

FUNCTION(PARSE_EGG_NAMES OUT_VARIABLE LOG)

    STRING(REGEX MATCH "##### .*\\.egg" RAW_MATCH ${LOG})
    STRING(REPLACE "##### " "" EGG_FILE ${RAW_MATCH})
    FILE(TO_CMAKE_PATH ${EGG_FILE} EGG_FILE)
    SET(${OUT_VARIABLE} ${EGG_FILE} PARENT_SCOPE)

ENDFUNCTION()

SET(EXPERIMENTAL_BASE_PACKAGE "rstexperimental")

INCLUDE(ParseArguments)
FUNCTION(BUILD_PYTHON_DOMAIN)

    # parse arguments
    PARSE_ARGUMENTS(ARG "USE_DOMAINS;NAME_OUTPUT" "INIT_HACK" ${ARGN})
    STRING(TOLOWER "${ARG_DEFAULT_ARGS}" MY_NAME_LOWER)
    STRING(TOUPPER "${ARG_DEFAULT_ARGS}" MY_NAME_UPPER)
    SET(USE_DOMAINS_LOWER)
    SET(USE_DOMAINS_UPPER)
    FOREACH(USE_DOMAIN ${ARG_USE_DOMAINS})
        STRING(TOLOWER "${USE_DOMAIN}" L)
        LIST(APPEND USE_DOMAINS_LOWER "${L}")
        STRING(TOUPPER "${USE_DOMAIN}" U)
        LIST(APPEND USE_DOMAINS_UPPER "${U}")
    ENDFOREACH()

    # configure utility files
    SET(CMAKE_FILE "${CMAKE_CURRENT_BINARY_DIR}/${MY_NAME_LOWER}/CreatePythonPackages${MY_NAME_LOWER}.cmake")
    CONFIGURE_FILE(CreatePythonPackages.cmake.in
                   ${CMAKE_FILE}
                   @ONLY)
    SET(SETUP_PY "${CMAKE_CURRENT_BINARY_DIR}/${MY_NAME_LOWER}/setup.py")
    CONFIGURE_FILE("${CMAKE_CURRENT_SOURCE_DIR}/setup-${MY_NAME_LOWER}.py.in"
                   ${SETUP_PY} @ONLY)

    # generate the protocol
    SET(INCLUDE_ARG)
    SET(UPSTREAM_DOMAIN_TARGETS)
    LIST(LENGTH USE_DOMAINS_UPPER HAS_USE_DOMAINS)
    IF(${HAS_USE_DOMAINS} GREATER 0)
        SET(INCLUDE_ARG "INCLUDES")
        FOREACH(DOMAIN ${USE_DOMAINS_UPPER})
            LIST(APPEND INCLUDE_ARG ${${DOMAIN}_ROOT})
            STRING(TOLOWER "${DOMAIN}" LOWER_DOMAIN)
            LIST(APPEND UPSTREAM_DOMAIN_TARGETS "${LOWER_DOMAIN}_protos")
        ENDFOREACH()
    ENDIF()
    FOREACH(DOMAIN STABLE SANDBOX DEPRECATED)
        LIST(APPEND INCLUDE_ARG ${RST_${DOMAIN}_PROTO_ROOT})
    ENDFOREACH()
    PROTOBUF_GENERATE(PYTHON PYTHON_FILES
                      PROTOFILES ${${MY_NAME_UPPER}_PROTOS}
                      PROTOROOT ${${MY_NAME_UPPER}_ROOT}
                      ${INCLUDE_ARG}
                      DEPENDS "${MY_NAME_LOWER}_protos" ${UPSTREAM_DOMAIN_TARGETS}
                      OUTPATH "${CMAKE_CURRENT_BINARY_DIR}/${MY_NAME_LOWER}")

    # find out the name of the egg file that is going to be generated
    EXECUTE_PROCESS(COMMAND ${PYTHON_EXECUTABLE} setup.py print_outputs
                    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/${MY_NAME_LOWER}"
                    OUTPUT_VARIABLE EGG_RAW)
    PARSE_EGG_NAMES(EGG ${EGG_RAW})
    SET(EGG "${CMAKE_CURRENT_BINARY_DIR}/${MY_NAME_LOWER}/${EGG}")

    # build the python target
    SET(INIT_HACK "${CMAKE_CURRENT_SOURCE_DIR}/init-hack-${MY_NAME_LOWER}.py")
    SET(INIT_PY "${CMAKE_CURRENT_BINARY_DIR}/${MY_NAME_LOWER}/${${MY_NAME_UPPER}_BASE_PACKAGE}/__init__.py")
    IF(UNIX)
        SET(CMAKE_FILE_QUOTED "'${CMAKE_FILE}'")
        SET(INIT_HACK_QUOTED "'${INIT_HACK}'")
        SET(INIT_PY_QUOTED "'${INIT_PY}'")
        SET(SETUP_PY_QUOTED "'${SETUP_PY}'")
    ELSE()
        SET(CMAKE_FILE_QUOTED "${CMAKE_FILE}")
        SET(INIT_HACK_QUOTED "${INIT_HACK}")
        SET(INIT_PY_QUOTED "${INIT_PY}")
        SET(SETUP_PY_QUOTED "${SETUP_PY}")
    ENDIF()
    SET(INIT_HACK_ARGS_PRE)
    SET(INIT_HACK_ARGS_POST)
    SET(INIT_HACK_DEPS)
    IF(ARG_INIT_HACK)
        SET(INIT_HACK_ARGS_PRE
            # first part of the hack: namespace of proto files is rst but we
            # want a module ${$MY_NAME_LOWER}_BASE_PACKAGE}, so move the
            # generated files to the right place
            COMMAND ${CMAKE_COMMAND} -E remove_directory ${${MY_NAME_UPPER}_BASE_PACKAGE}
            COMMAND ${CMAKE_COMMAND} -E copy_directory rst ${${MY_NAME_UPPER}_BASE_PACKAGE})
        SET(INIT_HACK_ARGS_POST
            # second part of the hack: install a patches __init__.py for which
            # installs our modules and packages in the rst namespace
            COMMAND ${CMAKE_COMMAND} -E copy ${INIT_HACK_QUOTED}
                                             ${INIT_PY_QUOTED})
        SET(INIT_HACK_DEPS ${INIT_HACK})
    ENDIF()
    ADD_CUSTOM_COMMAND(OUTPUT ${EGG}
                       ${INIT_HACK_ARGS_PRE}
                       # create __init__.py files so that we have a valid package structure
                       COMMAND ${CMAKE_COMMAND} -P ${CMAKE_FILE_QUOTED}
                       ${INIT_HACK_ARGS_POST}
                       COMMAND ${PYTHON_EXECUTABLE} ${SETUP_PY_QUOTED} bdist_egg
                       DEPENDS ${PYTHON_FILES}
                               ${INIT_HACK_DEPS}
                               ${SETUP_PY}
                               WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/${MY_NAME_LOWER}"
                       COMMENT "Creating ${MY_NAME_LOWER} python egg")
    ADD_CUSTOM_TARGET(python-${MY_NAME_LOWER} ALL DEPENDS ${EGG})

    # install the egg file
    INSTALL(FILES ${EGG}
            DESTINATION ${EGG_INSTALL_FOLDER})

    # expose the name of the generated egg file to the caller
    SET("${ARG_NAME_OUTPUT}" "${EGG}" PARENT_SCOPE)

ENDFUNCTION()

# here starts the building of the python modules
IF(PYTHONINTERP_FOUND AND
   ((NOT PYTHON_VERSION_MAJOR) OR (PYTHON_VERSION_MAJOR EQUAL 2))
   AND SETUPTOOLS_FOUND)

    SET_PROPERTY(GLOBAL APPEND PROPERTY ENABLED_FEATURES "python binding")

    # find out the correct install location:
    EXECUTE_PROCESS(COMMAND ${PYTHON_EXECUTABLE} -c "from distutils.sysconfig import get_python_lib; import os.path; print os.path.relpath(get_python_lib(prefix='${CMAKE_INSTALL_PREFIX}'), '${CMAKE_INSTALL_PREFIX}')" OUTPUT_VARIABLE EGG_INSTALL_FOLDER)
    STRING(STRIP ${EGG_INSTALL_FOLDER} EGG_INSTALL_FOLDER)
    # work around bug 5117 in python 2.6 which won't be fixed there
    STRING(REGEX REPLACE "^\\.\\./(.*)" "\\1" EGG_INSTALL_FOLDER "${EGG_INSTALL_FOLDER}")
    MESSAGE(STATUS "Python egg install folder: ${EGG_INSTALL_FOLDER}")

    BUILD_PYTHON_DOMAIN("experimental"
                        USE_DOMAINS "experimental"
                        NAME_OUTPUT EXPERIMENTAL_EGG
                        INIT_HACK)

    # generate pth file for easy-install
    GET_FILENAME_COMPONENT(EXPERIMENTAL_EGG_NAME ${EXPERIMENTAL_EGG} NAME)
    CONFIGURE_FILE(rst.pth.in "${CMAKE_CURRENT_BINARY_DIR}/${INSTALL_PREFIX}.pth" @ONLY)
    INSTALL(FILES "${CMAKE_CURRENT_BINARY_DIR}/${INSTALL_PREFIX}.pth"
            DESTINATION ${EGG_INSTALL_FOLDER})

    # use site.py hack from setuptools to ensure that we have a working python
    # site in the installation destination
    # see https://code.cor-lab.org/issues/1623
    #INSTALL(CODE "EXECUTE_PROCESS(COMMAND ${PYTHON_EXECUTABLE} -c \"print 'install to ${CMAKE_INSTALL_PREFIX}/${EGG_INSTALL_FOLDER}/site.py'; import pkg_resources; f = open('${CMAKE_INSTALL_PREFIX}/${EGG_INSTALL_FOLDER}/site.py', 'w'); f.write(pkg_resources.resource_string('setuptools', 'site-patch.py')); f.close()\")")

ELSE()
    MESSAGE(STATUS "Python 2 not found or setuptools not available. Not installing python bindings.")
ENDIF()
