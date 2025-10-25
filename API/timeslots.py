from datetime import date, timedelta

def next_monday(from_date=None):
    if from_date is None:
        from_date = date.today()
    # Monday is weekday 0, Sunday is 6
    days_ahead = 0 - from_date.weekday() + 7
    if days_ahead <= 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)

today = date.today()

nextMonday = next_monday(today)

monday = str(nextMonday)
tuesday = str(nextMonday + timedelta(days = 1))
wednesday = str(nextMonday + timedelta(days = 2))
thursday = str(nextMonday + timedelta(days = 3))
friday = str(nextMonday + timedelta(days = 4))

timeslots = {
    # Monday / Wednesday / Friday morning slots
    "A1": ["08:30", "09:20", monday],
    "B1": ["09:30", "10:20", monday],
    "C1": ["10:30", "11:20", monday],
    "D1": ["11:30", "12:20", monday],

    "D2": ["08:30", "09:20", wednesday],
    "A2": ["09:30", "10:20", wednesday],
    "B2": ["10:30", "11:20", wednesday],
    "C2": ["11:30", "12:20", wednesday],

    "C3": ["08:30", "09:20", friday],
    "D3": ["09:30", "10:20", friday],
    "A3": ["10:30", "11:20", friday],
    "B3": ["11:30", "12:20", friday],

    # Afternoon slots (same timing across days)
    "H1": ["14:00", "14:50", monday],
    "I1": ["15:00", "15:50", monday],
    "J1": ["16:00", "16:50", monday],
    "K1": ["17:00", "17:50", monday],

    "J2": ["14:00", "14:50", wednesday],
    "H2": ["15:00", "15:50", wednesday],
    "I2": ["16:00", "16:50", wednesday],
    "K2": ["17:00", "17:50", wednesday],

    "I3": ["14:00", "14:50", friday],
    "J3": ["15:00", "15:50", friday],
    "H3": ["16:00", "16:50", friday],
    "K3": ["17:00", "17:50", friday],

    # Tuesday / Thursday slots
    "E1": ["08:30", "09:45", tuesday],
    "F1": ["09:50", "11:05", tuesday],
    "G1": ["11:10", "12:25", tuesday],

    "G2": ["08:30", "09:45", thursday],
    "E2": ["09:50", "11:05", thursday],
    "F2": ["11:10", "12:25", thursday],

    # Afternoon (Tuesday / Thursday)
    "SP1": ["14:00", "15:15", tuesday],
    "L1": ["15:20", "16:35", tuesday],
    "L2": ["16:40", "17:55", tuesday],

    "SP2": ["14:00", "15:15", thursday],
    "M1": ["15:20", "16:35", thursday],
    "M2": ["16:40", "17:55", thursday]
}