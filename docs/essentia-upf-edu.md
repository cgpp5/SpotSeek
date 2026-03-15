# Installing Essentia [Link to this heading](https://essentia.upf.edu/installing.html\#installing-essentia "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#installing-essentia "Permalink to this headline")

## macOS [Link to this heading](https://essentia.upf.edu/installing.html\#macos "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#macos "Permalink to this headline")

The easiest way to install Essentia on macOS is by using [our Homebrew formula](https://github.com/MTG/homebrew-essentia). You will need to install [Homebrew package manager](http://brew.sh/) first (and there are other good reasons to do so apart from Essentia).

Note that packages location for Python installed via Homebrew is different from the system Python. If you plan to use Essentia with Python, make sure the Homebrew directory is at the top of your PATH environment variable. To this end, add the line:

```
export PATH=/usr/local/bin:/usr/local/sbin:$PATH
```

at the bottom of your `~/.bash_profile` file. More information about using Python and Homebrew is [here](https://docs.brew.sh/Homebrew-and-Python).

## Linux [Link to this heading](https://essentia.upf.edu/installing.html\#linux "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#linux "Permalink to this headline")

You can install Essentia Python extension from PyPi:

```
pip install essentia
```

For other needs, you need to compile Essentia from source (see below).

## Windows, Android, iOS [Link to this heading](https://essentia.upf.edu/installing.html\#windows-android-ios "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#windows-android-ios "Permalink to this headline")

Cross-compile Essentia from Linux/macOS (see below).

# Compiling Essentia from source [Link to this heading](https://essentia.upf.edu/installing.html\#compiling-essentia-from-source "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#compiling-essentia-from-source "Permalink to this headline")

Essentia depends on (at least) the following libraries:

- [Eigen](http://eigen.tuxfamily.org/): for linear algebra

- [FFTW](http://www.fftw.org/): for the FFT implementation _(optional)_

- [libavcodec/libavformat/libavutil/libswresample](http://ffmpeg.org/) (from the FFmpeg/LibAv project): for loading/saving any type of audio files _(optional)_

- [libsamplerate](http://www.mega-nerd.com/SRC/): for resampling audio _(optional)_

- [TagLib](http://developer.kde.org/~wheeler/taglib.html): for reading audio metadata tags _(optional)_

- [LibYAML](http://pyyaml.org/wiki/LibYAML): for YAML files input/output _(optional)_

- [Gaia](https://github.com/MTG/gaia): for using SVM classifier models _(optional)_

- [Chromaprint](https://github.com/acoustid/chromaprint): for audio fingerprinting _(optional)_

- [TensorFlow](https://tensorflow.org/): for inference with TensorFlow deep learning models _(optional)_


All dependencies are optional, and some functionality will be excluded when a dependency is not found.

## Installing dependencies on Linux [Link to this heading](https://essentia.upf.edu/installing.html\#installing-dependencies-on-linux "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#installing-dependencies-on-linux "Permalink to this headline")

You can install those dependencies on a Debian/Ubuntu system from official repositories using the command below:

```
sudo apt-get install build-essential libeigen3-dev libyaml-dev libfftw3-dev libavcodec-dev libavformat-dev libavutil-dev libswresample-dev libsamplerate0-dev libtag1-dev libchromaprint-dev
```

In order to use Python 3 bindings for the library, you might also need to install python3-dev, python3-numpy-dev (or python3-numpy on Ubuntu) and python3-yaml for YAML support in python:

```
sudo apt-get install python3-dev python3-numpy-dev python3-numpy python3-yaml python3-six
```

Note that, depending on the version of Essentia, different versions of `libav*` and `libtag1-dev` packages are required. See [release notes for official releases](https://github.com/MTG/essentia/releases).

Since the 2.1-beta3 release of Essentia, the required version of TagLib (`libtag1-dev`) is greater or equal to `1.9`. The required version of LibAv (`libavcodec-dev`, `libavformat-dev`, `libavutil-dev` and `libswresample-dev`) is greater or equal to `10`. The appropriate versions are distributed in Ubuntu 14.10 or later, and in Debian wheezy-backports. If you want to install Essentia on older versions of Ubuntu/Debian, you will have to [install a proper LibAv version from source](https://essentia.upf.edu/FAQ.html#build-essentia-on-ubuntu-14-04-or-earlier).

If you are willing to use Essentia with a TensorFlow wrapper in C++, install the TensorFlow shared library using a helper script inside our source code:

```
src/3rdparty/tensorflow/setup_from_libtensorflow.sh
```

## Installing dependencies on macOS [Link to this heading](https://essentia.upf.edu/installing.html\#installing-dependencies-on-macos "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#installing-dependencies-on-macos "Permalink to this headline")

Install Command Line Tools for Xcode. Even if you install Xcode from the app store you must configure command-line compilation by running:

```
xcode-select --install
```

Install [Homebrew package manager](http://brew.sh/).

Insert the Homebrew directory at the top of your PATH environment variable by adding the following line at the bottom of your `~/.profile` file:

```
export PATH=/usr/local/bin:/usr/local/sbin:$PATH
```

Install prerequisites:

```
brew install pkg-config gcc readline sqlite gdbm freetype libpng
```

Install Essentia’s dependencies:

```
brew install eigen libyaml fftw ffmpeg@2.8 libsamplerate libtag chromaprint tensorflow
```

[Install Python environment using Homebrew](http://docs.python-guide.org/en/latest/starting/install/osx) (Note that you are advised to do as described here and there are [good reasons to do so](http://docs.python-guide.org/en/latest/starting/install/osx/). You will most probably encounter installation errors when using Python/NumPy preinstalled with macOS.):

```
brew install python --framework
pip install ipython numpy matplotlib pyyaml
```

## Compiling Essentia [Link to this heading](https://essentia.upf.edu/installing.html\#compiling-essentia "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#compiling-essentia "Permalink to this headline")

Once your dependencies are installed, you can proceed to compiling Essentia. Download Essentia’s source code at [Github](https://github.com/MTG/essentia). Due to different dependencies requirement (see [release notes for official releases](https://github.com/MTG/essentia/releases)), make sure to download the version compatible with your system:

- **master** branch is the most updated version of Essentia in development

- **2.1 beta5** is the current stable version recommended to install.


Go into its source code directory and start by configuring the build:

```
python3 waf configure --build-static --with-python --with-cpptests --with-examples --with-vamp
```

Use these (optional) flags:

- `--with-python` to build with Python bindings,

- `--with-examples` to build [command line extractors](https://essentia.upf.edu/extractors_out_of_box.html) based on the library,

- `--with-vamp` to build Vamp plugin wrapper,

- `--with-gaia` to build with Gaia support,

- `--with-tensorflow` to build with TensorFlow support,

- `--mode=debug` to build in debug mode,

- `--with-cpptests` to build cpptests


Note: you must _always_ configure at least once before building!

The following will give you the full list of options:

```
python3 waf --help
```

If you want to build with a custom toolchain, you can pass in the CC and CXX variables for using another compiler. For example, to build the library and examples with clang:

```
CC=clang CXX=clang++ python3 waf configure
```

To compile everything you’ve configured:

```
python3 waf
```

All built examples will be located in `build/src/examples/` folder, as well as the Vamp plugin file `libvamp_essentia.so`.

To install the C++ library, Python bindings, extractors and Vamp plugin (if configured successfully; you might need to run this command with sudo):

```
python3 waf install
```

## Python 3 bindings [Link to this heading](https://essentia.upf.edu/installing.html\#python-3-bindings "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#python-3-bindings "Permalink to this headline")

To build Essentia with Python 3 bindings, use the `--with-python` configuration flag.

By default, the waf build script will auto-detect the `site-packages` (or `dist-packages`) directory to install Essentia’s Python package according to the Python binary used to execute it. Alternatively, you can set a specific Python binary using the `--python=PYTHON` configuration option.

Note that when installing Essentia to the default `/usr/local` prefix, on some Linux distributions this results in a wrong `/usr/local/lib/python3/dist-packages/` package installation path (for example, Ubuntu, see
[here](https://bugs.launchpad.net/ubuntu/+source/python3-defaults/+bug/1814653) and
[here](https://bugs.launchpad.net/ubuntu/+source/python3-stdlib-extensions/+bug/1832215)).

To avoid import errors on such systems, specify the correct path in `waf configure` using a `--pythondir` option or the `PYTHONDIR` environmental variable. For example, on Ubuntu 22.04 the correct path for the default Python 3.10 is `/usr/local/lib/python3.10/dist-packages/`.

Alternatively, you can also configure the `PYTHONPATH` variable to include the `/usr/local/lib/python3/dist-packages/` path in the list of Python 3 [module search paths](https://docs.python.org/3/tutorial/modules.html#the-module-search-path).

Finally, if you are having `ImportError: libessentia.so: cannot open shared object file: No such file or directory` in Python after installation on Linux, make sure that `/usr/local/lib` is included to `LD_LIBRARY_PATH` or run `ldconfig`.

## Running tests (optional) [Link to this heading](https://essentia.upf.edu/installing.html\#running-tests-optional "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#running-tests-optional "Permalink to this headline")

Run tests if you want to ensure that Essentia works correctly.

To run the C++ base unit tests (only test basic library behavior):

```
python3 waf run_tests
```

To run the Python unit tests (test all algorithms):

```
python3 waf run_python_tests
```

To run Python unit tests, you need to install Python bindings first. Some of these tests require additional audio files and binaries stored in [essentia-audio](https://github.com/MTG/essentia-audio) and [essentia-models](https://github.com/MTG/essentia-models/) submodule repositories. Therefore, make sure to clone Essentia git repository recursively with its submodules (`git clone --recursive https://github.com/MTG/essentia.git`).

Also, some tests require additional dependencies. Install those with:

```
pip3 install scikit-learn
```

See more information about running tests [in our FAQ](https://essentia.upf.edu/FAQ.html#running-tests).

## Building documentation (optional) [Link to this heading](https://essentia.upf.edu/installing.html\#building-documentation-optional "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#building-documentation-optional "Permalink to this headline")

All documentation is provided on the official website of Essentia library. Follow the steps below to generate it by yourself.

Install doxigen and pip3. If you are on Linux:

```
sudo apt-get install doxygen python3-pip
```

Install additional dependencies (you might need to run this command with sudo):

```
pip3 install sphinx pyparsing sphinxcontrib-doxylink docutils jupyter sphinx-toolbox nbformat gitpython
sudo apt-get install pandoc
```

Make sure to build Essentia with Python 3 bindings and run:

```
python3 waf doc
```

Documentation will be located in `doc/sphinxdoc/_build/html/` folder.

Note: Code examples embedded in the documentation page for Essentia Models require Python example files located in `src/examples/python/models/scripts/`. These scripts can be automatically regenerated with `src/examples/python/models/generate_example_scripts.sh`.

## Building Essentia on Windows [Link to this heading](https://essentia.upf.edu/installing.html\#building-essentia-on-windows "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#building-essentia-on-windows "Permalink to this headline")

Essentia C++ library and extractors based on it can be compiled and run correctly on Windows, but Python bindings are not supported yet. The easiest way to build Essentia is by [cross-compilation on Linux using MinGW](https://essentia.upf.edu/FAQ.html#cross-compiling-for-windows-on-linux). However the resulting library binaries are only compatible within C++ projects using MinGW compilers, and therefore they are not compatible with Visual Studio. If you want to use Visual Studio, there is no project readily available, so you will have to setup one yourself and compile the dependencies too.

## Building Essentia in Windows Subsystem for Linux (WSL) [Link to this heading](https://essentia.upf.edu/installing.html\#building-essentia-in-windows-subsystem-for-linux-wsl "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#building-essentia-in-windows-subsystem-for-linux-wsl "Permalink to this headline")

It is possible to install Essentia easily in the _Windows Subsystem for Linux_ on Windows 10. This environment allows to run the same command-line utilities that could be run within your favorite [distribution](https://aka.ms/wslstore). Note that WSL is still in its infancy and the methods of interoperability between Windows applications and WSL are likely to change in the future.

To install WSL, follow the [official guide](https://aka.ms/wsl2).

After WSL is successfully installed, you should open a bash terminal and install the dependencies (see: [Installing dependencies on Linux](https://essentia.upf.edu/installing.html#installing-dependencies-on-linux)).
Finally, you can compile Essentia (see: [Compiling Essentia](https://essentia.upf.edu/installing.html#compiling-essentia)).

## Building Essentia on Android [Link to this heading](https://essentia.upf.edu/installing.html\#building-essentia-on-android "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#building-essentia-on-android "Permalink to this headline")

A lightweight version of Essentia can be [cross-compiled for Android](https://essentia.upf.edu/FAQ.html#cross-compiling-for-android) from Linux or macOS.

## Building Essentia on iOS [Link to this heading](https://essentia.upf.edu/installing.html\#building-essentia-on-ios "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#building-essentia-on-ios "Permalink to this headline")

A lightweight version of Essentia can be [cross-compiled for iOS](https://essentia.upf.edu/FAQ.html#cross-compiling-for-ios) from macOS.

## Building Essentia for Web using asm.js or WebAssembly [Link to this heading](https://essentia.upf.edu/installing.html\#building-essentia-for-web-using-asm-js-or-webassembly "Link to this heading") [Permalink to this headline](https://essentia.upf.edu/installing.html\#building-essentia-for-web-using-asm-js-or-webassembly "Permalink to this headline")

A lightweight version of Essentia can be cross-compiled to asm.js or WebAssembly targets using Emscripten for it’s usage on the Web. See [FAQ](https://essentia.upf.edu/FAQ.html) for more details.