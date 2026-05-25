SUPPORTED_PLATFORMS = [
    "Instagram",
    "YouTube",
    "Telegram",
    "Facebook",
    "X",
    "TikTok",
    "LinkedIn",
    "Spotify",
    "Threads",
    "Snapchat",
    "Pinterest",
    "Website Traffic",
    "Discord",
    "Reddit",
]


def platform_catalog() -> list[dict]:
    return [
        {
            "platform": p,
            "enabled": True,
            "status": "launch_ready",
            "supports": ["followers", "likes", "views", "comments", "members"],
        }
        {"platform": p, "enabled": True, "status": "launch_ready"}
        for p in SUPPORTED_PLATFORMS
    ]
