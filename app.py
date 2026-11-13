import json
import os
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.json")

app = Flask(__name__)


def load_messages():
    """读取全部留言，文件不存在时返回空列表"""
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("messages", [])


def save_messages(messages):
    """整体写回 database.json"""
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump({"messages": messages}, f, ensure_ascii=False, indent=2)


def next_id(messages):
    return max((m["id"] for m in messages), default=0) + 1


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


if __name__ == "__main__":
    # 5001：避开已有项目占用的 5000
    app.run(host="0.0.0.0", port=5001, debug=True)
