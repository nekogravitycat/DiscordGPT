import os
import shutil
import json
from src.log import log

# default values
available_servers: list[str] = []
max_prompt_token: int = 650
max_sys_prompt_token: int = 500
max_history_len: int = 12
max_history_age: int = 15  # in minutes
max_history_token: int = 1500
api_timeout: int = 60  # in seconds
default_sys_prompt: str = "You have a great sense of humor and are an independent thinker who likes to chat."


def load_config():
	try:
		if not os.path.exists("config.json"):
			shutil.copy("config_default.json", "config.json")

		with open("config.json", "r") as f:
			config: dict = json.load(f)
			global available_servers
			available_servers = config.get("available_servers")
			global max_prompt_token
			max_prompt_token = config.get("max_prompt_token")
			global max_sys_prompt_token
			max_sys_prompt_token = config.get("max_sys_prompt_token")
			global max_history_len
			max_history_len = config.get("max_history_len")
			global max_history_age
			max_history_age = config.get("max_history_age")
			global max_history_token
			max_history_token = config.get("max_history_token")
			global api_timeout
			api_timeout = config.get("api_timeout")
			global default_sys_prompt
			default_sys_prompt = config.get("default_sys_prompt")

	except IOError:
		log("IO error when loading config.json")
		log("not able to open or create a config file")

	except Exception as e:
		log("unknown error when loading config.json")
		log(repr(e))


def save_config():
	try:
		if not os.path.exists("config.json"):
			shutil.copy("config_default.json", "config.json")

		config: dict = {
			"available_servers": available_servers,
			"max_prompt_token": max_prompt_token,
			"max_sys_prompt_token": max_sys_prompt_token,
			"max_history_len": max_history_len,
			"max_history_age": max_history_age,
			"max_history_token": max_history_token,
			"api_timeout": api_timeout,
			"default_sys_prompt": default_sys_prompt
		}

		with open("config.json", "w") as f:
			json.dump(config, f, indent="\t")

	except IOError:
		log("IO error when saving config.json")
		log("not able to save config file")

	except Exception as e:
		log("unknown error when saving config.json")
		log(repr(e))
