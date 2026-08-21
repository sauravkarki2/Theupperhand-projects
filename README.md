# Theupperhand-projects

## Blender MCP

This repo ships a `.mcp.json` that registers the [`blender-mcp`](https://github.com/ahujasid/blender-mcp)
server, so Claude Code picks it up automatically in any clone. Approve the server when
Claude Code prompts on first run in this project.

The server is only half of the setup: it talks to a **locally running Blender** over a
socket on `localhost:9876`, opened by a Blender addon. Both halves must be on the same
machine — a cloud/remote Claude Code session has no route to your desktop's Blender, so
the tools will fail on connect there no matter how the server is configured.

### Setup

1. Install [`uv`](https://docs.astral.sh/uv/) — `.mcp.json` launches the server via `uvx`.
2. Download `addon.py` from the [blender-mcp repo](https://github.com/ahujasid/blender-mcp).
3. In Blender: *Edit → Preferences → Add-ons → Install…*, pick `addon.py`, enable **Interface: Blender MCP**.
4. In the 3D viewport, press `N` to open the sidebar → **BlenderMCP** tab → **Connect**.
5. Start Claude Code in this directory. Verify with `claude mcp list` — `blender` should report `Connected`.

Keep Blender open with the addon connected for the whole session.

### Verifying the link

`claude mcp list` reporting `Connected` only means the server process started and
completed the MCP handshake — it does **not** mean Blender is reachable. To check the
actual link, ask Claude for the scene info, or probe the port directly:

```bash
python3 -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('localhost',9876)); print('Blender addon is listening')"
```

`ConnectionRefusedError` means Blender isn't running, the addon isn't enabled, or you
haven't hit **Connect** in the sidebar.

### What it exposes

Scene inspection (`get_scene_info`, `get_object_info`, `get_viewport_screenshot`),
arbitrary Python execution inside Blender (`execute_blender_code`), and asset sourcing
via Poly Haven, Sketchfab, and Hyper3D/Rodin text- and image-to-3D generation.

`execute_blender_code` runs unsandboxed Python in your Blender process. Review what it
runs, and save your work before letting it touch a file you care about.
