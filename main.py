import discord
from discord.ext import commands
from discord.ui import Button, View
import os
from dotenv import load_dotenv
import datetime
from flask import Flask
import threading

load_dotenv()

TOKEN = os.getenv("TOKEN")

TICKET_CHANNEL_ID = 1520433917692477490
TICKET_CATEGORY_ID = 1520734487107866624
LOG_CHANNEL_ID = 1520428694152155166
STAFF_ROLE_ID = 1373912127362039869

THUMBNAIL = "https://cdn.discordapp.com/attachments/1519426746041110791/1520049279408799816/unfortune_pp.jpg?ex=6a411935&is=6a3fc7b5&hm=40aa141983c744859563dee20a2f4cf3a909f69c615ad597ec7f4a5b1b83a68e"
BANNER = "https://cdn.discordapp.com/attachments/1519426746041110791/1520049279773708429/unfortune_banner.webp?ex=6a411935&is=6a3fc7b5&hm=371e186a5325dda82c27bac1a22e14de376abb65d825a0e651d6670be746cba3"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Render Port Hatasını Çözmek İçin Web Sunucusu Kurulumu
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif ve calisiyor!"

def run_web_server():
    # Render'ın atadığı portu alıyoruz, bulamazsa varsayılan 8080 portunu açıyoruz
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket Oluştur", style=discord.ButtonStyle.primary, custom_id="ticket_create")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):

        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        for ch in category.text_channels:
            if ch.topic == str(interaction.user.id):
                await interaction.response.send_message("Zaten açık bir ticketın var.", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            topic=str(interaction.user.id)
        )

        embed = discord.Embed(
            title="UNFORTUNE Ticket",
            description=f"{interaction.user.mention}\nTicketınız oluşturuldu.\nYetkililer en kısa sürede ilgilenecektir.",
            color=0x2b2d31
        )

        await channel.send(content=f"<@&{STAFF_ROLE_ID}>", embed=embed, view=CloseView())
        await interaction.response.send_message(f"Ticket açıldı: {channel.mention}", ephemeral=True)


class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Ticket Kapat", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction, button: Button):

        if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            await interaction.response.send_message("Bu işlemi sadece yetkililer yapabilir.", ephemeral=True)
            return

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)

        # DeprecationWarning uyarısı veren utcnow() kısmı güncellendi
        embed = discord.Embed(
            title="Ticket Kapatıldı",
            description=f"Kapatan: {interaction.user.mention}\nKanal: {interaction.channel.name}",
            color=0xff0000,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )

        await log.send(embed=embed)
        await interaction.channel.delete()


@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseView())
    print(f"{bot.user} aktif")


@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):

    embed = discord.Embed(
        title="UNFORTUNE",
        description=(
            "## Unfortune Ticket Botu Hakkında\n"
            "Aşağıdaki butona basarak ticket oluşturabilirsiniz.\n\n"
            "## Ekip Bilgisi\n"
            "Sunucunu Kurallarını Okumuş Varsayılacaksınız"
        ),
        color=0x5865F2
    )

    embed.set_thumbnail(url=THUMBNAIL)
    embed.set_image(url=BANNER)

    await ctx.send(embed=embed, view=TicketView())


if __name__ == "__main__":
    # Web sunucusunu bot başlamadan hemen önce ayrı bir thread olarak çalıştırıyoruz
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.run(TOKEN)