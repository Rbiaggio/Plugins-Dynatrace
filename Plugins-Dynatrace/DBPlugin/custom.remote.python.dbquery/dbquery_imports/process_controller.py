import os
import subprocess
import logging

log = logging.getLogger(__name__)


def start_process(cmd):
    log.info(f"Attempting to execute command '{' '.join(cmd)}'")
    if os.name == "nt":
        p = subprocess.Popen(cmd, creationflags=0x00000008)
    else:
        p = subprocess.Popen(cmd)
    log.info(f"Successfully started the process, PID: {p.pid}")
