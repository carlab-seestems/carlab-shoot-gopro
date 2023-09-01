import os
import requests
from fastapi import HTTPException
import shutil

from backend import schemas
from backend.config import LOCAL_STORAGE_PATH


class CameraNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Camera not found")


class BatteryNotPresentException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Internal battery not present")


class BatteryLevelZeroException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Internal battery level is zero")


class SystemOverheatingException(HTTPException):
    def __init__(self):
        super().__init__(status_code=429, detail="System is overheating")


class CameraBusyException(HTTPException):
    def __init__(self):
        super().__init__(status_code=409, detail="Camera is busy")


class SDStatusException(HTTPException):
    def __init__(self, detail):
        super().__init__(status_code=400, detail=detail)


class InvalidSettingException(HTTPException):
    def __init__(self, detail):
        super().__init__(status_code=400, detail=detail)


def get_ip_address(serial_number):
    X = int(serial_number[-3])
    Y = int(serial_number[-2])
    Z = int(serial_number[-1])
    return f"172.2{X}.{1}{Y}{Z}.51:8080"


def check_camera_ready(ip):
    try:
        response = requests.get(f"http://{ip}/gopro/camera/state", timeout=3)
    except requests.exceptions.Timeout:
        raise CameraNotFoundException()

    camera_state = response.json()['status']

    # Check internal battery presence
    # if camera_state['1'] == 0:
    #     raise BatteryNotPresentException()

    # # Check internal battery level
    # if camera_state['2'] == 0:
    #     raise BatteryLevelZeroException()

    # Check if the system is overheating
    if camera_state['6'] == 1:
        raise SystemOverheatingException()

    # Check if the camera is busy
    if camera_state['8'] == 1:
        raise CameraBusyException()

    # Check SD card status
    sd_status = camera_state['33']
    if sd_status == -1:
        raise SDStatusException("SD Card status is unknown")
    elif sd_status == 1:
        raise HTTPException(status_code=507, detail="SD Card is full")
    elif sd_status == 2:
        raise SDStatusException("SD Card is removed")
    elif sd_status == 3:
        raise SDStatusException("SD Card format error")
    elif sd_status == 4:
        raise SDStatusException("SD Card is busy")
    elif sd_status == 8:
        raise SDStatusException("SD Card is swapped")


def send_command(ip, command_url, verify_busy=True):
    if verify_busy:
        check_camera_ready(ip)
    response = requests.get(command_url)
    return response.json()


def send_modify_setting(ip, setting_url):
    check_camera_ready(ip)

    response = requests.get(setting_url)
    response_json = response.json()
    if 'error' in response_json.keys():
        error = f"Invalid setting or option. Supported Options : {response_json['supported_options']}" if 'supported_options' in response_json.keys(
        ) else "Invalid setting or option."
        raise InvalidSettingException(detail=error)
    return response.json()


def download_and_save_file(serial_number, file_url, save_path):
    response = requests.get(file_url, stream=True)
    response.raise_for_status()

    # Including the serial number in the filename
    filename_with_serial = f"{serial_number}_{save_path}.mp4"
    full_save_path = os.path.join(LOCAL_STORAGE_PATH, filename_with_serial)

    with open(full_save_path, 'wb') as file:
        shutil.copyfileobj(response.raw, file)
    absolute_file_path = os.path.abspath(full_save_path)

    file_info = schemas.FileInfo(path=absolute_file_path,
                                 size=os.path.getsize(full_save_path),
                                 creation_time=os.path.getctime(
                                     full_save_path),
                                 modification_time=os.path.getmtime(
                                     full_save_path),
                                 camera_serial_number=serial_number)

    return file_info
