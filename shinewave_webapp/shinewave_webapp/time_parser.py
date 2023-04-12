from collections import OrderedDict
from datetime import datetime, timedelta
import html

import pytz

def get_format_dict():
    datetime_format_dict = OrderedDict(
        {'%Y/%m/%d %H:%M': 'YYYY/MM/DD HOUR:MINUTE', '%Y-%m-%d %H:%M': 'YYYY-MM-DD HOUR:MINUTE'}
    )

    date_format_dict = OrderedDict(
        {'%Y/%m/%d': 'YYYY/MM/DD', '%Y-%m-%d': 'YYYY-MM-DD'}
    )