<h1 align="center">DockerRegistryGrabber</h1>
<p align="center">
    A python tool to easly enum and dump images on a Docker Registry.
</p>
<p align="center">
<img  alt="X" src="https://img.shields.io/twitter/follow/SyzikSecu?label=SyzikSecu&style=social">
<img alt="Static Badge" src="https://img.shields.io/badge/python-3.7+-blue.svg">
</p>

---
### Install 
```
git clone git@github.com:Syzik/DockerRegistryGrabber.git
cd DockerRegistryGrabber
python -m pip install -r requirements.txt
```

---
### Usage 
```
python drg.py -h                                                                      

usage: drg.py [-h] [-p port] [-U USERNAME] [-P PASSWORD] [--dump DOCKERNAME | --list | --dump_all] url

positional arguments:
  url                URL

options:
  -h, --help         show this help message and exit
  -p port            port to use (default : 5000)
  --dump DOCKERNAME  DockerName
  --list
  --dump_all

Authentication:
  -U USERNAME        Username
  -P PASSWORD        Password
```

### Without authentification 

#### Listing available images  
```
python drg.py http://127.0.0.1 --list
```
![](./screenshot/list.png)

#### Dump an image
```
python drg.py http://127.0.0.1 --dump my-ubuntu
``` 
![](./screenshot/dump1.png)

#### Dump images 
```
python drg.py http://127.0.0.1 --dump_all
```
![](./screenshot/dump_all.png)

---

### With Basic Authentification

#### Listing available images
```
python drg.py http://127.0.0.1 -U 'testuser' -P 'testpassword' --list
```
![](screenshot/authlist.png)

#### Dump a specific image 
```
python drg.py http://127.0.0.1 -U 'testuser' -P 'testpassword' --dump my-ubuntu
```
![](screenshot/authdump1.png)

#### Dump every images 
```
python drg.py http://127.0.0.1 -U 'testuser' -P 'testpassword' --dump_all
```
![](screenshot/authdump_all.png)

