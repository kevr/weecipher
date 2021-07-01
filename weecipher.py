#!/usr/bin/env python3
# Project: weecipher
# Description: Cipher communication between specific hostmasks.
#
# This script depends on the langdetect Python package
#
#
# Author: Kevin Morris <kevr@0cost.org>
# License: MIT
#
import os
import random
import re
import sys
import weechat
import json

usage = "usage: /weecipher (help|add nick|rm nick)"

script_name = "weecipher"
script_desc = "Establish cipher communication between friends."
script_author = "Kevin Morris <kevr@0cost.org>"
script_version = "1.0.0"
script_license = "MIT"


def increment_with_offset(c: str, increment: int, offset: int) -> str:
    """ Caesar shift cipher. """
    return chr(((ord(c) - offset + increment) % 26) + offset)


def transform(string: str, increment: int) -> str:
    chars = []
    for ch in string:
        if ch.isalpha():
            if ch.isupper():
                chars.append(increment_with_offset(ch, increment, 65))
            else:
                chars.append(increment_with_offset(ch, increment, 97))
        else:
            chars.append(ch)
    return ''.join(chars)


def encode(string: str, key: int) -> str:
    key = abs(key)
    return transform(string, key)


def decode(string: str, key: int) -> str:
    key = -abs(key)
    parts = string.split(' ')
    string = " ".join(parts[1:])
    return " ".join([parts[0], transform(string, key)])


def eprint(buf: str, message: str) -> int:
    weechat.prnt(buf, f"weecipher: {message}")
    return weechat.WEECHAT_RC_ERROR


class Action:
    def __init__(self, pbuffer: str):
        self.pbuffer = pbuffer

    def add(self, args: list) -> int:
        if len(args) != 1:
            return eprint(self.pbuffer, usage)

        nick = args[0]
        config_key = f"{nick}.key"
        key = weechat.config_get_plugin(config_key)
        if not key:
            key = str(random.randint(16, 65535))
            weechat.config_set_plugin(config_key, key)

        buf = weechat.buffer_get_string(
            weechat.current_buffer(), "name").split(".")[0]
        weechat.prnt(self.pbuffer, f"Negotiating with {nick}...")
        weechat.hook_signal_send(
            "irc_input_send",
            weechat.WEECHAT_HOOK_SIGNAL_STRING,
            f"{buf};;priority_low;;/notice {nick} WEECIPHER-NEGOTIATE {key}")
        return weechat.WEECHAT_RC_OK

    def rm(self, args: list) -> int:
        if len(args) != 1:
            return eprint(self.pbuffer, usage)

        nick = args[0]
        config_key = f"{nick}.key"
        key = weechat.config_get_plugin(config_key)
        if not key:
            return eprint(self.pbuffer, "nickname does not exist")
        weechat.config_unset_plugin(config_key)
        weechat.hook_signal_send(
            "irc_input_send",
            weechat.WEECHAT_HOOK_SIGNAL_STRING,
            f"{buf};;priority_low;;/notice {nick} WEECIPHER-KILL")
        return weechat.WEECHAT_RC_OK

    def help(self, args: list):
        weechat.prnt(self.pbuffer, f"""{usage}

Create a weak alpha encryption to communicate with friends.

To add a friend for encrypted communication:

    /weecipher add friend_nick

To remove a friend and delete shared keys:

    /weecipher rm friend_nick

After adding a nick and exchanging a shared secret key, users
can begin speaking with their added friends using /encrypt:

    /encrypt friend_nick: Hey dude, how are you doing?

It is important to lead the message with your friend's nick,
otherwise we cannot know which secret key to decrypt with.

All shared keys are stored in the plugin's configuration
under plugins.var.python.weecipher.<nick>.key. When
/weecipher rm is used on a friend, their key is deleted
from your configuration.

Secret key exchange occurs over direct nickname NOTICE
on the server where /add is executed or the notice is
received.
""")
        return weechat.WEECHAT_RC_OK


def notice_cb(data, pbuffer, date, tags,
              displayed, highlight, prefix, message):
    parts = message.split(" ")
    if len(parts) < 4:
        return weechat.WEECHAT_RC_OK

    nick = parts[0]
    parts = parts[2:]

    metacmd = parts[0]

    negotiate = 1
    kill = 2

    cmds = {
        "WEECIPHER-NEGOTIATE": negotiate,
        "WEECIPHER-KILL": kill
    }

    if metacmd not in cmds:
        return weechat.WEECHAT_RC_OK

    meta_id = cmds.get(metacmd)
    if meta_id == negotiate:
        key = parts[1]
        cfg = weechat.config_get_plugin(f"{nick}.key")
        buf = weechat.buffer_get_string(
            weechat.current_buffer(), "name").split(".")[1]
        weechat.config_set_plugin(f"{nick}.key", key)
        weechat.prnt(buf,
                     f"Received negotiation from {nick}, "
                     "you can now begin encrypting toward them!")
    elif meta_id == kill:
        cfg = weechat.config_get_plugin(f"{nick}.key")
        if cfg:
            weechat.config_unset_plugin(f"{nick}.key")

    return weechat.WEECHAT_RC_OK


def command_cb(data, pbuffer, args):
    args = args.split(' ')
    if len(args) < 1:
        return eprint(pbuffer, usage)

    command = args[0]
    actions = Action(pbuffer)
    action = getattr(actions, command)
    if not action:
        return eprint(pbuffer, "invalid command")

    return action(args[1:])


def encrypt_cb(data, pbuffer, args):
    if not args:
        return weechat.WEECHAT_RC_OK

    args = args.strip().split(" ")
    first = args[0]
    first = first.rstrip(":-_^&;.,")

    key = weechat.config_get_plugin(f"{first}.key")
    if not key:
        # No user specified. Not encrypting; what key to use?
        weechat.prnt(pbuffer, f"No key found for nickname '{nick}', skipping.")
        return weechat.WEECHAT_RC_OK

    key = int(key)
    encoded = encode(" ".join(args[1:]), key)
    output = " ".join([args[0], encoded])

    # Add encryption signal to the beginning of the message (unicode bullet).
    output = (b"\xe2\x80\xa2".decode()) + " " + output

    serv, buf = weechat.buffer_get_string(pbuffer, "name").split(".")
    weechat.hook_signal_send("irc_input_send",
                             weechat.WEECHAT_HOOK_SIGNAL_STRING,
                             f"{serv};;priority_high;;/msg {buf} {output}")

    return weechat.WEECHAT_RC_OK


def message_cb(data, pbuffer, date, tags,
               displayed, highlight, prefix, message):
    # If the first character is not our encryption signal, pass.
    if message[0].encode() != b"\xe2\x80\xa2":
        return weechat.WEECHAT_RC_OK
    message = message[2:]  # Otherwise, truncate the signal off.

    key = weechat.config_get_plugin(f"{prefix}.key")
    if not key:
        return weechat.WEECHAT_RC_OK

    try:
        decoded = decode(message, int(key))
    except ValueError:  # Unable to decode. Not encrypted?
        return weechat.WEECHAT_RC_OK

    # Print out the decoded message with a [ Decoded ] prefix.
    weechat.prnt(pbuffer, f"[ Decoded ]: {decoded}")
    return weechat.WEECHAT_RC_OK


if __name__ == "__main__":
    weechat.register(script_name, script_author, script_version,
                     script_license, script_desc, "", "")
    desc = "Create an encryption session with another IRC nickname."
    weechat.hook_command("weecipher", desc,
                         "[add|rm [nick]]",
                         f"{usage}\n"
                         "add: negotiate a new key with a nickname\n"
                         "rm: remove a nickname's key\n",
                         "", ""
                         "command_cb", "")
    weechat.hook_command("encrypt",
                         "Send an encrypted message to nick "
                         "(tagging nick required)",
                         "nick: phrase to encrypt",
                         f"usage: /encrypt nick: Yo dawg!",
                         "", ""
                         "encrypt_cb", "")
    weechat.hook_print("", "", "", 1, "notice_cb", "")
    weechat.hook_print("", "", "", 1, "message_cb", "")
