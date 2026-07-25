import json
try:
    c = json.load(open('comments.json'))
    if isinstance(c, list):
        for x in c:
            if x.get('user', {}).get('login') != 'kiet08hogit':
                print(f"General Comment by {x['user']['login']}:\n{x['body']}\n---\n")
except Exception as e: print(e)
try:
    r = json.load(open('review_comments.json'))
    if isinstance(r, list):
        for x in r:
            if x.get('user', {}).get('login') != 'kiet08hogit':
                print(f"Review Comment by {x['user']['login']} on {x.get('path', '')}:\n{x['body']}\n---\n")
except Exception as e: print(e)
