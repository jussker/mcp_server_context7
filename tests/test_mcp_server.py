import os
import json

import pytest

import mcp_server_context7 as mcp
import asyncio
from fastmcp import Client


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


def test_validate_encryption_key():
    assert mcp.validate_encryption_key("a" * 64) is True
    assert mcp.validate_encryption_key("zz") is False


def test_generate_headers_and_server_version():
    ctx = {"clientIp": "1.2.3.4", "apiKey": "ctx7sk_test", "clientInfo": {"ide": "testide", "version": "1.2"}, "transport": "http"}
    headers = mcp.generate_headers(ctx)
    assert headers["X-Context7-Source"] == "mcp-server"
    assert "X-Context7-Server-Version" in headers
    assert headers["mcp-client-ip"]  # encrypted or fallback string
    assert headers["Authorization"] == "Bearer ctx7sk_test"
    assert headers["X-Context7-Client-IDE"] == "testide"
    assert headers["X-Context7-Client-Version"] == "1.2"


def test_format_search_results_labels():
    resp = {
        "results": [
            {"title": "A", "id": "/a", "description": "d", "trustScore": 8, "totalSnippets": 10, "benchmarkScore": 50, "versions": ["v1"]},
            {"title": "B", "id": "/b", "description": "d2", "trustScore": 2, "totalSnippets": -1},
        ]
    }
    out = mcp.format_search_results(resp)
    assert "Source Reputation: High" in out
    assert "Source Reputation: Low" in out
    assert "Benchmark Score: 50" in out


def test_extract_github_repo_from_doc():
    txt = "Some docs\nSOURCE: https://github.com/owner/repo.git\nmore"
    repo = mcp.extract_github_repo_from_doc(txt)
    assert repo == "https://github.com/owner/repo"


def test_search_libraries_impl_monkeypatch(monkeypatch):
    sample = {"results": [{"title": "X", "id": "/x", "description": "d"}]}

    def fake_get(url, params=None, headers=None, proxies=None):
        return DummyResponse(status_code=200, json_data=sample)

    monkeypatch.setattr(mcp, "requests", type("R", (), {"get": staticmethod(fake_get)}))

    res = mcp._search_libraries_impl("q", "libname", {"clientIp": "1.2.3.4"})
    assert "results" in res
    assert len(res["results"]) == 1


def test_fetch_library_documentation_impl_monkeypatch(monkeypatch):
    text = "Documentation text\nhttps://github.com/owner/repo\n"

    def fake_get(url, params=None, headers=None, proxies=None):
        return DummyResponse(status_code=200, text=text)

    monkeypatch.setattr(mcp, "requests", type("R", (), {"get": staticmethod(fake_get)}))

    res = mcp._fetch_library_documentation_impl("/owner/pkg", query="help", tokens=None, client_context=None, save_to_file=False, sync_repo=False)
    assert res.get("content") == text
    assert res.get("library_id") == "owner/pkg"


def test_list_and_get_file_ops(tmp_path):
    base = tmp_path / "km-base"
    base.mkdir()
    f = base / "sample_lib.md"
    f.write_text("hello world")

    repo_dir = base / "sample_lib_repo"
    repo_dir.mkdir()

    # Use an in-process MCP Client to call the remote tool interface
    async def _run():
        client = Client(mcp.mcp)
        async with client:
            resp = await client.call_tool("list_downloaded_libraries", {"base_dir": str(base)})
            # normalize response
            if hasattr(resp, "result"):
                out = resp.result
            elif hasattr(resp, "data"):
                out = resp.data
            else:
                out = resp

            assert out and "libraries" in out

            # test get_library_content via MCP (file exists)
            resp2 = await client.call_tool(
                "get_library_content", {"filename": "sample_lib.md", "base_dir": str(base), "max_chars": 5}
            )
            if hasattr(resp2, "result"):
                out2 = resp2.result
            elif hasattr(resp2, "data"):
                out2 = resp2.data
            else:
                out2 = resp2

            assert out2.get("truncated") is True

    import asyncio

    asyncio.run(_run())


def test_mcp_client_inprocess():
    """Start an in-process Client against the `mcp` object and call tools.

    This avoids external transport and verifies tool wiring end-to-end.
    """

    async def _run():
        client = Client(mcp.mcp)
        async with client:
            tools = await client.list_tools()
            # Normalize tool names
            names = []
            for t in tools:
                if hasattr(t, "name"):
                    names.append(t.name)
                elif isinstance(t, dict):
                    names.append(t.get("name"))
                else:
                    names.append(str(t))

            assert "search_libraries" in names

            # Call search_libraries
            resp = await client.call_tool("search_libraries", {"query": "gradio"})
            if hasattr(resp, "result"):
                out = resp.result
            elif hasattr(resp, "data"):
                out = resp.data
            elif hasattr(resp, "text"):
                out = resp.text
            else:
                out = resp

            assert out and ("results" in out or "formatted_text" in out or "message" in out)

            # Call list_downloaded_libraries
            resp2 = await client.call_tool("list_downloaded_libraries", {})
            if hasattr(resp2, "result"):
                out2 = resp2.result
            elif hasattr(resp2, "data"):
                out2 = resp2.data
            else:
                out2 = resp2

            assert out2 and "libraries" in out2

    asyncio.run(_run())
