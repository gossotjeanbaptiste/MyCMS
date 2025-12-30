cmake_minimum_required(VERSION 3.20)

# Tests avec Criterion
enable_testing()

# Test Git Manager
add_executable(test_git_manager test_git_manager.cpp)
target_include_directories(test_git_manager PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_link_libraries(test_git_manager 
    PRIVATE
    criterion
    libgit2::libgit2
)
add_test(NAME GitManagerTests COMMAND test_git_manager)

# Test HTML Manager
add_executable(test_html_manager test_html_manager.cpp)
target_include_directories(test_html_manager PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_link_libraries(test_html_manager 
    PRIVATE
    criterion
    pugixml::pugixml
)
add_test(NAME HTMLManagerTests COMMAND test_html_manager)
