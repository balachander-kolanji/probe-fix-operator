#!/bin/bash

# Check if Kopf operator is running
pgrep -f probe_controller.py >/dev/null || exit 1
