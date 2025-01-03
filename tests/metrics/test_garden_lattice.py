"""
Tests for the Almanack's Garden Lattice specific functions.
"""

import pytest

from almanack.metrics.garden_lattice.connectedness import detect_social_media_links


@pytest.mark.parametrize(
    "content, expected",
    [
        # Test case: Single platform (Twitter)
        (
            "Follow us on Twitter: https://twitter.com/ourproject",
            {"social_media_platforms": ["Twitter"], "social_media_platforms_count": 1},
        ),
        # Test case: Multiple platforms
        (
            """Connect with us:
            - Twitter: https://twitter.com/ourproject
            - LinkedIn: https://linkedin.com/company/ourcompany
            - Discord: https://discord.gg/invitecode
            """,
            {
                "social_media_platforms": ["Discord", "LinkedIn", "Twitter"],
                "social_media_platforms_count": 3,
            },
        ),
        # Test case: No social media links
        (
            "This README.md contains no social media links.",
            {"social_media_platforms": [], "social_media_platforms_count": 0},
        ),
        # Test case: Duplicate platforms (should only count each platform once)
        (
            """Follow us:
            - Twitter: https://twitter.com/ourproject
            - Twitter: https://twitter.com/anotherproject
            """,
            {"social_media_platforms": ["Twitter"], "social_media_platforms_count": 1},
        ),
        # Test case: Less common platforms (Bluesky and Threads)
        (
            """Find us:
            - Bluesky: https://bsky.app/profile/ourproject
            - Threads: https://threads.net/ourproject
            """,
            {
                "social_media_platforms": ["Bluesky", "Threads"],
                "social_media_platforms_count": 2,
            },
        ),
        # Test case: Mixed case URLs (case-insensitive match)
        (
            """Stay connected:
            - YouTube: https://www.youtube.com/channel/OurChannel
            - Facebook: https://facebook.com/OurPage
            """,
            {
                "social_media_platforms": ["Facebook", "YouTube"],
                "social_media_platforms_count": 2,
            },
        ),
        # Test case: social media links without specific channels / users
        (
            """Stay connected:
            - YouTube: https://www.youtube.com
            - Facebook: https://facebook.com
            """,
            {
                "social_media_platforms": [],
                "social_media_platforms_count": 0,
            },
        ),
    ],
)
def test_detect_social_media_links(content, expected):
    result = detect_social_media_links(content)
    assert result == expected
