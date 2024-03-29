docker run -d -p 5000:5000 --restart=unless-stopped --name registry2 registry:2
docker pull ubuntu
docker image tag ubuntu localhost:5000/my-ubuntu
docker image tag ubuntu localhost:5000/my-ubuntu2
docker push localhost:5000/my-ubuntu
docker push localhost:5000/my-ubuntu2

