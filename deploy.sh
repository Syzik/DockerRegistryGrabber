sudo docker run -d -p 5000:5000 --restart=unless-stopped --name registry2 registry:2
sudo docker pull ubuntu
sudo docker image tag ubuntu localhost:5000/my-ubuntu
sudo docker image tag ubuntu localhost:5000/my-ubuntu2
sudo docker push localhost:5000/my-ubuntu
sudo docker push localhost:5000/my-ubuntu2

