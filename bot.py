import discord
from discord.ext import commands
from discord import ui
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration - replace these with your actual values
BOT_TOKEN = "MTM4MzE2MjY2NjAxMjUxMjMwNg.GVEkrw.9TtcEXbzrue_Nfg4euLlFJvDT9laVM30R2v6Q4"
TICKET_CHANNEL_ID = 1383174379386572903
STAFF_ROLE_ID = 1382414903712808960
TICKET_CATEGORY_ID = 1382417269514305808
OWNER_IDS = [1263429383473987605, 1382054370455064636]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # Uncomment to send ticket message on startup
    # await send_ticket_message()

async def send_ticket_message():
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Ticket System",
            description="Please select an option from the menu below to create a ticket.",
            color=discord.Color.blue()
        )
        view = TicketMenuView()
        await channel.send(embed=embed, view=view)

class TicketMenuView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @ui.select(
        placeholder="Select a ticket type...",
        options=[
            discord.SelectOption(label="General Support", value="general", emoji="❓"),
            discord.SelectOption(label="Blacklist Request", value="blacklist", emoji="🚫"),
            discord.SelectOption(label="Report a User", value="report", emoji="⚠️"),
            discord.SelectOption(label="Other Issue", value="other", emoji="📝")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: ui.Select):
        value = select.values[0]
        
        if value == "blacklist":
            modal = BlacklistRequestModal()
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message(f"You selected {value}. Creating ticket...", ephemeral=True)
            await create_ticket(interaction, value)

async def create_ticket(interaction, ticket_type):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
    staff_role = guild.get_role(STAFF_ROLE_ID)
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    ticket_channel = await category.create_text_channel(
        name=f"{ticket_type}-{interaction.user.name}",
        overwrites=overwrites
    )
    
    embed = discord.Embed(
        title=f"{ticket_type.capitalize()} Ticket",
        description=f"Hello {interaction.user.mention},\n\nA staff member will be with you shortly.\n\nPlease explain your issue here.",
        color=discord.Color.green()
    )
    
    # Add close button to the ticket
    close_view = CloseTicketView()
    await ticket_channel.send(
        content=f"{interaction.user.mention} {staff_role.mention}",
        embed=embed,
        view=close_view
    )
    
    await interaction.followup.send(f"Ticket created: {ticket_channel.mention}", ephemeral=True)

class CloseTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        # Check if user is staff or ticket creator
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles and interaction.user != interaction.channel.topic:
            await interaction.response.send_message("You don't have permission to close this ticket.", ephemeral=True)
            return
        
        # Send confirmation message
        embed = discord.Embed(
            title="Ticket Closed",
            description="This ticket will be deleted in 10 seconds.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        
        # Delete the channel after delay
        await asyncio.sleep(10)
        await interaction.channel.delete()

class BlacklistRequestModal(ui.Modal, title="Blacklist Request"):
    def __init__(self):
        super().__init__(timeout=None)
        
    server_invite = ui.TextInput(
        label="Server/User Info",
        placeholder="Server invite or UserID + Username",
        style=discord.TextStyle.short,
        required=True,
        max_length=45  # Added max_length to prevent the error
    )
    
    proof = ui.TextInput(
        label="Proof Link",
        placeholder="Imgur/Gyazo link",
        style=discord.TextStyle.short,
        required=True,
        max_length=45
    )
    
    member_count = ui.TextInput(
        label="Member Count (if server)",
        placeholder="Leave blank for users",
        style=discord.TextStyle.short,
        required=False,
        max_length=45
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_channel = await category.create_text_channel(
            name=f"blacklist-{interaction.user.name}",
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title="Blacklist Request",
            description=f"Submitted by {interaction.user.mention}",
            color=discord.Color.red()
        )
        
        embed.add_field(name="Server/User", value=self.server_invite, inline=False)
        embed.add_field(name="Proof", value=self.proof, inline=False)
        if self.member_count.value:
            embed.add_field(name="Member Count", value=self.member_count, inline=False)
        
        embed.set_footer(text="Please verify this request by DMing an owner/founder")
        
        message_content = f"{interaction.user.mention} {staff_role.mention}"
        
        try:
            member_count = int(self.member_count.value) if self.member_count.value else 0
            if member_count >= 1000:
                message_content += " @everyone"
        except ValueError:
            pass
        
        close_view = CloseTicketView()
        await ticket_channel.send(content=message_content, embed=embed, view=close_view)
        
        embed_user = discord.Embed(
            title="Blacklist Request Submitted",
            description=f"Your request has been submitted in {ticket_channel.mention}.\n\n**IMPORTANT:** You must verify this request by DMing one of the owners/founders.",
            color=discord.Color.orange()
        )
        
        owners_mention = ", ".join([f"<@{owner_id}>" for owner_id in OWNER_IDS])
        embed_user.add_field(name="Owners/Founders", value=owners_mention, inline=False)
        
        await interaction.response.send_message(embed=embed_user, ephemeral=True)

@bot.command()
@commands.has_role(STAFF_ROLE_ID)
async def setup(ctx):
    await send_ticket_message()
    await ctx.send("Ticket system setup complete!", delete_after=5)

bot.run(BOT_TOKEN)