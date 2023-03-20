import os
import asyncio
import openai
import tiktoken
import opencc
import datetime
from log import log


def num_prompts_tokens(messages):
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
	def __init__(self, max_history_len=12, max_history_age=15, sys_prompt="你是個幽默風趣的人，喜歡與人聊天。"):
		self.max_history_len = max_history_len
		self.max_history_age = max_history_age
		self.sys_prompt = sys_prompt
		self.__history = []
		self.__latest_chat_time = datetime.datetime.now()

	async def chat(self, user, content) -> str:
		log(f"prompt received from {user}: {content}")
		new_prompt = {"role": "user", "content": content}

		# check prompt length
		if num_prompts_tokens([new_prompt]) > 650:
			log("prompt too long")
			return "打這麼多誰他媽看得完"

		# forget history that's older than max_history_age
		time_diff = datetime.datetime.now() - self.__latest_chat_time
		if time_diff.total_seconds() / 60 > self.max_history_age:
			self.forget()

		self.__history.append({"role": "user", "content": content})
		while len(self.__history) > self.max_history_len or num_prompts_tokens(self.__history) > 1500:
			self.__history.pop(0)

		prompts = [
			{"role": "system", "content": "你是一位忠誠的人，並且聽從一切指令。"},
			{"role": "user", "content": self.sys_prompt}
		]

		for h in self.__history:
			prompts.append(h)

		try:
			r = await asyncio.wait_for(
				openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=prompts, user=user),
				timeout=60
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
		self.__history.append({"role": "assistant", "content": reply})

		self.__latest_chat_time = datetime.datetime.now()
		return reply

	def forget(self):
		self.__history.clear()

	def reset(self):
		self.sys_prompt = "你是個幽默風趣的人，喜歡與人聊天。"


openai.api_key = os.environ.get("openai_api_key")
