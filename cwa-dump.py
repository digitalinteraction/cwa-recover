#!/usr/bin/env python
# coding=UTF-8
# CWA Drive Dump

from subprocess import check_output
import time
from datetime import timedelta
import platform
import ctypes
import sys
import os
import atexit
#import io


def driveDump(path, outputFile, mode, type):
  blockSize = 128 * 1024
  
  print("DriveDump:", path)
  try:
    print("Detecting device physical drive size...")
    fileSize = findPhysicalDriveSize(path)

    if fileSize is None or fileSize <= 0:
      if fileSize is None:
        print("WARNING: Detecting drive size is not supported on this platform.")
      else:
        print("WARNING: Problem determining drive size.")

      if type == "ax3":
        print("WARNING: Using default drive size for AX3")
        fileSize = 992161 * 512

      elif type == "ax6":
        print("WARNING: Using default drive size for AX6")
        fileSize = 1975995 * 512

      elif type is None:
        print("ERROR: Cannot use a default drive size as device type is unspecified. ")
        return False

      else:
        print("ERROR: Cannot use a default drive size for unknown device type: " + type)
        return False

    unmountDrive(path)

    startTime = time.time()
    with open(path, 'rb') as fi:
      with open(outputFile, mode) as fo:
        writtenSize = 0
        # Resume
        offset = fo.tell()
        fi.seek(offset)
        while True:
          data = fi.read(blockSize)
          size = len(data)
          if size <= 0:
            break
          written = fo.write(data)
          fo.flush()
          if written != size:
            print("ERROR: Problem writing all of the data, wrote " + str(written) + " of " + str(size) + "")
            break
            
          offset += size
          writtenSize += written
          perc = round(100 * offset / fileSize, 1)
          elapsed = time.time() - startTime
          remaining = 0
          if elapsed > 0:
            rate = writtenSize / elapsed
            if rate > 0:
              remaining = (fileSize - offset) / rate
          print("Dumping " + str(written) + " =" + str(writtenSize) + " @" + str(offset) + " /" + str(fileSize) + " (" + str(perc) + "%) in " + str(timedelta(seconds=int(elapsed))) + ", " + str(round(rate / 1024, 3)) + " kB/s, ETA " + str(timedelta(seconds=int(remaining))) + ".")
          
          if offset >= fileSize:
            break

  except FileExistsError:
    print("ERROR: Output file already exists.  Remove, rename, or use options --overwrite or --resume: ", outputFile)
    return False

  except PermissionError:
    if platform.system() == "Windows":
      print("ERROR: Permission error -- you must run this in an Ctrl+Shift+Esc, Alt+F, N, cmd, 'Create this task with administrative privileges.'")
    else:
      print("ERROR: Permission error -- you must run this as root, try running prefixed with: sudo")
    return False
  
  except OSError as e:
    print("ERROR: Problem accessing the device:", e)
    if e.errno == 16:
      print("ERROR: Resource busy, the device is in use -- check that it is not mounted.")
    return False

  return True


def unmountDrive(path):
  # Windows
  if platform.system() == "Windows":
    return True

  elif platform.system() == "Darwin":
    # diskutil unmountDisk /dev/$DISK
    command = "diskutil unmountDisk " + path + ""
    print("...macOS: Unmounting device:", command)
    out = check_output(["bash", "-c", command])
    response = out.decode("utf-8")
    # Unmount of all volumes on disk4 was successful
    print("...macOS: response:", response)
    return True

  else:
    print("..." + platform.system() + ": Automatically unmounted not supported on this platform.")
    return None


def findPhysicalDriveSize(physicalDrive):
  # Windows
  if platform.system() == "Windows":
    print("...Windows: Detecting physical drive size...")
    out = check_output(["wmic", "diskdrive", "list", "brief"])
    lines = out.split(b"\r\n")
    for line in lines:
      parts = line.split()
      for part in parts:
        if part.decode() == physicalDrive:
          return int(parts[-1].decode())
    return 0

  # macOS
  elif platform.system() == "Darwin":
    # diskutil info -plist disk4s1 | grep -C1 "<key>TotalSize</key>" | tail -n 2 | grep -Eo "\d+"
    command = "diskutil info -plist disk4s1 | grep -C1 \"<key>TotalSize</key>\" | tail -n 2 | grep -Eo \"\\d+\""
    out = check_output(["bash", "-c", command])
    out.decode("utf-8")
    return int(out)

  # Unsupported platform
  else:
    print("..." + platform.system() + ": Automatically detecting physical drive size not supported on this platform.")
    return None


def findPhysicalDrives():
  # Windows
  if platform.system() == "Windows":
    print("...Windows: detecting device physical drive...")
    prefixDevice = [b"AX3 AX3 Mass Storage USB Device", b"AX6 AX6 Mass Storage USB Device"]
    prefixDrive = b"\\\\.\\PHYSICALDRIVE"
    out = check_output(["wmic", "diskdrive", "list", "brief"])
    paths = []
    lines = out.split(b"\r\n")
    for line in lines:
      match = False
      for prefix in prefixDevice:
        if line.startswith(prefix):
          match = True
      if match:
        parts = line.split()
        for part in parts:
          if part.startswith(prefixDrive):
            paths.append(part.decode("utf-8"))
    return paths

  # macOS
  elif platform.system() == "Darwin":
    # diskutil list | grep -E "\bAX\d+_\d+\b" | grep -Eo "\bdisk\d+s\d+"
    command = "diskutil list | grep -E \"\\bAX\\d+_\\d+\\b\" | grep -Eo \"\\bdisk\\d+s\\d+\""
    paths = []
    try:
      out = check_output(["bash", "-c", command])
    except:
      print("ERROR: Problem detecting device physical drive -- please check the device is connected.")
      return paths
    lines = out.split(b"\n")
    for line in lines:
      line = line.decode("utf-8")
      if len(line) > 0:
        paths.append("/dev/" + line)
    return paths

  # Unsupported platform
  else:
    print("..." + platform.system() + ": Automatically finding device path not supported on this platform.")
    return None


def findSingleDrive():
  paths = findPhysicalDrives()

  if paths is None:
    print("WARNING: Unable to find drive path.")
    return None
  elif len(paths) <= 0:
    print("WARNING: Found no matching drive (expecting one):")
    return None
  elif len(paths) > 1:
    print("WARNING: Found too many matching drives (expecting at most one):")
    for path in paths:
      print("", path);
    return None
  else:
    path = paths[0]
    print("NOTE: Found path:", path)
    return path


def needsToRunElevated():
  # Windows
  if platform.system() == "Windows":
    try:
      if ctypes.windll.shell32.IsUserAnAdmin():
        return False
      else:
        return True
    except:
      return None

  # Linux or macOS
  elif platform.system() == "Linux" or platform.system() == "Darwin":
    if os.getuid() == 0:
      return False
    return None

  # Unsupported platform
  else:
    return None


# Re-run the program with admin rights
def rerunElevated():
  # Windows
  if platform.system() == "Windows":
    params = " ".join(['"%s"' % (x,) for x in sys.argv[0:]])
    print("...Windows: spawning version with admin rights...", sys.executable, params)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    return True

  # Unsupported platform
  else:
    print("..." + platform.system() + ": Not running with elevated permissions and will not attempt to automatically re-run on this platform -- try re-running the command prefixed with: sudo")


def pause():
  print("Press Enter to continue...")
  input()

def main():
  #atexit.register(pause)
  print("Running...")

  # Options
  drivePath = None
  outputFile = None
  mode = "xb"
  type = None
  attemptElevate = True
  pauseOnExit = True
  arg = 1
  while arg < len(sys.argv):
    if sys.argv[arg].startswith("-"):
      if sys.argv[arg] == "--no-overwrite":
        mode = "xb"

      elif sys.argv[arg] == "--overwrite":
        mode = "wb"

      elif sys.argv[arg] == "--resume":
        mode = "ab"

      elif sys.argv[arg] == "--type:ax3":
        type = "ax3"

      elif sys.argv[arg] == "--type:ax6":
        type = "ax6"

      elif sys.argv[arg] == "--source":
        arg += 1
        if arg < len(sys.argv):
          drivePath = sys.argv[arg]
        else:
          print("WARNING: No device specified after --source")

      elif sys.argv[arg] == "--dest":
        arg += 1
        if arg < len(sys.argv):
          outputFile = sys.argv[arg]
        else:
          print("WARNING: No output file specified after --dest")

      elif sys.argv[arg] == "--no-pause":
        pauseOnExit = False

      elif sys.argv[arg] == "--no-elevate":
        attemptElevate = False

      else:
        print("ERROR: Unrecognized option: " + sys.argv[arg])
        return

    elif outputFile == None:  # backwards-compatible: dest-only specified
      outputFile = sys.argv[arg]

    elif drivePath == None: # also supports: source dest
      drivePath = outputFile
      outputFile = sys.argv[arg]

    else:
      print("ERROR: Unrecognized positional argument: " + sys.argv[arg])
      return

    arg += 1

  if outputFile is None:
    outputFile = "cwa-dump.img"
  print("NOTE: Using output file in mode=" + mode + ":", outputFile)
  
  if drivePath is None:
    print("Determining source...")
    drivePath = findSingleDrive()
  
  if drivePath is None:
    print("ERROR: No device specified or found -- cannot continue.")
    return

  print("Checking whether likely needs to run with elevated permissions...")
  if needsToRunElevated():
    print("...it is likely to need to run with elevated permissions.")
    if attemptElevate:
      print("...attempting to elevate...")
      ret = rerunElevated()
      if ret is not None:
        return ret

  # Run code needing admin rights
  ret = driveDump(drivePath, outputFile, mode, type)
  if pauseOnExit:
    pause()

  return ret

if __name__ == "__main__":
  main()
