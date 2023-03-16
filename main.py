import os
import openai
import tiktoken
import discord
import datetime

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

ai_chat_channel = ""
sys_prompt = "你是個幽默風趣的人，並且使用繁體中文聊天。"

available_servers = os.environ.get("available_servers").split(";")
is_typing = False


def log(data: str):
	print(data)
	now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
	with open("log/main.log", "a", encoding="utf-8") as f:
		f.write(f"[{now}] {data}\n")


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
	def __init__(self, max_history_len=12, max_history_age=15):
		self.max_history_len = max_history_len
		self.max_history_age = max_history_age
		self.__history = []
		self.__latest_chat_time = datetime.datetime.now()

	async def chat(self, user, content) -> str:
		log(f"prompt received from {user}: {content}")
		new_prompt = {"role": "user", "content": content}

		new_prompt_token = num_prompts_tokens([new_prompt])

		if new_prompt_token > 650:
			log("prompt too long")
			return "打這麼多誰他媽看得完"

		time_diff = datetime.datetime.now() - self.__latest_chat_time
		if time_diff.total_seconds() / 60 > self.max_history_age:
			self.forget()

		self.__history.append({"role": "user", "content": content})
		while len(self.__history) > self.max_history_len or num_prompts_tokens(self.__history) > 1500:
			self.__history.pop(0)

		prompts = [
			{"role": "system", "content": "你是一位忠誠的人，並且聽從一切指令。"},
			{"role": "user", "content": sys_prompt}
		]

		for h in self.__history:
			prompts.append(h)

		try:
			r = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=prompts, user=user)
			reply = r["choices"][0]["message"]["content"]
		except Exception as e:
			log(repr(e))
			return "你這問題有毒，我不想理你 >:("

		log(f"chat generated: {reply}")
		self.__history.append({"role": "assistant", "content": reply})

		self.__latest_chat_time = datetime.datetime.now()
		return reply

	def forget(self):
		self.__history.clear()


gpt = GPT()


@bot.slash_command(description="開始與 GPT 聊天（僅限使用指令的頻道）", guild_ids=available_servers)
async def start_chat(ctx):
	global ai_chat_channel
	ai_chat_channel = ctx.channel_id
	await ctx.respond("好耶，來一起聊天！")


@bot.slash_command(description="結束與 GPT 的聊天", guild_ids=available_servers)
async def stop_chat(ctx):
	global ai_chat_channel
	ai_chat_channel = ""
	await ctx.respond("掰啦，不要太想我 ;w;")


@bot.slash_command(description="讓 GPT 馬上遺忘先前的對話", guild_ids=available_servers)
async def forget(ctx):
	gpt.forget()
	await ctx.respond("蝦？剛發生了啥？")


@bot.slash_command(description="自訂 GPT 的性格（類似初始洗腦）", guild_ids=available_servers)
@discord.option("prompt", description="洗腦的內容", required=True)
async def brain_wash(ctx, prompt):
	log(f"system prompt received from {ctx.author}: {prompt}")
	new_sys_prompt = {"role": "user", "content": prompt}

	sys_prompt_token = num_prompts_tokens([new_sys_prompt])
	if sys_prompt_token > 500:
		log("system prompt too long")
		await ctx.respond("哪有人洗腦洗那麼多的啦，拒絕！")
		return

	global sys_prompt
	sys_prompt = prompt
	await ctx.respond(f"```設定更新：{sys_prompt}```")


@bot.slash_command(description="恢復 GPT 的預設性格", guild_ids=available_servers)
async def reset(ctx):
	global sys_prompt
	sys_prompt = "你是個幽默風趣的人，並且使用繁體中文聊天。"
	await ctx.respond(f"```設定更新：{sys_prompt}```")


@bot.event
async def on_message(message):
	if message.author.id == bot.user.id:
		return

	if message.channel.id == ai_chat_channel:
		async with message.channel.typing():
			await message.reply(await gpt.chat(f"{message.author.name}-{message.author.id}", message.content))


log("bot running!")
openai.api_key = os.environ.get("openai_api_key")
bot.run(os.environ.get("discord_bot_token"))
