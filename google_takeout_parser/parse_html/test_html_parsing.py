import bs4  # type: ignore[import]

from ..models import Subtitles, Details, LocationInfo
from .activity import _parse_subtitles, _parse_caption, _is_location_api_link

# bring into scope
from .comment import test_parse_html_comment_file
from .html_time_utils import test_parse_dt


def bs4_div(html: str) -> bs4.element.Tag:
    return bs4.BeautifulSoup(html, "lxml").select_one("div")


def test_parse_subtitles() -> None:
    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">Visited&nbsp;<a href="https://support.google.com/youtube/answer/7071292?hl=en">Get support with Premium memberships &amp; purchases - YouTube Help</a><br>Aug 25, 2020, 5:06:44 PM PDT</div>"""
    )
    subs, dt = _parse_subtitles(content)
    assert subs == [
        Subtitles(
            name="Visited Get support with Premium memberships & purchases - YouTube Help",
            url="https://support.google.com/youtube/answer/7071292?hl=en",
        )
    ]
    assert dt is not None

    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">6 cards in your feed<br/>Sep 4, 2020, 11:01:46 AM PDT</div>"""
    )
    subs, dt = _parse_subtitles(content)
    assert subs == [Subtitles(name="6 cards in your feed", url=None)]
    # parses into a DstTzInfo timezone, so just testing that it parsed
    assert int(dt.timestamp()) == 1599242506

    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">1 notification<br>Including topics:<br><a href="https://www.google.com/maps/place/?q=place_id:XX">Emergency resources and information</a><br>Sep 1, 2020, 9:27:07 PM PDT</div>""",
    )
    subs, dt = _parse_subtitles(content)

    # how multiple lines of body look in subtitles
    assert subs == [
        Subtitles(name="1 notification", url=None),
        Subtitles(name="Including topics:", url=None),
        Subtitles(
            name="Emergency resources and information",
            url="https://www.google.com/maps/place/?q=place_id:XX",
        ),
    ]
    assert dt is not None


def test_parse_captions() -> None:
    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"><b>Products:</b><br> Drive<br><b>Details:</b><br> From IP 8.8.8.8<br></div>"""
    )

    details, locationInfos, products = _parse_caption(content)

    assert details == [Details(name="From IP 8.8.8.8")]
    assert products == ["Drive"]
    assert locationInfos == []


def test_parse_locations() -> None:

    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"><b>Products:</b><br> Discover<br><b>Locations:</b><br> At <a href="https://www.google.com/maps/@?something">this general area</a> - From <a href="https://support.google.com/maps/answer/1">your places</a> (Home)<br></div>"""
    )

    details, locationInfos, products = _parse_caption(content)

    assert details == []
    assert products == ["Discover"]

    assert locationInfos == [
        LocationInfo(
            name="At this general area",
            url="https://www.google.com/maps/@?something",
            source="From your places (Home)",
            sourceUrl="https://support.google.com/maps/answer/1",
        )
    ]

    content = bs4_div(
        """<div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"><b>Products:</b><br> Maps<br><b>Locations:</b><br> At <a href="https://www.google.com/maps/@?api=1&map_action=map&center=3,-18&zoom=11">this general area</a> - Based on your past activity<br></div>"""
    )

    details, locationInfos, products = _parse_caption(content)

    assert details == []
    assert products == ["Maps"]

    assert locationInfos == [
        LocationInfo(
            name="At this general area",
            url="https://www.google.com/maps/@?api=1&map_action=map&center=3,-18&zoom=11",
            source="Based on your past activity",
            sourceUrl=None,
        )
    ]


def test_parse_is_google_url() -> None:
    assert _is_location_api_link(
        "https://www.google.com/maps/@?api=1&map_action=map&center=3,-18&zoom=11"
    )
    assert not _is_location_api_link("https://www.google.com/")
