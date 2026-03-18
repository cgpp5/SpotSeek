Essentia is a library for audio and music analysis, description and synthesis. Though you can find build instructions on [https://essentia.upf.edu/installing.html](https://essentia.upf.edu/installing.html), those won’t help you much compiling Essentia with a recent version of Visual Studio. The original build script is based on Python [Waf](https://waf.io/), which seems a natural choice since the project also provides Python bindings and a large part of the [GitHub repository](https://github.com/MTG/essentia) is taken up by Jupyter notebooks. On the other hand, Essentia is a C++ library at its core, so I thought a CMake build script might be useful. The project is available at [https://github.com/wo80/essentia/tree/cmake](https://github.com/wo80/essentia/tree/cmake).

## Prerequisites

Essentia depends on the following libraries:

- [Eigen](https://libeigen.gitlab.io/): for linear algebra
- [FFTW](https://www.fftw.org/download.html): for the FFT implementation _(optional)_
- [FFmpeg](https://ffmpeg.org/download.html): avcodec/avformat/avutil/swresample for loading/saving any type of audio files _(optional)_
- [libsamplerate](https://github.com/libsndfile/libsamplerate): for resampling audio _(optional)_
- [TagLib](https://github.com/taglib/taglib): for reading audio metadata tags _(optional)_
- [YAML](https://github.com/yaml/libyaml): for YAML files input/output _(optional)_
- [Chromaprint](https://github.com/acoustid/chromaprint): for audio fingerprinting _(optional)_
- [Gaia](https://github.com/MTG/gaia): for using SVM classifier models _(optional)_
- [TensorFlow](https://tensorflow.org/): for inference with TensorFlow deep learning models _(optional)_
- [VAMP SDK](https://github.com/vamp-plugins/vamp-plugin-sdk): for the VAMP plugin _(optional)_

## Building Essentia on Windows

To ensure a smooth build, follow the instructions on [managing C/C++ library dependencies on Windows](https://wo80.webspace.rocks/posts/2022/11-manage-deps-win/) when installing the dependencies. You can download most of them from my [package](https://wo80.webspace.rocks/packages/#tag:essentia) site.

A batch script [build-dependencies-msvc.bat](https://github.com/wo80/essentia/blob/cmake/packaging/build-dependencies-msvc.bat) is now available to fetch all dependencies. Take a look at the Github [cmake workflow](https://github.com/wo80/essentia/blob/cmake/.github/workflows/build-cmake.yml#L54) to see how this can be used to build Essentia.


A full `FFmpeg` Windows build is available at [github.com/GyanD/codexffmpeg](https://github.com/GyanD/codexffmpeg/releases). If you want to build an audio-only version of `FFmpeg`, take a look at the [Compiling audio-only FFmpeg on Windows](https://wo80.webspace.rocks/posts/2022/11-compile-ffmpeg-win/) post. A Github workflow with audio-only FFmpeg releases providing static and shared libraries for Visual Studio is available at [github.com/wo80/ffmpeg-audio-only](https://github.com/wo80/ffmpeg-audio-only).

Despite `Eigen` being a header only library, recent releases come with a CMake build system. Follow the usual CMake practices and install `Eigen` according to the instructions in the [blog post](https://wo80.webspace.rocks/posts/2022/11-manage-deps-win/) mentioned above.

If you want to use `Gaia2` SVM models with Essentia, use the CMake project available at [https://github.com/wo80/gaia/tree/cmake](https://github.com/wo80/gaia/tree/cmake). This will also add a dependency on Qt5. You can find build instructions for Qt in [Compiling Qt with Visual C++ compiler on Windows](https://wo80.webspace.rocks/posts/2023/01-compile-qt-win/).

Note that the Gaia code is no longer maintained and support for the SVM models will probably be removed in a future version of Essentia. It is recommended to use the [TensorFlow models](https://essentia.upf.edu/models.html) instead.


To use `TensorFlow` models with Essentia, use the following package:

- [storage.googleapis.com/tensorflow/versions/2.16.2/libtensorflow-cpu-windows-x86\_64.zip](https://storage.googleapis.com/tensorflow/versions/2.16.2/libtensorflow-cpu-windows-x86_64.zip)

More recent versions may be found on [tensorflow.org](https://www.tensorflow.org/install/lang_c), but weren’t tested by me.

## Building with CMake

First, clone the repository (including submodules for Essentia test data and machine learning models) and switch to the _cmake_ branch:

```
git clone --recurse-submodules https://github.com/wo80/essentia.git
cd essentia
git switch cmake
```

The CMake script provides the following configuration options:

- `BUILD_TESTS`: Build tests (default `ON`)
- `BUILD_EXAMPLES`: Build examples (default `OFF`)
- `BUILD_PYTHON_BINDINGS`: Build Python bindings (default `OFF`)
- `BUILD_VAMP_PLUGIN`: Build VAMP plugin (default `OFF`)
- `USE_TENSORFLOW`: Use TensorFlow (default `OFF`)
- `USE_GAIA2`: Use Gaia2 (default `OFF`)

Configure and build the project, then run the tests:

```
cmake -B build -D BUILD_EXAMPLES=ON
cmake --build build --config Release
ctest --test-dir build --output-on-failure -C Release
```

Install the project (adjust install prefix) with:

```
cmake --install build --config Release --prefix /path/to/install
```

## Building a Python wheel on Windows

The CMake script can be configured to build Python bindings using the `BUILD_PYTHON_BINDINGS` option (be aware that some problems have been reported in the [Github issue](https://github.com/MTG/essentia/issues/1398#issuecomment-1989125322)).

Make sure you have [Python](https://www.python.org/downloads/windows/) installed. In case you want to compile for debugging, make sure to include the debug symbols when installing Python, for example by running the following install command (see [docs.python.org](https://docs.python.org/3/using/windows.html#installing-without-ui)):

```cmd
python-3.13.3-amd64.exe /quiet Include_debug=1 \
                               Include_dev=1 \
                               Include_lib=1 \
                               Include_pip=1 \
                               PrependPath=1 \
                               CompileAll=1 \
                               InstallAllUsers=0
```

Copy

Building the Python bindings requires `numpy`. Install the latest version with `pip install numpy`.

To install the other dependencies use the `build-dependencies-msvc.bat` batch script. Open a terminal in the Essentia root folder and run

```cmd
.\packaging\build-dependencies-msvc.bat --static --build-type Release
```

Copy

The `--static` flag will build static libraries and the `--build-type Release` option will use the release configuration (default is `Debug`). Now you should be ready to configure with CMake and build:

```cmd
cmake -B build -DUSE_TENSORFLOW=ON \
               -DBUILD_PYTHON_BINDINGS=ON \
               -DENABLE_STATIC_DEPENDENCIES=ON \
               -DCMAKE_PREFIX_PATH=%CD%\packaging\msvc

cmake --build build --config Release --parallel
```

Copy

The `ENABLE_STATIC_DEPENDENCIES` option will set some MSVC specific compiler options to ensure static dependencies are used (be aware that TensorFlow is available as a shared library only, see remarks below). The final wheel should then be available in the `build\wheel` subfolder.

You can test the wheel in a virtual environment:

```cmd
python -m venv essentia-test
cd essentia-test
Scripts\activate.bat
pip install C:/path/to/essentia/build/wheel/essentia-2.1b6.dev0-cp313-cp313-win_amd64.whl
```

Copy

A simple Essentia test could look something like

```python
import essentia
import essentia.standard as es

# Loading audio file
audio = es.MonoLoader(filename='C:/path/to/some/audio.mp3')()

# Compute beat positions and BPM
rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
bpm, beats, beats_confidence, _, intervals = rhythm_extractor(audio)

print("BPM:", bpm)
print("Beat positions (sec.):", beats)
```

Copy

### TensorFlow

When trying to run the above Python test, you will most likely get an error like `ImportError: DLL load failed while importing _essentia`. This is because Python cannot load the TensorFlow DLL. There are a couple of ways to fix this:

- In case you won’t be using TensorFlow models, compile Essentia without setting `USE_TENSORFLOW=ON`.
- Tell Python where to look for the TensorFlow DLL using [`os.add_dll_directory`](https://docs.python.org/3/library/os.html#os.add_dll_directory).
- Copy the TensorFlow DLL to the Essentia wheel installation directory (alongside the `_essentia.cp313-win_amd64.pyd` file).

## Building Essentia on Linux

In this section you can find concise instructions on how to build Essentia using CMake on Linux. In case you want to use SVM machine learning models, you will have to build and install Gaia locally. For TensorFlow models, follow the instructions on [tensorflow.org](https://www.tensorflow.org/install/lang_c).

### Debian

Make sure basic build tools are installed:

```sh
sudo apt install build-essential
```

Copy

Next, install CMake and dependencies:

```sh
sudo apt install cmake \
  libeigen3-dev \
  libyaml-dev \
  libfftw3-dev \
  libavcodec-dev \
  libavformat-dev \
  libavutil-dev \
  libswresample-dev \
  libsamplerate0-dev \
  libtag1-dev \
  libchromaprint-dev
```

Copy

Add `python3-dev` and `python3-numpy` to build Python bindings, `vamp-plugin-sdk` for the VAMP plugin. Then follow the CMake build instructions [above](https://wo80.webspace.rocks/posts/2024/01-compile-essentia-cmake/#building-with-cmake).

### Fedora

Make sure basic build tools are installed:

```sh
sudo dnf groupinstall "C Development Tools and Libraries" "Development Tools"
```

Copy

Next, install CMake and dependencies:

```sh
sudo dnf install cmake \
  eigen3-devel \
  libyaml-devel \
  libavcodec-free-devel \
  libavformat-free-devel \
  libavutil-free-devel \
  libswresample-free-devel \
  fftw-devel \
  taglib-devel \
  libsamplerate-devel \
  libchromaprint-devel
```

Copy

Add `python3-devel` and `python3-numpy` to build Python bindings (you might also need `patchelf`), `vamp-plugin-sdk-devel` for the VAMP plugin. Then follow the CMake build instructions [above](https://wo80.webspace.rocks/posts/2024/01-compile-essentia-cmake/#building-with-cmake).

### Arch Linux

Make sure basic build tools are installed:

```sh
sudo pacman -S base-devel --needed
```

Copy

Next, install CMake and dependencies:

```sh
sudo pacman -S cmake eigen libyaml ffmpeg fftw taglib libsamplerate chromaprint
```

Copy

Add `python-numpy` to build Python bindings, `vamp-plugin-sdk` for the VAMP plugin. Then follow the CMake build instructions [above](https://wo80.webspace.rocks/posts/2024/01-compile-essentia-cmake/#building-with-cmake).

## Building with MSYS2

For `mingw64` the package names are

```
mingw-w64-x86_64-eigen3
mingw-w64-x86_64-ffmpeg
mingw-w64-x86_64-fftw
mingw-w64-x86_64-taglib
mingw-w64-x86_64-libsamplerate
mingw-w64-x86_64-libyaml
mingw-w64-x86_64-chromaprint
mingw-w64-x86_64-vamp-plugin-sdk
```

For `ucrt64`, add `-ucrt` after `mingw-w64`, for example `mingw-w64-ucrt-x86_64-eigen3`.

* * *

Please use the [contact](https://wo80.webspace.rocks/contact/?q=Building%20Essentia%20with%20CMake) form or [Github](https://github.com/MTG/essentia/issues/1398) for comments.

* * *