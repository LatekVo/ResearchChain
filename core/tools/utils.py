import asyncio
import multiprocessing
import re
import uuid


def purify_name(name):
    return '_'.join('_'.join(name.split(':')).split('-'))


def is_text_junk(text: str):
    # checks if text contains any of junky keywords eg: privacy policy, subscribe, cookies etc.
    # do not expand this list, it has to be small to be efficient, and these words are grouped either way.
    trigger_list = [
        'sign in', 'privacy policy', 'skip to', 'newsletter', 'subscribe', 'related tags', 'share price'
    ]
    low_text = text.lower()
    for trigger in trigger_list:
        if trigger in low_text:
            return True
    return False


def extract_from_quote(text: str):
    if '"' in text:
        return text.split('"')[1]
    else:
        return text


def reduce(text: str, goal: str, match: str):
    if match in text:
        text = goal.join(text.split(match))
        return reduce(text, goal, match)
    return goal.join(text.split(match))


def remove(text: str, wordlist: list):
    for word in wordlist:
        text = ''.join(text.split(word))
    return text


def timeout_function(task, timeout=2.0):
    # FIXME: THIS FUNCTION MAY BE BROKEN, TEST THIS

    ctx = multiprocessing.get_context('spawn')
    q = ctx.Queue()

    def wrapper(q):
        task_result = task()
        q.put(task_result)

    thread_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(thread_loop)

    thread = ctx.Process(target=wrapper, args=(q,))

    thread.start()
    thread.join(timeout)  # close thread if work is finished
    if thread.is_alive():
        thread.kill()
        return None

    result = q.get()

    thread_loop.run_until_complete(asyncio.sleep(0))
    thread_loop.close()

    return result


def extract_links(text: str):
    return re.findall(r'(https?://\S+)', text)


def gen_uuid() -> str:
    return uuid.uuid4().hex
