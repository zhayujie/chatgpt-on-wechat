IMG:=`cat Name`
MOUNT:=-v `pwd`/config.json:/app/config.json
PORT_MAP:=
DOTENV:=.env
CONTAINER_NAME:=sample-chatgpt-on-wechat

echo:
	echo $(IMG)

run_d:
	docker rm $(CONTAINER_NAME) || echo
	docker run -dt  --name $(CONTAINER_NAME) $(PORT_MAP) \
			--env-file=$(DOTENV) \
			$(MOUNT) $(IMG) 

run_i:
	docker rm $(CONTAINER_NAME) || echo
	docker run -it  --name $(CONTAINER_NAME) $(PORT_MAP) \
			--env-file=$(DOTENV) \
			$(MOUNT) $(IMG) 

stop:
	docker stop $(CONTAINER_NAME)

rm:     stop
	docker rm $(CONTAINER_NAME)
