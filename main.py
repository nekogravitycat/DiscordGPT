import os
import discord
from log import log
import ai

bot = discord.Bot(intents=discord.Intents.all())
available_servers: list = os.environ.get("available_servers").split(";")
gpts: dict = {}


@bot.slash_command(description="開始與 GPT 聊天（僅限使用指令的頻道）", guild_ids=available_servers)
async def start_chat(ctx):
	if ctx.channel_id not in gpts:
		gpts[ctx.channel_id] = ai.GPT()
		await ctx.respond("好耶，來一起聊天！")
	else:
		await ctx.respond("我已經在聊天室裡了，你一點都沒有在注意我 ;w;")


@bot.slash_command(description="結束與 GPT 的聊天", guild_ids=available_servers)
async def stop_chat(ctx):
	if gpts.pop(ctx.channel_id, True):
		await ctx.respond("掰啦，不要太想我 ;w;")
	else:
		await ctx.respond("？我本來就沒在這聊天啊")


@bot.slash_command(description="讓 GPT 馬上遺忘先前的對話", guild_ids=available_servers)
async def forget(ctx):
	gpt = gpts.get(ctx.channel.id)
	gpt.forget()
	await ctx.respond("蝦？剛發生了啥？")


@bot.slash_command(description="自訂 GPT 的性格（類似初始洗腦）", guild_ids=available_servers)
@discord.option("prompt", description="洗腦的內容", required=True)
async def brain_wash(ctx, prompt):
	log(f"system prompt received from {ctx.author}: {prompt}")

	if ai.num_prompts_tokens([{"role": "user", "content": prompt}]) > 500:
		log("system prompt too long")
		await ctx.respond("哪有人洗腦洗那麼多的啦，拒絕！")
		return

	gpt = gpts.get(ctx.channel.id)
	gpt.sys_prompt = prompt
	await ctx.respond(f"```設定更新：{gpt.sys_prompt}```")


@bot.slash_command(description="恢復 GPT 的預設性格", guild_ids=available_servers)
async def reset(ctx):
	gpt = gpts.get(ctx.channel.id)
	gpt.reset()
	await ctx.respond(f"```設定更新：{gpt.sys_prompt}```")


@bot.event
async def on_message(message):
	if message.author.id == bot.user.id:
		return

	if message.channel.id in gpts:
		async with message.channel.typing():
			gpt = gpts.get(message.channel.id)
			await message.reply(await gpt.chat(f"{message.author.name}-{message.author.id}", message.content))


log("bot running!")
bot.run(os.environ.get("discord_bot_token"))
