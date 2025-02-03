# RealmTester1: Reddit simulator (old.reddit.com)

RealmTester1 is a python program by github.com/Qin2007 to simulate reddit conversations

to make a fake convo simply make a `comments.yaml` in the directory.

## set up

[download python from python.org](https://www.python.org/downloads/) and make python
install `requirements.txt` (`pip install -r requirements.txt` or the path to that file)

# yaml config

in the yaml configuration you write the exact convocation you want your characters to have (profile images not
supported).

```yaml
RealmTester: 0.0
post:
  title: Hot takes?
  subrealm: m/HotTakes
  body: |
    what are you guy's hot takes
  author_id: Favicond
authors:
  Favicond:
    flair_text: ""
    profile_image_url: https://ant.ractoc.com/dollmaker1/?bgcolor=%2300a8f3&fgcolor=%238cfffb&L=%23fff200&W=%23000000
```

that is a basic example of what to write.

`RealmTester: 0.0` is the version of the RealmTester script (does nothing)

`post:` is the main item you'll be writing under. the post sub-block has a few items ("keys")

- `title:` is the post title
- `subrealm:` is basically the subreddit (RealmTester uses `m/` instead of `r/`)
- `body:` is the post body. it supports markdown (be careful about html, it supports that too)
- `author_id:` an author under the `authors:` sub-block
- `approval_status:` approval_status is either "approved" or "removed" or "none" (DEFAULT="none"), [true, false, null]
  works too
- `is_moderator:` if `true` it will show the mod badge (ADMIN is not supported)
- `flair_text:` is the post flair text
- `date:` date is some numbers with a letter after it: `Y` for years, `M` for months (not minutes), `D` for days, `H`
  for hours, `i` for minutes, and `s` for seconds  
  otherwise it can be a valid timestamp formatted `YYYY-MM-DD`  
  for example `7i 5s` is 7 minutes and 5 seconds ago
- `current_user_vote:` current_user_vote is either "up" or "down" or "none" (DEFAULT="none"), [true, false, null] works
  too. current user vote is how the votes are displayed, if its `up` then it will look like you upvoted
- `votes:` (must be a valid number) is the score displayed, unaffected by `current_user_vote:`

the main thing you'll be here for is

`comments:` each comment has the following keys (comments are very similar to posts)

- `body:` is the comment body. it supports markdown.
- `author_id:` an author under the `authors:` sub-block
- `is_moderator:` if `true` it will show the mod badge (ADMIN is not supported)
- `date:` (currently not implemented) date is some numbers with a letter after it: `Y` for years, `M` for months (not
  minutes), `D` for days, `H` for hours, `i` for minutes, and `s` for seconds  
  otherwise it can be a valid timestamp formatted `YYYY-MM-DD`  
  for example `7i 5s` is 7 minutes and 5 seconds ago
- `current_user_vote:`  current_user_vote is either "up" or "down" or "none" (DEFAULT="
  none"), [true, false, null] works too. current user vote is how the votes are displayed, if its `up` then it will look
  like you upvoted
- `votes:` (must be a valid number) is the score displayed, unaffected
  by `current_user_vote:`
- `is_locked:` (currently not implemented) whether a comment is locked (boolean)
- `is_stickied:` (currently not implemented) whether a comment is stickied, note that only top level comments can be
  stickied and only one. the
  first one will be stickied if there are multiple with this on (boolean)

have fun