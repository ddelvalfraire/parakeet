"""GitHub REST API wrapper for live demo remediation.

Provides async methods for reading repo files, creating branches,
committing changes, and managing pull requests.
"""

import base64
import logging

import httpx

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """Raised when a GitHub API call fails."""

    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"GitHub API {status}: {message}")


class GitHubService:
    def __init__(self, token: str, repo: str):
        self._repo = repo
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        accept: str | None = None,
    ) -> httpx.Response:
        headers = {"Accept": accept} if accept else {}
        resp = await self._client.request(
            method,
            f"/repos/{self._repo}{path}",
            json=json,
            headers=headers,
        )
        if resp.status_code >= 400:
            detail = resp.text[:500]
            raise GitHubError(resp.status_code, detail)
        return resp

    # ---- Read operations ----

    async def get_file_content(self, path: str, ref: str = "main") -> dict:
        """Return decoded file text + blob SHA."""
        resp = await self._request("GET", f"/contents/{path}?ref={ref}")
        data = resp.json()
        content = base64.b64decode(data["content"]).decode()
        return {"path": path, "content": content, "sha": data["sha"]}

    async def list_directory(self, path: str = "", ref: str = "main") -> list[dict]:
        """List files/dirs at *path* (empty = repo root). Returns name + type."""
        qs = f"?ref={ref}" if ref else ""
        resp = await self._request("GET", f"/contents/{path}{qs}")
        items = resp.json()
        if not isinstance(items, list):
            # Single file, not a directory
            return [{"name": items["name"], "type": items["type"], "path": items["path"]}]
        return [
            {"name": item["name"], "type": item["type"], "path": item["path"]}
            for item in items
        ]

    async def search_code(self, query: str, max_results: int = 5) -> list[dict]:
        """Search for code in the repo using GitHub's code search API.

        Returns file paths and text-match fragments so the agent can locate
        relevant symbols without reading entire files.

        Args:
            query: Search term — function name, error string, log message, etc.
            max_results: Cap on returned items (GitHub max is 100).
        """
        full_query = f"{query} repo:{self._repo}"
        resp = await self._client.request(
            "GET",
            "/search/code",
            params={"q": full_query, "per_page": min(max_results, 100)},
            headers={"Accept": "application/vnd.github.text-match+json"},
        )
        if resp.status_code >= 400:
            detail = resp.text[:500]
            raise GitHubError(resp.status_code, detail)

        items = resp.json().get("items", [])
        results: list[dict] = []
        for item in items:
            fragments = [
                tm["fragment"] for tm in item.get("text_matches", [])
            ]
            results.append({
                "path": item["path"],
                "name": item["name"],
                "fragments": fragments,
            })
        return results

    async def get_head_sha(self, branch: str = "main") -> str:
        resp = await self._request("GET", f"/git/ref/heads/{branch}")
        return resp.json()["object"]["sha"]

    # ---- Branch operations ----

    async def create_branch(self, name: str, from_sha: str) -> None:
        """Create a new branch from a given commit SHA."""
        await self._request(
            "POST",
            "/git/refs",
            json={"ref": f"refs/heads/{name}", "sha": from_sha},
        )

    async def delete_branch(self, name: str) -> None:
        try:
            await self._request("DELETE", f"/git/refs/heads/{name}")
        except GitHubError as e:
            if e.status not in (404, 422):  # already deleted / not found
                raise

    async def force_update_branch(self, branch: str, sha: str) -> None:
        await self._request(
            "PATCH",
            f"/git/refs/heads/{branch}",
            json={"sha": sha, "force": True},
        )

    # ---- File operations ----

    async def update_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: str,
        file_sha: str,
    ) -> dict:
        """Commit an updated file to a branch."""
        encoded = base64.b64encode(content.encode()).decode()
        resp = await self._request(
            "PUT",
            f"/contents/{path}",
            json={
                "message": message,
                "content": encoded,
                "sha": file_sha,
                "branch": branch,
            },
        )
        return resp.json()

    # ---- Pull request operations ----

    async def create_pr(
        self, title: str, body: str, head: str, base: str = "main"
    ) -> dict:
        resp = await self._request(
            "POST",
            "/pulls",
            json={"title": title, "body": body, "head": head, "base": base},
        )
        data = resp.json()
        return {"number": data["number"], "html_url": data["html_url"]}

    async def get_pr_diff(self, pr_number: int) -> str:
        resp = await self._request(
            "GET",
            f"/pulls/{pr_number}",
            accept="application/vnd.github.diff",
        )
        return resp.text

    async def merge_pr(self, pr_number: int) -> None:
        await self._request("PUT", f"/pulls/{pr_number}/merge")

    async def close_pr(self, pr_number: int) -> None:
        await self._request(
            "PATCH",
            f"/pulls/{pr_number}",
            json={"state": "closed"},
        )

    async def list_open_prs(self, head_prefix: str = "parakeet-fix/") -> list[dict]:
        resp = await self._request("GET", "/pulls?state=open&per_page=50")
        prs = resp.json()
        return [
            {"number": pr["number"], "head": pr["head"]["ref"]}
            for pr in prs
            if pr["head"]["ref"].startswith(head_prefix)
        ]

    # ---- Lifecycle ----

    async def close(self) -> None:
        await self._client.aclose()
