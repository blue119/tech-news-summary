import json
import pickle

import httpx
import yaml
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.llm.openai import OpenAIChat

from telegram_sender import TelegramSender


# walk thru max 3 levels of comments and 3 comments per level
def _walk_thru_comments(comments=[], kids=[], max_comments: int = 3, level: int = 3):
    #     print("Getting comments", level, kids, max_comments, level)
    if level == 0:
        return

    for kid_id in kids[:max_comments]:
        kid_response = httpx.get(
            f"https://hacker-news.firebaseio.com/v0/item/{kid_id}.json"
        )
        resp = kid_response.json()
        if resp.get("deleted", False):
            continue
        comments.append(resp)
        _walk_thru_comments(comments, resp.get("kids", []), level - 1, max_comments)
    return comments


def _sort_comments(comments):
    d = {}
    res = []
    for _, c in enumerate(comments):
        d[c.get("id")] = c.get("by")

    for _, c in enumerate(comments):
        #         print(c)
        if d.get(c["parent"]):
            _pre = f"{c['by']} responsed to {d[c['parent']]}"
        else:
            _pre = f"{c['by']} say"
        res.append(f"{_pre}: {c.get('text')}")

    return res


def get_top_hackernews_stories_n_comments(
    num_stories: int = 10,
    num_comments: int = 3,
    max_comment_level: int = 3,
    ids_cache: list = [],
) -> list:
    """Use this function to get top stories and its comments from Hacker News.

    Args:
        num_stories (int): Number of stories to return. Defaults to 10.
        num_comments (int): Number of comment of story to return. Defaults to 3. max_comments_level (int): Number of comment level deep. Defaults to 1.

    Returns:
        str: JSON string of top stories w/ comments.
    """

    # Fetch top story IDs
    resp = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = resp.json()

    # Fetch story details
    stories = []
    for story_id in story_ids[:num_stories]:
        if story_id in ids_cache:
            print("Skip", story_id)
            continue
        story_response = httpx.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        )
        story = story_response.json()
        print(story["title"])
        comments = _walk_thru_comments(
            [], story.get("kids", []), num_comments, max_comment_level
        )

        story["comments"] = _sort_comments(comments)

        stories.append(story)

    return stories


prompt = """
those comments are from hackernews
the comments summary should be less than 300 words and give it a proper emoji.
you should also summarize the comments in Tranditional Han. 

please return a json format  that can be used in the following format.
please don't include others information such as json word in begin and ``` that is important. if you include it
following parsing is able to prase it and let the program crash.

    {"en": <summary>, "zh": <中文評論>}

here is comments

"""


def main(n_of_story=7):
    try:
        with open("ids_cache.pkl", "rb") as file:
            ids_cache = pickle.load(file)
    except FileNotFoundError:
        ids_cache = []

    stories = get_top_hackernews_stories_n_comments(
        num_stories=n_of_story, ids_cache=ids_cache
    )

    with open("cfg.yml", "r", encoding="utf-8") as file:
        cfg = yaml.safe_load(file)

    assistant = Assistant(
        llm=OpenAIChat(model="gpt-4o-mini", max_tokens=500, temperature=0.5),
        api_key=cfg["openai"]["api_key"],
        debug_mode=False,
        markdown=True,
    )

    ts = TelegramSender(
        token=cfg["telegram"]["token"], chat_id=cfg["telegram"]["chat_id"]
    )

    for t in stories:
        response = ""
        _prompt = 'title: {t["title"]}\n' + prompt + "\n".join(t["comments"])
        for delta in assistant.run(_prompt):
            response += delta
        comments = json.loads(response)
        template = f"""{t.get('url')}
    
        {t['title']} ({t['score']}/{t['descendants']})
    
        ● {comments['en']}
    
        ● {comments['zh']}
        """
        ts.send_telegram_message(message=template)
        ids_cache.append(t["id"])

    with open("ids_cache.pkl", "wb") as file:
        pickle.dump(ids_cache, file)


if __name__ == "__main__":
    main()
