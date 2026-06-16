cmake_minimum_required(VERSION 3.20)
project(NativeExtensionFixture)

add_subdirectory(src)
pybind11_add_module(native_fixture src/bindings.cpp src/Sound.cpp)
target_include_directories(native_fixture PRIVATE src)
target_link_libraries(native_fixture PRIVATE praatlib)
