import re
import typing

import markdown2
import yaml
from aiohttp import web
from datetime import datetime, date, time


class TimeInterval:
    def __init__(self, hours=0, minutes=0, seconds=0, months=0, days=0, years=0):
        self._throw_on_negative(hours, minutes, seconds, months, days, years)
        self.hours = int(hours)
        self.minutes = int(minutes)
        self.seconds = int(seconds)
        self.months = int(months)
        self.days = int(days)
        self.years = int(years)

    def _throw_on_negative(self, *values):
        labels = ['hours', 'minutes', 'seconds', 'months', 'days', 'years']
        for value, label in zip(values, labels):
            if value < 0:
                raise ValueError(f"{label} is negative")

    def to_machine_string(self, use_i_for_minutes=False):
        result = "P"
        if self.years:
            result += f"{self.years}Y"
        if self.months:
            result += f"{self.months}M"
        if self.days:
            result += f"{self.days}D"
        if self.hours or self.minutes or self.seconds:
            result += "T"
            if self.hours:
                result += f"{self.hours}H"
            if self.minutes:
                result += f"{self.minutes}{'I' if use_i_for_minutes else 'M'}"
            if self.seconds:
                result += f"{self.seconds}S"
        return result

    def to_human_string(self):
        parts = []
        if self.years:
            parts.append(f"{self.years} year{'s' if self.years > 1 else ''}")
        if self.months:
            parts.append(f"{self.months} month{'s' if self.months > 1 else ''}")
        if self.days:
            parts.append(f"{self.days} day{'s' if self.days > 1 else ''}")
        if self.hours:
            parts.append(f"{self.hours} hour{'s' if self.hours > 1 else ''}")
        if self.minutes:
            parts.append(f"{self.minutes} minute{'s' if self.minutes > 1 else ''}")
        if self.seconds:
            parts.append(f"{self.seconds} second{'s' if self.seconds > 1 else ''}")
        if not parts:
            return "0 seconds"
        return ", ".join(parts[:-1]) + (" and " + parts[-1] if len(parts) > 1 else parts[0])

    def __str__(self):
        return self.to_human_string()

    def add(self, hours=0, minutes=0, seconds=0, months=0, days=0, years=0):
        self._throw_on_negative(self.hours + hours, self.minutes + minutes, self.seconds + seconds,
                                self.months + months, self.days + days, self.years + years)
        self.hours += hours
        self.minutes += minutes
        self.seconds += seconds
        self.months += months
        self.days += days
        self.years += years
        return self

    @staticmethod
    def difference_between(date_left, date_right):
        if not isinstance(date_left, datetime):
            date_left = datetime.fromisoformat(date_left)
        if not isinstance(date_right, datetime):
            date_right = datetime.fromisoformat(date_right)

        delta = abs(date_left - date_right)
        return TimeInterval(
            hours=delta.seconds // 3600,
            minutes=(delta.seconds % 3600) // 60,
            seconds=delta.seconds % 60,
            days=delta.days
        )

    @classmethod
    def from_string(cls, time_string):
        pattern = re.compile(
            r"(?:(\d+)Y)? ?(?:(\d+)M)? ?(?:(\d+)D)?T? ?(?:(\d+)H)? ?(?:(\d+)i)? ?(?:(\d+)s)?",
            flags=re.IGNORECASE)
        match = pattern.fullmatch(time_string.strip())
        if not match:
            raise ValueError("Invalid time interval format")
        years, months, days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
        return cls(hours=hours, minutes=minutes, seconds=seconds, months=months, days=days, years=years)

    def add_to_datetime(self, datetime_local: datetime) -> datetime:
        return datetime(
            datetime_local.year + self.years,
            datetime_local.month + self.months,
            datetime_local.day + self.days,
            datetime_local.hour + self.hours,
            datetime_local.minute + self.minutes,
            datetime_local.second + self.seconds)
        pass

    def sub_to_datetime(self, datetime_local: datetime) -> datetime:
        return datetime(
            datetime_local.year - self.years,
            datetime_local.month - self.months,
            datetime_local.day - self.days,
            datetime_local.hour - self.hours,
            datetime_local.minute - self.minutes,
            datetime_local.second - self.seconds)
        pass

    pass


routes = web.RouteTableDef()


def html_encode(strx: str) -> str:
    strx = strx.replace('&', '&amp;')
    strx = strx.replace('"', '&quot;')
    strx = strx.replace("'", '&#39;')
    return strx.replace('<', '&lt;').replace('>', '&gt;')


def load_comments():
    with open('comments.yaml', 'rt', encoding='utf8') as file:
        try:
            comments = yaml.safe_load_all(file.read())
            comments = list(comments)[0]
        except ValueError as e:
            print('error:', f'{e}')
            comments = dict(status=500, error=f'{e}')
    # if cache is None:
    #     with open('comments.yaml', 'rt', encoding='utf8') as file:
    #         comments = yaml.safe_load_all(file.read())
    #     cache = comments = list(comments)[0]
    # else:
    #     comments = cache
    return comments


@routes.get('/favicon.ico')
@routes.get('/favicond.svg')
async def icond(_: web.Request) -> web.Response:
    with open('favicond.svg', 'rt', encoding='utf8') as src:
        text = src.read()
    return web.Response(text=text, content_type='image/svg+xml')


class Flair:
    def __init__(self, flair: dict):
        self.flair_color = str(flair.get('flair_color', ''))
        self.flair_color = self.flair_color if re.search(
            '^#?[a-f0-9]{6}$|^$', self.flair_color,
            flags=re.I) else 'transparent'
        self.flair_text = str(flair.get('flair_text', ''))

    def __str__(self):
        return f'<span style="background-color:{self.flair_color}">{html_encode(self.flair_text)}</span>'


class User:
    def __init__(self, name: str, authors: dict, is_original_poster: bool):
        name = re.sub('^(?:[a-zA-Z]/)?', 'u/', str(name))
        self.profile_image_url = str(authors.get('profile_image_url', '/favicon.ico'))
        self.username = re.sub('^u/', '', name)
        self.flair_css_class = flair_text if isinstance(flair_text := authors.get('flair', dict()), dict) else dict()
        self.name = name
        self.is_valid = \
            re.search('^m/[a-zA-Z0-9\\-_]$', name)
        self.is_original_poster = is_original_poster

    def get(self):
        if self.is_valid:
            return self
        else:
            return deleted

    pass


deleted = User('[deleted]', dict(), False)


def istype(dict_: dict, key_: str, type_: type):
    return object_ if isinstance(object_ := dict_.get(key_, type_()), type_) else type_()


def casefold(anything):
    return str(anything).casefold()


class Comment:
    moderator_marking = ' <span style="color:green;font-weight:bold">MOD</span>'

    def __init__(self, comment_dict: dict, author: User):
        if bool(local := comment_dict.get('body')):
            self.body = markdown2.markdown(local)
        else:
            self.body = '[invalid]'
        self.is_moderator = comment_dict.get('is_moderator') is True
        self.author = author if bool(local) else deleted
        self.replies: list[Comment] = list()
        const = comment_dict.get('current_user_vote')
        if const is True or casefold(const) == 'up':
            self.current_user_vote = True
        elif const is False or casefold(const) == 'down':
            self.current_user_vote = True
        else:
            self.current_user_vote = None

    def __str__(self):
        user_markings = ' <span style="color:blue;font-weight:bold">OP</span>' if self.author.is_original_poster else ''
        user_markings = Comment.moderator_marking if self.is_moderator else user_markings
        markings = html_encode(self.author.username) + user_markings
        replies = ''.join(str(i) for i in self.replies)
        return f'<details open="" class=comment role=article><summary>{markings}</summary><div class=commentBody' \
            + f'>{self.body}</div><div role="none" class="replies">{replies}</div></details>'
        pass

    def add_reply(self, comment: typing.Self):
        self.replies.append(comment)
        return self

    def append(self, comment: typing.Self):
        self.add_reply(comment)
        return self

    pass


def comment_chain(list_: list, comments: typing.Union[list | Comment], authors: dict, comment_counted: int):
    for comment in list_:
        comment_counted += 1
        comments.append(comment_body := Comment(comment, authors.get(comment.get('author_id', '[deleted]'), deleted)))
        comment_counted = comment_chain(istype(comment, 'comments', list), comment_body, authors, comment_counted)
    return comment_counted


def to_number(number):
    if re.search('^\\d+$', str(number)):
        return int(number)
    else:
        return float('nan')


@routes.get('/vote')
async def current_user_vote(request: web.Request) -> web.Response:
    text = '<svg viewBox="0 0 1024 512" width="1024" height="512" xmlns="http://www.w3.org/2000/svg">'
    match (side := (counter := dict(request.query)).get('vote', 'n')):
        case 'u':
            color = '#ff7126'
        case 'd':
            color = '#aaaaff'
        case _:
            color = 'white'
    text += f'<rect width="1024" height="512" fill="{color}"/>'
    path_up = 'M 128 192 l 64 -64 l 64 64 h -32 v 192 h -64 v -192 Z'
    path_down = 'M 768 320 l 64 64 l 64 -64 h -32 v -192 h -64 v 192 Z'
    if side == 'u':
        text += f'<path d="{path_up}" fill="#ff7126" stroke-width="8" stroke="#000000"/>'
    else:
        text += f'<path d="{path_up}" fill="#000000" stroke-width="8" stroke="#000000"/>'
    text += '<text fill="black" id="text" font-size="256" dominant-baseline="middle" text-anchor="middle" ' + \
            'font-family="monospace" y="256" x="512">' + str(to_number(counter.get('counter', '0'))) + '</text>'
    if side == 'd':
        text += f'<path d="{path_down}" fill="#aaaaff" stroke-width="8" stroke="#000000"/>'
    else:
        text += f'<path d="{path_down}" fill="#000000" stroke-width="8" stroke="#000000"/>'

    return web.Response(text=f'{text}</svg>', content_type='image/svg+xml')


@routes.get('/')
async def comments_function(_: web.Request) -> web.Response:
    if (post := load_comments()).get('status', 200) != 200:
        text = f'<style>body{{}}*{{font-family:monospace}}</style><h1>You have malformed data</h1>'
        return web.Response(text=f'<!DOCTYPE html>{text}<pre>{html_encode(post['error'])}', content_type='text/html')
    with open('src.html', 'rt', encoding='utf8') as src:
        text = src.read()
    title = html_encode((post := load_comments()).get('post', dict()).get('title', '(untitled) RealmTester post'))
    text = text.replace('<title>RealmTester post</title>', f'<title>{title} (RealmTester)</title>')
    post = (root := post).get('post', dict())
    realm = re.sub('^(?:[a-zA-Z]/)?', 'm/', post.get('subrealm', 'RealmTester'))
    realm = dict(realm=realm, subrealm=realm.replace('m/', ''))

    text = text.replace('{{RealmTester.realm}}', html_encode(realm['subrealm']))
    text = text.replace('{{RealmTester.subrealm}}', html_encode(realm['realm']))
    text = text.replace('{{RealmTester.title}}', html_encode(post.get('title', '(untitled) RealmTester post')))
    #
    text = text.replace('{{flair_text}}', html_encode(post.get('flair_text', 'unknown')))
    text = text.replace('{{flair_css_class}}', html_encode(post.get('flair_css_class', 'unknown')))
    text = text.replace('/*flair_color*/', 'background-color:' +
                        html_encode(post.get('flair_color', '#ff4500')))
    text = text.replace('/*datetime-local*/', f"'{datetime.now().isoformat()}'")
    # datetime(2024, 6, 19)
    datetime_local = post.get('date', 'PT0S')
    if isinstance(datetime_local, datetime) or isinstance(datetime_local, date) or isinstance(datetime_local, time):
        text = text.replace(
            '<time>{{temporaryTime}}</time>',
            f'<time datetime="{datetime_local.isoformat()}Z" ' +
            f'class="toLocalTime">{datetime_local.isoformat()}</time>')
    else:
        try:
            # const = TimeInterval.from_string(str(datetime_local)).sub_to_datetime(datetime.now())
            text = text.replace(
                '<time>{{temporaryTime}}</time>',
                f'<time data-toLocalTime="{html_encode(datetime_local)}">{{enable javascript}}</time>')
        except ValueError as e:
            print('error:', e)
    if bool(author_op := post.get('author_id')):
        user = User(author_op, root.get('authors', dict()).get(author_op), True)
        text = text.replace('{{RealmTester.author}}', html_encode(user.name))
        text = text.replace('{{RealmTester.mark}}', (
            Comment.moderator_marking if (post.get('is_moderator') is True)
            else str()
        ))

    text = text.replace('{{RealmTester.body}}', markdown2.markdown(post.get('body', '[empty]')))
    if len(post.get('flair_text', '')) > 0:
        text = text.replace('data-flair_hidden hidden="hidden"', 'data-until-found=""')
    comments = list()
    authors = dict()
    for author_name, value in root.get('authors', dict()).items():
        authors[author_name] = User(author_name, value, author_op == author_name)
    comment_counted = comment_chain(istype(post, 'comments', list), comments, authors, 0)
    # <!--comment_counted-->
    # <section class="section-comment">
    # <!--comments-->
    text = re.sub('\\s*<!--comments-->\\s*', ''.join(str(i) for i in comments), text)
    text = re.sub('\\s*<!--comment_counted-->\\s*', str(comment_counted), text)
    return web.Response(text=text, content_type='text/html')


# @lambda _: _()
# def printout():
#     with open('comments-piout.json', 'wt', encoding='utf8') as file:
#         file.write(json.dumps(load_comments(), indent=4))
#     pass


(app := web.Application()).add_routes(routes)
web.run_app(app)
pass
re.compile(r'/(?:(\d)Y)? (?:(\d)M)? (?:(\d)d)? (?:(\d)H)? (?:(\d)i)? (?:(\d)s)?/')
