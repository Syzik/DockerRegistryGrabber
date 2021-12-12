#!/usr/bin/env python3

import requests
import argparse
import re
import sys
import os
from base64 import b64encode
import urllib3
from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "OK": "bright_green",
    "NOK": "red3"
})

def manageArgs():
    parser = argparse.ArgumentParser()
        # Positionnal args
    parser.add_argument("url", help="URL")
        # Optionnal args
    parser.add_argument("-p", dest='port', metavar='port', type=int, default=5000, help="port to use (default : 5000)")
        ## Authentification
    auth = parser.add_argument_group("Authentication")
    auth.add_argument('-U', dest='username', type=str, default="", help='Username')
    auth.add_argument('-P', dest='password', type=str, default="", help='Password')
        ### Args Action en opposition
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--dump", metavar="DOCKERNAME", dest='dump', type=str,  help="DockerName")
    action.add_argument("--list", dest='list', action="store_true")
    action.add_argument("--dump_all",dest='dump_all',action="store_true")
    args = parser.parse_args()
    return args

def printList(dockerlist):
    for element in dockerlist:
        if element:
            console.print(f"[+] {element}", style="OK")
        else:
            console.print(f"[-] No Docker found", style="NOK")

def tryReq(url, username=None,password=None):
    try:
        if username and password:
            r = requests.get(url,verify=False, auth=(username,password))
            r.raise_for_status()
        else:
            r = requests.get(url)
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

def downloadSha(url, port, docker, sha256, username=None, password=None):
    createDir(docker)
    directory = f"./{docker}/"
    for sha in sha256:
        filenamesha = f"{sha}.tar.gz"
        geturl = f"{url}:{str(port)}/v2/{docker}/blobs/sha256:{sha}"
        r = tryReq(geturl,username,password) 
        if r.status_code == 200:
            console.print(f"    [+] Downloading : {sha}", style="OK")
            with open(directory+filenamesha, 'wb') as out:
                for bits in r.iter_content():
                    out.write(bits)

def getBlob(docker, url, port, username=None, password=None):
    url = f"{url}:{str(port)}/v2/{docker}/manifests/latest"
    r = tryReq(url,username,password) 
    blobSum = []
    if r.status_code == 200:
        regex = re.compile('blobSum')
        for aa in r.text.splitlines():
            match = regex.search(aa)
            if match:
                blobSum.append(aa)
        if not blobSum :
            console.print(f"[-] No blobSum found", style="NOK")
            sys.exit(1)
        else :
            sha256 = []
            cpt = 1
            for sha in blobSum:
                console.print(f"[+] BlobSum found {cpt}", end='\r', style="OK")
                cpt += 1
                a = re.split(':|,',sha)
                sha256.append(a[2].strip("\""))
            print()
            return sha256

def enumList(url, port, username=None, password=None,checklist=None):
    url = f"{url}:{str(port)}/v2/_catalog"
    try :
        r = tryReq(url,username,password) 
        if r.status_code == 200:
            catalog2 = re.split(':|,|\n ',r.text)
            catalog3 = []
            for docker in catalog2:
                dockername = docker.strip("[\'\"\n]}{")
                catalog3.append(dockername)
        printList(catalog3[1:])
        return catalog3
    except:
        exit()

def dump(args):
    sha256 = getBlob(args.dump, args.url, args.port, args.username, args.password)
    console.print(f"[+] Dumping {args.dump}", style="OK")
    downloadSha(args.url, args.port, args.dump, sha256, args.username, args.password)

def dumpAll(args):
    dockerlist = enumList(args.url, args.port, args.username,args.password)
    for docker in dockerlist[1:]:
        sha256 = getBlob(docker, args.url, args.port, args.username,args.password)
        console.print(f"[+] Dumping {docker}", style="OK")
        downloadSha(args.url, args.port,docker,sha256,args.username,args.password)

def options():
    args = manageArgs()
    if args.list:
        enumList(args.url, args.port,args.username,args.password)
    elif args.dump_all:
        dumpAll(args)
    elif args.dump:
        dump(args)

if __name__ == '__main__':
    print(f"[+]======================================================[+]")
    print(f"[|]    Docker Registry Grabber v1       @SyzikSecu       [|]")
    print(f"[+]======================================================[+]")
    print()
    urllib3.disable_warnings()
    console = Console(theme=custom_theme)
    options()
