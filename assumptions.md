## Допущения

- Горизонт анализа: 2023-01-01 — 2024-12-31.
- Выручка по подпискам считается как monthly_price за каждый активный месяц подписки.
- Выручка по add-ons считается как monthly_price за каждый активный месяц (если клиент активен).
- Фиксированные расходы берутся из fixed_costs.csv (ежемесячно).
- Вместимость зала (capacity): 180 человек одновременно.
- Utilization считаем по логам посещений (checkin/checkout) и capacity.
- Revenue is modeled as recurring monthly billing. Charges occur on the same day-of-month as subscription start. If the day does not exist (e.g., 31st), billing happens on the last day of the month.
