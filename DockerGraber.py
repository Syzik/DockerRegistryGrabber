#!/usr/bin/env python3

# Imports
import requests
import argparse
import re
import sys
import os
import urllib3
from rich.console import Console
from rich.theme import Theme
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
req = requests.Session()

http_proxy = ""
os.environ["HTTP_PROXY"] = http_proxy
os.environ["HTTPS_PROXY"] = http_proxy


custom_theme = Theme({"OK": "bright_green", "NOK": "red3"})


def print_list(docker_list):
    for element in docker_list:
        if element:
            console.print(f"[+] {element}", style="OK")
        else:
            console.print(f"[-] No Docker found", style="NOK")


def send_request(url):
    try:
        headers = {}
        if args.token:
            headers = {"Authorization": "Bearer " + args.token}
        if args.username and args.password:
            r = req.get(url, verify=False, auth=(args.username, args.password), headers=headers)
            r.raise_for_status()
        else:
            r = req.get(url, verify=False, headers=headers)
            r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        console.print(f"Http Error: {errh}", style="NOK")
        sys.exit(1)
    except requests.exceptions.ConnectionError as errc:
        console.print(f"Error Connecting : {errc}", style="NOK")
        sys.exit(1)
    except requests.exceptions.Timeout as errt:
        console.print(f"Timeout Error : {errt}", style="NOK")
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        console.print(f"Dunno what happend but something fucked up {err}", style="NOK")
        sys.exit(1)
    return r


def create_directory(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def download_hash(docker, sha256):
    create_directory(docker)
    directory = f"./{docker}/"
    for sha in sha256:
        filenamesha = f"{sha}.tar.gz"
        r = send_request(f"{args.url}:{str(args.port)}/v2/{docker}/blobs/sha256:{sha}")
        if r.status_code == 200:
            console.print(f"    [+] Downloading : {sha}", style="OK")
            with open(directory + filenamesha, "wb") as out:
                for bits in r.iter_content():
                    out.write(bits)


def get_blob(docker):
    rr = send_request(f"{args.url}:{str(args.port)}/v2/{docker}/tags/list")
    data = rr.json()
    image = data["tags"][0]
    r = send_request(f"{args.url}:{str(args.port)}/v2/{docker}/manifests/" + image + "")
    blobSum = []
    if r.status_code == 200:
        regex = re.compile("blobSum")
        for aa in r.text.splitlines():
            match = regex.search(aa)
            if match:
                blobSum.append(aa)
        if not blobSum:
            console.print(f"[-] No blobSum found", style="NOK")
            sys.exit(1)
        else:
            sha256 = []
            cpt = 1
            for sha in blobSum:
                console.print(f"[+] BlobSum found {cpt}", end="\r", style="OK")
                cpt += 1
                a = re.split(":|,", sha)
                sha256.append(a[2].strip('"'))
            print()
            return sha256


def enumerate_list():
    try:
        r = send_request( f"{args.url}:{str(args.port)}/v2/_catalog")
        if r.status_code == 200:
            catalog2 = re.split(":|,|\n ", r.text)
            catalog3 = []
            for docker in catalog2:
                dockername = docker.strip("['\"\n]}{")
                catalog3.append(dockername)
        print_list(catalog3[1:])
        return catalog3
    except:
        exit()


def dump(docker):
    sha256 = get_blob(docker)
    console.print(f"[+] Dumping {args.dump}", style="OK")
    download_hash(docker, sha256)


def dump_all():
    dockerlist = enumerate_list()
    for docker in dockerlist[1:]:
        sha256 = get_blob(docker)
        console.print(f"[+] Dumping {docker}", style="OK")
        download_hash(docker, sha256)


def get_args():
    parser = argparse.ArgumentParser()
    # Positional args
    parser.add_argument("url", help="URL")
    # Optional args
    parser.add_argument(
        "-p",
        dest="port",
        metavar="port",
        type=int,
        default=5000,
        help="port to use (default : 5000)",
    )
    ## Authentication
    auth = parser.add_argument_group("Authentication")
    auth.add_argument("-U", dest="username", type=str, default="", help="Username")
    auth.add_argument("-P", dest="password", type=str, default="", help="Password")
    auth.add_argument("-T", dest="token", type=str, default="", help="Token")
    ### Args Action en opposition
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--dump", metavar="DOCKERNAME", dest="dump", type=str, help="DockerName"
    )
    action.add_argument("--list", dest="list", action="store_true")
    action.add_argument("--dump_all", dest="dump_all", action="store_true")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    print(f"[+]======================================================[+]")
    print(f"[|]    Docker Registry Grabber v1       @SyzikSecu       [|]")
    print(f"[+]======================================================[+]")
    print()
    
    urllib3.disable_warnings()
    
    console = Console(theme=custom_theme)

    args = get_args()
    
    if args.list:
        enumerate_list()
    elif args.dump_all:
        dump_all()
    elif args.dump:
        dump(args.dump)
