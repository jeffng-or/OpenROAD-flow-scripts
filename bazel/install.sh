#!/bin/bash
set -e

# ORFS install script
# Single user-facing entry point: bazelisk run //:install
#
# Builds and installs tools to tools/install/ where flow/Makefile expects them.
# Uses stamp files for fast no-op re-runs (seconds when nothing changed).

WORKSPACE="${BUILD_WORKSPACE_DIRECTORY:-.}"
INSTALL_DIR="${WORKSPACE}/tools/install"
NUM_THREADS=$(nproc)

usage() {
    cat <<'EOF'
Usage: bazelisk run //:install [-- OPTIONS]

Installs tools required for the ORFS flow/Makefile.

Installed:
  openroad      OpenROAD with GUI support
  yosys         Yosys synthesis tool
  yosys-slang   Yosys SystemVerilog plugin

Not yet supported (use sudo ./setup.sh):
  klayout       KLayout layout viewer
  kepler        Kepler formal verification

Nix users: nix develop already provides all tools. See flake.nix.

Options:
  --help, -h        Show this help
  --skip-openroad   Skip OpenROAD build
  --threads N       Compilation threads (default: nproc)
EOF
    exit 0
}

# Check for required system dependencies before expensive builds.
# ORFS checks deps for what it builds (yosys/slang). OpenROAD checks
# its own deps in tools/OpenROAD/bazel/install.sh (separation of concerns).
#
# Currently only Ubuntu/Debian is checked. Dependency checking for
# other platforms (macOS, RHEL, Fedora, etc.) is not implemented
# because we cannot test them. Contributions welcome.
check_ubuntu_deps() {
    local missing_cmds=()
    local missing_pkgs=()

    # Commands needed for yosys build
    command -v bison   &>/dev/null || { missing_cmds+=(bison);   missing_pkgs+=(bison); }
    command -v flex    &>/dev/null || { missing_cmds+=(flex);    missing_pkgs+=(flex); }
    command -v gawk    &>/dev/null || { missing_cmds+=(gawk);    missing_pkgs+=(gawk); }
    command -v g++     &>/dev/null || { missing_cmds+=(g++);     missing_pkgs+=(g++); }
    command -v pkg-config &>/dev/null || { missing_cmds+=(pkg-config); missing_pkgs+=(pkg-config); }
    command -v tclsh   &>/dev/null || { missing_cmds+=(tclsh);   missing_pkgs+=(tcl); }
    command -v git     &>/dev/null || { missing_cmds+=(git);     missing_pkgs+=(git); }
    command -v cmake   &>/dev/null || { missing_cmds+=(cmake);   missing_pkgs+=(cmake); }

    # Dev libraries needed for yosys/slang compilation (check via dpkg)
    for pkg in tcl-dev libffi-dev libreadline-dev zlib1g-dev; do
        if ! dpkg -s "$pkg" &>/dev/null 2>&1; then
            missing_pkgs+=("$pkg")
        fi
    done

    if [[ ${#missing_pkgs[@]} -gt 0 ]]; then
        echo "ERROR: Missing dependencies for Yosys build."
        if [[ ${#missing_cmds[@]} -gt 0 ]]; then
            echo "  Missing commands: ${missing_cmds[*]}"
        fi
        echo ""
        echo "On Ubuntu this would be:"
        echo "  sudo apt install ${missing_pkgs[*]}"
        exit 1
    fi
}

if command -v dpkg &>/dev/null; then
    check_ubuntu_deps
fi

BUILD_OPENROAD=1

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            usage
            ;;
        --skip-openroad)
            BUILD_OPENROAD=0
            ;;
        --threads)
            NUM_THREADS="$2"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
    shift
done

# --- Check submodules are initialized ---
for sub in tools/OpenROAD tools/yosys tools/yosys-slang; do
    if [[ ! -d "${WORKSPACE}/${sub}" ]] || [[ -z "$(ls -A "${WORKSPACE}/${sub}" 2>/dev/null)" ]]; then
        echo "ERROR: ${sub} not initialized."
        echo "Run: git submodule update --init --recursive"
        exit 1
    fi
done

# --- OpenROAD (delegates to its own //:install) ---
if [[ $BUILD_OPENROAD -eq 1 ]]; then
    echo "=== Building OpenROAD with GUI support ==="
    (cd "${WORKSPACE}/tools/OpenROAD" && bazelisk run --//:platform=gui //:install)
fi

# --- Yosys ---
# Uses stamp file for fast no-op: if the yosys submodule commit hasn't
# changed, skip the build entirely.
YOSYS_INSTALL="${INSTALL_DIR}/yosys"
YOSYS_STAMP="${YOSYS_INSTALL}/.yosys_commit"
YOSYS_COMMIT="$(git -C "${WORKSPACE}/tools/yosys" rev-parse HEAD)"

if [[ -f "${YOSYS_STAMP}" ]] && [[ "$(cat "${YOSYS_STAMP}")" == "${YOSYS_COMMIT}" ]]; then
    echo "=== Yosys already up to date (${YOSYS_COMMIT:0:12}) ==="
else
    echo "=== Building Yosys ==="
    (
        cd "${WORKSPACE}/tools/yosys"
        make -j "${NUM_THREADS}" PREFIX="${YOSYS_INSTALL}" ABC_ARCHFLAGS=-Wno-register
        make install PREFIX="${YOSYS_INSTALL}"
    )
    echo "${YOSYS_COMMIT}" > "${YOSYS_STAMP}"
    echo "Yosys installed to ${YOSYS_INSTALL}/bin/yosys"
fi

# --- yosys-slang ---
SLANG_STAMP="${YOSYS_INSTALL}/.slang_commit"
SLANG_COMMIT="$(git -C "${WORKSPACE}/tools/yosys-slang" rev-parse HEAD)"

if [[ -f "${SLANG_STAMP}" ]] && [[ "$(cat "${SLANG_STAMP}")" == "${SLANG_COMMIT}" ]]; then
    echo "=== yosys-slang already up to date (${SLANG_COMMIT:0:12}) ==="
else
    echo "=== Building yosys-slang ==="
    (
        cd "${WORKSPACE}/tools/yosys-slang"
        cmake -S . -B build \
            -DYOSYS_CONFIG="${YOSYS_INSTALL}/bin/yosys-config" \
            -DCMAKE_BUILD_TYPE=Release \
            -DYOSYS_SLANG_REVISION=unknown \
            -DSLANG_REVISION=unknown
        cmake --build build -j "${NUM_THREADS}"
        cmake --install build --prefix "${YOSYS_INSTALL}"
    )
    echo "${SLANG_COMMIT}" > "${SLANG_STAMP}"
    echo "yosys-slang installed to ${YOSYS_INSTALL}/share/yosys/plugins/"
fi

echo ""
echo "=== Done ==="
echo "cd flow && make"
