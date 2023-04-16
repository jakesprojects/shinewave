from collections import OrderedDict
from datetime import datetime, timedelta
import html

import pytz


def get_format_dict(format_type):
    """
        Returns a dictionary containing various acceptable formats for dates and times. The output is an ordered
        dictionary formatted as follows: {<datetime.strftime FORMAT>: <PLAINTEXT DESCRIPTION OF FORMAT>}

        Parameters
        ----------
        format_type : str
            The set of date formats to return. Must be one of the following:
                'date'
                'datetime'
                'all'
            'date' will restrict outputs to date formats without times. Conversely, 'datetime' will output formats that
            mandate both a date and a time. 'all' will return both.
    """

    date_format_dict = OrderedDict(
        {'%Y/%m/%d': 'YYYY/MM/DD', '%Y-%m-%d': 'YYYY-MM-DD'}
    )

    datetime_format_dict = OrderedDict(
        {'%Y/%m/%d %H:%M': 'YYYY/MM/DD HOUR:MINUTE', '%Y-%m-%d %H:%M': 'YYYY-MM-DD HOUR:MINUTE'}
    )

    if format_type == 'date':
        return date_format_dict
    elif format_type == 'datetime':
        return datetime_format_dict
    elif format_type == 'all':
        format_dict = datetime_format_dict
        format_dict.update(date_format_dict)
        return format_dict
    else:
        raise ValueError("Argument 'format_type' must be one of the following strings: 'date', 'datetime', 'all'.")


def get_timezones(include_synthetic_timezones):
    """
        Returns an ordered dictionary of all acceptable timezones.

        Parameters
        ----------
        include_synthetic_timezones : bool
            If True, synthetic timezones will be included in the output. These are timezones that only have meaning to
            the application, and rely on its data model. They are:
                'Local to Recipient Area Code':
                    A timezone that is generated based on the area code of the recipient's phone number.
                'Defined by Recipient Data':
                    A timezone that is read from the database, specifically the members/recipients table, and must
                    conform to one of the non-synthetic timezone names.
    """

    timezone_dict = OrderedDict(
        {
            'Hawaii': 'US/Hawaii',
            'Alaska': 'US/Alaska',
            'Pacific': 'US/Pacific',
            'Mountain': 'US/Mountain',
            'Central': 'US/Central',
            'Eastern': 'US/Eastern',
            'UTC': 'UTC'
        }
    )

    if include_synthetic_timezones:
        timezone_dict.update({'Local to Recipient Area Code': None, 'Defined by Recipient Data': None})

    return timezone_dict
