"""GitHub collector — monitors repos, orgs, and trending projects."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx

from radar.collectors.base import BaseCollector, Signal


class GitHubCollector(BaseCollector):
    """Collects intelligence from GitHub."""

    name = "github"
    description = "GitHub repos, releases, issues, trending"

    GITHUB_API = "https://api.github.com"

    async def collect(self) -> list[Signal]:
        """Collect signals from configured GitHub sources."""
        signals: list[Signal] = []
        async with httpx.AsyncClient(timeout=30) as client:
            # Monitor specific repos
            for repo in self.config.get("repos", []):
                signals.extend(await self._collect_repo(client, repo))

            # Monitor orgs
            for org in self.config.get("orgs", []):
                signals.extend(await self._collect_org(client, org))

            # Monitor topics
            for topic in self.config.get("topics", []):
                signals.extend(await self._collect_topic(client, topic))

            # GitHub trending
            signals.extend(await self._collect_trending(client))

        return signals

    async def _collect_repo(self, client: httpx.AsyncClient, repo: str) -> list[Signal]:
        """Collect recent activity from a specific repo."""
        signals = []
        since = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"

        try:
            # Recent commits
            resp = await client.get(
                f"{self.GITHUB_API}/repos/{repo}/commits",
                params={"since": since, "per_page": 5},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                commits = resp.json()
                if commits:
                    signals.append(
                        Signal(
                            source="github",
                            title=f"📦 {repo} — {len(commits)} new commit(s)",
                            url=f"https://github.com/{repo}",
                            summary="\n".join(
                                f"• {c['commit']['message'].split(chr(10))[0]}"
                                for c in commits[:5]
                            ),
                            metadata={"type": "commits", "count": len(commits)},
                        )
                    )

            # Recent releases
            resp = await client.get(
                f"{self.GITHUB_API}/repos/{repo}/releases",
                params={"per_page": 3},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                releases = resp.json()
                for release in releases[:1]:
                    release_date = release.get("published_at", "")
                    if release_date and release_date > since:
                        signals.append(
                            Signal(
                                source="github",
                                title=f"🏷️ {repo} — New release: {release['tag_name']}",
                                url=release.get("html_url", ""),
                                summary=release.get("body", "")[:300],
                                metadata={"type": "release", "tag": release["tag_name"]},
                            )
                        )

            # Stars change (approximation via watchers_count)
            resp = await client.get(
                f"{self.GITHUB_API}/repos/{repo}",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                data = resp.json()
                signals.append(
                    Signal(
                        source="github",
                        title=f"⭐ {repo} — {data['stargazers_count']:,} stars",
                        url=data["html_url"],
                        summary=f"Language: {data.get('language', 'N/A')} | "
                        f"Forks: {data['forks_count']:,} | "
                        f"Open Issues: {data['open_issues_count']:,} | "
                        f"Updated: {data['pushed_at'][:10]}",
                        metadata={
                            "type": "repo_stats",
                            "stars": data["stargazers_count"],
                            "forks": data["forks_count"],
                            "language": data.get("language"),
                        },
                    )
                )

        except Exception as e:
            signals.append(
                Signal(
                    source="github",
                    title=f"⚠️ Error monitoring {repo}",
                    url="",
                    summary=str(e),
                )
            )

        return signals

    async def _collect_org(self, client: httpx.AsyncClient, org: str) -> list[Signal]:
        """Collect recent repos from an org."""
        signals = []
        try:
            resp = await client.get(
                f"{self.GITHUB_API}/orgs/{org}/repos",
                params={"sort": "updated", "per_page": 5, "type": "public"},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                repos = resp.json()
                for repo in repos:
                    signals.append(
                        Signal(
                            source="github",
                            title=f"🏢 {org}/{repo['name']} — updated",
                            url=repo["html_url"],
                            summary=f"{repo.get('description', 'No description')} | "
                            f"⭐ {repo['stargazers_count']:,}",
                            metadata={
                                "type": "org_repo",
                                "stars": repo["stargazers_count"],
                                "language": repo.get("language"),
                            },
                        )
                    )
        except Exception as e:
            signals.append(
                Signal(source="github", title=f"⚠️ Error monitoring org {org}", url="", summary=str(e))
            )
        return signals

    async def _collect_topic(self, client: httpx.AsyncClient, topic: str) -> list[Signal]:
        """Search for popular repos matching a topic."""
        signals = []
        try:
            resp = await client.get(
                f"{self.GITHUB_API}/search/repositories",
                params={
                    "q": f"topic:{topic} pushed:>={(datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')}",
                    "sort": "stars",
                    "per_page": 5,
                },
                headers=self._headers(),
            )
            if resp.status_code == 200:
                data = resp.json()
                for repo in data.get("items", []):
                    signals.append(
                        Signal(
                            source="github",
                            title=f"🔍 [{topic}] {repo['full_name']}",
                            url=repo["html_url"],
                            summary=f"{repo.get('description', '')} | ⭐ {repo['stargazers_count']:,}",
                            metadata={
                                "type": "topic_search",
                                "stars": repo["stargazers_count"],
                                "language": repo.get("language"),
                            },
                        )
                    )
        except Exception:
            pass
        return signals

    async def _collect_trending(self, client: httpx.AsyncClient) -> list[Signal]:
        """Scrape GitHub trending page."""
        signals = []
        try:
            import re
            resp = await client.get(
                "https://github.com/trending?since=daily",
                headers={"Accept": "text/html", "User-Agent": "radar-agent/0.1"},
            )
            if resp.status_code == 200:
                html = resp.text
                # Extract repos from <article> tags with <h2> containing repo links
                articles = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
                for art in articles[:10]:
                    h2_match = re.search(r'<h2[^>]*>.*?href="(/[^"]+)".*?</h2>', art, re.DOTALL)
                    if h2_match:
                        repo_path = h2_match.group(1).strip("/")
                        if "/" not in repo_path:
                            continue

                        # Try to extract description
                        desc_match = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', art, re.DOTALL)
                        description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip() if desc_match else ""

                        # Try to extract stars today
                        stars_match = re.search(r'([\d,]+)\s+stars\s+today', art)
                        stars_today = stars_match.group(1) if stars_match else ""

                        summary = description[:200] if description else "Trending on GitHub today"
                        if stars_today:
                            summary += f" | ⭐ {stars_today} stars today"

                        signals.append(
                            Signal(
                                source="github",
                                title=f"🔥 Trending: {repo_path}",
                                url=f"https://github.com/{repo_path}",
                                summary=summary,
                                metadata={"type": "trending", "stars_today": stars_today},
                            )
                        )
        except Exception:
            pass
        return signals

    def _headers(self) -> dict[str, str]:
        """Get API headers with optional auth."""
        headers = {"Accept": "application/vnd.github+json"}
        import os
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
