If you have worked with Linux you might know that it uses a special directory structure common to all Linux systems, the [Filesystem Hierarchy Standard](https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard) (FHS). One aspect is the common location for libraries and header files in the `/usr` directory. If you’re programming on Windows, it is very convenient to mimic this folder structure. As we will see in the example in the last section, this also plays very well with how CMake works.

The approach presented here still means that a large part of the dependency management (building, installing, updating) is up to you. Personally, I very much prefer to have the ability to control those aspects of dependency management, but if you’re looking for a more automated way of building C/C++ projects, a package management system like [Conan](https://conan.io/) or [vcpkg](https://vcpkg.io/) might be the right choice.

Back in the days when I started programming (long before Github or tools like CMake became mainstream), I often used to copy external code to the current project directory and include it directly in the solution. Obviously, this is very laborious and when working on different projects having the same dependencies (and probably many of them), you need to come up with a solution to manage those dependencies. What I found to work best for me, is imposing the following directory structure:

- `C:\usr\bin` for dynamic libraries ( _DLLs_) and executables
- `C:\usr\include` for C/C++ header files
- `C:\usr\lib` for shared libraries

Of course, the actual location and name of the root folder is up to you. You can just as well put it into a subdirectory of your home folder `%USERPROFILE%`. To simplify the access to the compiled dynamic libraries and executables, you should add the `bin` folder to the `PATH` environment variable:

1. Press the Windows key to open the start menu and type `variable`
2. Select “Edit system environment variables”
3. Click “Environment Variables” button
4. Double click “Path” (either in _User variables_ or _System variables_ section)
5. Click “New” and add entry `C:\usr\bin`

Also make sure to add the path of the `cmake.exe` executable. You can test whether CMake is available by opening a terminal and executing `cmake --version`. If you haven’t installed CMake already, go to [cmake.org/download](https://cmake.org/download/#latest) and install the latest version.

## Using CMake

In general, building a project from source could now look like the following. The commands should be run in a terminal with working directory being the root of the project (i.e. the directory containing the top level `CMakeLists.txt` file):

```sh
cmake -B build
      -G "Visual Studio 17 2022" -A x64
      -DCMAKE_INSTALL_PREFIX=C:/usr
      -DCMAKE_BUILD_TYPE=Release
cmake --build build
cmake --install build
```

Copy

If dependencies of the project you are trying to build cannot be found, though they are already installed somewhere on your system, you can help CMake by setting the [`CMAKE_PREFIX_PATH`](https://cmake.org/cmake/help/latest/variable/CMAKE_PREFIX_PATH.html) variable.

Specifying the generator with `-G` and the architecture with `-A` isn’t necessary, CMake should pick the right values automatically. Note that you can specify a build type in the build step, so setting `CMAKE_BUILD_TYPE` isn’t necessary, too:

```sh
cmake --build build --config Release
```

Copy

The same applies to `CMAKE_INSTALL_PREFIX`, which can be specified in the install step:

```sh
cmake --install build --prefix C:/usr
```

Copy

I recommend always setting the `CMAKE_INSTALL_PREFIX` variable in the configuration step for reasons explained below.

To speed up the build process, you can use the `--parallel` option:

```sh
cmake --build build --config Release --parallel
```

Copy

When using _GCC_ or _clang_, you can specify the number of parallel threads passing the `-j` compiler option:

```sh
cmake --build build --config Release -- -j4
```

Copy

In case the project you are building provides tests, those can be run using [ctest](https://cmake.org/cmake/help/latest/manual/ctest.1.html):

```sh
ctest --test-dir build --output-on-failure -C Release
```

Copy

## Example

This concluding section will serve as a short CMake tutorial. We will build `TagLib`, an open source library for reading and writing audio meta-data. Download the [latest release](https://github.com/taglib/taglib/releases) from GitHub and extract the archive. `TagLib` has an optional dependency `zlib` \- download the [latest release](https://github.com/madler/zlib/releases) from GitHub. Extract the archive, open a terminal in the `zlib` folder and run the following commands to configure, build and install `zlib`:

```sh
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=C:/usr
cmake --build build --config Release
cmake --install build
```

Copy

Note that in the case of `zlib`, specifying the `--prefix` in the install step will not work. This is due to some misconfiguration of the `CMakeLists.txt` file, see this [discussion](https://discourse.cmake.org/t/cmake-install-prefix-not-work/5040). Unfortunately, you cannot know, how a project will handle the installation (i.e. whether it follows CMake’s best practices), so as mentioned above, I recommend specifying the `CMAKE_INSTALL_PREFIX` in the configuration step.

Now that `zlib` is installed, open a terminal in the `TagLib` folder and run the following command:

```sh
cmake -LAH
```

Copy

After the initial configuration, this command will list all available build options of the project (including options marked as [advanced](https://cmake.org/cmake/help/latest/prop_cache/ADVANCED.html)). We will disable `BUILD_BINDINGS` since we’re not interested in building the C bindings. The `BUILD_SHARED_LIBS` option will be enabled to build a shared DLL. Also note the line

```sh
ZLIB_LIBRARY_RELEASE:FILEPATH=C:/usr/lib/zlib.lib
```

Copy

This means that `TagLib` will be dynamically linked against `zlib`. Since we want to link `zlib` statically, we will use the following command:

```sh
cmake -S . -B build
      -DBUILD_BINDINGS=OFF
      -DBUILD_SHARED_LIBS=ON
      -DZLIB_LIBRARY_RELEASE=C:/usr/lib/zlibstatic.lib
```

Copy

In the output you should find that `zlib` has been found and `CppUnit` has not been found, so tests will be skipped. Now run the following commands to build and install:

```sh
cmake --build build --config Release
cmake --install build --prefix C:/usr
```

Copy

Note that in this case, using `--prefix` in the install step will work as expected.

* * *

Please use the [contact](https://wo80.webspace.rocks/contact/?q=Managing%20C%2FC%2B%2B%20library%20dependencies%20on%20Windows) form for comments.

* * *