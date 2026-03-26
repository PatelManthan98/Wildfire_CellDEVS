cmake_minimum_required(VERSION 3.16)
project(wildfire_celldevs LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT DEFINED CADMIUM_DIR)
    set(CADMIUM_DIR "$ENV{HOME}/cadmium_v2" CACHE PATH "Path to cadmium_v2")
endif()

include_directories(
    ${CADMIUM_DIR}/include
    ${CADMIUM_DIR}/json/include
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/include
)

add_executable(wildfire main.cpp)
target_compile_options(wildfire PRIVATE -Wall -Wextra -O2 -Wno-unused-parameter -Wno-sign-compare)