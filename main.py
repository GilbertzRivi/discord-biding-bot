import discord, asyncio, datetime, time
from discord.ext import commands, tasks
from os import getenv
from dotenv import load_dotenv
from database import database
from client import client

load_dotenv('token.env')

currencies = {
    'ADA': 5,
    'ROG': 50,
    'Djed': 2.5
}

@client.event
async def on_ready():
    
    print(f'Logged in as {client.user.name}')           #changing activity and printing bot name while ready
    await client.change_presence(activity=discord.Activity(name='.help', type=discord.ActivityType.watching))
    
    loop_1m.start()
              

def check_permissions(ctx):
    
    permissions = False
    config = database.config
    mod_roles = config.find({'type': 'mod_role'})       #getting mod roles from database
    mod_roles = [ctx.guild.get_role(id['value']) for id in mod_roles]   #converting them to discord.Role objects
    
    #if any role is in author roles, or author is administrator, return true
    if [role for role in ctx.author.roles if role in mod_roles] or ctx.author.guild_permissions.administrator:
        permissions = True
    return permissions


def timestamp_to_days(timestamp):

    days = int(timestamp / 86400)
    rest = time % 86400
    hours = int(rest / 3600)
    rest = rest % 3600
    minutes = int(rest / 60)
    seckonds = int(rest % 60)

    return days, hours, minutes, seckonds


def check_bid_permissions(ctx, id):
    bids = database.bids
    bid = bids.find_one({'id': id})
    if bid is None:
        return 'There is no bid with given ID'
    
    creator_id = bid['creator_id']
    if ctx.author.id != creator_id:
        return 'Only the creator of the bid can edid it'
    
    database_channel = database.config.find_one({'name':'bid_creation_channel'})
    if database_channel is None:
        return 'The command can only be used on a channel intended for creating bids'
    elif ctx.channel.id != database_channel['value']:
        return 'The command can only be used on a channel intended for creating bids'
            
    return True


@client.command()
async def changewalletadress(ctx, adress):
    if not ctx.author.guild_permissions.administrator:
        return
    
    config = database.config
    config.find_one_and_replace({'name': 'wallet_adress'}, {'name': 'wallet_adress','value': adress})
    await ctx.send('Wallet address successfully changed')
    
@client.command()
async def seewalletadress(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    
    config = database.config
    result = config.find_one({'name': 'wallet_adress'})
    await ctx.send(f'Wallet adress:\n```{result["value"]}```')
    
@client.command()
async def help(ctx):
    content_adm = f"""
```
Arguments in [] can't have any spaces in them, arguments in <> can.
Arguments in () are optional.

.changewalletadress [adress] - Set wallet adress, wich bot sends to the auction winners.
.seewalletadress - Shows curent wallet adress.

When message with any given slur is detected, it'll be removed.
.addslur [slur] - Adds given slur to the database.
.remslur [slur] - Removes given slur from the database.
.seeslurs - Lists all the slurs that are currently in the database.

Moderational roles are roles that give their owners special permisions while using this bot.
.addmodrole [@role] - Adds given role to the database.
.remmodrole [@role] - Removes given role from the database
.seemodroles - Lists all the roles that are currently "mod roles"

Veryfication gives special role to anybody that completed it.
.setverification [@role] - creates veryfication message.
To dissable veryfication just delete the message that the bot have created.

Other commands
.ban [@member] <reason> - Bans given member with given reason.
.guildinfo - Shows some info about current guild.
.kick [@member] <reason> - Kicks given member with given reason.
.purge [amount] - Deletes given amount of messages from current chat.
.roleinfo [@role] - Shows some info about given role.
.userpurge [amount] <@member> - deletes given amount of messages from current chat,
but only the ones that were sent by <@member>.
.userinfo [@member] - shows some info about given member.
```
    """
    content_user = """
```
Arguments in [] can't have any spaces in them, arguments in <> can.
Arguments in () are optional.

.avatar (@member) - Shows your's or @member's avatar.
.changenotif - Enables/Dissables notifications about someone overbiding you.
```
    """
    
    content_bids = """
```
Arguments in [] can't have any spaces in them, arguments in <> can.
Arguments in () are optional.

Setting channels for given operations.
.setprepchan - Sets current channnel as bid preparation channel.
.seeprepchan - Shows current bid preparation channel.
.setnotifchan - Sets channel where bot will send notifications about auctions.
.seenotifchan - Shows current notification channel.
.addbidingchan - Adds current channel to bidding channels.
.rembidingchan - Removes current channels from bidding channels.
.seebidingchan - Shows all current bidding channels.

Creating bid.
.createbid [id] - Starts the process of creating bid.
.changetitle [id] <title> - Changes bids title.
.changeimage [id] [image url] - Changes bids image.
.changedesc - [id] <description> - Changes bids description.
.changecurrency [id] <currency> - Changes bids currency. 
.changestartprice [id] [price] - Changes bids starting price.
.changeminimalprice [id] [price] - Changes bids minimal price.
.changeendtime [id] <day.month.year hour:minute> - Changes when the bid should end.
.publishbid [id] [#channel] - Publishes choosen bid. You can't edid published bids.
.seebids - shows all published/completed bids
.rembid [id] - Removes choosen bid completly.
```
    """
    
    permissions = check_permissions(ctx)
    
    await ctx.message.delete()
    
    if not permissions:
        await ctx.author.send(content=content_user)
        return
    
    else:
        await ctx.author.send(content=content_adm)
        await ctx.author.send(content=content_user)
        await ctx.author.send(content=content_bids)
    
    
##################################################### slurs


@client.command()
async def addslur(ctx, slur):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    pl_signs = {
        'ą': 'a',
        'ć': 'c',
        'ę': 'e',
        'ł': 'l',
        'ń': 'n',
        'ó': 'o',
        'ś': 's',
        'ź': 'z',
        'ż': 'z'
        }
    #deleting spaces from input
    slur = slur.lower().replace(' ', '')
    slur = list(slur)
    for i, sign in enumerate(slur):
        if sign in pl_signs.keys():
            slur[i] = pl_signs[sign]    #deleting polish signs from input
    slur = ''.join(slur)
    
    slurs = database.slurs
    result = slurs.find_one({'value': slur})
    if result is None:
        slurs.insert_one({'value': slur})
        await ctx.send('Given slur was successfully added to the database')
    else:
        await ctx.send('Given slur is already in the database')
    
@client.command()
async def remslur(ctx, slur):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    pl_signs = {
        'ą': 'a',
        'ć': 'c',
        'ę': 'e',
        'ł': 'l',
        'ń': 'n',
        'ó': 'o',
        'ś': 's',
        'ź': 'z',
        'ż': 'z'
        }

    slur = slur.lower().replace(' ', '')
    slur = list(slur)
    for i, sign in enumerate(slur):
        if sign in pl_signs.keys():
            slur[i] = pl_signs[sign]
    slur = ''.join(slur)
    
    slurs = database.slurs
    result = slurs.find_one_and_delete({'value': slur})
    if result is None:
        await ctx.send('No such slur was found in the database')
    else:
        await ctx.send('Given slur was successfully removed from the database')

@client.command()
async def seeslurs(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    slurs_embed = discord.Embed(color=ctx.author.color, title='Slurs', timestamp=ctx.message.created_at)
    slurs_embed.set_footer(icon_url=ctx.author.avatar_url, text='Slurs')
    
    slurs = []
    result = database.slurs.find()
    for i, row in enumerate(result):
        slurs.append(row['value'])
    
    chunked_list = [slurs[i:i + 20] for i in range(0, len(slurs), 20)]
    for i, chunk in enumerate(chunked_list):
        slurs_embed.add_field(name=(i+1)*20, value='\n'.join(chunk), inline=True)
    
    await ctx.send(embed=slurs_embed)


##################################################### mod roles


@client.command()
async def addmodrole(ctx, *, role: discord.Role):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permissions")
        return
        
    data = {
        'type': 'mod_role',
        'name': role.name,
        'value': role.id
        }
    
    config = database.config
    result = config.find_one({'value': role.id})
    if result is None:
        config.insert_one(data)
        await ctx.send('Given role was successfully added to the database')
    else:
        await ctx.send('Given role is already in the database')
    
@addmodrole.error
async def addmodrole_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('The given role is invalid')
             
####  
           
@client.command()
async def remmodrole(ctx, *, role: discord.Role):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permissions")
        return
        
    data = {
        'type': 'mod_role',
        'name': role.name,
        'value': role.id
        }
    
    config = database.config
    result = config.find_one_and_delete({'value': role.id})
    if result is None:
        await ctx.send('No such role was found in the database')
    else:
        await ctx.send('Given role was successfully removed from the database')
    
@remmodrole.error
async def remmodrole_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('The given role is invalid')
        
####  
        
@client.command()
async def seemodroles(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permissions")
        return
    
    config = database.config
    result = config.find({'type': 'mod_role'})
    roles = []
    for row in result:
        roles.append((row['name'], row['value']))
    
    mod_roles_embed = discord.Embed(color=ctx.author.color, title='Moderation roles', timestamp=ctx.message.created_at)  
    mod_roles_embed.set_footer(icon_url=ctx.author.avatar_url, text='Moderation roles')     
    for role in roles:
        mod_roles_embed.add_field(name=role[0], value=role[1]) 
    if len(roles) == 0:
        mod_roles_embed.add_field(name='Missing', value='No role has been set as moderation role') 
    await ctx.send(embed=mod_roles_embed)
    
    
##################################################### verification


@client.command()
async def setverification(ctx, *, role: discord.Role):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permissions")
        return
    
    await ctx.message.delete()
    
    message = await ctx.send('Click ☑ under this meesage to gain access to this server')
    
    await message.add_reaction('☑')
    try:
        await client.wait_for('reaction_add', timeout=5.0)
    except asyncio.TimeoutError:
        await message.add_reaction('☑')
    
    config = database.config
    config.find_one_and_delete({'name': 'verification'})

    data = {
        'name': 'verification',
        'channel_id': message.channel.id,
        'message_id': message.id,
        'role_id': role.id
    }
    
    config.insert_one(data)

@setverification.error
async def setverification_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Given role is invalid')
    
    
##################################################### basic commands


@client.command()
async def ban(ctx, member: discord.Member, *, reason = 'reason not provided'):
    permissions = check_permissions(ctx)
    
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    await member.ban(reason=f'{ctx.author.name} - {reason}', delete_message_days=0)
    await ctx.send(f'Successfully banned {member.name}')
    
@client.command()
async def kick(ctx, member: discord.Member, *, reason = 'reason not provided'):
    permissions = check_permissions(ctx)
    
    if not permissions:
        await ctx.send("You don't have permissions")
        return
            
    await member.kick(reason=f'{ctx.author.name} - {reason}')
    await ctx.send(f'Successfully kicked {member.name}')

@client.command()
async def purge(ctx, amount: int):
    permissions = check_permissions(ctx)
    
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    await ctx.channel.purge(limit=amount+1)
    
@client.command()
async def userpurge(ctx, amount: int, *, member: discord.Member):
    permissions = check_permissions(ctx)
    
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    counter = 0
    async for message in ctx.channel.history(limit=10000):
        
        if message.author == member:
            await message.delete()
            counter += 1
            
        if (amount + 1) <= counter:
            break
        
####  
        
@client.command()
async def avatar(ctx, *, member: discord.Member):
    await ctx.message.delete()
    e = discord.Embed(color=ctx.author.colour, timestamp=ctx.message.created_at)
    e.set_footer(text=f"{ctx.author.name} Asked for {member.display_name}'s avatar", icon_url=ctx.author.avatar_url)
    e.set_image(url=member.avatar_url)
    await ctx.send(embed=e)

@avatar.error
async def avatar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.delete()
        e = discord.Embed(color=ctx.author.colour)
        e.set_footer(text=f"That's your avatar", icon_url=ctx.author.avatar_url)
        e.set_image(url=ctx.author.avatar_url)
        await ctx.send(embed=e)
        
####  
        
@client.command()
async def roleinfo(ctx, *, role: discord.Role):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    e = discord.Embed(color=role.color, timestamp=ctx.message.created_at)
    e.set_author(name=f"Information about {role.name}")
    e.set_footer(text=f"As {ctx.author} requested", icon_url=ctx.author.avatar_url)
    e.add_field(name="Role name:", value=role.name, inline=False)
    e.add_field(name="Role color:", value=role.color, inline=False)
    e.add_field(name="Role ID:", value=role.id, inline=False)
    e.add_field(name="Number of members with given role:", value=str(len(role.members)), inline=False)
    
    await ctx.send(embed=e)

@client.command()
async def guildinfo(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    d, h, m, s = timestamp_to_days(datetime.datetime.utcnow().timestamp() - ctx.guild.created_at.timestamp())
    
    age = ''
    if d == 0:
        if h == 0:
            if m == 0:
                age = f'**{s}** seconds'
            else:
                age = f'**{m}** minutes and **{s}** seconds'
        else:
            age = f'**{h}** hours, **{m}** minutes and **{s}** seconds'
    else:
        age = f'**{d}** days, **{h}** hours, **{m}** minutes and **{s}** seconds'

    counter = 0
    for member in ctx.guild.members:
        if member.bot:
            counter += 1 
    e = discord.Embed(color=ctx.author.color, name=f"Information about {ctx.guild.name}", timestamp=ctx.message.created_at)
    e.add_field(name='Guild name:', value=ctx.guild.name, inline=True)
    e.set_thumbnail(url=ctx.guild.icon_url)
    e.add_field(name="Guilds host:", value=f"{ctx.guild.owner} aka {ctx.guild.owner.display_name}", inline=True)
    e.add_field(name="Emojis count:", value=len(ctx.guild.emojis), inline=True)
    e.add_field(name="Text channels count:", value=len(ctx.guild.text_channels), inline=True)
    e.add_field(name="Voice channels count:", value=len(ctx.guild.voice_channels), inline=True)
    e.add_field(name="Channels count:", value=len(ctx.guild.voice_channels) + len(ctx.guild.text_channels), inline=True)
    e.add_field(name="Members count:", value=len(ctx.guild.members) - counter, inline=True)
    e.add_field(name="Bots count:", value=counter, inline=True)
    e.add_field(name="Roles count:", value=len(ctx.guild.roles), inline=True)
    e.add_field(name="Created:", value=f'{ctx.guild.created_at.strftime(("%S:%H:%M - %d.%m.%Y"))}\nCzyli:\n{age} temu', inline=False)
    e.set_footer(text=f'As {ctx.author.display_name} requested', icon_url=ctx.author.avatar_url)
    
    await ctx.send(embed=e)

@client.command()
async def userinfo(ctx, *, member: discord.Member):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    user_info_embed = discord.Embed(color=member.color, timestamp=ctx.message.created_at)
    user_info_embed.set_footer(text=f"As {ctx.author} requested", icon_url=ctx.author.avatar_url)

    d_os, h_os, m_os, s_os = timestamp_to_days(datetime.datetime.utcnow().timestamp() - member.joined_at.timestamp())
    d_ae, h_ae, m_ae, s_ae = timestamp_to_days(datetime.datetime.utcnow().timestamp() - member.created_at.timestamp())

    on_serv = ''
    if d_os == 0:
        if h_os == 0:
            if m_os == 0:
                on_serv = f'{s_os} seconds'
            else:
                on_serv = f'{m_os} minutes and {s_os} seconds'
        else:
            on_serv = f'{h_os} hours, {m_os} minutes and {s_os} seconds'
    else:
        on_serv = f'{d_os} days, {h_os} hours, {m_os} minutes and {s_os} seconds'

    acc_age = ''
    if d_ae == 0:
        if h_ae == 0:
            if m_ae == 0:
                acc_age = f'{s_ae} seconds'
            else:
                acc_age = f'{m_ae} minutes and {s_ae} seconds'
        else:
            acc_age = f'{h_ae} hours, {m_ae} minutes and {s_ae} seconds'
    else:
        acc_age = f'{d_ae} days, {h_ae} hours, {m_ae} minutes and {s_ae} seconds'

    user_info_embed.set_author(name=f"Information about {member.name}")
    user_info_embed.set_thumbnail(url=member.avatar_url)
    user_info_embed.add_field(name="ID:", value=member.id, inline=False)
    user_info_embed.add_field(name="Nick:", value=member.name, inline=False)
    user_info_embed.add_field(name="Guild nick:", value=member.display_name, inline=False)
    user_info_embed.add_field(name="Account created:", value=member.created_at.strftime("%H:%M - %d.%m.%Y"), inline=False)
    user_info_embed.add_field(name="Joined at:", value=member.joined_at.strftime("%H:%M - %d.%m.%Y"), inline=False)
    user_info_embed.add_field(name="Time on this guild:", value=on_serv, inline=False)
    user_info_embed.add_field(name="Account age:", value=acc_age, inline=False)
    await ctx.send(embed=user_info_embed)


##################################################### bid


@client.command()
async def setprepchan(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    config = database.config
    config.find_one_and_delete({'name':'bid_creation_channel'})
    
    data = {
        'name': 'bid_creation_channel',
        'value': ctx.channel.id
    }
    
    config.insert_one(data)
        
    await ctx.send(f'{ctx.channel.mention} was successfully set as bid preparation channel')

@client.command()
async def seeprepchan(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    config = database.config
    result = config.find_one({'name':'bid_creation_channel'})
    channel = client.get_channel(result["value"])
    
    await ctx.send(f'Bid preparation channel: {channel.mention}')

@client.command()
async def setnotifchan(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    config = database.config
    config.find_one_and_replace({'name': 'notification_channel'}, {'name': 'notification_channel', 'value': ctx.channel.id})
    await ctx.send(f'{ctx.channel.mention} was successfully set as notification channel')
    
@client.command()
async def seenotifchan(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    config = database.config
    result = config.find_one({'name': 'notification_channel'})
    channel = client.get_channel(result["value"])
    
    await ctx.send(f'Notification channel: {channel.mention}')
            
####  
        
@client.command()
async def createbid(ctx, id: int):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    bid_creation_channel = database.config.find_one({'name':'bid_creation_channel'})
    if bid_creation_channel is None:
        await ctx.send('The command can only be used on a channel intended for creating bids')
        return
    elif ctx.channel.id != bid_creation_channel['value']:
        await ctx.send('The command can only be used on a channel intended for creating bids')
        return
    
    bids = database.bids
    bid_existence_check = bids.find_one({'id': id})
    if bid_existence_check is not None:
        await ctx.send('Bid with given ID already exists')
        return
    
    content = f"""
Successfully created bid, to finish creating it, use this commands:.
.settitle ID title
.setimage ID link
.setdesc ID description
.setcurrency ID {" ".join([currency for currency in currencies])}
.setstartprice ID starting price
.setminimalprice ID minimal price
.setendtime ID day.month.year hour:minute
.publishbid ID channel
To delete auction use .rembid ID
        """
    
    embed=discord.Embed(title='Title not provided', description="Description not provided\n\nBid by clicking ☑ under this message")
    embed.set_thumbnail(url=ctx.guild.icon_url)
    embed.add_field(name="Current Price", value="Not provided", inline=False)
    embed.add_field(name="Minimal Price", value="Not provided", inline=False)
    embed.add_field(name="Last bids", value="None", inline=False)  
    embed.add_field(name="Ends at", value="Not provided", inline=False)  
    embed.add_field(name="id", value=id, inline=False)  
    message = await ctx.send(content=content ,embed=embed)
    
    data = {
        'start_time': int(time.time()),
        'creator_id': ctx.author.id,
        'id': id,
        'message_id': message.id,
        'title': None,
        'description': None,
        'image_url': None,
        'end_time': None,
        'minimal_price': None,
        'current_price': None,
        'currency': None,
        'published': False
    }
    
    bids.insert_one(data)

@createbid.error
async def createbid_error(ctx, error):
    await ctx.send('Missing argument\n.createbid ID')
        
####  
        
@client.command()
async def settitle(ctx, id: int, *, title):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    response = check_bid_permissions(ctx, id)

    if isinstance(response, str):
        await ctx.send(response)
        return
    
    await ctx.message.delete()

    bids = database.bids
    bid = bids.find_one({'id': id})
    
    if bid is None:
        await ctx.send('There is no bid with given ID in the database')
        return
    
    if bid['published']:
        await ctx.send("You can't edit published bid")
        return
    
    config = database.config
    message_id = bid['message_id']
    auction_setting_channel_id = config.find_one({"name":"bid_creation_channel"})['value']
    auction_message = await client.get_channel(auction_setting_channel_id).fetch_message(message_id)
    auction_embed = auction_message.embeds[0]
    auction_embed.title = title
    
    await auction_message.edit(embed=auction_embed)
        
    bids.find_one_and_update({"id": id}, {'$set': {"title": title}})  

@settitle.error
async def settitle_error(ctx, error):
    await ctx.send('Missing argument\n.changetitle ID Title')
            
####  
        
@client.command()
async def setimage(ctx, id: int, url):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    response = check_bid_permissions(ctx, id)

    if isinstance(response, str):
        await ctx.send(response)
        return
    
    await ctx.message.delete()

    bids = database.bids
    bid = bids.find_one({'id': id})
    
    if bid is None:
        await ctx.send('There is no bid with given ID in the database')
        return
    
    if bid['published']:
        await ctx.send("You can't edit published bid")
        return
        
    config = database.config
    message_id = bid['message_id']
    auction_setting_channel_id = config.find_one({"name":"bid_creation_channel"})['value']
    auction_message = await client.get_channel(auction_setting_channel_id).fetch_message(message_id)
    auction_embed = auction_message.embeds[0]
    auction_embed.set_image(url=url)
    
    await auction_message.edit(embed=auction_embed)
        
    bids.find_one_and_update({"id": id}, {'$set': {"image_url": url}})  
    
@setimage.error
async def setimage_error(ctx, error):
    await ctx.send('Missing argument\n.changeimage ID Image url')
            
####  
        
@client.command()
async def setdesc(ctx, id: int, *, description):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    response = check_bid_permissions(ctx, id)

    if isinstance(response, str):
        await ctx.send(response)
        return
    
    await ctx.message.delete()
    
    bids = database.bids
    bid = bids.find_one({'id': id})
    
    if bid is None:
        await ctx.send('There is no bid with given ID in the database')
        return
    
    if bid['published']:
        await ctx.send("You can't edit published bid")
        return
        
    message_id = bid['message_id']
    config = database.config
    auction_setting_channel_id = config.find_one({"name":"bid_creation_channel"})['value']
    auction_message = await client.get_channel(auction_setting_channel_id).fetch_message(message_id)
    auction_embed = auction_message.embeds[0]
    auction_embed.description = description + '\n\nBid by clicking ☑ under this message'
    
    bids.find_one_and_update({"id": id}, {'$set': {"description": description}})  
    await auction_message.edit(embed=auction_embed)  

@setdesc.error
async def setdesc_error(ctx, error):
    await ctx.send('Missing argument\n.changedesc ID Description')
            
####  
        
@client.command()
async def rembid(ctx, id: int):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    bids = database.bids
    bid_existence_check = bids.find_one({'id': id})
    if bid_existence_check is None:
        await ctx.send('There is no bid with given ID')
    
    bid = bids.find_one({'id': id})
    creator_id = bid['creator_id']
    if ctx.author.id != creator_id and not ctx.author.guild_permissions.administrator:
        await ctx.send('Only the creator of the bid can edid it')
        return
    
    database_channel = database.config.find_one({'name':'bid_creation_channel'})
    if database_channel is None:
        await ctx.send('The command can only be used on a channel intended for creating bids')
        return
    elif ctx.channel.id != database_channel['value']:
        await ctx.send('The command can only be used on a channel intended for creating bids')
        return
    
    await ctx.message.delete()
            
    bids.find_one_and_delete({'id': id})
    await ctx.send('Successfully deleted bid from the database')
    
    if bid['published']:
        published_channel = bid['published_channel_id']
        published_id = bid['published_id']
        published_auction_message = await client.get_channel(published_channel).fetch_message(published_id)
        await published_auction_message.delete()
        await ctx.send('Successfully deleted published bid')
        
    message_id = bid['message_id']
    config = database.config
    auction_setting_channel_id = config.find_one({"name":"bid_creation_channel"})['value']
    auction_message = await client.get_channel(auction_setting_channel_id).fetch_message(message_id)
    title = auction_message.embeds[0].title
    
    await ctx.send(f'Successfully deleted bid **"{title}"** with ID ``{id}``')
        
@rembid.error
async def rembid_error(ctx, error):
    await ctx.send('Missing argument\n.rembid ID')
            
####  
        
@client.command()
async def setstartprice(ctx, id: int, price: float):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    response = check_bid_permissions(ctx, id)

    if isinstance(response, str):
        await ctx.send(response)
        return
    
    await ctx.message.delete()
    
    bids = database.bids
    bid = bids.find_one({'id': id})
    
    if bid is None:
        await ctx.send('There is no bid with given ID in the database')
        return
    
    if bid['published']:
        await ctx.send("You can't edit published bid")
        return
        
    try:
        currency = bid['currency']
    except NameError:
        await ctx.send('Set the currency first')
        return
    
    message_id = bid['message_id']
    config = database.config
    auction_setting_channel_id = config.find_one({"name":"bid_creation_channel"})['value']
    auction_message = await client.get_channel(auction_setting_channel_id).fetch_message(message_id)
    auction_embed = auction_message.embeds[0]
    auction_embed.set_field_at(0, name = 'Current Price', value = f'```fix\n{price} {currency}```\n\n1 bid costs {currencies[currency]} {currency}', inline=False)
    
    bids.find_one_and_update({'id': id}, {'$set': {'current_price': price}})
    
    await auction_message.edit(embed=auction_embed)

@setstartprice.error
async def setstartprice_error(ctx, error):
    await ctx.send('Missing argument\n.changestartprice ID Price')
        
####  
        
@client.command()
async def setminimalprice(ctx, id: int, price: float):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    response = check_bid_permissions(ctx, id)

    if isinstance(response, str):
        await ctx.send(response)
        return
    
    await ctx.message.delete()
    
    bids = database.bids
    bid = bids.find_one({'id': id})
    
    if bid is None:
        await ctx.send('There is no bid with given ID in the database')
        return
    
    if bid['published']:
        await ctx.send("You can't edit published bid")
        return
    
    try:
        currency = bid['currency']
    except NameError:
        await ctx.send('Set currency first')
        return
    
    message_id = bid['message_id']
    config = database.config
    auction_setting_channel_id = config.find_one({"name":"bid_creation_channel"})['value']
    auction_message = await client.get_channel(auction_setting_channel_id).fetch_message(message_id)
        
    auction_embed = auction_message.embeds[0]
    auction_embed.set_field_at(1, name = 'Minimal Price', value = f'{price} {currency}', inline=False)
    
    bids.find_one_and_update({'id': id}, {'$set': {'minimal_price': price}})
    
    await auction_message.edit(embed=auction_embed)

@setminimalprice.error
async def setminimalprice_error(ctx, error):
    await ctx.send('Missing argument\n.changeminimalprice ID Price')
        
####  
        
@client.command()
async def setcurrency(ctx, id: int, *, currency):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    response = check_bid_permissions(ctx, id)

    if isinstance(response, str):
        await ctx.send(response)
        return
    
    bids = database.bids
    bid = bids.find_one({'id': id})
    
    if bid is None:
        await ctx.send('There is no bid with given ID in the database')
        return
    
    if bid['published']:
        await ctx.send("You can't edit published bid")
        return
    
    if currency not in currencies.keys():
        await ctx.send(f'Invalid currency, available currencies: {" ".join([currency for currency in currencies])}')
        return
    
    bids.find_one_and_update({'id': id}, {'$set': {'currency': currency}})
    await ctx.send(f'Successfully set currency to **"{currency}"**')
    await ctx.message.delete()

@setcurrency.error
async def setcurrency_error(ctx, error):
    await ctx.send(f'Missing argument\n.changecurrency ID [{" ".join([currency for currency in currencies])}]')
        
####  
        
@client.command()
async def setendtime(ctx, id: int, *, date):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send('Nie posiadasz odpowiednich uprawnień')
        return

    response = check_bid_permissions(ctx, id)

    if isinstance(response, str):
        await ctx.send(response)
        return
        
    await ctx.message.delete()

    bids = database.bids
    bid = bids.find_one({'id': id})

    if bid is None:
        await ctx.send('There is no bid with given ID in the database')
        return
    
    if bid['published']:
        await ctx.send("You can't edit published bid")
        return
    
    date_time_obj = datetime.datetime.strptime(date, '%d.%m.%Y %H:%M')
    end_timestamp = datetime.datetime.timestamp(date_time_obj)
    # + (12*60*60)
    if end_timestamp < datetime.datetime.now().timestamp():
        await ctx.send('Give the date at least 12 hours in advance')
        return
    
    bids.find_one_and_update({'id': id}, {'$set': {'end_time': end_timestamp}})
    message_id = bid['message_id']
    config = database.config
    auction_setting_channel_id = config.find_one({"name":"bid_creation_channel"})['value']
    auction_message = await client.get_channel(auction_setting_channel_id).fetch_message(message_id)
    auction_embed = auction_message.embeds[0]
    auction_embed.set_field_at(3, name = 'Ends at', value = f'``{date}``', inline=False)
    await auction_message.edit(embed=auction_embed)
    
@setendtime.error
async def setendtime_error(ctx, error):
    await ctx.send(f'Missing argument\n.changeendtime ID day.month.year hour:minute')
        
####  
        
@client.command()
async def seebids(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return
    
    bids = database.bids
    if len([bid for bid in bids.find()]) == 0:
        await ctx.send('There are currently no bids in the database')
        return
    
    for bid in bids.find():
        
        title = bid['title']
        description = bid['description']
        image_url = bid['image_url']
        id = bid['id']
        end_timestamp = bid['end_time']
        minimal_price = bid['minimal_price']
        current_price = bid['current_price']
        currency = bid['currency']
        
        if None in [description, image_url, id, end_timestamp, minimal_price, current_price, currency]:
            await ctx.send(f'Creation of bid "{title} - ID: {id}" has not been completed, so it has been skipped')
            continue
        
        end_time = datetime.datetime.fromtimestamp(end_timestamp).strftime('%d.%m.%Y %H:%M')
        
        embed = discord.Embed(title=title, description=f"{description}\n\nBid by clicking ☑ under this message")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name = 'Current price', value = f'```fix\n{current_price} {currency}```\n1 bid costs {currencies[currency]} {currency}', inline=False)
        embed.add_field(name="Minimal Price", value=f'{minimal_price} {currency}', inline=False)
        embed.add_field(name="Last bids", value="None", inline=False)  
        embed.add_field(name="Ends at", value=end_time, inline=False)  
        embed.add_field(name="id", value=id, inline=False)  
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)
            
####  
        
@client.command()
async def publishbid(ctx, id: int, channel: discord.TextChannel):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    response = check_bid_permissions(ctx, id)

    if isinstance(response, str):
        await ctx.send(response)
        return
    
    config = database.config
    result = config.find_one({'name': 'auction_channels'})
    channels = result['value']
    if not channel.id in channels:
        await ctx.send('Aukcje można publikować tylko na kanale do tego przeznaczonym')
        return
    
    bids = database.bids
    bid = database.bids.find_one({'id': id})
    
    published = bid['published']
    if published:
        await ctx.send('Aukcja już została opublikowana')
        return
        
    title = bid['title']
    description = bid['description']
    image_url = bid['image_url']
    end_timestamp = bid['end_time']
    minimal_price = bid['minimal_price']
    current_price = bid['current_price']
    currency = bid['currency']
    
    if None in [description, image_url, id, end_timestamp, minimal_price, current_price, currency]:
        await ctx.send(f'Aukcja "{title} - id: {id}" nie została ukończona')
        return
    
    end_time = datetime.datetime.fromtimestamp(end_timestamp).strftime('%d.%m.%Y %H:%M')
    
    embed = discord.Embed(title=title, description=f"{description}\n\nBid by clicking ☑ under this message", timestamp=ctx.message.created_at)
    embed.set_thumbnail(url=ctx.guild.icon_url)
    embed.add_field(name = 'Current price', value = f'```fix\n{current_price} {currency}```\n\n1 bid costs {currencies[currency]} {currency}', inline=False)
    
    if current_price >= minimal_price:
        embed.add_field(name="Minimal Price", value=f'{minimal_price} {currency}', inline=False)
    else:
        embed.add_field(name="Minimal Price", value=f'has not been reached', inline=False)
        
    embed.add_field(name="Last bids", value="None", inline=False)  
    embed.add_field(name="Ends at", value=end_time, inline=False)  
    embed.set_image(url=image_url)
    embed.set_footer(text='Click emoji under this message to place your bid!')
    message = await channel.send(content='@everyone',embed=embed)
    
    bids.find_one_and_update(
        {
        'id': id
        },
            {
            '$set': {
                'last_bids': [],
                'published_id': message.id,
                'winer': None,
                'published': True,
                'published_channel_id': channel.id,
                'last_bids_ids': []
                }
            }
        )
    
    await message.add_reaction('☑')
    try:
        await client.wait_for('reaction_add', timeout=5.0)
    except asyncio.TimeoutError:
        await message.add_reaction('☑')
        
    await ctx.send('The bid has been published successfully')
      
@publishbid.error
async def publishbid_error(ctx, error):
    await ctx.send(f'Missing argument\n.publishbid ID #channel')
        
####  
        
@client.command()
async def changenotif(ctx):
    user_mentions = database.user_mentions
    result = user_mentions.find_one({'id': ctx.author.id})
    if result is None:
        user_mentions.insert_one({'id': ctx.author.id, 'value': False})
        await ctx.send('Your notifications are now turned off')
        return
    else:
        if result['value']:
            user_mentions.find_one_and_update({'id': ctx.author.id}, {'$set': {'value': False}})
            await ctx.send('Your notifications are now turned off')
        if not result['value']:
            user_mentions.find_one_and_update({'id': ctx.author.id}, {'$set': {'value': True}})
            await ctx.send('Your notifications are now turned on')
        
@client.command()
async def addbidingchan(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    config = database.config
    result = config.find_one({'name': 'auction_channels'})
    channels = result['value']
    channels.append(ctx.channel.id)
    config.find_one_and_update(
        {
            'name': 'auction_channels'
        },
        {
            '$set': {
                'value': channels
            }
        }
    )
    await ctx.send(f'Successfully added {ctx.channel.name} to the database')

@client.command()
async def rembidingchan(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    config = database.config
    result = config.find_one({'name': 'auction_channels'})
    channels = result['value']
    channels.remove(ctx.channel.id)
    config.find_one_and_update(
        {
            'name': 'auction_channels'
        },
        {
            '$set': {
                'value': channels
            }
        }
    )
    await ctx.send(f'Successfully deleted {ctx.channel.name} from the database')

@client.command()
async def seebidingchan(ctx):
    permissions = check_permissions(ctx)
        
    if not permissions:
        await ctx.send("You don't have permissions")
        return

    config = database.config
    channels = config.find_one({'name': 'auction_channels'})
    if len(channels['value']) == 0:
        await ctx.send('There is currently no auction channel')
        return
    
    channels_mentions = '\n'.join([client.get_channel(id).mention for id in channels['value']])
    
    embed = discord.Embed(title='Biding channels', color=ctx.author.color, timestasmp=ctx.message.created_at)
    embed.add_field(name='List', value=channels_mentions)
    
    await ctx.send(embed=embed)
    
    
##################################################### events


@client.event
async def on_message(msg):
    
    if msg.guild is None or msg.author == client.user:
        return
    
    pl_signs = {
        'ą': 'a',
        'ć': 'c',
        'ę': 'e',
        'ł': 'l',
        'ń': 'n',
        'ó': 'o',
        'ś': 's',
        'ź': 'z',
        'ż': 'z'
        }

    slurs = database.slurs.find()
    content_no_pl = msg.content.lower().replace(' ', '')
    content_no_pl = list(content_no_pl)
    for i, sign in enumerate(content_no_pl):
        if sign in pl_signs.keys():
            content_no_pl[i] = pl_signs[sign]
    content_no_pl = ''.join(content_no_pl)
        
    permissions = False
    config = database.config
    mod_roles = config.find({'type': 'mod_role'})
    mod_roles = [msg.guild.get_role(id['value']) for id in mod_roles]
    if [role for role in msg.author.roles if role in mod_roles] or msg.author.guild_permissions.administrator:
        permissions = True
    
    for slur in slurs:
        if ('.removeslur' in msg.content or '.addslur' in msg.content) and permissions:
            break
        if slur['value'] in content_no_pl:
            await msg.delete()
            break
        
    await client.process_commands(msg)
        
@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return
    
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    guild = channel.guild
    member = channel.guild.get_member(payload.user_id)  
    
    config = database.config
    verification_channel_id = config.find_one({'name': 'verification'})['channel_id']
    verification_message_id = config.find_one({'name': 'verification'})['message_id']
    verification_role_id =  config.find_one({'name': 'verification'})['role_id']
    
    if message.id == verification_message_id and channel.id == verification_channel_id:
        await member.add_roles(guild.get_role(verification_role_id))
        
    bids = database.bids
    bid = bids.find_one({"published_id": message.id})
    if bid is not None and payload.emoji.name == '☑':
        
        last_bids_ids = bid['last_bids_ids']
        if len(last_bids_ids) > 0:
            if last_bids_ids[-1] == member.id:
                await member.send(f"{member.mention} You can't bid two times in a row")
                await message.remove_reaction('☑', member)
                return
            else:
                user_mentions = database.user_mentions
                user_mentions_result = user_mentions.find_one({'id': last_bids_ids[-1]})
                if user_mentions_result is not None:
                    embed = discord.Embed(title=f'Notification', timestamp=datetime.datetime.utcnow())
                    embed.add_field(name= f'VVV', value=f"```diff\n- You've been overbid by {member.name}```[Link to auction]({message.jump_url})")
                    if user_mentions_result['value']:
                        await client.get_user(last_bids_ids[-1]).send(embed=embed)
                elif user_mentions_result is None:
                    embed = discord.Embed(title=f'Notification', timestamp=datetime.datetime.utcnow())
                    embed.add_field(name= f'VVV', value=f"```diff\n- You've been overbid by {member.name}```[Link to auction]({message.jump_url})")
                    await client.get_user(last_bids_ids[-1]).send(embed=embed)

        currency = bid['currency']
        current_price = bid['current_price']
        minimal_price = bid['minimal_price']
        auction_embed = message.embeds[0]

        current_price += currencies[currency]
        auction_embed.set_field_at(0, name = 'Current Price', value = f'```fix\n{current_price} {currency}```\n1 bid costs {currencies[currency]} {currency}', inline=False)
        
        if current_price >= minimal_price:
            auction_embed.set_field_at(1, name = 'Minimal Price', value = f'Reached minimal price {minimal_price} {currency}', inline=False)
        
        last_bids = bid['last_bids']
        last_bids_formated = []
        if len(last_bids) >= 3: last_bids = last_bids[-2:]
        last_bids.append(f'{member.name} gave {current_price} {currency}')
        for bid_string in last_bids:
            last_bids_formated.append(f'```diff\n- {bid_string}```')
        
        last_bids_reversed = last_bids_formated[::-1]
        last_bids_reversed.insert(1, '\n')
        last_bids_reversed[0] = f'```diff\n+ {member.name} gave {current_price} {currency}```'
        last_bids_ids.append(member.id)
                
        auction_embed.set_field_at(2, name = 'Last Bids', value = ''.join(last_bids_reversed), inline=False)
        
        end_time = bid['end_time']
        if end_time - datetime.datetime.now().timestamp() < 30*60:
            end_time += 60
        
        bids.find_one_and_update(
            {
                "published_id": message.id
                },{
                '$set': {
                        'winer': member.id,
                        'current_price': current_price,
                        'last_bids': last_bids,
                        'last_bids_ids': last_bids_ids,
                        'end_time': end_time
                        }
                })
        
        auction_embed.set_field_at(3, name = 'Ends at', value = datetime.datetime.fromtimestamp(end_time).strftime('%d.%m.%Y %H:%M'), inline=False)
        
        await message.edit(embed=auction_embed)
        await message.remove_reaction('☑', member)

@client.event
async def on_member_remove(member):
    user_mentions = database.user_mentions
    user_mentions.find_one_and_delete({'id': member.id})
    
    
##################################################### loops

@tasks.loop(minutes=1)
async def loop_1m():
    bids = database.bids
    for bid in bids.find(): 
        if bid['published']:
            if bid['end_time'] <= datetime.datetime.now().timestamp():
                
                try:
                    winner = None
                    if bid['current_price'] >= bid['minimal_price']:
                        winner = bid['winer']

                    channel = client.get_channel(bid['published_channel_id'])
                    message = await channel.fetch_message(bid['published_id'])
                    auction_embed = message.embeds[0]
                    title = auction_embed.title
                    price = bid['current_price']
                    currency = bid['currency']
                    notification_channel = client.get_channel(database.config.find_one({'name': 'notification_channel'})['value'])

                    auction_embed.title = 'AUCTION ENDED'
                    await message.edit(embed=auction_embed)

                    if winner is not None:
                        winner = client.get_user(winner)
                        await winner.send(f"You won this auction:\n{title}\nIn 24 hours transfer {price} + 1,6 (transaction fee) {currency} on to this wallet:\n```fix\n{database.config.find_one({'name': 'wallet_adress'})['value']}```")
                        await notification_channel.send(f'Bid {title}, Ended reaching {price} {currency},\nThe winner: {winner.mention}')
                    else: 
                        await notification_channel.send(f'Bid {title}, Ended without reaching minimal price')

                    last_bids_ids = bid['last_bids_ids']
                    list_bids_ids_withouot_duplicates = list(set(last_bids_ids))

                    if winner is not None:
                        list_bids_ids_withouot_duplicates.remove(winner.id)

                    for id in list_bids_ids_withouot_duplicates:
                        user = client.get_user(id)
                        await user.send(f"You didn't won the auction {title}")

                    bids.find_one_and_delete({'id': bid['id']})
                except Exception as e:
                    config = database.config
                    bid_creation_channel_id = config.find_one({'name': 'bid_creation_channel'})['value']
                    bid_creation_channel = client.get_channel(bid_creation_channel_id)
                    await bid_creation_channel.send(content=e)                

@loop_1m.error
async def loop1merror(error):
    loop_1m.restart()
            
client.run(getenv('token'))
