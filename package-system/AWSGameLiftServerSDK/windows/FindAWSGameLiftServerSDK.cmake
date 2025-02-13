#
# All or portions of this file Copyright (c) Amazon.com, Inc. or its affiliates or
# its licensors.
#
# For complete copyright and license terms please see the LICENSE at the root of this
# distribution (the "License"). All use of this software is governed by the License,
# or, if provided, by the license below or the license accompanying this file. Do not
# remove or modify any license notices. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#

set(TARGET_WITH_NAMESPACE "3rdParty::AWSGameLiftServerSDK")
if (TARGET ${TARGET_WITH_NAMESPACE})
    return()
endif()

set(LIB_NAME "AWSGameLiftServerSDK")

set(${LIB_NAME}_INCLUDE_DIR ${CMAKE_CURRENT_LIST_DIR}/${LIB_NAME}/include)
set(${LIB_NAME}_BIN_DIR ${CMAKE_CURRENT_LIST_DIR}/${LIB_NAME}/bin)
set(${LIB_NAME}_LIBS_DIR ${CMAKE_CURRENT_LIST_DIR}/${LIB_NAME}/lib)

if (LY_MONOLITHIC_GAME)
    # Import libs path
    set(AWSGAMELIFTSERVERSDK_LIB_PATH ${${LIB_NAME}_LIBS_DIR}/intel64/msvc-14.1/$<IF:$<CONFIG:Debug>,Debug,Release>)
else()
    # Static libs path
    set(AWSGAMELIFTSERVERSDK_LIB_PATH ${${LIB_NAME}_BIN_DIR}/intel64/msvc-14.1/$<IF:$<CONFIG:Debug>,Debug,Release>)
endif()

set(AWSGAMELIFTSERVERSDK_LIBS
    ${AWSGAMELIFTSERVERSDK_LIB_PATH}/sioclient.lib
    ${AWSGAMELIFTSERVERSDK_LIB_PATH}/libboost_date_time.lib
    ${AWSGAMELIFTSERVERSDK_LIB_PATH}/libboost_random.lib
    ${AWSGAMELIFTSERVERSDK_LIB_PATH}/libboost_system.lib
    ${AWSGAMELIFTSERVERSDK_LIB_PATH}/libprotobuf$<$<CONFIG:Debug>:d>.lib
    ${AWSGAMELIFTSERVERSDK_LIB_PATH}/aws-cpp-sdk-gamelift-server.lib
)

set(AWSGAMELIFTSERVERSDK_COMPILE_DEFINITIONS
    AWS_CUSTOM_MEMORY_MANAGEMENT
    BUILD_GAMELIFT_SERVER
    PLATFORM_SUPPORTS_AWS_NATIVE_SDK
    GAMELIFT_USE_STD
)

if (NOT LY_MONOLITHIC_GAME)
    # Add 'USE_IMPORT_EXPORT' for external linkage
    LIST(APPEND AWSGAMELIFTSERVERSDK_COMPILE_DEFINITIONS USE_IMPORT_EXPORT)
    # Runtime dependencies
    set(AWSGAMELIFTSERVERSDK_RUNTIME_DEPENDENCIES ${AWSGAMELIFTSERVERSDK_LIB_PATH}/aws-cpp-sdk-gamelift-server.dll)
endif()

# Declare target
add_library(${TARGET_WITH_NAMESPACE} INTERFACE IMPORTED GLOBAL)

# Add include folder
ly_target_include_system_directories(TARGET ${TARGET_WITH_NAMESPACE} INTERFACE ${${LIB_NAME}_INCLUDE_DIR})

# Add link libs
target_link_libraries(${TARGET_WITH_NAMESPACE} INTERFACE ${AWSGAMELIFTSERVERSDK_LIBS})

# Add runtime dependencies if defined
if(DEFINED AWSGAMELIFTSERVERSDK_RUNTIME_DEPENDENCIES)
    ly_add_dependencies(${TARGET_WITH_NAMESPACE} ${AWSGAMELIFTSERVERSDK_RUNTIME_DEPENDENCIES})
endif()

# Set compile definitions
target_compile_definitions(${TARGET_WITH_NAMESPACE} INTERFACE ${AWSGAMELIFTSERVERSDK_COMPILE_DEFINITIONS})

set(${LIB_NAME}_FOUND True)
