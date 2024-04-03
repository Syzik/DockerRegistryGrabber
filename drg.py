#!/usr/bin/env python3

import requests
import argparse
import re
import sys
import os
import urllib3
from rich.console import Console
from rich.theme import Theme
from argparse import RawTextHelpFormatter
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
req = requests.Session()

http_proxy = ""
os.environ["HTTP_PROXY"] = http_proxy
os.environ["HTTPS_PROXY"] = http_proxy


custom_theme = Theme({
    "OK": "bright_green",
    "MOK":"magenta",
    "NOK": "red3"
})

def printList(dockerlist):
    for element in dockerlist:
        if element:
            console.print(f"[+] {element}", style="OK")
        else:
            console.print("[-] No Docker found", style="NOK")

def checkUnauthorized(r, r2=None):
    if r.status_code == 401 and r.headers.get("Www-Authenticate"):
        console.print(f"[-] Http Error: 401 Client Error: Unauthorized for url: {r2}", style="NOK")
        console.print(f"    [+] Www-Authenticate Header Found : {r.headers.get('Www-Authenticate')}", style="OK")
        realm = re.search('realm="([^"]+)"', r.headers.get("Www-Authenticate")).group(1)
        service=re.search('service="([^"]+)"', r.headers.get("Www-Authenticate")).group(1)
        scope=re.search('scope="([^"]+)"', r.headers.get("Www-Authenticate")).group(1)
        console.print(f"    [~] Trying to authenticate on Realm : {realm}", style="MOK")
        url_auth = f"{realm}?service={service}&scope={scope}"
        auth = req.get(url_auth, verify=False)
        if auth.status_code == 200:
            console.print(f"    [+] Authentication success", style="OK")
            jwt_list = re.findall(r'"access_token":"([^"]+)"', auth.text)
            args = manageArgs()
            for i in jwt_list:
                args.header = i
                if args.list:
                    enumList(args.url, args.port, args.username, args.password, args.header)
                elif args.dump_all:
                    dumpAll(args)
                elif args.dump:
                    dump(args)
        else:
            console.print(f"    [-] Authentication failed", style="NOK")
        sys.exit(1)

def tryReq(url, username=None, password=None, header=None):
    try:
        if header and username and password:
            auth = {"Authorization": "Bearer " + header}
            r = req.get(url, verify=False, auth=(username, password), headers=auth)
            checkUnauthorized(r, url)
            r.raise_for_status()
        elif username and password:
            r = req.get(url, verify=False, auth=(username, password))
            checkUnauthorized(r, url)
            r.raise_for_status()
        elif header:
            auth = {"Authorization": "Bearer " + header}
            r = req.get(url, verify=False, headers=auth)
            checkUnauthorized(r, url)
            r.raise_for_status()
        else:
            r = req.get(url, verify=False)
            checkUnauthorized(r, url)
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

def createDir(directoryName):
    if not os.path.exists(directoryName):
        os.makedirs(directoryName)

def downloadSha(url, port, docker, sha256, username=None, password=None, header=None):
    createDir(docker)
    directory = f"./{docker}/"
    for sha in sha256:
        filenamesha = f"{sha}.tar.gz"
        geturl = f"{url}:{port!s}/v2/{docker}/blobs/sha256:{sha}"
        r = tryReq(geturl, username, password, header) 
        if r.status_code == 200:
            console.print(f"    [+] Downloading : {sha}", style="OK")
            with open(directory + filenamesha, "wb") as out:
                for bits in r.iter_content():
                    out.write(bits)

def getBlob(docker, url, port, username=None, password=None, header=None):
    tags = f"{url}:{port!s}/v2/{docker}/tags/list"
    rr = tryReq(tags, username, password, header)
    data = rr.json()
    image = data["tags"][0]
    url = f"{url}:{port!s}/v2/{docker}/manifests/" + image + ""
    r = tryReq(url, username, password, header) 
    blobSum = []
    if r.status_code == 200:
        regex = re.compile("blobSum")
        for aa in r.text.splitlines():
            match = regex.search(aa)
            if match:
                blobSum.append(aa)
        if not blobSum:
            console.print("[-] No blobSum found", style="NOK")
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

def enumList(url, port, username=None, password=None, header=None):
    url = f"{url}:{port!s}/v2/_catalog"
    try:
        r = tryReq(url, username, password, header) 
        if r.status_code == 200:
            catalog2 = re.split(":|,|\n ", r.text)
            catalog3 = []
            for docker in catalog2:
                dockername = docker.strip("[\'\"\n]}{")
                catalog3.append(dockername)
        printList(catalog3[1:])
        return catalog3
    except Exception as e:
        sys.exit(e)

def dump(args):
    sha256 = getBlob(args.dump, args.url, args.port, args.username, args.password, args.header)
    console.print(f"[+] Dumping {args.dump}", style="OK")
    downloadSha(args.url, args.port, args.dump, sha256, args.username, args.password, args.header)

def dumpAll(args):
    dockerlist = enumList(args.url, args.port, args.username, args.password, args.header)
    for docker in dockerlist[1:]:
        sha256 = getBlob(docker, args.url, args.port, args.username, args.password, args.header)
        console.print(f"[+] Dumping {docker}", style="OK")
        downloadSha(args.url, args.port, docker, sha256, args.username, args.password, args.header)

def options():
    args = manageArgs()
    if args.list:
        enumList(args.url, args.port, args.username, args.password, args.header)
    elif args.dump_all:
        dumpAll(args)
    elif args.dump:
        dump(args)

def manageArgs():
    parser = argparse.ArgumentParser(description=r"""     ____   ____    ____
    |  _ \ |  _ \  / ___|
    | | | || |_) || |  _ 
    | |_| ||  _ < | |_| |
    |____/ |_| \_\ \____|
     Docker Registry grabber tool v2.1
     by @SyzikSecu""",
     epilog=r"""
Example commands:
  python drg.py http://127.0.0.1 --list
  python drg.py http://127.0.0.1 --dump my-ubuntu
  python drg.py http://127.0.0.1 --dump_all
  python drg.py https://127.0.0.1 -U 'testuser' -P 'testpassword' --list
  python drg.py https://127.0.0.1 -U 'testuser' -P 'testpassword' --dump my-ubuntu
  python drg.py https://127.0.0.1 -U 'testuser' -P 'testpassword' --dump_all
  python drg.py https://127.0.0.1 -A '<Auth BEARER TOKEN>' --list
  python drg.py https://127.0.0.1 -A '<Auth BEARER TOKEN>' --dump my-ubuntu
  python drg.py https://127.0.0.1 -A '<Auth BEARER TOKEN>' --dump_all
""", formatter_class=RawTextHelpFormatter)
    # parser.epilog
    # Positionnal args
    parser.add_argument("url", help="URL")
    # Optionnal args
    parser.add_argument("-p", dest="port", metavar="port", type=int, default=5000, help="port to use (default : 5000)")
    # Authentification
    auth = parser.add_argument_group("Authentication")
    auth.add_argument("-U", dest="username", type=str, default="", help="Username")
    auth.add_argument("-P", dest="password", type=str, default="", help="Password")
    auth.add_argument("-A", dest="header", metavar="header", type=str, default="", help="Authorization bearer token")
    # Args Action en opposition
    action_group = parser.add_argument_group("Actions")
    action = action_group.add_mutually_exclusive_group()
    action.add_argument("--list", dest="list", action="store_true")
    action.add_argument("--dump_all", dest="dump_all", action="store_true")
    action.add_argument("--dump", metavar="DOCKERNAME", dest="dump", type=str, help="DockerName")
    return parser.parse_args()

if __name__ == "__main__":
    urllib3.disable_warnings()
    console = Console(theme=custom_theme)
    options()
    
