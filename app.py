import json
import os
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据目录与代码目录分离：部署后代码会被新版本覆盖，数据必须留在外面
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "database.json")
LEGACY_DB_PATH = os.path.join(BASE_DIR, "database.json")

app = Flask(__name__)


def migrate_legacy():
    """首次启动时把旧位置的数据迁移到 DATA_DIR"""
    if os.path.exists(LEGACY_DB_PATH) and not os.path.exists(DB_PATH):
        os.replace(LEGACY_DB_PATH, DB_PATH)


def load_messages():
    """读取全部留言，文件不存在时返回空列表"""
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("messages", [])


def save_messages(messages):
    """整体写回 database.json（先写临时文件再替换，避免写一半）"""
    tmp = DB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"messages": messages}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_PATH)


def next_id(messages):
    return max((m["id"] for m in messages), default=0) + 1


migrate_legacy()


@app.route("/")
def index():
    # 最新的排在最前面
    messages = sorted(load_messages(), key=lambda m: m["id"], reverse=True)
    return render_template("index.html", messages=messages)


@app.route("/new", methods=["GET", "POST"])
def new_message():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip() or "匿名"
        text = (request.form.get("text") or "").strip()
        if text:
            messages = load_messages()
            messages.append(
                {
                    "id": next_id(messages),
                    "name": name,
                    "text": text,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            )
            save_messages(messages)
        # PRG：提交后重定向，刷新不会重复写入
        return redirect(url_for("index"))
    return render_template("new.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/api/messages")
def api_messages():
    messages = sorted(load_messages(), key=lambda m: m["id"], reverse=True)
    return jsonify({"count": len(messages), "messages": messages})


@app.route("/healthz")
def healthz():
    # 只确认数据目录可写，不依赖任何外部服务
    os.makedirs(DATA_DIR, exist_ok=True)
    probe = os.path.join(DATA_DIR, ".probe")
    with open(probe, "w", encoding="utf-8") as f:
        f.write("ok")
    os.remove(probe)
    return "ok", 200
