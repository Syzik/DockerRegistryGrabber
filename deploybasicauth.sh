mkdir auth
mkdir certs

openssl req -newkey rsa:2048 -nodes -keyout ./certs/domain.key -x509 -days 365 -out ./certs/domain.crt

sudo docker run \
  --entrypoint htpasswd \
  httpd:2 -Bbn testuser testpassword > auth/htpasswd

sudo docker run -d \
  -p 5000:5000 \
  --restart=always \
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
sudo docker login 127.0.0.1:5000

sudo docker push 127.0.0.1:5000/my-ubuntu
