import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismasyncjmfjdf import prismasyncjmfjdf as module


class DummyResponse:
    def __init__(self, content: bytes):
        self.content = content


def _queueentry_xml(queue_entry_id="QPH2"):
    return (
        '<?xml version="1.0"?>'
        '<JMF><Response><QueueEntry QueueEntryID="' + queue_entry_id + '"/></Response></JMF>'
    ).encode("utf-8")


class TestCreateMimePackagePhase2(unittest.TestCase):

    def _create_inputs(self, tmp_dir: Path):
        jmf_file = tmp_dir / "SubmitQueueEntry.jmf"
        jdf_file = tmp_dir / "Ticket.jdf"
        pdf_file = tmp_dir / "Job1.pdf"

        jmf_file.write_text(
            '<JMF><Command><QueueSubmissionParams URL="http://original.local/ticket.jdf"/></Command></JMF>',
            encoding="utf-8",
        )
        jdf_file.write_text(
            '<JDF><ResourceLinkPool><FileSpec URL="http://original.local/job.pdf"/></ResourceLinkPool>'
            '<NodeInfo JobID="REPLACE_JOBID" JobPartID="REPLACE_JOBPARTID" ID="REPLACE_ID"/></JDF>',
            encoding="utf-8",
        )
        pdf_file.write_bytes((b"%PDF-1.7\n" + b"A" * 131072 + b"\n%%EOF\n"))
        return jmf_file, jdf_file, pdf_file

    def test_createmime_binary_streams_pdf_copy_and_preserves_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            jmf_file, jdf_file, pdf_file = self._create_inputs(tmp_dir)

            mime_file = module.CreateMimePackage(
                str(jmf_file),
                str(jdf_file),
                f"file://{pdf_file}",
                pdf_coding="binary",
            )

            mime_path = Path(mime_file)
            self.assertTrue(mime_path.exists())
            content = mime_path.read_bytes()

            jmf_idx = content.find(module.mimeheader_jmf.encode("utf-8"))
            jdf_idx = content.find(module.mimeheader_jdf.encode("utf-8"))
            pdf_idx = content.find(module.mimeheader_pdf_bin.encode("utf-8"))
            footer_idx = content.find(module.mimefooter.encode("utf-8"))

            self.assertNotEqual(jmf_idx, -1)
            self.assertNotEqual(jdf_idx, -1)
            self.assertNotEqual(pdf_idx, -1)
            self.assertNotEqual(footer_idx, -1)
            self.assertTrue(jmf_idx < jdf_idx < pdf_idx < footer_idx)

            self.assertIn(b'URL="cid:part2@PRISMAsync.printer"', content)
            self.assertIn(b'URL="cid:part3@PRISMAsync.printer"', content)
            self.assertIn(pdf_file.read_bytes(), content)

            mime_path.unlink()

    def test_createmime_binary_does_not_call_full_read_on_payload(self):
        class RejectingPayloadFile:
            def __init__(self, payload: bytes):
                self._payload = payload
                self._offset = 0

            def read(self, size=-1):
                if size == -1:
                    raise AssertionError("Full payload read() is not allowed in phase 2")
                if self._offset >= len(self._payload):
                    return b""
                end = min(self._offset + size, len(self._payload))
                chunk = self._payload[self._offset:end]
                self._offset = end
                return chunk

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            jmf_file, jdf_file, pdf_file = self._create_inputs(tmp_dir)
            payload = pdf_file.read_bytes()
            real_open = open

            def patched_open(file, mode="r", *args, **kwargs):
                if str(file) == str(pdf_file) and mode == "rb":
                    return RejectingPayloadFile(payload)
                return real_open(file, mode, *args, **kwargs)

            with patch("builtins.open", patched_open):
                mime_file = module.CreateMimePackage(
                    str(jmf_file),
                    str(jdf_file),
                    f"file://{pdf_file}",
                    pdf_coding="binary",
                )

            mime_path = Path(mime_file)
            self.assertTrue(mime_path.exists())
            mime_path.unlink()

    def test_createmime_output_accepted_by_sendmime_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            jmf_file, jdf_file, pdf_file = self._create_inputs(tmp_dir)

            mime_file = module.CreateMimePackage(
                str(jmf_file),
                str(jdf_file),
                f"file://{pdf_file}",
                pdf_coding="binary",
            )

            seen = {}

            def fake_post(*, url, data, headers, timeout, verify):
                seen["headers"] = headers
                seen["payload_prefix"] = data.read(128)
                return DummyResponse(_queueentry_xml("QPH2OK"))

            with patch.object(module.requests, "post", fake_post):
                result = module.SendMime("https://printer.local:8010", mime_file)

            self.assertEqual(result, "QPH2OK")
            self.assertEqual(seen["headers"]["Content-Type"], "multipart/related")
            self.assertTrue(seen["payload_prefix"].startswith(b"MIME-Version: 1.0"))

            Path(mime_file).unlink()


if __name__ == "__main__":
    unittest.main()
