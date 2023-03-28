import os
import discord
from src.log import log
from src import ai
from src import config
from src import record

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
						log(f"downgraded model to gpt-3.5-turbo for user {message.author.name} because of missing privilege")
						user.model = "gpt-3.5-turbo"

					if user.credits <= 0 and not user.credits == -1:
						await message.reply("```您已到達使用上限，請待下個月用量重置、或考慮贊助以增加許可用量```")

					else:
						result = await self.gpt.chat(f"{message.author.id}", message.content, user.model)
						user.credits -= result["usage"]
						reply = await message.reply(result["reply"])
						if user.model == "gpt-4":
							await reply.add_reaction("⭐")

				user.save_data()

			except Exception as e:
				log(repr(e))

			self.__messages.pop(0)
			await self.__reply_next()


chats: dict[int, Chat] = {}
all_servers: list = config.available_servers + config.admin_servers


@bot.slash_command(description="開始與 GPT 聊天（僅限使用指令的頻道）", guild_ids=all_servers)
async def start_chat(ctx: discord.ApplicationContext):
	if ctx.channel_id not in chats:
		chats[ctx.channel_id] = Chat()
		await ctx.respond("好耶，來一起聊天！ (ﾉ>ω<)ﾉ")
	else:
		await ctx.respond("我已經在聊天室裡了，你一點都沒有在注意我 ( ˘･з･)")


@bot.slash_command(description="結束與 GPT 的聊天", guild_ids=all_servers)
async def stop_chat(ctx: discord.ApplicationContext):
	if not chats.pop(ctx.channel_id, None):
		await ctx.respond("我本來就沒在這聊天啊 ( •́ _ •̀)？")
	else:
		await ctx.respond("掰啦⋯⋯不要太想我 (☍﹏⁰)")


@bot.slash_command(description="讓 GPT 馬上遺忘先前的對話", guild_ids=all_servers)
async def forget(ctx: discord.ApplicationContext):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```")
		return

	chat = chats.get(ctx.channel.id)
	chat.gpt.history.clear()
	await ctx.respond("蝦？剛發生了啥？ Σ( ° △ °)")


@bot.slash_command(description="自訂 GPT 的性格（類似洗腦）", guild_ids=all_servers)
@discord.option("prompt", description="洗腦的內容", required=True)
async def brain_wash(ctx: discord.ApplicationContext, prompt: str):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```")
		return

	log(f"system prompt received from {ctx.author}: {prompt}")

	if ai.count_token([{"role": "user", "content": prompt}]) > config.max_sys_prompt_token:
		log("system prompt too long")
		await ctx.respond("太多了太多了！是想把我洗成智障嗎？！拒絕！！ (╬ﾟдﾟ)凸")
		return

	chat = chats.get(ctx.channel.id, None)
	if chat is not None:
		chat.gpt.sys_prompt = prompt
		await ctx.respond(f"```設定更新：{chat.gpt.sys_prompt}```")
	else:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```")


@bot.slash_command(description="顯示目前的 GPT 機器人設定", guild_ids=all_servers)
async def status(ctx: discord.ApplicationContext):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```")
		return

	chat = chats.get(ctx.channel.id)
	await ctx.respond(f"```目前設定：{chat.gpt.sys_prompt}```")


@bot.slash_command(description="恢復 GPT 的預設性格", guild_ids=all_servers)
async def reset(ctx: discord.ApplicationContext):
	if ctx.channel.id not in chats:
		await ctx.respond(f"```機器人尚未加入此頻道，請先使用 /start_chat 指令```")
		return

	chat = chats.get(ctx.channel.id, None)
	chat.gpt.sys_prompt = config.default_sys_prompt
	await ctx.respond(f"```設定更新：{chat.gpt.sys_prompt}```")


supported_models = ["gpt-3.5-turbo", "gpt-4"]


@bot.slash_command(description="選擇語言模型", guild_ids=all_servers)
@discord.option("model", choices=supported_models)
async def set_model(ctx: discord.ApplicationContext, model: str):
	log(f"{ctx.user.name} set their model to {model}")
	if model == "gpt-4" and not record.is_privileged([role.id for role in ctx.user.roles]):
		await ctx.respond("```您沒有權限訪問 GPT-4 模型，請考慮贊助以獲得使用許可量```")
	else:
		user = record.User(ctx.user.id)
		user.model = model
		user.save_data()
		await ctx.respond(f"```成功切換至模型：{user.model}```")


@bot.slash_command(description="查看目前的使用額度", guild_ids=all_servers)
async def quota(ctx: discord.ApplicationContext):
	if not record.user_exists(ctx.user.id):
		await ctx.respond(f"```您目前的使用額度：${config.free_credits} USD```")
		return

	user = record.User(ctx.user.id)
	await ctx.respond(f"```您目前的使用額度：${round(user.credits, 5)} USD```")


@bot.slash_command(description="Add quota to a user", guild_ids=config.admin_servers)
@discord.option("user_id", description="user id", required=True)
@discord.option("amount", description="amount", required=True)
@discord.option("create_new_user", choices=[True, False], required=False, default=False)
async def add_quota(ctx: discord.ApplicationContext, user_id: str, amount: float, create_new_user: bool):
	if int(ctx.user.id) != config.admin_id:
		await ctx.respond("```you're not the admin```")
		return

	log(f"add quota {amount} usd to {user_id}")
	if not create_new_user and not record.user_exists(int(user_id)):
		log("user not exists")
		await ctx.respond(f"```user {user_id} does not exist in database```")
		return

	user = record.User(int(user_id))
	old = user.credits
	user.credits += amount
	user.save_data()
	log(f"user quota: ${round(old, 5)} -> ${round(user.credits, 5)} USD")
	await ctx.respond(f"```user quota: ${round(old, 5)} -> ${round(user.credits, 5)} USD```")


@bot.event
async def on_message(message: discord.Message):
	if message.author.id == bot.user.id:
		return

	if message.content.startswith("#") or message.content.startswith("＃"):
		return

	if message.channel.id in chats:
		chat = chats.get(message.channel.id)
		await chat.add_message(message)


log("bot running!")
bot.run(os.environ.get("discord_bot_token"))
