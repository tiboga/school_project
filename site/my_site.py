from asyncio import Task
import json
import logging
import os
import sys
from flask import Flask, flash, jsonify, redirect, render_template, request
from flask_login import LoginManager, current_user, login_fresh, login_required, logout_user, login_user
import requests
from sqlalchemy import desc, func, or_


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from db.db_models.tasks import Tasks
from db.db_models import cities, db_session
from db.db_models.users import Users
app = Flask(__name__)
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    level=logging.INFO
)
app.config['SECRET_KEY'] = 'flask_project_secret_key'
login_manager = LoginManager(app)
login_manager.login_message = "Авторизация успешно выполнена"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Users).filter(Users.id == user_id).first()

@app.route("/reg", methods=["GET", "POST"])
def reg():
    return render_template("registration.html")
@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")
@app.route("/add_task")
def add_task():
    return render_template("add_task.html")



@app.route("/profile")
def profile():
    db_sess = db_session.create_session()
    volunteer_applications = db_sess.query(Tasks).filter(Tasks.volunteer_id==current_user.id).all()
    vol_app = []
    for elem in volunteer_applications:
        vol_app.append({"address":
                        json.loads(
                            requests.get(
                                f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key[:-1]}&geocode={elem.coord_2}, {elem.coord_1}&format=json").text)["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["Address"]["formatted"],
                        "coord_1": elem.coord_1,
                        "coord_2": elem.coord_2,
                        "note": "Описания нет" if elem.note == "" else elem.note,
                        })
    user_applications = db_sess.query(Tasks).filter(Tasks.user_id==current_user.id).all()
    us_app = []
    for elem in user_applications:
        us_app.append(
            {"address":
             json.loads(
                 requests.get(
                     f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key[:-1]}&geocode={elem.coord_2}, {elem.coord_1}&format=json").text)["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["Address"]["formatted"],
            "coord_1": elem.coord_1,
            "coord_2": elem.coord_2,
            "note": "Описания нет" if elem.note is None else elem.note,
            "volunteer": "Пока никто не принял Вашу заявку" if elem.volunteer_id is None else db_sess.query(Users).filter(elem.volunteer_id==Users.id).first().login
            })
                     
    profile_info = {"vol_app":vol_app,
                    "user_app":us_app,
                    "name":current_user.login,
                    "city":current_user.city,
                    "count_order_placed":current_user.count_order_placed if current_user.count_order_placed is not None else 0,
                    "count_order_completed":current_user.count_order_completed if current_user.count_order_completed is not None else 0
    }
    return render_template("profile.html", profile_info=profile_info)
@app.route("/")
def main():
    return render_template("main.html")
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/get_task")
@login_required
def get_task():
    db_sess = db_session.create_session()
    tasks = db_sess.query(Tasks, Users).filter(Tasks.ended==False, Tasks.user_id==Users.id, Tasks.volunteer_id == None).order_by(desc(Tasks.id)).all()
    out_sp = []
    for elem in tasks:
        address = json.loads(requests.get(f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key[:-1]}&geocode={elem[0].coord_2}, {elem[0].coord_1}&format=json").text)["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["Address"]["formatted"]
        out_sp.append({"note" : elem[0].note if elem[0].note!="" else "Пользователь не предоставил описание",
                       "name_user": elem[1].login, 
                       "address": address,
                       "created_on": elem[0].created_on.strftime("%Y-%m-%d %H:%M"),
                       "coord_1": elem[0].coord_1,
                       "coord_2": elem[0].coord_2,
                       "id":elem[0].id})
    out_sp_formatted = []
    tmp = []
    for elem in out_sp:
        tmp.append(elem)
        if len(tmp) == 4:
            out_sp_formatted.append(tmp)
            tmp = []
    if len(tmp) != 4:
        out_sp_formatted.append(tmp)
    return render_template("find_tasks.html", sp=out_sp_formatted, id_of_user=current_user.id)



# API


@app.route("/api/get_task", methods=["POST"])
def api_get_task():
    user_id = request.args.get("user_id")
    task_id = request.args.get("task_id")
    db_sess = db_session.create_session()
    task = db_sess.query(Tasks).filter(Tasks.id==int(task_id)).first()
    task.volunteer_id = user_id
    db_sess.commit()
    db_sess.close()
    return {"Status":"ok"}
@app.route("/api/city", methods=["GET"])
def city():
    db_sess = db_session.create_session()
    my_cities = list(map(lambda x: x.name, db_sess.query(cities.Cities).filter(
        or_(func.lower(cities.Cities.name).like(f"г {request.args.get('city').lower()}%"),
             func.lower(cities.Cities.name).like(f"{request.args.get('city').lower()}%"))).order_by(cities.Cities.population.desc()).all()[:3]))
    
    db_sess.close()
    return jsonify({"Status":"ok", "city":my_cities}), 200
@app.route("/api/reg", methods=["POST"])
def reg_vol():
    try:
        username = request.args.get("username")
        password = request.args.get("password")
        city = request.args.get("city")
        db_sess = db_session.create_session()
        if len(db_sess.query(Users).filter(Users.login == username).all()) != 0:
            return jsonify({"Status":"err", "Error":"username is exits"}), 200
        true_name_city = db_sess.query(cities.Cities).filter(or_(or_(func.lower(cities.Cities.name).like(f"г {city.lower()}%"),
                func.lower(cities.Cities.name).like(f"{city.lower()}%")))).all()
        if len(true_name_city) != 1:
            return jsonify({"Status":"err", "Error":"name of city bad"}), 200
        user = Users()
        user.id = max([0]+[vol.id for vol in db_sess.query(Users).all()]) + 1
        user.login = username
        user.set_password(password)
        user.city = true_name_city[0].name
        user.count_resolved_tasks = 0
        user.volunteer = 1
        login_user(user, remember=True)
        db_sess.add(user)
        db_sess.commit()
        u_id = user.id
        db_sess.close()
        return jsonify({"Status": "ok", "id": u_id}), 200
    except Exception as exc:
        print(exc)
        return jsonify({"Status": "err", "Error": "Something went wrong"}), 200
@app.route("/api/login", methods={"POST"})
def api_login():
    try:
        db_sess = db_session.create_session()
        username = request.args.get("username")
        password = request.args.get("password")
        user = db_sess.query(Users).filter(Users.login == username).all()
        if len(user) == 0:
            return {"Status":"err", "Error":"username is not exists"}
        if user[0].check_password(password) == True:
            login_user(user[0], remember=True)
            return {"Status": "ok", "id": user[0].id}, 200
        else:
            return {"Status": "err", "Error":"incorrect password"}, 200
    except:
        return {"Status":"err", "Error":"Something went wrong"}, 200

@app.route("/api/add_task", methods=["POST"])
def api_add_task():
    try:
        db_sess = db_session.create_session()
        task = Tasks()
        task.coord_1 = float(request.args.get("coord").split(",")[0])
        task.coord_2 = float(request.args.get("coord").split(",")[1])
        task.note = request.args.get("note")
        task.ended = False
        task.user_id = current_user.id
        db_sess.add(task)
        db_sess.commit()
        db_sess.close()
        return {"Status":"ok"}, 200
    except:
        return {"Status":"err", "Error":"Something went wrong"}, 200
if __name__ == '__main__':
    api_key = open("api_key.txt", 'r').readline()
    db_session.global_init()
    app.run(host='0.0.0.0', port=5050)