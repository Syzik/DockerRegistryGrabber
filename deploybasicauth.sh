mkdir auth
mkdir certs

openssl req -newkey rsa:2048 -nodes -keyout ./certs/domain.key -x509 -days 365 -out ./certs/domain.crt

docker run \
  --entrypoint htpasswd \
  httpd:2 -Bbn testuser testpassword > auth/htpasswd

docker run -d \
  -p 5000:5000 \
  --restart=unless-stopped\
  --name registry \
  -v "$(pwd)"/auth:/auth \
  -e "REGISTRY_AUTH=htpasswd" \
  -e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
  -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
  -v "$(pwd)"/certs:/certs \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
  registry

echo -n "testuser:testpassword"
docker login localhost:5000
docker pull ubuntu
docker image tag ubuntu localhost:5000/my-ubuntu
docker image tag ubuntu localhost:5000/my-ubuntu2
docker push localhost:5000/my-ubuntu
docker push localhost:5000/my-ubuntu2
