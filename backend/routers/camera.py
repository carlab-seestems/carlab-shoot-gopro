import datetime
from time import sleep
from fastapi import APIRouter, HTTPException
import requests
import os
from backend import schemas
from backend.config import LOCAL_STORAGE_PATH, SFTP_HOSTNAME, SFTP_PASSWORD, SFTP_PORT, SFTP_USERNAME

from backend.utils import CameraBusyException, check_camera_ready, download_and_save_file, get_ip_address, send_command, send_modify_setting
import paramiko

router = APIRouter()


@router.get("/start-recording/")
def start_recording(serial_number: str):
    ip = get_ip_address(serial_number)
    return send_command(ip, f"http://{ip}/gopro/camera/shutter/start")


@router.get("/stop-recording/", response_model=schemas.FileInfo)
def stop_recording(serial_number: str):
    ip = get_ip_address(serial_number)

    # Stop recording command
    try:
        check_camera_ready(ip)

        raise HTTPException(status_code=400, detail='Camera is not recording')
    except CameraBusyException:
        send_command(
            ip, f"http://{ip}/gopro/camera/shutter/stop", verify_busy=False)
        pass

    except:
        raise

    # Get the media list
    while True:
        try:
            media_list = send_command(ip, f"http://{ip}/gopro/media/list")
        except CameraBusyException:
            sleep(1)
            continue
        except:
            raise
        break

    # Get the media file with the latest "cre" timestamp
    latest_media = max(media_list['media'][0]['fs'],
                       key=lambda x: int(x['cre']))

    # Get the directory and name of the latest media file
    directory_name = media_list['media'][0]['d']
    latest_media_name = latest_media['n']

    # Define the URL and local save path
    media_url = f"http://{ip}/videos/DCIM/{directory_name}/{latest_media_name}"

    # Download and save the file
    file_info = download_and_save_file(serial_number, media_url)

    send_command(
        ip, f"http://{ip}/gopro/media/delete/file?path={directory_name}/{latest_media_name}")

    return file_info


@router.get("/activate-wired-usb/")
def activate_wired_usb_control(serial_number: str):
    ip = get_ip_address(serial_number)
    return send_command(ip, f"http://{ip}/gopro/camera/control/wired_usb?p=1")


@router.get("/list-local-files/", response_model=list[schemas.FileInfo])
def list_local_files():
    file_list = []
    for filename in os.listdir(LOCAL_STORAGE_PATH):
        file_path = os.path.join(LOCAL_STORAGE_PATH, filename)
        absolute_file_path = os.path.abspath(file_path)

        if os.path.isfile(file_path):
            # Assuming serial number is part of the filename, you can split it
            try:
                serial_number, _ = filename.split("_", 1)
            except ValueError:
                continue
            file_info = schemas.FileInfo(
                path=absolute_file_path,
                size=os.path.getsize(file_path),
                creation_time=datetime.datetime.utcfromtimestamp(
                    os.path.getctime(file_path)).timestamp(),
                modification_time=datetime.datetime.utcfromtimestamp(
                    os.path.getmtime(file_path)).timestamp(),
                camera_serial_number=serial_number
            )
            file_list.append(file_info)
    return file_list


@router.get("/list-camera-files/")
def list_camera_files(serial_number: str):
    ip = get_ip_address(serial_number)
    media_list = send_command(ip, f"http://{ip}/gopro/media/list")

    return media_list


@router.get("/delete-camera-file/")
def delete_camera_files(serial_number: str, file_path: str):
    ip = get_ip_address(serial_number)
    media_list = send_command(
        ip, f"http://{ip}/gopro/media/delete/file?path={file_path}")

    return media_list


@router.get("/modify-settings/")
def modify_setting(serial_number: str, setting: int, option: int):
    ip = get_ip_address(serial_number)
    response = send_modify_setting(
        ip, f"http://{ip}/gopro/camera/setting?setting={setting}&option={option}")

    return response


@router.post("/upload-to-sftp/")
def upload_to_sftp(file_path: str, remote_path: str):

    try:
        transport = paramiko.Transport((SFTP_HOSTNAME, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = transport.open_sftp()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        sftp.put(file_path, remote_path)
    except Exception as e:
        sftp.close()
        transport.close()
        raise HTTPException(status_code=500, detail=str(e))

    sftp.close()
    transport.close()

    return {"message": "File uploaded successfully"}
