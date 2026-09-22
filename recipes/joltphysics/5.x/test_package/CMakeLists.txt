cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(Jolt REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE Jolt::Jolt)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_17)

if(JOLT_TEST_METAL)
    enable_language(OBJCXX)
    add_executable(test_metal test_metal.mm)
    set_target_properties(test_metal PROPERTIES OBJCXX_STANDARD 17 OBJCXX_STANDARD_REQUIRED ON)
    target_link_libraries(test_metal PRIVATE Jolt::Jolt)
endif()
