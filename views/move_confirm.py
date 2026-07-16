import discord

from core import storage

class MoveConfirmView(discord.ui.View):

    def __init__(self, new_channel_id):

        super().__init__(timeout=60)

        self.new_channel_id = new_channel_id

    @discord.ui.button(
        label="확인 (이동하기)",
        style=discord.ButtonStyle.green,
        emoji="✅"
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        storage.target_channel_id = self.new_channel_id

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            "⚙️ 채널 이동 완료!"
        )

    @discord.ui.button(
        label="취소",
        style=discord.ButtonStyle.red,
        emoji="❌"
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            "❌ 채널 이동 취소"
        )
