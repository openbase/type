SET(EXPERIMENTAL_JAR_FILE "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME_LOWERCASE}-${RST_EXPERIMENTAL_VERSION}.jar")
SET(JAR_FILES ${EXPERIMENTAL_JAR_FILE})

FIND_PROGRAM(ANT_EXECUTABLE ant)
IF(ANT_EXECUTABLE AND PROTOBUF_JAVA_LIBRARY)

    SET_PROPERTY(GLOBAL APPEND PROPERTY ENABLED_FEATURES "java binding")

    SET_DIRECTORY_PROPERTIES(PROPERTIES ADDITIONAL_MAKE_CLEAN_FILES "classes-experimental;experimental")

    SET(INCLUDE_ARG "INCLUDES")
    FOREACH(DOMAIN STABLE SANDBOX DEPRECATED)
        LIST(APPEND INCLUDE_ARG ${RST_${DOMAIN}_PROTO_ROOT})
    ENDFOREACH()

    PROTOBUF_GENERATE(JAVA EXPERIMENTAL_PROTO_FILES
                      PROTOFILES ${EXPERIMENTAL_PROTOS}
                      PROTOROOT ${EXPERIMENTAL_ROOT}
                      ${INCLUDE_ARG}
                      OUTPATH "${CMAKE_CURRENT_BINARY_DIR}/experimental")


    # Prepare safe variables and configure ant build files.
    STRING(REPLACE "&" "&amp;" SAFE_CMAKE_CURRENT_BINARY_DIR  "${CMAKE_CURRENT_BINARY_DIR}")
    STRING(REPLACE "&" "&amp;" JAR_LINES "<jar jarfile=\"${EXPERIMENTAL_JAR_FILE}\" basedir=\"classes-experimental\" manifest=\"MANIFEST.MF\"><fileset dir=\"${CMAKE_SOURCE_DIR}/proto/experimental\"><include name=\"**/*.proto\"/></fileset></jar>\n")
    CONFIGURE_FILE("${CMAKE_CURRENT_SOURCE_DIR}/build.xml.in"
                   "${CMAKE_CURRENT_BINARY_DIR}/build.xml"
                   @ONLY)
    CONFIGURE_FILE("${CMAKE_CURRENT_SOURCE_DIR}/MANIFEST.MF.in"
                   "${CMAKE_CURRENT_BINARY_DIR}/MANIFEST.MF"
                   @ONLY)

    # maven poms
    IF(RST_EXPERIMENTAL_IS_RELEASE)
        IF(RST_EXPERIMENTAL_VERSION_PATCH EQUAL 0)
            # it seems the maven convention is to leave out the revision / patch
            # version in case it is 0
            SET(RST_EXPERIMENTAL_MVN_VERSION "${RST_EXPERIMENTAL_VERSION_MAJOR}.${RST_EXPERIMENTAL_VERSION_MINOR}")
        ELSE()
            SET(RST_EXPERIMENTAL_MVN_VERSION ${RST_EXPERIMENTAL_VERSION})
        ENDIF()
        SET(RST_EXPERIMENTAL_MVN_UPSTREAM_VERSION "[${RST_EXPERIMENTAL_MVN_VERSION}]")
    ELSE()
        SET(RST_EXPERIMENTAL_MVN_VERSION "${RST_EXPERIMENTAL_VERSION_MAJOR}.${RST_EXPERIMENTAL_VERSION_MINOR}-SNAPSHOT")
        SET(RST_EXPERIMENTAL_MVN_UPSTREAM_VERSION "${RST_EXPERIMENTAL_MVN_VERSION}")
    ENDIF()
    CONFIGURE_FILE("${CMAKE_CURRENT_SOURCE_DIR}/pom-experimental.xml.in"
                   "${CMAKE_CURRENT_BINARY_DIR}/pom-experimental${RST_EXPERIMENTAL_VERSION}.xml"
                   @ONLY)
    INSTALL(FILES "${CMAKE_CURRENT_BINARY_DIR}/pom-experimental${RST_EXPERIMENTAL_VERSION}.xml"
            DESTINATION share/java)

    ADD_CUSTOM_COMMAND(OUTPUT  ${JAR_FILES}
                       COMMAND ${ANT_EXECUTABLE} dist
                       DEPENDS ${EXPERIMENTAL_PROTO_FILES}
                               "${CMAKE_CURRENT_BINARY_DIR}/build.xml" "${CMAKE_CURRENT_BINARY_DIR}/MANIFEST.MF"
                       COMMENT "Creating jar files")
    ADD_CUSTOM_TARGET(java ALL DEPENDS ${JAR_FILES})

    INSTALL(FILES ${JAR_FILES} DESTINATION share/java)

ELSE()
    MESSAGE(STATUS "ant not found or protobuf java library not available. Java bindings will not be created")
ENDIF()
