#!/usr/bin/env python3
import asyncio
import json
import iterm2
import time
import sys

__DEBUG = True

async def try_set_profile(connection, app, payload):
    if not "profile" in payload:
        print("Couldn't find 'profile' property in payload: ", payload)
        return

    profiles = await iterm2.PartialProfile.async_query(connection)
    matching_profiles = [ p for p in profiles if p.name == payload["profile"] ]
    if not matching_profiles:
        return

    profile = await matching_profiles[0].async_get_full_profile()
    if profile is None:
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

    argv = ["/Users/sean/src/thcon/target/debug/thcon-listen", "iterm2"]
    if __DEBUG:
        argv.append("--verbose")

    stderr_pipe = asyncio.subprocess.STDOUT if __DEBUG else None
    proc = await asyncio.create_subprocess_exec(*argv,
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
