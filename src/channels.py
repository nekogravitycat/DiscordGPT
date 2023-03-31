import os
import json
from src.log import log

channels_file: str = "data/channels.json"

channels: dict[int, str] = {}


def load_data():
	try:
		if not os.path.exists(channels_file):
			save_data()
		with open(channels_file, "r") as f:
			global channels
			channels = json.load(f)
	except Exception as e:
		log("channels.load_data() error")
		log(repr(e))


def save_data():
	try:
		with open(channels_file, "w") as f:
			info: dict = channels
			json.dump(info, f, indent="\t")
	except Exception as e:
		log("channels.save_data() error")
		log(repr(e))


def add_channel(channel_id: int, sys_message: str):
	load_data()
	channels[channel_id] = sys_message
	save_data()


def del_channel(channel_id: int):
	load_data()
	channels.pop(channel_id)
	save_data()


def is_on_channel(channel_id: int):
	load_data()
	return channel_id in channels
