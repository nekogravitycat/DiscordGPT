import os
import discord
from src.log import log
from src import ai
from src import config

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

			try:
				async with message.channel.typing():
					await message.reply(await self.gpt.chat(f"{message.author.name}-{message.author.id}", message.content))

			except Exception as e:
				log(repr(e))

			self.__messages.pop(0)
			await self.__reply_next()


chats: dict[str, Chat] = {}


@bot.slash_command(description="開始與 GPT 聊天（僅限使用指令的頻道）", guild_ids=config.available_servers)
async def start_chat(ctx):
	if ctx.channel_id not in chats:
		chats[ctx.channel_id] = Chat()
		await ctx.respond("好耶，來一起聊天！ (ﾉ>ω<)ﾉ")
	else:
		await ctx.respond("我已經在聊天室裡了，你一點都沒有在注意我 ( ˘･з･)")


@bot.slash_command(description="結束與 GPT 的聊天", guild_ids=config.available_servers)
async def stop_chat(ctx):
	if not chats.pop(ctx.channel_id, None):
		await ctx.respond("我本來就沒在這聊天啊 ( •́ _ •̀)？")
	else:
		await ctx.respond("掰啦⋯⋯不要太想我 (☍﹏⁰)")


@bot.slash_command(description="讓 GPT 馬上遺忘先前的對話", guild_ids=config.available_servers)
async def forget(ctx):
	chat = chats.get(ctx.channel.id)
	chat.gpt.history.clear()
	await ctx.respond("蝦？剛發生了啥？ Σ( ° △ °)")


@bot.slash_command(description="自訂 GPT 的性格（類似洗腦）", guild_ids=config.available_servers)
@discord.option("prompt", description="洗腦的內容", required=True)
async def brain_wash(ctx, prompt):
	log(f"system prompt received from {ctx.author}: {prompt}")

	if ai.count_token([{"role": "user", "content": prompt}]) > config.max_sys_prompt_token:
		log("system prompt too long")
		await ctx.respond("太多了太多了！是想把我洗成智障嗎？！拒絕！！ (╬ﾟдﾟ)凸")
		return

	chat = chats.get(ctx.channel.id)
	chat.gpt.init_prompt = prompt
	await ctx.respond(f"```設定更新：{chat.gpt.init_prompt}```")


@bot.slash_command(description="顯示 GPT 機器人的詳細資訊", guild_ids=config.available_servers)
async def status(ctx):
	await ctx.respond("")


@bot.slash_command(description="恢復 GPT 的預設性格", guild_ids=config.available_servers)
async def reset(ctx):
	chat = chats.get(ctx.channel.id)
	chat.gpt.init_prompt = config.default_sys_prompt
	await ctx.respond(f"```設定更新：{chat.gpt.sys_prompt}```")


@bot.event
async def on_message(message):
	if message.author.id == bot.user.id:
		return

	if message.content.startswith("#") or message.content.startswith("＃"):
		return

	if message.channel.id in chats:
		chat = chats.get(message.channel.id)
		await chat.add_message(message)


log("bot running!")
bot.run(os.environ.get("discord_bot_token"))
