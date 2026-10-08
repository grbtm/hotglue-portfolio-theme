"""Run a real hotglue2 (the software behind hotglue.me) in Docker and fill it with test pages.

The tests run our head.html/body.html on pages rendered by hotglue itself, not on hand-made
copies, so they notice when hotglue's markup differs from what body.html expects. Pages are
created through hotglue's own JSON API (json.php), the same calls its editor makes.
"""

import json
import os
import re
import socket
import struct
import subprocess
import time
import urllib.error
import urllib.request
import uuid
import zlib
from base64 import b64encode
from pathlib import Path

HERE = Path(__file__).parent
IMAGE = "hotglue-portfolio-theme-php"
REPO = "https://github.com/k0a1a/hotglue2.git"
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "hotglue-portfolio-theme"
USER, PASSWORD = "admin", "test"
STARTUP_SECONDS = 5


def _run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kwargs).stdout.strip()


def build_image():
    _run("docker", "build", "-q", "-t", IMAGE, str(HERE))


def checkout(ref):
    """The commit `ref` (commit or branch) names, from a clone kept in the user's cache folder."""
    clone = CACHE / "hotglue2.git"
    if not clone.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        _run("git", "clone", "-q", "--bare", REPO, str(clone))
    else:
        _run("git", "-C", str(clone), "fetch", "-q", "origin", "+refs/heads/*:refs/heads/*")
    sha = _run("git", "-C", str(clone), "rev-parse", ref + "^{commit}")
    return clone, sha


def png(width, height, rgb):
    """A solid-colour PNG, made without image libraries."""
    row = b"\x00" + bytes(rgb) * width
    raw = zlib.compress(row * height)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")


class Hotglue:
    """One hotglue2 instance at one commit, served on http://127.0.0.1:<port>/."""

    def __init__(self, ref, workdir):
        """Unpack hotglue2 at `ref` into the empty directory `workdir` and configure it."""
        clone, self.sha = checkout(ref)
        self.root = Path(workdir)
        archive = subprocess.run(["git", "-C", str(clone), "archive", self.sha], check=True, capture_output=True)
        subprocess.run(["tar", "-x", "-C", str(self.root)], input=archive.stdout, check=True)
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.url = f"http://127.0.0.1:{self.port}/"
        config = (self.root / "user-config.inc.php-dist").read_text()
        config = config.replace("'changeme'", repr(PASSWORD))
        # The address the browser uses (hotglue would otherwise guess it from the request)
        config += f"\n@define('BASE_URL', '{self.url}');\n"
        (self.root / "user-config.inc.php").write_text(config)
        (self.root / "content").chmod(0o777)
        self.strips_slashes = bool(
            re.search(r"^\s*\$val = stripslashes", (self.root / "json.php").read_text(), re.MULTILINE)
        )
        self.is_ng = (self.root / "js" / "mobile-guided.js").exists()  # hotglue-ng's phone view
        self.container = "hotglue-test-" + uuid.uuid4().hex[:8]

    def start(self):
        _run(
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            self.container,
            "-p",
            f"127.0.0.1:{self.port}:8000",
            "-v",
            f"{self.root}:/app",
            IMAGE,
        )
        deadline = time.monotonic() + STARTUP_SECONDS
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(self.url + "css/main.css", timeout=1)
                return self
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                time.sleep(0.1)
        raise RuntimeError("hotglue did not start: " + _run("docker", "logs", self.container))

    def stop(self):
        subprocess.run(["docker", "rm", "-f", self.container], capture_output=True, check=False)  # may be gone already

    # ---------- hotglue's JSON API ----------

    def _encode(self, value):
        text = json.dumps(value)
        # master's json.php runs stripslashes() before decoding (ng-dev doesn't): double the
        # backslashes there so they survive it
        return text.replace("\\", "\\\\") if self.strips_slashes else text

    def call(self, method, files=None, **args):
        """POST to json.php. Every argument is JSON-encoded, as hotglue's editor does."""
        fields = {"method": method, **args}
        boundary = uuid.uuid4().hex
        body = b""
        for key, value in fields.items():
            body += (
                f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{self._encode(value)}\r\n'
            ).encode()
        for i, (filename, data, mime) in enumerate(files or []):
            body += (
                (
                    f'--{boundary}\r\nContent-Disposition: form-data; name="file{i}"; '
                    f'filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n'
                ).encode()
                + data
                + b"\r\n"
            )
        body += f"--{boundary}--\r\n".encode()
        request = urllib.request.Request(
            self.url + "json.php",
            data=body,
            headers={
                "Content-Type": "multipart/form-data; boundary=" + boundary,
                "Authorization": "Basic " + b64encode(f"{USER}:{PASSWORD}".encode()).decode(),
            },
        )
        reply = json.loads(urllib.request.urlopen(request, timeout=10).read())
        if reply.get("#error"):
            raise RuntimeError(f"{method}: {reply.get('#data')}")
        return reply.get("#data")

    def set_code(self, head, body):
        """What pasting into the boxes at /code and saving does."""
        self.call("user_code.set_code", page=False, head=head, body=body)

    def add_page(self, page):
        """Create a page (see pages.py) with all its objects; returns {key: object name}."""
        name = page.name + ".head"
        try:
            self.call("glue.create_page", page=name)
        except RuntimeError as error:
            if "already exists" not in str(error):  # the start page exists from the start
                raise
        if page.centered_width and self.is_ng:  # hotglue.me has no centered pages
            self.call("page.set_layout", page=name, mode="centered", width=page.centered_width)
        names = {}
        for obj in page.objects:
            attrs = {
                "object-left": f"{obj.left}px",
                "object-top": f"{obj.top}px",
                "object-width": f"{obj.width}px",
                "object-height": f"{obj.height}px",
                "object-zindex": "100",
            }
            if obj.kind == "image":
                html = self.call(
                    "glue.upload_files",
                    page=name,
                    files=[(f"{obj.key}.png", png(obj.width, obj.height, obj.colour), "image/png")],
                )[0]
                # the reply is the new object's HTML: <div id="<page>.head.<number>" ...>
                obj_name = html.split('id="', 1)[1].split('"', 1)[0]
                if obj.tiled:
                    attrs["image-background-repeat"] = "repeat"
            else:
                obj_name = self.call("glue.create_object", page=name)["name"]
                attrs.update({"type": "text", "module": "text", "content": obj.text})
            if obj.link:
                attrs["object-link"] = obj.link
            self.call("glue.update_object", name=obj_name, **attrs)
            names[obj.key] = obj_name
        return names
