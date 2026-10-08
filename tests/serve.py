"""Start the test site in a real hotglue and keep it running, to look at it in a browser.

    uv run tests/serve.py [master|dev|ng-dev]     (default: master; Ctrl+C stops it)

Log in to the editor as admin / test (hotglue.server.USER, PASSWORD).
"""

import sys
import tempfile

from conftest import VERSIONS, start_site
from hotglue.pages import PAGES

version = sys.argv[1] if len(sys.argv) > 1 else "master"
site = start_site(VERSIONS[version], tempfile.mkdtemp(prefix="hotglue-"))
try:
    print(f"hotglue {version} at {site.url}")
    for page in PAGES:
        print(f"  {site.view(page.name):50} editor: {site.edit(page.name)}")
    input("Enter or Ctrl+C stops it. ")
except KeyboardInterrupt:
    pass
finally:
    site.hotglue.stop()
