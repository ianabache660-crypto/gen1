import discord
from discord import app_commands
from discord.ext import commands
import json
import random
import string
import os
from datetime import datetime, timedelta

TOKEN = "YOUR_BOT_TOKEN"
GUILD_ID = YOUR_GUILD_ID  # Put your server ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "data.json"

# ------------------------
# DATA HANDLER
# ------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "keys": {},
                "users": {},
                "stock": {}
            }, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ------------------------
# KEY GENERATOR
# ------------------------

def generate_key():
    return f"Superino-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(100,999)}"

# ------------------------
# READY EVENT
# ------------------------

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user}")

# ------------------------
# ADMIN: GENKEY
# ------------------------

@tree.command(name="genkey", description="Generate keys", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(amount="How many keys?")
async def genkey(interaction: discord.Interaction, amount: int):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("Admin only.", ephemeral=True)

    data = load_data()
    keys = []

    for _ in range(amount):
        key = generate_key()
        data["keys"][key] = {
            "used": False,
            "expires": str(datetime.now() + timedelta(days=30))
        }
        keys.append(key)

    save_data(data)

    await interaction.response.send_message(
        "Generated Keys:\n" + "\n".join(keys),
        ephemeral=True
    )

# ------------------------
# VERIFY KEY
# ------------------------

@tree.command(name="verify", description="Verify key", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(key="Enter your key")
async def verify(interaction: discord.Interaction, key: str):

    data = load_data()

    if key not in data["keys"]:
        return await interaction.response.send_message("Invalid key.", ephemeral=True)

    if data["keys"][key]["used"]:
        return await interaction.response.send_message("Key already used.", ephemeral=True)

    data["keys"][key]["used"] = True
    data["users"][str(interaction.user.id)] = {
        "expires": data["keys"][key]["expires"],
        "generated": 0
    }

    save_data(data)

    await interaction.response.send_message("Key verified successfully!", ephemeral=True)

# ------------------------
# ADD STOCK
# ------------------------

@tree.command(name="addstock", description="Add stock", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(category="Category name")
async def addstock(interaction: discord.Interaction, category: str):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("Admin only.", ephemeral=True)

    data = load_data()

    if category not in data["stock"]:
        data["stock"][category] = []

    save_data(data)

    await interaction.response.send_message(f"Category `{category}` created.", ephemeral=True)

# ------------------------
# CHECK STOCK
# ------------------------

@tree.command(name="checkstock", description="Check available stock", guild=discord.Object(id=GUILD_ID))
async def checkstock(interaction: discord.Interaction):

    data = load_data()

    msg = ""
    for cat, items in data["stock"].items():
        msg += f"{cat} : {len(items)}\n"

    if msg == "":
        msg = "No stock available."

    await interaction.response.send_message(msg, ephemeral=True)

# ------------------------
# GENERATE ITEM
# ------------------------

@tree.command(name="generate", description="Generate item", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(category="Category name")
async def generate(interaction: discord.Interaction, category: str):

    data = load_data()
    user_id = str(interaction.user.id)

    if user_id not in data["users"]:
        return await interaction.response.send_message("You need to verify first.", ephemeral=True)

    if category not in data["stock"] or len(data["stock"][category]) == 0:
        return await interaction.response.send_message("Out of stock.", ephemeral=True)

    item = data["stock"][category].pop(0)
    data["users"][user_id]["generated"] += 1
    save_data(data)

    try:
        await interaction.user.send(f"Here is your item:\n{item}")
        await interaction.response.send_message("Sent in DM.", ephemeral=True)
    except:
        await interaction.response.send_message("Enable DMs first.", ephemeral=True)

# ------------------------
# REPORT (WITH IMAGE ATTACHMENT)
# ------------------------

@tree.command(name="report", description="Report something", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(message="Your report message")
async def report(interaction: discord.Interaction, message: str):

    if not interaction.attachments:
        return await interaction.response.send_message("Attach an image.", ephemeral=True)

    channel = interaction.channel
    embed = discord.Embed(title="New Report", description=message)
    embed.set_image(url=interaction.attachments[0].url)

    await channel.send(embed=embed)
    await interaction.response.send_message("Report submitted.", ephemeral=True)

bot.run(TOKEN)
