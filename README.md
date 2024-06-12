# Open Movement CWA Data Recovery

> This repository is split from the main [Open Movement](https://github.com/digitalinteraction/openmovement) repository.

If you have a AX device where the filesystem has been corrupted, or a file that might have been corrupted, it may be possible to salvage the data.

**IMPORTANT:** At no point should you accept any offer by Windows of fixing the drive, as this can make things worse!


## Step 1: Attempt a manual copy

If the data is still on the device, you should first try to manually copy the file off the drive (otherwise, you can skip this step).

1. Open Windows *File Manager*
2. Click on *This PC*
3. Connect the device and wait 10 seconds
4. Identify the drive letter for the device and double-click it
5. Locate the file `CWA-DATA.CWA` and drag-and-drop the file to another location to copy it.

If the copy completes, you have successfully downloaded the data file, and should not need any of the following steps.

If the copy does not complete successfully, or you suspect the file is incomplete, then try the steps below to run the recovery script.


## Step 2: Getting started with the recovery scripts

1. Check whether you have *Python* installed.  e.g., on Windows: <kbd>Windows</kbd>+<kbd>R</kbd>: `cmd /k python` -- if you get an error message, you may not have Python installed.  You can install Python from: [python.org/downloads](https://www.python.org/downloads/)

2. If you are on Windows or Mac and want to be able to create a disk image from the device itself, save this page: [cwa-dump.py](https://raw.githubusercontent.com/digitalinteraction/cwa-recover/main/cwa-dump.py) as a file on your computer named `cwa-dump.py`.

3. Save this page: [cwa-recover.py](https://raw.githubusercontent.com/digitalinteraction/cwa-recover/main/cwa-recover.py) as a file on your computer named `cwa-recover.py`, in the same directory as the previous file.

4. Open a terminal / command-line in the same folder as your downloaded files.  For example:
    * **Windows:** Press <kbd>Windows</kbd>+<kbd>R</kbd>, type: `cmd /k "cd Downloads"` and press <kbd>Enter</kbd>.
    * **macOS:** Open *Terminal*, type: `cd ~/Downloads` and press <kbd>Enter</kbd>.


## Step 3: Create a disk image from the device

If the data is still on the device: follow these steps to create an *image* file from the device -- this should be done even if you have previously copied off the file, as that data could be incomplete.  If the data was cleared from the device, you can skip this step.

* **Windows/Mac:**  You can use the `cwa-dump.py` script (downloaded above) to read the drive to create a disk image.

    1. Make sure you have a single AX device attached.

    2. Run the *cwa-dump* script: `python cwa-dump.py` 

    3. Wait for the script to complete -- this could take a long time

    The script will create a disk image file `cwa-dump.img` from the single attached AX device.

* **Windows (alternative):** You could use [imageUSB](https://www.osforensics.com/tools/write-usb-images.html) tool to *Create image from USB drive*.

* **macOS (alternative):** Ensure the AX device is attached.  Open the *Terminal*.  List the connected drives with: `diskutil list`.  Use the appropriate device name instead of the `$DISK` placeholder while running the following commands.  Unmount the drive: `diskutil unmountDisk /dev/$DISK` -- now create the drive image (this will take a long time with no progress shown): `sudo dd if=/dev/$DISK of=cwa-dump.img bs=512`

* **Other OS:** You can use the `dd` command to create a disk image.


## Step 4: Recover a `.cwa` file

1. Run the *cwa-recover* script, either for the disk image (`cwa-dump.img`):

    ```bash
    python cwa-recover.py
    ````
      
    ...or, for a possibly-corrupted `.cwa` file, type the line above, plus a space, then the full path name and surround with double quotes into the command prompt (on Windows, you can drag-and-drop your `.cwa` file into the command prompt window to write the full name).  The full command should be something like this (where `CWA-DATA.CWA` is your filename):

    ```bash
    python cwa-recover.py "CWA-DATA.CWA"
    ```

2. The script will attempt reconstruction and write a file: `cwa-recover.cwa`

3. Inspect the `cwa-recover.cwa` file (e.g. setting the Working Directory in *OmGui* software) to gauge how successful the process was.

If you have both a disk image and a downloaded file, you can repeat this process for both files and compare the outputs, but you must rename the `cwa-recover.cwa` file between each attempt, so that it is not overwritten.

<!-- 
There is a possibility that in some circumstances that being able to read the underlying physical NAND block memory could increase the data recovered, as this would include NAND blocks not used by the logical drive -- however, this is not an interface provided by the current device firmware, and would complicate the recovery, e.g. for overwritten blocks 

Read sectors from a device -- for any header or data sectors found: for each session id, create a map of sequence id to dump file offset (should sort by timestamp as the sequence id can be reset).  If more than one session id is found, the user must choose which to restore.  If no header was found for a specific session id, then a dummy one can be created (but the device id should be specified).  It may be necessary to re-base the sequence id so that it starts at 0).
-->


## Step 5: Configure and test the device for reuse

These steps for when the original device, that was a source of the corrupt data, has not yet been cleared and tested.

Once the data is recovered, you can clear the data from the device so that it can be used to make a new recording:
* Use [OmGui](https://github.com/digitalinteraction/openmovement/wiki/AX3-GUI) software, select the device and press *Clear*.
* If there is any problem with the previous step, see the [Troubleshooting Guide](https://github.com/digitalinteraction/openmovement/blob/master/Docs/ax3/ax3-troubleshooting.md)
* If none of the troubleshooting steps work, you can try [resetting the device](https://github.com/digitalinteraction/openmovement/blob/master/Docs/ax3/ax3-troubleshooting.md#resetting-the-device).

To verify the performance of the device, it is strongly recommended that you make a test recording (e.g. a static device) using the same parameters as you would like to use in the future (i.e. initial charge level, sensor configuration, time delay, recording duration).  This test recording should be indicative of future device performance.  
