from asyncio import Task
import os
import sys
from flask import Flask, flash, jsonify, redirect, render_template, request
from flask_login import LoginManager, current_user, login_fresh, login_required, logout_user, login_user
from sqlalchemy import func, or_


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from db.db_models.tasks import Tasks
from db.db_models import cities, db_session
from db.db_models.users import Users
app = Flask(__name__)
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
@app.route("/add_task")
def add_task():
    return render_template("add_task.html")
@app.route("/profile")
def profile():
    return render_template("profile.html")
@app.route("/")
def main():
    return render_template("main.html")
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


# API



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
        db_sess.close()
        return jsonify({"Status": "ok"}), 200
    except Exception as exc:
        print(exc)
        return jsonify({"Status": "err", "Error": "Something went wrong"}), 200
@app.route("/api/add_task", methods=["POST"])
def api_add_task():
    try:
        db_sess = db_session.create_session()
        task = Tasks()
        task.coord_1 = float(request.args.get("coord").split(",")[0])
        task.coord_2 = float(request.args.get("coord").split(",")[1])
        task.note = request.args.get("note")
        task.ended = False
        db_sess.add(task)
        db_sess.commit()
        db_sess.close()
        return {"Status":"ok"}, 200
    except:
        return {"Status":"err", "Error":"Something went wrong"}, 200
if __name__ == '__main__':
    db_session.global_init()
    app.run(port=5050)