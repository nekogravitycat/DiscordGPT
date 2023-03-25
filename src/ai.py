import os
import asyncio
import openai
import tiktoken
import opencc
import datetime
from src.log import log
from src import config


def count_token(messages: list[dict]):
	try:
		encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
	except KeyError:
		encoding = tiktoken.get_encoding("cl100k_base")

	num_tokens = 0
	for message in messages:
		num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
		for key, value in message.items():
			num_tokens += len(encoding.encode(value))
			if key == "name":  # if there's a name, the role is omitted
				num_tokens += -1  # role is always required and always 1 token

	num_tokens += 2  # every reply is primed with <im_start>assistant
	return num_tokens


class GPT:
	def __init__(self):
		self.sys_prompt: str = config.default_sys_prompt
		self.history: list[dict] = []
		self.__latest_chat_time = datetime.datetime.now()

	async def chat(self, user: str, content: str) -> str:
		log(f"prompt received from {user}: {content}")
		new_prompt = {"role": "user", "content": content}

		# check prompt length
		if count_token([new_prompt]) > config.max_prompt_token:
			log("prompt too long")
			return "打這麼多誰他媽看得完？"

		# forget history that's older than max_history_age
		time_diff = datetime.datetime.now() - self.__latest_chat_time
		if time_diff.total_seconds() / 60 > config.max_history_age:
			self.history.clear()

		self.history.append({"role": "user", "content": content})
		while len(self.history) > config.max_history_len or count_token(self.history) > config.max_history_token:
			self.history.pop(0)

		prompts = [{"role": "system", "content": self.sys_prompt}]

		for h in self.history:
			prompts.append(h)

		try:
			r = await asyncio.wait_for(
				openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=prompts, user=user),
				timeout=config.api_timeout
			)
			reply = r["choices"][0]["message"]["content"]
			reply = opencc.OpenCC("s2twp").convert(reply)

		except asyncio.TimeoutError as e:
			log(f"asyncio.TimeoutError:\n{repr(e)}")
			return "```等待執行呼叫 API 時間過久，請再試一次。如果問題持續請通知管理員。（asyncio.TimeoutError）```"

		except openai.error.Timeout as e:
			log(f"openai.error.Timeout\n{repr(e)}")
			return "```等待 API 回復時間過久，請再試一次。如果問題持續請通知管理員。（openai.error.Timeout）```"

		except Exception as e:
			log(repr(e))
			return "```回答問題時出了點差錯，請再試一次。如果問題持續請通知管理員。```"

		log(f"chat generated: {reply}")
		self.history.append({"role": "assistant", "content": reply})

		self.__latest_chat_time = datetime.datetime.now()
		return reply


openai.api_key = os.environ.get("openai_api_key")
