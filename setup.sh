#!/bin/bash


EPIC_DIR=$(pwd)/epic-geom/
if [ ! -d "$EPIC_DIR" ]; then
    echo "local ePIC source code not found, downloading"
    git clone "https://github.com/eic/epic.git"
    EPIC_DIR=$(pwd)/epic-geom/
else
    echo "ePIC geometry source code found"
fi

EIC_SHELL_DIR=$(pwd)
if [ ! -f "$EIC_SHELL_DIR/eic-shell" ]; then
    echo "eic-shell not found, downloading"
    curl --location https://get.epic-eic.org | bash
    EIC_SHELL_DIR=$(pwd)
else
    echo "eic-shell found"
fi

export EIC_SHELL_HOME=$EIC_SHELL_DIR
export EPIC_HOME=$EPIC_DIR

export DETECTOR=epic
export DETECTOR_PATH=$EPIC_HOME
export DETECTOR_CONFIG=${1:-epic}
export DETECTOR_VERSION=main

export EPIC_DETECTOR=$(pwd)/ProjectUtils/ePICUtils/
export AID2E_HOME=$(pwd)