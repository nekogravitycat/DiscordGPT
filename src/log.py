import datetime


def log(data: str):
	print(data)
	now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
	with open("log/main.log", "a", encoding="utf-8") as f:
		f.write(f"[{now}] {data}\n")
