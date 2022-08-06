from disnake import Embed


def add_content_to_embed(embed: Embed, content: str):
    embed.add_field('Content', value=content[:1020], inline=False)
    if len(content) > 1020:
        embed.add_field('Content2', content[1021:2040], inline=False)
    if len(content) > 2040:
        embed.add_field('Content3', content[2041:3060], inline=False)
    if len(content) > 3060:
        embed.add_field('Content4', content[3061:], inline=False)
