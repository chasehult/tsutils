import asyncio
import re


async def doubleup(ctx, message):
    """Edit the last message to x2 or more if it's being repeated"""
    lmessage = await ctx.history().__anext__()
    fullmatch = re.escape(message) + r"(?: x(\d+))?"
    match = re.match(fullmatch, lmessage.content)
    if match and lmessage.author == ctx.bot.user:
        n = match.group(1) or "1"
        await lmessage.edit(content=message + " x" + str(int(n) + 1))
    else:
        await ctx.send(message)


async def confirm_message(ctx, text, yemoji="✅", nemoji="❌", timeout=10):
    msg = await ctx.send(text)
    await msg.add_reaction(yemoji)
    await msg.add_reaction(nemoji)

    def check(reaction, user):
        return (str(reaction.emoji) in [yemoji, nemoji]
                and user.id == ctx.author.id
                and reaction.message.id == msg.id)

    ret = False
    try:
        r, u = await ctx.bot.wait_for('reaction_add', check=check, timeout=timeout)
        if r.emoji == yemoji:
            ret = True
    except asyncio.TimeoutError:
        ret = None

    await msg.delete()
    return ret


async def await_and_remove(bot, react_msg, listen_user, delete_msgs=None, emoji="❌", timeout=15):
    try:
        await react_msg.add_reaction(emoji)
    except Exception as e:
        # failed to add reaction, ignore
        return

    def check(payload):
        return str(payload.emoji.name) == emoji and \
               payload.user_id == listen_user.id and \
               payload.message_id == react_msg.id

    try:
        p = await bot.wait_for('add_reaction', check=check, timeout=timeout)
    except asyncio.TimeoutError:
        # Expected after {timeout} seconds
        p = None

    if p is None:
        try:
            await react_msg.remove_reaction(emoji, react_msg.guild.me)
        except Exception as e:
            # failed to remove reaction, ignore
            return
    else:
        msgs = delete_msgs or [react_msg]
        for m in msgs:
            await m.delete_message()


def make_non_gatekeeping_check(condition, failmessage):
    def non_gatekeep_check(**kwargs):
        def decorator(command):
            @command.before_invoke
            async def hook(instance, ctx):
                if not condition(ctx, **kwargs):
                    await ctx.send(failmessage.format(ctx))
                    raise discord.ext.commands.CheckFailure()

            return command

        return decorator

    return non_gatekeep_check