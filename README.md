# world-holiday-calendar
Global holiday dataset for 247 countries and territories, with CSV, calendar rules, cron integration and AI agent documentation.
# World Holiday Calendar (2026–2028)

Machine-readable global holidays, cultural observances, religious dates, and campaign occasions for apps, cron jobs, and AI agents. The current edition has 10,661 dated records across 247 countries and territories.

**[ThruMemory](https://thrumemory.com/)** · [US-only calendar](https://github.com/malkovych/holiday-calendar) · [Agent quick reference](llms.txt)

## Get the calendar

- [Generate the world CSV](generate_calendar.py) using Python 3.10+ and `holidays==0.108`.


```sh
python -m pip install holidays==0.108
python generate_calendar.py
```

## Use it in an app

Import the UTF-8 CSV by its header. Keep `start_date` and `end_date` as inclusive ISO 8601 civil dates and index `market,start_date`. `market` is an ISO-style country or subdivision code, or a grouping such as `WORLD` or `EU`. Match the recipient time zone separately.

For scheduling, subtract the corresponding lead time in days from `start_date`. Use `send_local_time` in the recipient’s IANA zone before converting to UTC. Use occurrence, campaign, recipient, action, and channel as the deduplication key. Activate campaigns per audience. Treat `review` and estimated dates as requiring review, and `off` as reference-only.

The calendar includes selected international observances and partial subdivision coverage. Local religious dates and official workday substitutions may differ. Personal and organizer-supplied events use dates from the app or an organizer.

Sources: [Python Holidays](https://holidays.readthedocs.io/en/latest/), [UN observances](https://www.un.org/en/observances/list-days-weeks), and the sources linked per event.
