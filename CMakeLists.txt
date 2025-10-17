cmake_minimum_required(VERSION 3.20)
project(HybridIDS VERSION 0.1.0 LANGUAGES CXX)

# ============================================
# Project Configuration
# ============================================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -fsanitize=address -fsanitize=undefined")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

# ============================================
# Options
# ============================================
option(BUILD_TESTS "Build unit tests" ON)
option(BUILD_BENCHMARKS "Build benchmarks" OFF)
option(ENABLE_COVERAGE "Enable code coverage" OFF)
option(USE_DPDK "Use DPDK for packet capture" OFF)

# ============================================
# Dependencies
# ============================================

# Threads
find_package(Threads REQUIRED)

# libpcap (required for S-IDS)
find_package(PkgConfig REQUIRED)
pkg_check_modules(PCAP REQUIRED libpcap)

# Optional: DPDK
if(USE_DPDK)
    pkg_check_modules(DPDK REQUIRED libdpdk)
    add_definitions(-DUSE_DPDK)
endif()

# ============================================
# Include Directories
# ============================================
include_directories(
    ${CMAKE_SOURCE_DIR}/src
    ${PCAP_INCLUDE_DIRS}
)

# ============================================
# Source Files
# ============================================

# S-IDS (Signature-based IDS) sources
set(SIDS_SOURCES
    src/nids/common/types.cpp
    src/nids/parser/packet_parser.cpp
    src/nids/rules/rule_engine.cpp
    src/nids/sids_main.cpp
)

# Header files (for IDEs)
set(SIDS_HEADERS
    src/nids/common/types.h
    src/nids/parser/packet_parser.h
    src/nids/rules/rule_engine.h
)

# ============================================
# S-IDS Executable
# ============================================
add_executable(sids ${SIDS_SOURCES} ${SIDS_HEADERS})

target_link_libraries(sids
    Threads::Threads
    ${PCAP_LIBRARIES}
    pcap
)

# Set output directory
set_target_properties(sids PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)

if(USE_DPDK)
    target_link_libraries(nids ${DPDK_LIBRARIES})
endif()

# ============================================
# Installation
# ============================================
install(TARGETS sids DESTINATION bin)
install(DIRECTORY config/ DESTINATION etc/hybrid-ids)

# ============================================
# Testing
# ============================================
if(BUILD_TESTS)
    enable_testing()

    # Google Test
    find_package(GTest REQUIRED)
    include_directories(${GTEST_INCLUDE_DIRS})

    # Test sources
    set(TEST_SOURCES
        tests/unit/test_packet_parser.cpp
        tests/unit/test_feature_extractor.cpp
        tests/unit/test_rule_engine.cpp
    )

    # Test executable
    add_executable(nids_tests ${TEST_SOURCES})

    target_link_libraries(nids_tests
        ${GTEST_LIBRARIES}
        ${GTEST_MAIN_LIBRARIES}
        Threads::Threads
        ${Boost_LIBRARIES}
        ${PCAP_LIBRARIES}
        ${ZMQ_LIBRARIES}
        nlohmann_json::nlohmann_json
        spdlog::spdlog
    )

    # Register tests
    add_test(NAME nids_tests COMMAND nids_tests)
endif()

# ============================================
# Benchmarks
# ============================================
if(BUILD_BENCHMARKS)
    # Google Benchmark
    find_package(benchmark REQUIRED)

    set(BENCHMARK_SOURCES
        benchmarks/benchmark_parser.cpp
        benchmarks/benchmark_features.cpp
    )

    add_executable(nids_benchmarks ${BENCHMARK_SOURCES})

    target_link_libraries(nids_benchmarks
        benchmark::benchmark
        ${Boost_LIBRARIES}
        ${PCAP_LIBRARIES}
        nlohmann_json::nlohmann_json
    )
endif()

# ============================================
# Code Coverage
# ============================================
if(ENABLE_COVERAGE)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --coverage")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
endif()

# ============================================
# Documentation
# ============================================
find_package(Doxygen)
if(DOXYGEN_FOUND)
    set(DOXYGEN_IN ${CMAKE_CURRENT_SOURCE_DIR}/docs/Doxyfile.in)
    set(DOXYGEN_OUT ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile)

    configure_file(${DOXYGEN_IN} ${DOXYGEN_OUT} @ONLY)

    add_custom_target(docs
        COMMAND ${DOXYGEN_EXECUTABLE} ${DOXYGEN_OUT}
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Generating API documentation with Doxygen"
        VERBATIM
    )
endif()

# ============================================
# Print Configuration Summary
# ============================================
message(STATUS "")
message(STATUS "========================================")
message(STATUS "Hybrid IDS Configuration Summary")
message(STATUS "========================================")
message(STATUS "Build Type:       ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard:     ${CMAKE_CXX_STANDARD}")
message(STATUS "Build Tests:      ${BUILD_TESTS}")
message(STATUS "Build Benchmarks: ${BUILD_BENCHMARKS}")
message(STATUS "Enable Coverage:  ${ENABLE_COVERAGE}")
message(STATUS "Use DPDK:         ${USE_DPDK}")
message(STATUS "Install Prefix:   ${CMAKE_INSTALL_PREFIX}")
message(STATUS "========================================")
message(STATUS "")
