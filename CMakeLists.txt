CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT("RST_EXPERIMENTAL")
STRING(TOLOWER ${CMAKE_PROJECT_NAME} PROJECT_NAME_LOWERCASE)

SET(CMAKE_ALLOW_LOOSE_LOOP_CONSTRUCTS TRUE)

SET(VERSION_MAJOR "0" CACHE STRING "Major project version part")
SET(VERSION_MINOR "17" CACHE STRING "Minor project version part")

# --- user options ---

OPTION(BUILD_CPP "Decide whether to build the CPP bindings." ON)
OPTION(BUILD_JAVA "Decide whether to build the Java bindings." ON)
OPTION(BUILD_PYTHON "Decide whether to build the Python bindings." ON)

# --- dependency handling ---

FIND_PACKAGE(RSC-CMake "${VERSION_MAJOR}.${VERSION_MINOR}" REQUIRED)
LIST(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_INSTALL_PREFIX}/share/cmake/Modules" ${RSC_CMAKE_MODULE_PATH})

FIND_PACKAGE(RST "${VERSION_MAJOR}.${VERSION_MINOR}" REQUIRED sandbox)
LIST(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_INSTALL_PREFIX}/share/cmake/Modules" ${RST_CMAKE_MODULE_PATH})


FIND_PACKAGE(ProtocolBuffers REQUIRED)
IF(NOT PROTOBUF_LIBRARY)
    MESSAGE(FATAL_ERROR "protobuf library not found")
ENDIF()
IF(NOT PROTOBUF_INCLUDE_DIR)
    MESSAGE(FATAL_ERROR "protobuf include dir not found")
ENDIF()
IF(NOT PROTOBUF_PROTOC_EXECUTABLE)
    MESSAGE(FATAL_ERROR "protoc executable not found")
ENDIF()

# --- final version definition ---

# finally we can deduce the real project version with the RSC macros
INCLUDE(DefineProjectVersion)
IF(NOT VERSION_PATCH)
SET(VERSION_PATCH 0)
ENDIF()

DEFINE_PROJECT_VERSION(RST_EXPERIMENTAL_ ${VERSION_MAJOR} ${VERSION_MINOR} ${VERSION_PATCH} "archive")

IF(VERSION_PATCH)
SET(RST_IS_RELEASE TRUE)
ENDIF()

MESSAGE(STATUS "This is rst version ${RST_EXPERIMENTAL_VERSION}")

SET(VERSION_SUFFIX "${RST_EXPERIMENTAL_VERSION_MAJOR}.${RST_EXPERIMENTAL_VERSION_MINOR}")
SET(INSTALL_PREFIX "${PROJECT_NAME_LOWERCASE}${VERSION_SUFFIX}")

# --- protocol files ---

FOREACH(DOMAIN experimental)
    STRING(TOUPPER ${DOMAIN} DOMAIN_UPPER)

    # List of absolute file names to each proto file in this domain
    SET(${DOMAIN_UPPER}_PROTOS)

    # define the root for each domain, now in the build tree, for later processing
    SET(${DOMAIN_UPPER}_ROOT "${CMAKE_BINARY_DIR}/proto/${DOMAIN}")

    # find all proto files in this domain relative to this source dir
    FILE(GLOB_RECURSE ${DOMAIN_UPPER}_PROTOS_REL
         RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
         "${CMAKE_CURRENT_SOURCE_DIR}/proto/${DOMAIN}/[^._]*.proto")

    # find all proto files for this domain, store them in a list for later processing, and copy them to the binary dir to create a single root for each domain which also contains the later generated collection types
    FOREACH(FILE ${${DOMAIN_UPPER}_PROTOS_REL})
        SET(OUT "${CMAKE_CURRENT_BINARY_DIR}/${FILE}")
        ADD_CUSTOM_COMMAND(
            OUTPUT ${OUT}
            COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}/${FILE}" "${OUT}"
            DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/${FILE}"
            COMMENT "Copying proto file ${FILE} to binary dir")
        LIST(APPEND ${DOMAIN_UPPER}_PROTOS "${OUT}")
    ENDFOREACH()

    # perform the same for package description files
    FILE(GLOB_RECURSE ${DOMAIN_UPPER}_PACKAGES_REL
         RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
         "${CMAKE_CURRENT_SOURCE_DIR}/proto/${DOMAIN}/__package.proto")
    SET(${DOMAIN_UPPER}_PACKAGES)
    FOREACH(FILE ${${DOMAIN_UPPER}_PACKAGES_REL})
        SET(OUT "${CMAKE_CURRENT_BINARY_DIR}/${FILE}")
        ADD_CUSTOM_COMMAND(
            OUTPUT "${OUT}"
            COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}/${FILE}" "${OUT}"
            DEPENDS "${FILE}"
            COMMENT "Copying package file ${FILE} to binary dir")
        LIST(APPEND ${DOMAIN_UPPER}_PACKAGES "${OUT}")
    ENDFOREACH()

    # generate collection types
    MESSAGE(STATUS "Generating commands for collection types in domain ${DOMAIN}")
    FOREACH(FILE ${${DOMAIN_UPPER}_PROTOS_REL})
        FILE(READ "${CMAKE_CURRENT_SOURCE_DIR}/${FILE}" CONTENTS)
        STRING(REGEX MATCH "// @create_collection(\\([a-zA-Z0-9]*\\))?" COLLECTION_CONTENTS ${CONTENTS})
        IF(NOT "${COLLECTION_CONTENTS}" STREQUAL "")
            STRING(REPLACE "/" ";" PATH_LIST "${FILE}")

            SET(PACKAGE ${PATH_LIST})
            # Remove proto/domain for the pure package
            LIST(REMOVE_AT PACKAGE 0)
            LIST(REMOVE_AT PACKAGE 0)

            # strip the name of the element type from the path list
            LIST(GET PACKAGE -1 SINGULAR_TYPE)
            STRING(REGEX REPLACE "\\..*" "" SINGULAR_TYPE "${SINGULAR_TYPE}")

            # determine the name of the collection type.
            # 1. Try to find a user annotation
            # 2. Use a default
            STRING(REGEX REPLACE "^.*\\(([a-zA-Z0-9]*)\\).*" "\\1" COLLECTION_TYPE "${COLLECTION_CONTENTS}")
            IF(COLLECTION_TYPE STREQUAL COLLECTION_CONTENTS)
                # nothing was replaced. Did not match, so default
                SET(COLLECTION_TYPE "${SINGULAR_TYPE}Collection")
            ENDIF()

            LIST(REMOVE_AT PACKAGE -1)
            STRING(REPLACE ";" "/" PACKAGE_PATH "${PACKAGE}")
            STRING(REPLACE ";" "." PACKAGE "${PACKAGE}")

            SET(SINGULAR_TYPE_FILE_REL ${PATH_LIST})
            LIST(REMOVE_AT SINGULAR_TYPE_FILE_REL 0)
            LIST(REMOVE_AT SINGULAR_TYPE_FILE_REL 0)
            STRING(REPLACE ";" "/" SINGULAR_TYPE_FILE_REL "${SINGULAR_TYPE_FILE_REL}")

            SET(OUT "${CMAKE_CURRENT_BINARY_DIR}/proto/${DOMAIN}/${PACKAGE_PATH}/${COLLECTION_TYPE}.proto")

            ADD_CUSTOM_COMMAND(
                OUTPUT "${OUT}"
                COMMAND ${CMAKE_COMMAND} "-DSINGULAR_TYPE=${SINGULAR_TYPE}" "-DSINGULAR_TYPE_FILE_REL=${SINGULAR_TYPE_FILE_REL}" "-DCOLLECTION_TYPE=${COLLECTION_TYPE}" "-DOUT=${OUT}" "-DPACKAGE=${PACKAGE}" -P "${CMAKE_SOURCE_DIR}/GenerateCollection.cmake"
                DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/proto/Collection.proto.in" "${CMAKE_CURRENT_SOURCE_DIR}/${FILE}"
                WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
                COMMENT "Creating collection type ${COLLECTION_TYPE} from singular type ${SINGULAR_TYPE}")

            LIST(APPEND ${DOMAIN_UPPER}_PROTOS "${OUT}")
            LIST(APPEND ${DOMAIN_UPPER}_PROTOS_REL "proto/${DOMAIN}/${PACKAGE_PATH}/${COLLECTION_TYPE}.proto")

        ENDIF()
    ENDFOREACH()

    ADD_CUSTOM_TARGET("${DOMAIN}_protos"
        DEPENDS ${${DOMAIN_UPPER}_PROTOS} ${${DOMAIN_UPPER}_PACKAGES})

ENDFOREACH()

# --- package ---

SET(CPACK_PACKAGE_VERSION_MAJOR ${RST_EXPERIMENTAL_VERSION_MAJOR})
SET(CPACK_PACKAGE_VERSION_MINOR ${RST_EXPERIMENTAL_VERSION_MINOR})
SET(CPACK_PACKAGE_VERSION_PATCH ${RST_EXPERIMENTAL_VERSION_PATCH})
SET(CPACK_PACKAGE_VERSION       "${CPACK_PACKAGE_VERSION_MAJOR}.${CPACK_PACKAGE_VERSION_MINOR}.${CPACK_PACKAGE_VERSION_PATCH}")

SET(CPACK_PACKAGE_VENDOR "CoR-Lab Bielefeld University")
SET(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/COPYING.txt")

INCLUDE(ProvideFlexibleCPack)

# --- install protocol anyways for backwards compatibility ---

ADD_SUBDIRECTORY(proto)

# --- language bindings ---

INCLUDE(FeatureSummary)

IF(BUILD_CPP)
    ADD_SUBDIRECTORY(cpp)
ENDIF()
IF(BUILD_JAVA)
    ADD_SUBDIRECTORY(java)
ENDIF()
IF(BUILD_PYTHON)
    ADD_SUBDIRECTORY(python)
ENDIF()

add_custom_target(do_always  ALL COMMAND "${PROJECT_SOURCE_DIR}/project/codeCheck.py" "-i" "${PROJECT_SOURCE_DIR}/project/codeCheckIgnore.txt")
add_custom_target(do_always2 ALL COMMAND "${PROJECT_SOURCE_DIR}/project/checkAmbiguities.sh" "${PROJECT_SOURCE_DIR}" "${RST_DIR}")

PRINT_ENABLED_FEATURES()
