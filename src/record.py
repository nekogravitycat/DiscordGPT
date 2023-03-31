import os
import json
import shutil
from src import config
from src.log import log


class User:
	def __init__(self, user_id: int):
		self.user_id: int = user_id
		self.model: str = "gpt-3.5-turbo"
		self.credits: float = 0
		self.load_data()

	def load_data(self):
		try:
			if not os.path.exists(f"data/users/{str(self.user_id)}.json"):
				self.credits = config.free_credits
				self.save_data()

			with open(f"data/users/{str(self.user_id)}.json", "r") as f:
				info: dict = json.load(f)
				self.model = info.get("model", self.model)
				self.credits = info.get("credits", self.credits)
		except Exception as e:
			log("record.User.load_data() error")
			log(repr(e))

	def save_data(self):
		try:
			with open(f"data/users/{str(self.user_id)}.json", "w") as f:
				info: dict = {
					"model": self.model,
					"credits": self.credits
				}
				json.dump(info, f, indent="\t")
		except Exception as e:
			log("record.User.save_data() error")
			log(repr(e))


def user_exists(user_id: int):
	return os.path.exists(f"data/users/{str(user_id)}.json")


dprivileged: str = "default_config/dprivileged.json"
privileged: str = "config/privileged.json"


def is_privileged(roles: list):
	try:
		if not os.path.exists(privileged):
			shutil.copy(dprivileged, privileged)
		with open(privileged, "r") as f:
			return set(roles).intersection(json.load(f)["roles"])  # true if any role the user has matches any privileged role
	except Exception as e:
		log("record.is_privileged() error")
		log(repr(e))
