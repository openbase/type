cmake_minimum_required(VERSION 3.5)

project(openbase_type VERSION 1.0.0 LANGUAGES CXX)
set(PROJECT_NAMESPACE "org_openbase")

find_package(Protobuf 3.0.2 REQUIRED)

set(CONFIG_PACKAGE_LOCATION "lib/cmake/${PROJECT_NAME}")

set(PROTO_SOURCE_DIR "${PROJECT_SOURCE_DIR}/src/main/proto")

file(GLOB_RECURSE PROTO "${PROTO_SOURCE_DIR}/*.proto")

set(PROTOBUF_IMPORT_DIRS "${PROJECT_SOURCE_DIR}/src/main/proto/")
set(PROTOBUF_GENERATE_CPP_APPEND_PATH TRUE)

set(PROTO_SOURCES)
set(PROTO_HEADERS)

foreach(PROTOFILE ${PROTO})
    string(REPLACE "${PROTO_SOURCE_DIR}/" "" PROTONAME "${PROTOFILE}")
    string(REPLACE "/" "." TARGETNAME "${PROTONAME}")
    string(REPLACE "${PROTO_SOURCE_DIR}" "${CMAKE_CURRENT_BINARY_DIR}" PROTOTARGET "${PROTOFILE}")
    string(REPLACE ".proto" ".pb.cc" CFILE "${PROTOTARGET}")
    string(REPLACE ".proto" ".pb.h"  HFILE "${PROTOTARGET}")

    list(APPEND PROTO_SOURCES ${CFILE})
    list(APPEND PROTO_HEADERS ${HFILE})

    add_custom_command(
        OUTPUT "${CFILE}" "${HFILE}"
        COMMAND  ${PROTOBUF_PROTOC_EXECUTABLE}
        ARGS --cpp_out ${CMAKE_CURRENT_BINARY_DIR} --proto_path=${PROTO_SOURCE_DIR} ${PROTOFILE}
        DEPENDS ${PROTOFILE} ${PROTOBUF_PROTOC_EXECUTABLE}
        COMMENT "Running C++ protocol buffer compiler on ${FIL}"
        VERBATIM
    )
endforeach()

add_library(${PROJECT_NAME} SHARED ${PROTO_SOURCES})

target_include_directories(${PROJECT_NAME}
    PUBLIC
        $<INSTALL_INTERFACE:include>
    PRIVATE
        $<BUILD_INTERFACE: ${CMAKE_BINARY_DIR} ${PROTOBUF_INCLUDE_DIRS}>
)

target_link_libraries(${PROJECT_NAME}
    PUBLIC
        ${PROTOBUF_LIBRARIES}
)

if(UNIX OR APPLE)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC -Wall -std=c++11")
endif()

install(TARGETS ${PROJECT_NAME}
    EXPORT ${PROJECT_NAME}-export
    LIBRARY DESTINATION lib
    PUBLIC_HEADER DESTINATION include
)

install(DIRECTORY "${CMAKE_BINARY_DIR}/org"
    DESTINATION "include"
    FILES_MATCHING PATTERN "*.h*")

install(DIRECTORY "${CMAKE_SOURCE_DIR}/src/main/proto"
    DESTINATION "share/${PROJECT_NAME}/"
    FILES_MATCHING PATTERN "*.proto*")

install(EXPORT ${PROJECT_NAME}-export
  FILE ${PROJECT_NAME}Config.cmake
  NAMESPACE ${PROJECT_NAMESPACE}::
  DESTINATION share/${PROJECT_NAME}
)
