cmake_minimum_required(VERSION 3.3)
project(ComputerNetworking)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Werror")

set(SOURCE_FILES 1SocketBasics/client.c)
add_executable(ComputerNetworking ${SOURCE_FILES})