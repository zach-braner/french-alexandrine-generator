from browser import document, ajax

url = "http://api.open-notify.org/iss-now.json"
msg = "Position of the International Space Station at {}: {}"

def complete(request):
    import json
    import datetime
    data = json.loads(request.responseText)
    position = data["iss_position"]
    ts = data["timestamp"]
    now = datetime.datetime.fromtimestamp(ts)
    document["zone10"].text = msg.format(now, position)

def click(event):
    req = ajax.ajax()
    req.open("GET", url, True)
    req.bind("complete", complete)
    document["result"].text = "waiting..."
    req.send()

document["button10"].bind("click", click)