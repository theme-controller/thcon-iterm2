#!/usr/bin/env python3
import asyncio
import json
import os
from pathlib import Path
import signal
import iterm2

__DEBUG = True

pipe_dir = Path(Path.home(), Path(".local/share/thcon/iterm2"))
pipe_dir.mkdir(parents=True, exist_ok=True)
pipe_path = Path(pipe_dir, str(os.getpid()))
os.mkfifo(pipe_path, mode=0o700)

on_exit = lambda sig, stack: pipe_path.unlink(missing_ok=True)
signal.signal(signal.SIGTERM, on_exit)
signal.signal(signal.SIGHUP, on_exit)

async def try_set_profile(connection, app, payload):
    if not "profile" in payload:
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

    while True:
        try:
            # block until pipe is readable
            with open(pipe_path, mode="r", encoding="utf8") as pipe:
                for line in pipe:
                    if __DEBUG:
                        print("received line from pipe: ", line.strip())
                    payload = json.loads(line)
                    if __DEBUG:
                        print("as json: ", payload)
                    await try_set_profile(connection, app, payload)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

iterm2.run_forever(main)
