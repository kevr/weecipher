# weecipher

A weechat script which enables users to communicate in ciphertext.


	testuser | • kevr: Wtaad, ltardbt id lttrxewtg!
	[ Decoded ]: kevr: Hello, welcome to weecipher!

	/encrypt testuser: Hello back to you, good sir!
	my_nick  | • testuser: Wtaad qprz id ndj, vdds hxg!

## Nickname-based Sessions

`weecipher` operates by encrypting and decrypting plaintext messages with a
shared secret key established during the `add` phase.

Both participants must have `weecipher` loaded, then either one can:

	/weecipher add your_friend

This act triggers your client to generate a random integer, store it locally
as the key it knows about for *your_friend*, then send that key over to
*your_friend* via `NOTICE` on the server where `/weecipher add` was invoked.

This will remain your shared key for the remainder of your conversations.

To remove a key and send a request your key be removed:

	/weecipher rm your_friend

This does the reverse.

## Communicating

After a session has been setup and a shared key is stored, users can
begin encrypting messages to eachother with the `/encrypt` command.

	/encrypt your_friend: Hello, friend! This is my message!

You **must** tag *your_friend* here; `weecipher` must know which friend you
are communicating with in order to encrypt with the proper key.

When your friend sends you an encrypted message, your client will automatically
attempt to decrypt it and print a following note:

	[ Decoded ]: your_nick: Your friend's cool message.

## Encryption

This script uses an overwhelmingly weak Caesar shift cipher to encrypt and
decrypt plaintext. This script is **not** meant to be used as a solution to
security or assumed to protect you from prying eyes.

It is merely a fun script for friends.

## Installation

Install it just like any other weechat script.

	~/weecipher $ install -m755 weecipher.py ~/.weechat/python
	~/weecipher $ cd ~/.weechat/python
	~/.weechat/python $ ln -s ../weecipher.py autoload

Once you've got the script installed, you can load or reload the script in Weechat.

	/script [re]load weecipher.py
	/weecipher help

## License

This project operates under the MIT General License, verbosely at [LICENSE](LICENSE).

## Authors

| Name         | Email          |
|--------------|----------------|
| Kevin Morris | kevr@0cost.org |

### Contact

Come chat with me on IRC; I use the nickname `kevr` on `irc.libera.chat` and often
hang `#0cost`, a personal organization channel of mine.