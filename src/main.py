import os
import discord
from src.log import log
from src import ai
from src import config
from src import record
from src import channels

config.load_config()
bot: discord.Bot = discord.Bot(intents=discord.Intents.all())


class Chat:
	def __init__(self):
		self.gpt: ai.GPT = ai.GPT()
		self.__messages: list[discord.Message] = []

	async def add_message(self, message: discord.Message):
		self.__messages.append(message)
		if len(self.__messages) == 1:
			await self.__reply_next()

	async def __reply_next(self):
		if len(self.__messages) > 0:
			message = self.__messages[0]

			user = record.User(message.author.id)

			try:
				async with message.channel.typing():
					if user.model == "gpt-4" and not record.is_privileged([role.id for role in message.author.roles]):
						log(f"downgraded model to gpt-3.5-turbo for '{message.author.name}' because of missing privilege")
						user.model = "gpt-3.5-turbo"

					if user.credits <= 0 and not user.credits == -1:
						await message.reply("```您已到達使用上限，請聯繫管理員。```")

					else:
						result = await self.gpt.chat(f"{message.author.id}", message.content, user.model)
						user.credits -= result["usage"]
						reply = await message.reply(result["reply"])
						if user.model == "gpt-4":
							await reply.add_reaction("⭐")

				user.save_data()

			except Exception as e:
				log(f"error in main.Chat.__reply_next(): {repr(e)}")

			self.__messages.pop(0)
			await self.__reply_next()


help_message: str = ""
chats: dict[int, Chat] = {}
all_servers: list = config.available_servers + config.admin_servers


@bot.slash_command(name="start-chat", description="開始與 GPT 聊天（僅限使用指令的頻道）", guild_ids=all_servers)
async def start_chat(ctx: discord.ApplicationContext):
	if ctx.channel_id in chats:
		await ctx.respond("我已經在聊天室裡了，你一點都沒有在注意我 ( ˘･з･)")
		return

	chats[ctx.channel_id] = Chat()
	channels.add_channel(ctx.channel_id, chats.get(ctx.channel_id).gpt.sys_prompt)
	await ctx.respond("好耶，來一起聊天！ (ﾉ>ω<)ﾉ")


@bot.slash_command(name="stop-chat", description="結束與 GPT 的聊天", guild_ids=all_servers)
async def stop_chat(ctx: discord.ApplicationContext):
	if not chats.pop(ctx.channel_id, None):
		await ctx.respond("我本來就沒在這聊天啊 ( •́ _ •̀)？")
		return

	channels.del_channel(ctx.channel_id)
	await ctx.respond("掰啦⋯⋯不要太想我 (☍﹏⁰)")


@bot.slash_command(description="遺忘最後 N 個對答", guild_ids=all_servers)
@discord.option("num", description="要遺忘的對答數", required=True)
async def forget(ctx: discord.ApplicationContext, num: int):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```", ephemeral=True)
		return

	if num <= 0 or not isinstance(num, int):
		await ctx.respond(f"```請輸入大於 0 的整數```", ephemeral=True)
		return

	chat = chats.get(ctx.channel.id, None)

	history = chat.gpt.history
	chat.gpt.history = history[:len(history) - min(num, len(history)) * 2]

	if len(chat.gpt.history) == 0:
		await ctx.respond(f"```已遺忘所有對答```")

	else:
		await ctx.respond(f"```已遺忘最後 {num} 個對答```")


@bot.slash_command(name="forget-all", description="遺忘所有對話", guild_ids=all_servers)
async def forget_all(ctx: discord.ApplicationContext):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```", ephemeral=True)
		return

	chat = chats.get(ctx.channel.id)
	chat.gpt.history.clear()
	await ctx.respond("蝦？剛發生了啥？ Σ( ° △ °)")


@bot.slash_command(description="自訂 GPT 的性格（類似洗腦）", guild_ids=all_servers)
@discord.option("prompt", description="洗腦的內容", required=True)
async def brainwash(ctx: discord.ApplicationContext, prompt: str):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```", ephemeral=True)
		return

	if ai.count_token([{"role": "user", "content": prompt}]) > config.max_sys_prompt_token:
		log("system prompt too long")
		await ctx.respond("太多了太多了！是想把我洗成智障嗎？！拒絕！！ (╬ﾟдﾟ)凸", ephemeral=True)
		return

	chat = chats.get(ctx.channel.id, None)
	if chat is None:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```", ephemeral=True)		
		return
	
	chat.gpt.sys_prompt = prompt
	channels.add_channel(ctx.channel_id, chat.gpt.sys_prompt)
	await ctx.respond(f"```設定更新：{chat.gpt.sys_prompt}```")


@bot.slash_command(description="顯示目前的 GPT 機器人設定", guild_ids=all_servers)
async def status(ctx: discord.ApplicationContext):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```", ephemeral=True)
		return

	chat = chats.get(ctx.channel.id)
	await ctx.respond(f"```目前設定：{chat.gpt.sys_prompt}```")


@bot.slash_command(description="恢復 GPT 的預設性格", guild_ids=all_servers)
async def reset(ctx: discord.ApplicationContext):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```", ephemeral=True)
		return

	chat = chats.get(ctx.channel.id, None)
	chat.gpt.sys_prompt = config.default_sys_prompt
	channels.add_channel(ctx.channel_id, chat.gpt.sys_prompt)
	await ctx.respond(f"```設定更新：{chat.gpt.sys_prompt}```")


supported_models = ["gpt-3.5-turbo", "gpt-4"]


@bot.slash_command(name="set-model", description="選擇語言模型", guild_ids=all_servers)
@discord.option("model", choices=supported_models)
async def set_model(ctx: discord.ApplicationContext, model: str):
	log(f"{ctx.user.name} set their model to {model}")
	if model == "gpt-4" and not record.is_privileged([role.id for role in ctx.user.roles]):
		log("no privilege")
		await ctx.respond("```您沒有權限訪問 GPT-4 模型，請聯繫管理員```", ephemeral=True)
		return

	user = record.User(ctx.user.id)
	user.model = model
	user.save_data()
	await ctx.respond(f"```成功切換至模型：{user.model}```", ephemeral=True)


@bot.slash_command(description="查看目前的使用額度", guild_ids=all_servers)
async def quota(ctx: discord.ApplicationContext):
	if not record.user_exists(ctx.user.id):
		await ctx.respond(f"```您目前的使用額度：${config.free_credits} USD```", ephemeral=True)
		return

	user = record.User(ctx.user.id)
	await ctx.respond(f"```您目前的使用額度：${round(user.credits, 5)} USD```", ephemeral=True)


@bot.slash_command(name="help", description="指令介紹", guild_ids=all_servers)
async def help_info(ctx: discord.ApplicationContext):
	await ctx.respond(help_message)


@bot.slash_command(name="add-quota", description="Add quota to a user", guild_ids=all_servers)
@discord.option("user_id", description="user id", required=True)
@discord.option("amount", description="amount", required=True)
@discord.option("create_new_user", choices=[True, False], required=False, default=False)
async def add_quota(ctx: discord.ApplicationContext, user_id: str, amount: float, create_new_user: bool):
	if int(ctx.user.id) != config.admin_id:
		await ctx.respond("```you're not the admin```", ephemeral=True)
		return

	log(f"add quota {amount} usd to {user_id}")
	if not create_new_user and not record.user_exists(int(user_id)):
		log("user not exists")
		await ctx.respond(f"```user {user_id} does not exist in database```", ephemeral=True)
		return

	user_name: str

	try:
		user_obj = await bot.fetch_user(int(user_id))
		user_name = user_obj.name

	except discord.NotFound:
		log(f"user with id '{user_id}' cannot be found")
		user_name = "NOT FOUND"

	except Exception as e:
		log(f"main.add_quota() error: cannot fetch user '{user_id}'")
		log(repr(e))
		user_name = "ERROR"

	user = record.User(int(user_id))
	old_credits = user.credits
	user.credits += amount
	user.save_data()

	result_message: str = f"{user_name}: ${round(old_credits, 5)} -> ${round(user.credits, 5)} (+${amount})"
	log(result_message)
	await ctx.respond(f"```{result_message}```", ephemeral=True)


@bot.event
async def on_message(message: discord.Message):
	if message.author.id == bot.user.id:
		return

	if message.author.bot:
		return

	if message.content.startswith("#") or message.content.startswith("＃"):
		return

	if message.channel.id not in chats and channels.is_on_channel(message.channel.id):
		log(f"restore active channel: {message.channel.id}")
		chats[message.channel.id] = Chat()
		chats.get(message.channel.id).gpt.sys_prompt = channels.channels.get(str(message.channel.id))

	if message.channel.id in chats:
		chat = chats.get(message.channel.id)
		await chat.add_message(message)


def load_help_message():
	try:
		with open("asset/help.md", "r", encoding="utf-8") as f:
			global help_message
			help_message = f.read()
	except Exception as e:
		log(f"error while reading help message:\n{repr(e)}")
		help_message = "```ERROR WHILE READING HELP MESSAGE```"


log("bot running!")
load_help_message()
bot.run(os.environ.get("discord_bot_token"))
