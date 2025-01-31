import json
import re
import typing

import markdown2
import yaml
from aiohttp import web

routes = web.RouteTableDef()
cache = None


def html_encode(strx: str) -> str:
    strx = strx.replace('&', '&amp;')
    strx = strx.replace('"', '&quot;')
    strx = strx.replace("'", '&#39;')
    return strx.replace('<', '&lt;').replace('>', '&gt;')


def load_comments():
    global cache
    with open('comments.yaml', 'rt', encoding='utf8') as file:
        comments = yaml.safe_load_all(file.read())
    cache = comments = list(comments)[0]
    # if cache is None:
    #     with open('comments.yaml', 'rt', encoding='utf8') as file:
    #         comments = yaml.safe_load_all(file.read())
    #     cache = comments = list(comments)[0]
    # else:
    #     comments = cache
    return comments


@routes.get('/favicon.ico')
@routes.get('/favicond.svg')
async def icond(request: web.Request) -> web.Response:
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
    def __init__(self, name: str, authors: dict):
        name = re.sub('^(?:[a-zA-Z]/)?', 'u/', str(name))
        self.profile_image_url = str(authors.get('profile_image_url', '/favicon.ico'))
        self.username = re.sub('^u/', '', name)
        self.flair_css_class = flair_text if isinstance(flair_text := authors.get('flair', dict()), dict) else dict()
        self.name = name
        self.is_valid = \
            re.search('^m/[a-zA-Z0-9\\-_]$', name)
        pass

    pass


deleted = User('[deleted]', dict())


def istype(dict_: dict, key_: str, type_: type):
    return object_ if isinstance(object_ := dict_.get(key_, type_()), type_) else type_()


def casefold(anything):
    return str(anything).casefold()


class Comment:
    def __init__(self, comment_dict: dict, author: User):
        if bool(local := comment_dict.get('body')):
            self.body = markdown2.markdown(local)
        else:
            self.body = '[invalid]'
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
        return f'<div class="comment" role=none><article><span>{html_encode(self.author.username)}</span>{self.body}' \
            + f'</article><div role="none" class="replies">{''.join(str(i) for i in self.replies)}</div></div>'

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
async def comments_function(request: web.Request) -> web.Response:
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
    text = text.replace('{{RealmTester.body}}', markdown2.markdown(post.get('body', '[empty]')))
    if len(post.get('flair_text', '')) > 0:
        text = text.replace('data-flair_hidden hidden="hidden"', 'data-until-found=""')
    comments = list()
    authors = dict()
    for author_name, value in root.get('authors', dict()).items():
        authors[author_name] = User(author_name, value)
    comment_counted = comment_chain(istype(post, 'comments', list), comments, authors, 0)
    # <!--comment_counted-->
    # <section class="section-comment">
    # <!--comments-->
    text = re.sub('\\s*<!--comments-->\\s*', ''.join(str(i) for i in comments), text)
    text = re.sub('\\s*<!--comment_counted-->\\s*', str(comment_counted), text)
    return web.Response(text=text, content_type='text/html')


# <article class="comment">
#             <span>username</span>
#             <p>comment body</p>
#
#             <div role=none class="replies">
#                 <article class="comment">
#                     <span>username</span>
#                     <p>comment body</p>
#
#                     <div role="none" class="replies">
#                         <!-- More nested comments can go here -->
#                     </div>
#                 </article>
#             </div>
#         </article>

@lambda _: _()
def printout():
    with open('comments-piout.json', 'wt', encoding='utf8') as file:
        file.write(json.dumps(load_comments(), indent=4))
    pass


(app := web.Application()).add_routes(routes)
web.run_app(app)
pass
