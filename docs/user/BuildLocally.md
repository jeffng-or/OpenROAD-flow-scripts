# Build from sources locally

## Choose Your Build Path

| Path | Prerequisites | sudo? | Best for |
|------|--------------|-------|----------|
| **Bazel** | [Bazelisk](https://bazel.build/install/bazelisk) | No | Most users |
| **Nix** | [Nix](https://github.com/DeterminateSystems/nix-installer) | No | Nix users |
| **CMake** | `sudo ./setup.sh` | Yes | Existing CMake developers |

### Bazel (recommended)

Install [Bazelisk](https://bazel.build/install/bazelisk) following the
[official instructions](https://bazel.build/install/bazelisk).

``` shell
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts
cd OpenROAD-flow-scripts
bazelisk run //:install
cd flow && make
```

For options: `bazelisk run //:install -- --help`

### Nix

``` shell
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts
cd OpenROAD-flow-scripts
nix develop
cd flow && make
```

### CMake (existing path)

## Clone and Install Dependencies

The `setup.sh` script installs all of the dependencies, including OpenROAD dependencies, if they are not already installed.

Supported configurations are: Ubuntu 20.04, Ubuntu 22.04, Ubuntu 22.04(aarch64), RHEL 8, RockyLinux 9 and Debian 11.

``` shell
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts
cd OpenROAD-flow-scripts
sudo ./setup.sh
```

## Build

``` shell
./build_openroad.sh --local
```
:::{Note}
There is a `build_openroad.log` file that is generated with every
build in the main directory. In case of filing issues, it can be uploaded
in the "Relevant log output" section of OpenROAD-flow-scripts repo
[issue form](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/new?assignees=&labels=&template=bug_report_with_orfs.yml).
:::

## Verify Installation

The binaries should be available on your `$PATH` after setting
up the environment. The `make` command runs from RTL-GDSII generation for default design `gcd` with `nangate45` PDK. 

``` shell
source ./env.sh
yosys -help
yosys -m slang -p "slang_version"
openroad -help
cd flow
make
```

You can view final layout images in OpenROAD GUI using this command.

``` shell
make gui_final
```

![gcd_final.webp](../images/gcd_final.webp)

## Compiling and debugging in Visual Studio Code

Set up environment variables using `dev_env.sh`, then start Visual Studio Code. Please ensure [CMake plugins](https://code.visualstudio.com/docs/cpp/cmake-linux) are installed.

``` shell
. ./dev_env.sh
code tools/OpenROAD/
```

## Build and run ORFS flows with Bazel

ORFS uses [bazel-orfs](https://github.com/The-OpenROAD-Project/bazel-orfs) to run
the flow entirely within Bazel. This is separate from `bazelisk run //:install` above
which installs tools for the Makefile-based flow.

To build a design with Bazel:

    cd flow
    bazelisk build designs/asap7/gcd:gcd_floorplan

Or to run all flows currently available in Bazel:

    cd flow
    bazelisk build ...

### Upgrading MODULE.bazel with the latest bazel-orfs and ORFS Docker image

Run:

    bazelisk run @bazel-orfs//:bump

Then commit MODULE.bazel and MODULE.bazel.lock.
