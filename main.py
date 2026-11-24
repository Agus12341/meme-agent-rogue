"""Meme Sprint 3: AI Agent Goes Rogue - a make.fun entry.

Validates the shipped meme image (entry.png) and copies it byte-for-byte
to the output directory as entry.png. Deterministic, stdlib only.
"""

import os
import struct
import sys
import zlib

MAX_BYTES = 1_048_576  # 1 MiB cap from the competition gate
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")


def validate_png(data):
    """Walk the PNG chunks, verify every CRC, return (width, height)."""
    if len(data) > MAX_BYTES:
        raise ValueError("image exceeds the 1 MiB cap: %d bytes" % len(data))
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG file (bad signature)")

    pos = len(PNG_SIGNATURE)
    width = None
    height = None
    seen_iend = False
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated chunk header at offset %d" % pos)
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        chunk_type = data[pos + 4:pos + 8]
        chunk_end = pos + 8 + length + 4
        if chunk_end > len(data):
            raise ValueError("truncated chunk %r at offset %d" % (chunk_type, pos))
        payload = data[pos + 8:pos + 8 + length]
        (crc_stored,) = struct.unpack(">I", data[pos + 8 + length:chunk_end])
        crc_actual = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if crc_actual != crc_stored:
            raise ValueError("CRC mismatch in chunk %r" % chunk_type)
        if chunk_type == b"IHDR":
            width, height = struct.unpack(">II", payload[:8])
        pos = chunk_end
        if chunk_type == b"IEND":
            seen_iend = True
            break

    if width is None:
        raise ValueError("no IHDR chunk found")
    if not seen_iend:
        raise ValueError("no IEND chunk found")
    if pos != len(data):
        raise ValueError("trailing bytes after IEND chunk")
    return width, height


def main():
    with open(SOURCE, "rb") as f:
        data = f.read()

    width, height = validate_png(data)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise ValueError(
            "image must be %dx%d, got %dx%d"
            % (EXPECTED_WIDTH, EXPECTED_HEIGHT, width, height)
        )

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    with open(out_path, "wb") as f:
        f.write(data)

    # The gate runs this program twice and requires identical bytes.
    with open(out_path, "rb") as f:
        written = f.read()
    if written != data:
        raise ValueError("written bytes differ from the shipped entry.png")

    print("wrote %s (%d bytes, %dx%d)" % (out_path, len(written), width, height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
