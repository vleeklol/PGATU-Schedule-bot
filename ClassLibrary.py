import datetime

class Student:
    def __init__(self, name: str) -> None:
        self.name = name


class Lecture:
    """
    Class specifically used to describe one lecture from schedule

    Attributes:
        room (str): Room where lecture will take place in.
        name (str): Name of the lecture. 
        teacher (str): Initials of teacher that will give this lecture.
        date (str): Start and end when this lecture can take place. In format of '%D.%M-%D.%M'
        start_time (str): Time when lecture will start. In format of '%H:%M:02'
        end_time (str): Time when lecture will end. Is automatically assigned with __init__()
    """

    def __init__(self, room: str, name: str, teacher: str, date: str, start_time: str) -> None:
        self.room = room
        self.name = name
        self.teacher = teacher
        self.date = date
        self.start_time = start_time
        self.end_time = self.get_end_time()


    def get_end_time(self) -> str:
        """Add 1 hour and 30 minutes to the lecture starting time.

        Gets starting time, converts it all to minutes.
        Then adds 90 minutes and converts it all back to '%H:%M'.

        Returns:
            str: String in format '%H:%M:02', time of lecture ending.
        
        >>> print(Lecture('Пр512', 'Психология', 'Челнокова А.В.', '09.09-07.12', '17:20')
        '18:50'
        """
        start_hours, start_minutes = self.start_time.split(':')
        start_overall = int(start_hours)*60+int(start_minutes)
        end_overall = start_overall + 90
        end_hours = end_overall // 60
        end_minutes = end_overall % 60
        return f'{end_hours}:{end_minutes:02}'
    

    def is_lecture_date_valid(self, week_day_index: int) -> bool:
        """Check if nearest lecture can take place on a nearest Day.

        Gets starting date and ending date from self.date.
        Checks if nearest lecture date is inbetween ending date and starting date.

        Note: 
            This function doesn't check if lecture is right on schedule, just if it CAN be on this certain day. 

        Args:
            week_day_index (int): the index of Day (e.g. Monday = 0 ... Sunday = 6)

        Returns:
            bool: Bool that represents if lecture is going to take place.
            True or False

        >>> print(Lecture('Пр512', 'Психология', 'Челнокова А.В.', '09.09-07.12', '17:20').is_lecture_date_valid(1))
        True

        Example's date is 29.09.2024 and is sunday. 
        Returns true because this lecture can take place on nearest Tuesday (01.10.2024).
        """
        start_date, end_date = self.date.split('-')
        start_day, start_month = map(int, start_date.split('.'))
        end_day, end_month = map(int, end_date.split('.'))

        today = datetime.datetime.today()
        today_index = today.weekday()

        start_year = int(today.year)
        end_year = start_year if end_month >= start_month else start_year+1

        offset = week_day_index - today_index if today_index <= week_day_index else week_day_index - today_index + 7

        start_date = datetime.date(start_year, start_month, start_day)
        end_date = datetime.date(end_year, end_month, end_day)
        check_date = (today+datetime.timedelta(days=offset)).date()
        # check_date = (today+datetime.timedelta(days=(offset+7))).date()
        return end_date >= check_date >= start_date


    def print_lecture_data(self) -> None:
        """ 
        Prints all of needed lecture's data in format '%START_TIME - %END_TIME | %LECTURE_NAME in %LECTURE_ROOM | %TEACHER_NAME'.

        >>> Lecture('Пр512', 'Психология', 'Челнокова А.В.', '09.09-07.12', '17:20').print_lecture_data()
        '17:20 - 18:50 | Психология в Пр512 | Челнокова А.В.'
        """
        print(f'{self.start_time} - {self.end_time} | {self.name} в {self.room} | {self.teacher}')
    

class Day:
    """
    Class used to contain all lectures held on one Day.

    Attributes:
        TIME_TABLE (list[str]): Constant and static list of all times lectures can start.
        lectures (list[Lecture]): List of all lectures on this day.
        name (str): Name of this day. ('Wednesday')
        day_index (int): Index of this day. (e.g. Monday = 0 ... Sunday = 6)
    """
    TIME_TABLE = ['8:30', '10:10', '12:00', '14:00', '15:40', '17:20', '19:00', '20:40']

    def __init__(self, day_index: int, lectures: list[Lecture] | None = None) -> None:
        if lectures is None:
            self.lectures = []
        else:
            self.lectures = lectures
        
        self.day_index = day_index
        self.name = Week.WEEK_TABLE[day_index]

    def add_lecture(self, lecture: Lecture) -> None:
        """
        Adds a lecture to lectures list.

        Args:
            lecture (Lecture): Lecture that is going to be added.
        """
        self.lectures.append(lecture)

    def print_all_lectures(self) -> None:
        """
        Prints formatted string of all lectures.
        Nothing is printed if day has 0 lectures.
        """
        if len(self.lectures) == 0:
            return

        print(f'{self.name:-^20}')
        for lecture in self.lectures:
            if lecture.is_lecture_date_valid(self.day_index):
                lecture.print_lecture_data()
        print()


class Week:
    """
    Class used to hold all Days with all of their lectures.

    Attributes:
        WEEK_TABLE (list[str]): Constant and static list of all Days from Monday to Sunday
        week_index (int): Index of this week. Basically means odd or even. (1 or 2)
        days (list[Day]): List of all Days in this week.  
    """

    WEEK_TABLE = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    def __init__(self, week_index: int, days: list[Day] | None = None) -> None:
        if days is None:
            self.days = [Day] * 7
        else:
            self.days = days

        self.week_index = week_index
        self.setup_days()
    
    def setup_days(self) -> None:
        """
        Function used to set up all days from Monday to Sunday.
        Every day has 0 lectures in it. 
        """
        for day_index in range(7):
            self.days[day_index] = Day(day_index)

    def print_week_lectures(self) -> None:
        """
        Prints all lectures within a week. 
        Goes through all Days and calls Day.print_all_lectures() function. 
        """

        for day in self.days:
            day.print_all_lectures()


class Group:
    """
    This class has all of the possible weeks and students that are in it.
    Specifically made for it to be in a dictionary of main file.
    
    Attributes:
        name (str): The name of group.
        id (int): Id of a group.
        students (list): List of all students in a group. By default is []
    """

    def __init__(self, name: str, id: int, weeks: list[Week] | None = None, students: list[Student]  | None = None) -> None:
        if students is None:
            self.students = []
        else:
            self.students = students

        if weeks is None:
            self.weeks = []
        else:
            self.weeks = weeks


        self.name = name
        self.id = id

    def add_student(self, student: Student) -> None:
        """
        Adds a student to students list.

        Args:
            student (Student): Student that is going to be added.
        """
        self.students.append(student)
