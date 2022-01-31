from discord import client, Intents
from discord.ext import commands

print('Pomyślnie załadowano client.py')

client = commands.Bot(command_prefix='.', fetch_offline_members=True, intents=Intents.all())
client.remove_command('help')