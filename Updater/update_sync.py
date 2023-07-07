import json
import os
from datetime import datetime

import requests
import sys


def check_and_return(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            releases = response.json()
            return releases
        elif response.status_code == 403:
            print(
                "Rate limit exceeded. Please try again later or provide an access token for authentication.")
            return None
        else:
            print(f"Error occurred during request: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during request: {e}")
        return None


def get_releases(repo_owner, repo_name):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    return check_and_return(url)


def get_release_files(release):
    release_files_url = release['assets_url']
    release_body = release['body']
    return check_and_return(release_files_url),release_body


def generate_release_dict(release_files, release_name, mode_type, device_name, release_desc):
    if release_files is None:
        return

    release_infos = []
    for file_info in release_files:
        if mode_type == "kernel":
            release_infos.append(generate_kernel_release_dict(file_info, release_name, device_name, release_desc))
        elif mode_type == "system":
            release_infos.append(generate_system_release_dict(file_info, mode_type))
    return release_infos


def generate_kernel_release_dict(file_info, release_name, device_name: str, release_desc):
    name = str(file_info["name"]).replace(".zip", "").upper()
    # filter device
    if device_name.lower() not in name.lower():
        return None
    tag = "KernelSU" if "KERNELSU" in name else "Original"
    return {
        "datetime": datetime.strptime(file_info["updated_at"], '%Y-%m-%dT%H:%M:%SZ').timestamp(),
        "filename": name,
        "id": file_info["id"],
        "tag": tag,
        "size": file_info["size"],
        "url": file_info['browser_download_url'],
        "version": release_name,
        "desc": release_desc
    }


# TODO
def generate_system_release_dict(file_info, release_name):
    return {
        "datetime": datetime.strptime(file_info["updated_at"], '%Y-%m-%dT%H:%M:%SZ').timestamp(),
        "filename": file_info["name"],
        "id": file_info["id"],
        "tag": "Tong",
        "size": file_info["size"],
        "url": file_info['browser_download_url'],
        "version": release_name
    }


def get_repo_release_info(repo_owner, repo_name, mode_type, device_name):
    releases = get_releases(repo_owner, repo_name)

    download_list = []

    if releases is not None:
        for release in releases:
            release_name = release['name']
            release_files, release_desc = get_release_files(release)
            download_list.extend(generate_release_dict(
                release_files, release_name, mode_type, device_name, release_desc))

    return download_list


def generate_save_path(mode_type, device_name):
    root_dir = os.getcwd()
    combine_path = os.path.join(root_dir, device_name)
    os.makedirs(combine_path, exist_ok=True)  # mkdir -p
    combine_path = os.path.join(combine_path, mode_type + ".json")
    return combine_path

def generate(owner,repo,mode_type,device_name):
    save_path = generate_save_path(mode_type, device_name)
    download_list = get_repo_release_info(owner, repo, mode_type, device_name)
    with open(save_path, "w", encoding='utf-8') as f:
        json.dump(download_list, f, indent=2, sort_keys=True, ensure_ascii=False)

if __name__ == '__main__':
    # Opening JSON file 
    with open('sync.json',) as f:
        sync_list = json.load(f)
        for device,repo_list in sync_list.items():
            # For kernel
            if repo_list["kernel_repo"]:
                owner, repo = repo_list["kernel_repo"].split('/')
                generate(owner,repo,"kernel",device)
            # For system
            if repo_list["system_repo"]:
                owner, repo = repo_list["system_repo"].split('/')
                generate(owner,repo,"system",device)
