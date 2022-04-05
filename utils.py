from datetime import datetime, timezone
import webbrowser


TEXT_BASED_BROWSERS = [webbrowser.GenericBrowser, webbrowser.Elinks]

def isTextBasedBrowser(browser):
    """Returns if browser is a text-based browser.

    Arguments:
        browser {webbrowser.BaseBrowser} -- A browser.

    Returns:
        bool -- True if browser is text-based, False if browser is not
            text-based.
    """
    for tb_browser in TEXT_BASED_BROWSERS:
        if type(browser) is tb_browser:
            return True
    return False


def parseTimestamp(timestamp: str) -> datetime:
    try:
        return datetime.fromtimestamp(int(timestamp) / 1000, tzinfo=timezone.utc)
    except ValueError:
        # timestamp like '2012-07-30T17:47:01.687Z' or '2012-08-03T03:53:44Z'
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def timestampInRange(timestamp: str, date_range) -> bool:
    """Returns if the timestamp is in the date range.

    Arguments:
        timestamp {str} -- A timestamp (in ms).
        date_range {tuple} -- A tuple of strings representing the date range.
        (min_date, max_date) (Date format: yyyy-mm-dd)
    """
    if date_range == (None, None):
        return True
    date_str = parseTimestamp(timestamp).strftime("%Y-%m-%d")
    return dateInRange(date_str, date_range)


def dateInRange(date, date_range) -> bool:
    """Returns if the date is in the date range.

    Arguments:
        date {str} -- A date (Format: yyyy-mm-dd).
        date_range {tuple} -- A tuple of strings representing the date range.
        (min_date, max_date) (Date format: yyyy-mm-dd)
    """
    if date_range == (None, None):
        return True
    if date_range[0] == None:
        min_date = None
    else:
        min_date = datetime.strptime(date_range[0], "%Y-%m-%d")
    if date_range[1] == None:
        max_date = None
    else:
        max_date = datetime.strptime(date_range[1], "%Y-%m-%d")
    date = datetime.strptime(date, "%Y-%m-%d")
    return (min_date is None or min_date <= date) and \
        (max_date is None or max_date >= date)
