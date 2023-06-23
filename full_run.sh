docker build -t jupyter .;
docker kill $(docker ps -q);
docker run -d --privileged -e DISPLAY=:0 -v /tmp/.X11-unix:/tmp/.X11-unix --user="$(id --user):$(id --group)" --net=host -v $(pwd)/file_mount:/srv jupyter;
docker exec -itd $(sudo docker ps -qf "ancestor=jupyter") bash -c "cd /srv/frontend && flask run -p 3000";
docker exec -itd $(sudo docker ps -qf "ancestor=jupyter") bash -c "cd /srv/node_app && python3 clear_workflow_routes.py";
docker exec -itd $(sudo docker ps -qf "ancestor=jupyter") bash -c "cd /srv/node_app && python3 launcher_app.py";
echo Jupyter Address: http://127.0.0.1:8888/?token=2a39e2ee44b7f07a3e9613d2880ebb3941798a0b332b2658;
docker stop /myPostgresDb;
docker start /myPostgresDb;