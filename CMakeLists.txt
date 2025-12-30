cmake_minimum_required(VERSION 3.20)
project(MyCMS VERSION 1.0.0 LANGUAGES CXX)

# ============================================================================
# Configuration générale
# ============================================================================

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)

# Activer MOC (Meta Object Compiler) pour Qt
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Build type par défaut
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# ============================================================================
# Dépendances
# ============================================================================

# Qt 6
find_package(Qt6 COMPONENTS 
    Core 
    Gui 
    Widgets 
    Network 
    Concurrent
    REQUIRED
)

# libgit2
find_package(libgit2 REQUIRED)

# pugixml
find_package(pugixml REQUIRED)

# nlohmann/json
find_package(nlohmann_json REQUIRED)

# ============================================================================
# Source files
# ============================================================================

set(PROJECT_SOURCES
    main.cpp
    
    # UI
    src/ui/main_window.cpp
    src/ui/git_tab.cpp
    src/ui/editor_tab.cpp
    src/ui/settings_tab.cpp
    
    # Core
    src/core/git_manager.cpp
    src/core/html_manager.cpp
    src/core/config_manager.cpp
    src/core/python_builder.cpp
    src/core/logger.cpp
    
    # Utils
    src/utils/file_utils.cpp
    src/utils/string_utils.cpp
)

set(PROJECT_HEADERS
    # UI
    include/ui/main_window.hpp
    include/ui/git_tab.hpp
    include/ui/editor_tab.hpp
    include/ui/settings_tab.hpp
    
    # Core
    include/core/git_manager.hpp
    include/core/html_manager.hpp
    include/core/config_manager.hpp
    include/core/python_builder.hpp
    include/core/logger.hpp
    
    # Utils
    include/utils/file_utils.hpp
    include/utils/string_utils.hpp
)

# ============================================================================
# Exécutable principal
# ============================================================================

add_executable(MyCMS WIN32 ${PROJECT_SOURCES} ${PROJECT_HEADERS})

# Include directories
target_include_directories(MyCMS PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Linking
target_link_libraries(MyCMS 
    PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
    Qt6::Concurrent
    libgit2::libgit2
    pugixml::pugixml
    nlohmann_json::nlohmann_json
)

# ============================================================================
# Tests (Criterion)
# ============================================================================

# Optionnel : activer avec -DBUILD_TESTS=ON
option(BUILD_TESTS "Build test suite with Criterion" OFF)

if(BUILD_TESTS)
    enable_testing()
    find_package(criterion REQUIRED)
    
    # Test files
    add_executable(test_git_manager tests/test_git_manager.cpp src/core/git_manager.cpp)
    target_include_directories(test_git_manager PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    target_link_libraries(test_git_manager PRIVATE criterion libgit2::libgit2)
    
    add_executable(test_html_manager tests/test_html_manager.cpp src/core/html_manager.cpp)
    target_include_directories(test_html_manager PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    target_link_libraries(test_html_manager PRIVATE criterion pugixml::pugixml)
    
    add_test(NAME GitManagerTests COMMAND test_git_manager)
    add_test(NAME HTMLManagerTests COMMAND test_html_manager)
endif()

# ============================================================================
# Compiler options
# ============================================================================

if(MSVC)
    # Windows / Visual Studio
    add_compile_options(/W4 /permissive-)
else()
    # GCC / Clang
    add_compile_options(-Wall -Wextra -pedantic)
endif()

# ============================================================================
# Output directories
# ============================================================================

set_target_properties(MyCMS PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)

# ============================================================================
# Installation
# ============================================================================

install(TARGETS MyCMS 
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

message(STATUS "MyCMS C++ - Configuration Summary")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Qt Version: ${Qt6_VERSION}")
message(STATUS "  Tests Enabled: ${BUILD_TESTS}")
