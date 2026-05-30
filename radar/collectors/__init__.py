"""Data collectors for various platforms."""

from radar.collectors.github_collector import GitHubCollector
from radar.collectors.hn_collector import HNCollector
from radar.collectors.ph_collector import ProductHuntCollector
from radar.collectors.rss_collector import RSSCollector
from radar.collectors.web_collector import WebCollector

ALL_COLLECTORS = {
    "github": GitHubCollector,
    "hackernews": HNCollector,
    "producthunt": ProductHuntCollector,
    "rss": RSSCollector,
    "web": WebCollector,
}
