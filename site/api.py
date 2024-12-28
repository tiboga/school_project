import json
import os
import sys
from flask import Flask, jsonify, request
from sqlalchemy import func
from sqlalchemy import or_
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from db.db_models import cities, db_session
from db.db_models.users import Users
app = Flask(__name__)
from flask_cors import CORS
CORS(app)
@app.route("/city", methods=["GET"])
def city():
    db_sess = db_session.create_session()
    my_cities = list(map(lambda x: x.name, db_sess.query(cities.Cities).filter(
        or_(func.lower(cities.Cities.name).like(f"г {request.args.get('city').lower()}%"),
             func.lower(cities.Cities.name).like(f"{request.args.get('city').lower()}%"))).order_by(cities.Cities.population.desc()).all()[:3]))
    
    db_sess.close()
    return json.dumps({"Status":"ok", "city":my_cities})
@app.route("/reg_vol", methods=["POST"])
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
        volunteer = Users()
        volunteer.login = username
        volunteer.set_password(password)
        volunteer.city = true_name_city[0].name
        volunteer.count_resolved_tasks = 0
        db_sess.add(volunteer)
        db_sess.commit()
        db_sess.close()
        return jsonify({"Status": "ok"}), 200
    except:
        return jsonify({"Status": "err", "Error": "Something went wrong"}), 200
if __name__ == '__main__':
    db_session.global_init()
    app.run(port=8000)