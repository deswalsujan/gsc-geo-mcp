# MCP server that lets Claude ask which pages lost AI-referral traffic.
# Exposes one tool that runs the same query as run_query.py. Talks to
# Claude over stdio, so Claude Code starts it as a local process.

from mcp.server.mcpserver import MCPServer

from gsc_geo_mcp.query import pages_losing_ai_referral_traffic

mcp = MCPServer("gsc-geo-mcp")

DESCRIPTION = """\
Lists pages that may be losing AI-referral traffic, using Google Search
Console data exported to BigQuery.

Definition: a page is flagged when its impressions in the last 7 days
are flat or up and its clicks in the last 7 days are down, compared
with the 7 days before that. The last 7 days end on the most recent
date in the data, which usually trails today by 2 to 3 days.

This is a proxy. Search Console has no AI-referral metric. What it can
show is clicks dropping while impressions hold, which is the pattern
expected when AI answers satisfy searchers before they click. A ranking
or snippet change can produce the same pattern.

Returns the project and dataset queried, then one entry per flagged
page with clicks and impressions for both windows and the change. An
empty list means no page matched. The dataset gsc_geo_mcp_test is
synthetic test data, so results from it are not real traffic.
"""


@mcp.tool(name="pages_losing_ai_referral_traffic", description=DESCRIPTION)
def pages_losing_ai_referral_traffic_tool() -> dict:
    return pages_losing_ai_referral_traffic()


def main() -> None:
    mcp.run()
