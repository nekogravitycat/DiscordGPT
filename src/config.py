import os
import shutil
import json
from src.log import log

# default values
admin_id: int = 0
admin_servers: list[int] = []
available_servers: list[int] = []
max_prompt_token: int = 650
max_sys_prompt_token: int = 500
max_generated_token: int = 1500
max_history_len: int = 12
max_history_age: int = 15  # in minutes
max_history_token: int = 1500
api_timeout: int = 60  # in seconds
free_credits: float = 0.05  # in USD
fee_rate: float = 0.1  # 0.1 for additional 10%
default_sys_prompt: str = "You have a great sense of humor and are an independent thinker who likes to chat."

dconfig_file: str = "default_config/dconfig.json"
config_file: str = "config/config.json"


def load_config():
	try:
		if not os.path.exists(config_file):
			shutil.copy(dconfig_file, config_file)

		with open(config_file, "r") as f:
			config: dict = json.load(f)
			global admin_id
			admin_id = config.get("admin_id", admin_id)
			global admin_servers
			admin_servers = config.get("admin_servers", admin_servers)
			global available_servers
			available_servers = config.get("available_servers", available_servers)
			global max_prompt_token
			max_prompt_token = config.get("max_prompt_token", max_prompt_token)
			global max_sys_prompt_token
			max_sys_prompt_token = config.get("max_sys_prompt_token", max_sys_prompt_token)
			global max_generated_token
			max_generated_token = config.get("max_generated_token", max_generated_token)
			global max_history_len
			max_history_len = config.get("max_history_len", max_history_len)
			global max_history_age
			max_history_age = config.get("max_history_age", max_history_age)
			global max_history_token
			max_history_token = config.get("max_history_token", max_history_token)
			global api_timeout
			api_timeout = config.get("api_timeout", api_timeout)
			global free_credits
			free_credits = config.get("free_credits", free_credits)
			global fee_rate
			fee_rate = config.get("fee_rate", fee_rate)
			global default_sys_prompt
			default_sys_prompt = config.get("default_sys_prompt", default_sys_prompt)

	except IOError:
		log("IO error when loading config.json")
		log("not able to open or create a config file")

	except Exception as e:
		log("unknown error when loading config.json")
		log(repr(e))
