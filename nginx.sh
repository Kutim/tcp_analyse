docker rm -f nginx
docker run --name=nginx -p 80:80 -d nginx
