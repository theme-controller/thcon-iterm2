#!/usr/bin/env python3
import asyncio
import json
import iterm2
import sys
import os

# If thcon was installed someplace non-standard, feel free to change
# this to the path to that file.
__THCON_BIN = "~/bin/thcon"

__DEBUG = False

async def try_set_profile(connection, app, payload):
    """
    Attempts to find an iTerm2 profile matching the name included in the payload,
    then uses that profile to change all sessions in all tabs in all windows and
    sets the default profile for any sessions made later.

    :param iterm2.Connection connection: a websocket connection to the iTerm2 backend
    :param iterm2.App app: a reference to the currently-running iTerm2 application
    :param dict payload: a dictionary matching ./thcon.schema.json
    """
    if not "profile" in payload:
        print("WARNING: Couldn't find 'profile' property in payload: ", payload)
        return

    profiles = await iterm2.PartialProfile.async_query(connection)
    matching_profiles = [ p for p in profiles if p.name == payload["profile"] ]
    if not matching_profiles:
        print("WARNING: Couldn't find profile named '{}'".format(payload["profile"]))
        return

    profile = await matching_profiles[0].async_get_full_profile()
    if profile is None:
        print("ERROR: Couldn't get full profile named '{}'".format(payload["profile"]))
        return

    futures = []
    # gather all sessions...
    for window in app.windows:
        for tab in window.tabs:
            for session in tab.sessions:
                futures.append(session.async_set_profile(profile))
    # ...then change their profiles concurrently
    await asyncio.gather(*futures)

    # ensure new sessions use the same profile as existing ones
    await profile.async_make_default()

async def main(connection):
    app = await iterm2.async_get_app(connection)

    argv = [__THCON_BIN, "listen", "iterm2"]
    if __DEBUG:
        argv.append("--verbose")

    stderr_pipe = asyncio.subprocess.STDOUT if __DEBUG else None
    proc = await asyncio.create_subprocess_shell(" ".join(argv),
            stdout=asyncio.subprocess.PIPE,
            stderr=stderr_pipe,
    )

    while True:
        line = await proc.stdout.readline()
        if line.strip():
            try:
                payload = json.loads(line)
                await try_set_profile(connection, app, payload)
            except json.JSONDecodeError:
                print("[dbg]", line.strip().decode(sys.stdout.encoding))
        else:
            break

iterm2.run_forever(main)
