import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismasyncjmfjdf import prismasyncjmfjdf as module


class DummyResponse:
    def __init__(self, content: bytes):
        self.content = content


def _queueentry_xml(queue_entry_id="Q123"):
    return (
            '<?xml version="1.0"?>'
            '<JMF><Response><QueueEntry QueueEntryID="' + queue_entry_id + '"/></Response></JMF>'
    ).encode("utf-8")


class TestSendMimePhase1(unittest.TestCase):

    def test_sendmime_chunked_sets_header_and_streams_generator(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mime_file = Path(tmp_dir) / "job.mjm"
            mime_file.write_bytes(b"abcde" * 100)
            seen = {}

            def fake_post(*, url, data, headers, timeout, verify):
                seen["url"] = url
                seen["headers"] = headers
                seen["timeout"] = timeout
                seen["verify"] = verify
                payload = b"".join(data)
                seen["payload"] = payload
                return DummyResponse(_queueentry_xml("QC1"))

            with patch.object(module.requests, "post", fake_post):
                result = module.SendMime(
                        "https://printer.local:8010",
                        str(mime_file),
                        chunked_upload=True,
                        chunk_size=64,
                )

            self.assertEqual(result, "QC1")
            self.assertEqual(seen["headers"]["Content-Type"], "multipart/related")
            self.assertEqual(seen["headers"]["Transfer-Encoding"], "chunked")
            self.assertEqual(seen["payload"], mime_file.read_bytes())

    def test_sendmime_default_mode_keeps_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mime_file = Path(tmp_dir) / "job2.mjm"
            mime_file.write_bytes(b"payload")
            seen = {}

            def fake_post(*, url, data, headers, timeout, verify):
                seen["headers"] = headers
                seen["data"] = data
                return DummyResponse(_queueentry_xml("QDEF"))

            with patch.object(module.requests, "post", fake_post):
                result = module.SendMime("https://printer.local:8010", str(mime_file))

            self.assertEqual(result, "QDEF")
            self.assertEqual(seen["headers"]["Content-Type"], "multipart/related")
            self.assertNotIn("Transfer-Encoding", seen["headers"])
            self.assertTrue(hasattr(seen["data"], "read"))

    def test_sendmime_invalid_chunk_size_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mime_file = Path(tmp_dir) / "job3.mjm"
            mime_file.write_bytes(b"x")
            result = module.SendMime(
                    "https://printer.local:8010",
                    str(mime_file),
                    chunked_upload=True,
                    chunk_size=0,
            )
            self.assertEqual(result, 0)

    def test_sendmime_non_xml_reply_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mime_file = Path(tmp_dir) / "job4.mjm"
            mime_file.write_bytes(b"x")

            def fake_post(*, url, data, headers, timeout, verify):
                return DummyResponse(b"not-xml")

            with patch.object(module.requests, "post", fake_post):
                result = module.SendMime("https://printer.local:8010", str(mime_file), chunked_upload=True)
            self.assertEqual(result, 0)

    def test_sendjob_passes_chunked_options(self):
        seen = {}

        def fake_create_mime(jmf_file, jdf_file, pdf_url, pdf_coding="binary"):
            return "dummy.mjm"

        def fake_send_mime(url, mime_file, chunked_upload=False, chunk_size=65536):
            seen["url"] = url
            seen["mime_file"] = mime_file
            seen["chunked_upload"] = chunked_upload
            seen["chunk_size"] = chunk_size
            return "QPASS"

        with patch.object(module, "CreateMimePackage", fake_create_mime), \
                 patch.object(module, "SendMime", fake_send_mime), \
                 patch.object(module.Path, "unlink", lambda _self: None):
            result = module.SendJob(
                    "https://printer.local:8010",
                    "file://dummy.pdf",
                    chunked_upload=True,
                    chunk_size=131072,
            )

        self.assertEqual(result, "QPASS")
        self.assertTrue(seen["chunked_upload"])
        self.assertEqual(seen["chunk_size"], 131072)


if __name__ == "__main__":
    unittest.main()
