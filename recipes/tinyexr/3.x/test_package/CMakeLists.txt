cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C CXX)

find_package(tinyexr CONFIG REQUIRED)
add_executable(test_package test_package.c)
target_compile_features(test_package PRIVATE c_std_11)
target_link_libraries(test_package PRIVATE tinyexr::tinyexr)

add_executable(test_cpp test_cpp.cpp)
target_link_libraries(test_cpp PRIVATE tinyexr::tinyexr)
