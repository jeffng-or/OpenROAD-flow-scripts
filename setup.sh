#!/usr/bin/env bash

set -euo pipefail

# allow this script to be invoked from any folder
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# macOS detection
IS_DARWIN=false
if [[ "$(uname)" == "Darwin" ]]; then
  IS_DARWIN=true
fi

if $IS_DARWIN && [[ $EUID -eq 0 ]]; then
  echo "Do NOT run this script with sudo on macOS"
  exit 1
fi

if ! $IS_DARWIN && [[ $EUID -ne 0 ]]; then
  echo "This script must be run with sudo on Linux"
  exit 1
fi

tmpfile=$(mktemp)
# any error messages from this command will stand out
# more clearly when run as a separate command rather than
# being piped
git submodule status --recursive > "$tmpfile"

if grep -q "^-" "$tmpfile"; then
  if $IS_DARWIN; then
    git submodule update --init --recursive
  else
    sudo -u $SUDO_USER git submodule update --init --recursive
  fi
elif grep -q "^+" "$tmpfile"; then
  # Make it easy for users who are not hacking ORFS to do the right thing,
  # run with current submodules, at the cost of having ORFS
  # hackers disable this test manually when hacking setup.sh
  echo "Submodules are not up to date, run 'git submodule update --recursive' and try again"
  exit 1
fi

"$DIR/etc/DependencyInstaller.sh" -base
if $IS_DARWIN; then
  "$DIR/etc/DependencyInstaller.sh" -common -prefix="$DIR/dependencies"
else
  sudo -u $SUDO_USER "$DIR/etc/DependencyInstaller.sh" -common -prefix="$DIR/dependencies"
fi
