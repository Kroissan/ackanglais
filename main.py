import requests
from datetime import datetime
from datetime import timezone

headers = {}
headers["Authorization"] = "a remplir"

user = requests.get("https://portal.gofluent.com/mobile-rest/ws/user", headers=headers).json()["User"]
userId = user['uuid']

deviceId = "a remplir"
tabId = "a remplir"
deviceTabId = "a remplir"
PortalId = "7449c9c9-6523-4e16-9767-00a775969c12"


def get_user_info():
    global headers
    return requests.get("https://portal.gofluent.com/mobile-rest/ws/user", headers=headers).json()["User"]

def get_article_list(list=0):
    res=[]
    for a in requests.get("https://portal.gofluent.com/en/api/v1.0/content/article/list/"+str(list), headers=headers).json():
        res.append(a['articleId'])
    return res

def get_video_list(list=0):
    res=[]
    for a in requests.get("https://portal.gofluent.com/en/api/v1.0/content/video/list/"+str(list), headers=headers).json():
        res.append(a['articleId'])
    return res

def track_event(json):
    global headers, deviceId, userId, tabId, PortalId
    json["deviceId"] = deviceId
    json["userId"] = userId
    json["tabId"] = tabId
    json["attributes"]["PortalId"] = PortalId
    json["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return requests.post("https://portal.gofluent.com/api/v1.0.0/track/event", json=json,
                         headers=headers).status_code == 200


def portal_track_event(json):
    global headers, deviceId, userId, deviceTabId
    json["deviceId"] = deviceId
    json["userId"] = userId
    json["deviceTabId"] = deviceTabId
    json["latitude"] = None
    json["longitude"] = None
    json["client"] = {"app": {"type": "browser", "version": "gofluent-portal 5.19.8"},
                      "browser": {"resolution": {"width": 1920, "height": 1080}}}
    json["timestamp"] = int(datetime.now(timezone.utc).timestamp())
    return requests.post("https://portal.gofluent.com/api/v1.0/portal/event", json=json,
                         headers=headers).status_code == 200


def get_article_info(uid):  # groupid & article id is associated to article
    global headers
    return requests.post("https://portal.gofluent.com/en/api/v1.0/content/article/" + str(uid), headers=headers).json()


def get_quiz(article):
    global headers, user
    params = {"qArticleId": int(article["quizArticleId"]), "articleId": int(article['articleId']),
              "learnerId": int(user["learnerId"]), "groupId": int(article["groupId"])}
    return requests.post("https://portal.gofluent.com/mobile-rest/ws/quiz", json=params, headers=headers).json()


def is_quizz_passed(quizz):
    if len(quizz['qh'])>0:
        return quizz['qh'][0]['s'] == "PASSED"
    return False


def get_answer(article):
    res = []
    for i in get_quiz(article)['q']:
        if isinstance(i['ans'], str):
            res.append(i['ans'])
        else:
            t = str(type(i['ans'][0]))
            if "int" in t:
                res.append(i['ans'])
            elif "dict" in t:
                tmp = []
                for q in i['ans']:
                    tmp.append(q['ans'][0])
                res.append(tmp)
            elif "str" in t:
                res.append(i['ans'][0])
    return res


def get_topic_from_content(contentid):
    global headers
    return requests.get("https://portal.gofluent.com/api/v1.0.0/content/" + contentid, headers=headers).json()['metadata']['topics'][0]


def solve_quizz(article):
    global headers, user
    answer = get_answer(article)
    quiz = get_quiz(article)
    params = {"interactions": [], "qArticleId": int(article["quizArticleId"]), "articleId": int(article['articleId']),
              "learnerId": int(user["learnerId"]), "groupId": int(article["groupId"]), "rawScore": 1, "sequence": [],
              "qResultId": 0, "totalItems": quiz['noi'], "trackable": "true"}
    qResultId = 0
    for i in range(0, quiz['noi']):
        interactions = []
        sequence = []
        for j in range(0, i + 1):
            interactions.append({"t": "00:00:00", "q": j + 1, "s": j + 1, "a": answer[j]})
            sequence.append(j + 1)
        params["rawScore"] = i + 1
        params["interactions"] = interactions
        params["sequence"] = sequence
        params["qResultId"] = qResultId
        x = requests.post("https://portal.gofluent.com/mobile-rest/ws/quiz/save", json=params, headers=headers)
        qResultId = x.json()['qri']

    savejson = {"topicId": get_topic_from_content(article['contentUUId']), "contentId": article['contentUUId'],
                "type": "QuizScore",
                "quizId": article['quizUUID'], "score": 1,
                "attributes": {"CourseId": article['articleId']}}
    track_event(savejson)


def oppen_content(content):
    track_event()
def ping(content):
    portal_track_event({"portalEvent":{"category": "control", "contentId":content, "topicId":get_topic_from_content(content)}});
    portal_track_event({"type":"PortalTabPresence", "topicId":get_topic_from_content(content)})


for a in get_video_list(0):
    art=get_article_info(a)
    if is_quizz_passed(get_quiz(art)) == False:
        print("solving: " + art['name'])
        solve_quizz(art)

exit()

