# PRISMAsync Python module
This repository contains a Python module for communication with PRISMAsync. It needs to be installed locally by using:

     pip install https://github.com/ddt3/prismasyncjmfjdf/releases/latest/download/prismasyncjmfjdf.tar.gz
# Contents of this module
For details on the contents of this module:

    python -m pydoc prismasyncjmfjdf
    or to create a html page:
    python -m pydoc -w prismasyncjmfjdf
# Building a new version
Make sure build and setuptools are installed:

    python -m pip install build setuptools

In the folder where ``pyproject.toml`` can be found, start build:

    python -m build .

# Automated release and package index
This repository contains a GitHub Actions workflow at [`.github/workflows/release-and-pages.yml`](.github/workflows/release-and-pages.yml) that automates:

1. Building wheel and sdist when a tag `v*` is pushed.
2. Creating/updating a GitHub release and uploading build artifacts.
3. Generating a static PEP 503-style package index page.
4. Publishing that index on GitHub Pages.

Expected package index URL after enabling GitHub Pages:

    https://ddt3.github.io/prismasyncjmfjdf/simple/prismasyncjmfjdf/

Use this URL in downstream requirements files with:

    -f https://ddt3.github.io/prismasyncjmfjdf/simple/prismasyncjmfjdf/
    prismasyncjmfjdf

This lets pip discover all released wheel versions and pick the latest compatible one without editing requirements for each release.

# Chunked MIME upload options (Phase 1)
For large MIME packages, upload can be streamed using HTTP chunked transfer encoding.

`SendMime` options:
- `chunked_upload` (default `False`): when `True`, uses `Transfer-Encoding: chunked`.
- `chunk_size` (default `65536`): bytes per uploaded chunk.

`SendJob` exposes the same options and passes them through to `SendMime`.

Example using `SendJob`:

    import prismasyncjmfjdf
    queue_id = prismasyncjmfjdf.SendJob(
        "https://printer.local:8010",
        "file://C:/jobs/myjob.pdf",
        chunked_upload=True,
        chunk_size=65536,
    )

Example using `SendMime`:

    import prismasyncjmfjdf
    queue_id = prismasyncjmfjdf.SendMime(
        "https://printer.local:8010",
        "myjob.mjm",
        chunked_upload=True,
        chunk_size=65536,
    )

Backward compatibility:
- Existing calls continue to work without changes because defaults remain unchanged.

Compatibility caveat:
- Some proxies/endpoints may not accept `Transfer-Encoding: chunked`.
  If upload fails in such environments, set `chunked_upload=False`.

