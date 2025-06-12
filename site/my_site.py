#!~/M2SAMSUNG/api/school_project
import json
import logging
import os
import re
from flask import Flask, jsonify, redirect, render_template, request, send_file
from flask_login import LoginManager, current_user
from flask_login import login_required, logout_user, login_user
import requests
from sqlalchemy import desc, func, or_
import sqlalchemy
from db.db_models.tasks import Tasks
from db.db_models import cities, db_session
from db.db_models.users import Users

import datetime

app = Flask(__name__)
logging.basicConfig(
    format=('%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'),
    level=logging.INFO,
)
app.config['SECRET_KEY'] = 'flask_project_secret_key'
login_manager = LoginManager(app)
login_manager.login_message = 'Авторизация успешно выполнена'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.id == user_id).first()
    db_sess.close()
    return user


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    return render_template('registration.html')


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/add_task')
def add_task():
    return render_template('add_task.html')


@app.route('/profile')
def profile():
    db_sess = db_session.create_session()
    volunteer_applications = (
        db_sess.query(Tasks)
        .filter(Tasks.volunteer_id == current_user.id)
        .all()
    )
    vol_app = []
    for elem in volunteer_applications:
        vol_app.append(
            {
                'address': json.loads(
                    requests.get(
                        (f'https://geocode-maps.yandex.ru/1.x/?apikey='
                         f'{api_key[:-1]}&geocode={elem.coord_2},'
                         f' {elem.coord_1}&format=json')
                    ).text
                )['response']['GeoObjectCollection']['featureMember'][0][
                    'GeoObject'
                ][
                    'metaDataProperty'
                ][
                    'GeocoderMetaData'
                ][
                    'Address'
                ][
                    'formatted'
                ],
                'coord_1': elem.coord_1,
                'coord_2': elem.coord_2,
                'note': 'Описания нет' if elem.note == '' else elem.note,
            }
        )
    user_applications = (
        db_sess.query(Tasks).filter(Tasks.user_id == current_user.id).all()
    )
    us_app = []
    for elem in user_applications:
        us_app.append(
            {
                'address': json.loads(
                    requests.get(
                        (f'https://geocode-maps.yandex.ru/1.x/?apikey='
                         f'{api_key[:-1]}&geocode={elem.coord_2},'
                         f' {elem.coord_1}&format=json')
                    ).text
                )['response']['GeoObjectCollection']['featureMember'][0][
                    'GeoObject'
                ][
                    'metaDataProperty'
                ][
                    'GeocoderMetaData'
                ][
                    'Address'
                ][
                    'formatted'
                ],
                'coord_1': elem.coord_1,
                'coord_2': elem.coord_2,
                'note': 'Описания нет' if elem.note is None else elem.note,
                'volunteer': (
                    'Пока никто не принял Вашу заявку'
                    if elem.volunteer_id is None
                    else db_sess.query(Users)
                    .filter(elem.volunteer_id == Users.id)
                    .first()
                    .login
                ),
            }
        )

    profile_info = {
        'vol_app': vol_app,
        'user_app': us_app,
        'name': current_user.login,
        'city': current_user.city,
        'count_order_placed': (
            current_user.count_order_placed
            if current_user.count_order_placed is not None
            else 0
        ),
        'count_order_completed': (
            current_user.count_order_completed
            if current_user.count_order_completed is not None
            else 0
        ),
    }
    db_sess.close()
    return render_template('profile.html', profile_info=profile_info)


@app.route('/')
def main():
    return render_template('main.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/get_task')
@login_required
def get_task():
    db_sess = db_session.create_session()
    tasks = (
        db_sess.query(Tasks, Users)
        .filter(
            Tasks.ended is False,
            Tasks.user_id == Users.id,
            Tasks.volunteer_id is None,
        )
        .order_by(desc(Tasks.id))
        .all()
    )
    out_sp = []
    for elem in tasks:
        address = json.loads(
            requests.get(
                (f'https://geocode-maps.yandex.ru/1.x/?apikey={api_key[:-1]}'
                 f'&geocode={elem[0].coord_2}, {elem[0].coord_1}&format=json')
            ).text
        )['response']['GeoObjectCollection']['featureMember'][0]['GeoObject'][
            'metaDataProperty'
        ][
            'GeocoderMetaData'
        ][
            'Address'
        ][
            'formatted'
        ]
        out_sp.append(
            {
                'note': (
                    elem[0].note
                    if elem[0].note != ''
                    else 'Пользователь не предоставил описание'
                ),
                'name_user': elem[1].login,
                'address': address,
                'created_on': elem[0].created_on.strftime('%Y-%m-%d %H:%M'),
                'coord_1': elem[0].coord_1,
                'coord_2': elem[0].coord_2,
                'id': elem[0].id,
            }
        )
    out_sp_formatted = []
    tmp = []
    for elem in out_sp:
        tmp.append(elem)
        if len(tmp) == 4:
            out_sp_formatted.append(tmp)
            tmp = []
    if len(tmp) != 4:
        out_sp_formatted.append(tmp)
    db_sess.close()
    return render_template(
        'find_tasks.html', sp=out_sp_formatted, id_of_user=current_user.id
    )


# API


@app.route('/api/get_task', methods=['POST'])
def api_get_task():
    user_id = request.args.get('user_id')
    task_id = request.args.get('task_id')
    db_sess = db_session.create_session()
    task = db_sess.query(Tasks).filter(Tasks.id == int(task_id)).first()
    task.volunteer_id = user_id
    db_sess.commit()
    db_sess.close()
    return {'Status': 'ok'}


@app.route('/api/city', methods=['GET'])
def city():
    db_sess = db_session.create_session()
    my_cities = list(
        map(
            lambda x: x.name,
            db_sess.query(cities.Cities)
            .filter(
                or_(
                    func.lower(cities.Cities.name).like(
                        f'г {request.args.get("city").lower()}%'
                    ),
                    func.lower(cities.Cities.name).like(
                        f'{request.args.get("city").lower()}%'
                    ),
                )
            )
            .order_by(cities.Cities.population.desc())
            .all()[:3],
        )
    )

    db_sess.close()
    return jsonify({'Status': 'ok', 'city': my_cities}), 200

@app.route('/api/add_fcm_token_to_user', methods=["POST"])
def add_fcm_token_to_user():
    try:
        uid = int(request.args.get('uid'))
        token = request.args.get('token')
        db_sess= db_session.create_session()
        user = db_sess.query(Users).filter(Users.id==uid).first()
        user.fcm_token = token
        db_sess.commit()
        db_sess.close()
        return {"Status": "ok"}
    except Exception as exc:
        print(exc)
        return jsonify({'Status': 'err', 'Error': 'Something went wrong'}), 200

@app.route('/api/change_password/<uid>', methods=['POST'])
def change_password(uid):
    try:
        data = request.get_json()
        password_pred = data.get("password_pred")
        password_current = data.get("password_current")
        db_sess = db_session.create_session()
        user = db_sess.query(Users).filter(Users.id==uid).first()
        if not user.check_password(password_pred):
            return jsonify({"Status": "err", "Error": "not valid password_pred"})
        user.set_password(password_current)
        db_sess.commit()
        db_sess.close()
        return {"Status": "ok"}
    except Exception as exc:
        print(exc)
        return jsonify({'Status': 'err', 'Error': 'Something went wrong'}), 200  

@app.route('/api/reg', methods=['POST'])
def reg_vol():
    try:
        username = request.args.get('username')
        password = request.args.get('password')
        contact_info = request.args.get('contact_info')
        city = request.args.get('city')
        db_sess = db_session.create_session()
        if (
            len(db_sess.query(Users).filter(Users.login == username).all())
            != 0
        ):
            return (
                jsonify({'Status': 'err', 'Error': 'username is exits'}),
                200,
            )
        true_name_city = (
            db_sess.query(cities.Cities)
            .filter(
                or_(
                    or_(
                        func.lower(cities.Cities.name).like(
                            f'г {city.lower()}%'
                        ),
                        func.lower(cities.Cities.name).like(
                            f'{city.lower()}%'
                        ),
                    )
                )
            )
            .all()
        )
        if len(true_name_city) != 1:
            return jsonify({'Status': 'err', 'Error': 'name of city bad'}), 200
        user = Users()
        user.id = max([0] + [vol.id for vol in db_sess.query(Users).all()]) + 1
        user.login = username
        user.set_password(password)
        user.city = true_name_city[0].name
        user.count_resolved_tasks = 0
        user.contact_information = contact_info
        user.volunteer = 1
        login_user(user, remember=True)
        db_sess.add(user)
        db_sess.commit()
        u_id = user.id
        db_sess.close()
        return jsonify({'Status': 'ok', 'id': u_id}), 200
    except Exception as exc:
        print(str(exc))
        return jsonify({'Status': 'err', 'Error': 'Something went wrong'}), 200


@app.route('/api/login', methods={'POST'})
def api_login():
    try:
        db_sess = db_session.create_session()
        username = request.args.get('username')
        password = request.args.get('password')
        user = db_sess.query(Users).filter(Users.login == username).all()
        if len(user) == 0:
            return {'Status': 'err', 'Error': 'username is not exists'}
        if user[0].check_password(password) is True:
            login_user(user[0], remember=True)
            return {'Status': 'ok', 'id': user[0].id}, 200
        else:
            return {'Status': 'err', 'Error': 'incorrect password'}, 200
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200
    finally:
        db_sess.close()

@app.route('/api/add_task_to_user', methods=['POST'])
def api_add_task_to_volunteer():
    try:
        db_sess = db_session.create_session()
        task = db_sess.query(Tasks).filter(Tasks.id == int(request.args.get('item_id'))).first()
        task.volunteer_id = int(request.args.get('user_id'))
        db_sess.commit()
        db_sess.close()
        return {'Status': 'ok'}, 200
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200

@app.route('/api/add_task', methods=['POST'])
def api_add_task():
    try:
        db_sess = db_session.create_session()
        task = Tasks()
        task.coord_1 = float(request.args.get('coord').split(',')[0])
        task.coord_2 = float(request.args.get('coord').split(',')[1])
        task.note = request.args.get('note')
        task.ended = False
        task.user_id = current_user.id
        task.status = 'Добавлено'
        db_sess.add(task)
        db_sess.commit()
        db_sess.close()
        return {'Status': 'ok'}, 200
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/add_task_from_mobile', methods=['POST'])
def api_add_task_from_mobile():
    try:
        db_sess = db_session.create_session()
        user = db_sess.query(Users).filter(Users.id==request.args.get('uid')).first()
        user.count_order_placed += 1
        task = Tasks()
        curr_id = sqlalchemy.func.max(Tasks.id)
        task.coord_1 = float(request.args.get('coord').split(',')[0])
        task.coord_2 = float(request.args.get('coord').split(',')[1])
        task.note = request.args.get('note')
        task.ended = False
        task.user_id = int(request.args.get('uid'))
        task.cost = int(request.args.get('cost'))
        task.status = 'Добавлено'
        curr_id = db_sess.query(sqlalchemy.func.max(Tasks.id)).first()[0]
        curr_id = curr_id + 1 if curr_id is not None else 1
        file_before = request.files['file']
        file_before.save(f'static/{curr_id}_before.jpg')
        task.picture_before = f'static/{curr_id}_before.jpg'
        
        db_sess.add(task)
        db_sess.commit()
        db_sess.close()
        return {'Status': 'ok'}, 200
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/change_profile/<id>', methods=["POST"])
def change_profile(id):
    try:
        db_sess = db_session.create_session()
        name = request.args.get("name")
        contact_info = request.args.get("contact_info")
        user = db_sess.query(Users).filter(Users.id==int(id)).first()
        if user.login != name:
            if len(list(db_sess.query(Users).filter(Users.login==name).all())) != 0:
                return {
                    "Status": "err",
                    "Error": "name already in database"
                }, 200
        user.login = name
        user.contact_information = contact_info
        db_sess.commit()
        db_sess.close()
        return {'Status': 'ok'}, 200
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/get_profile/<id>', methods=["GET"])
def get_profile(id):
    try:
        db_sess = db_session.create_session()
        user = db_sess.query(Users).filter(Users.id == id).first()
        return {
                "Status": "ok",
                "info": {
                    "name": user.login,
                    "count_completed": user.count_order_completed,
                    "count_placed": user.count_order_placed,
                    "balance": user.balance,
                    "city": user.city,
                    "contact_info": user.contact_information
                    }
            }
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200
    finally:
        db_sess.commit()
        db_sess.close()


@app.route('/api/task_to_revision', methods=["POST"])
def task_to_revision():
    try:
        db_sess = db_session.create_session()
        task_id = int(request.args.get('task_id'))
        task = db_sess.query(Tasks).filter(Tasks.id == task_id).first()
        task.status = 'Добавлено'
        db_sess.commit()
        db_sess.close()
        return {'Status': 'ok'}

    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/check_task', methods=['POST'])
def api_check_task():
    try:
        db_sess = db_session.create_session()
        task_id = int(request.args.get('task_id'))
        task = db_sess.query(Tasks).filter(Tasks.id == task_id).first()
        task.ended = True
        task.status = 'Одобрено'
        user = db_sess.query(Users).filter(Users.id==task.volunteer_id).first()
        user.count_order_completed += 1
        user.balance += task.cost
        db_sess.commit()
        db_sess.close()
        return {'Status': 'ok'}

    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/get_tasks_to_confirmation', methods=['GET'])
def get_tasks_to_confirmation():
    try:
        uid = int(request.args.get('uid'))
        db_sess = db_session.create_session()
        tasks = db_sess.query(Tasks).filter(Tasks.user_id==uid).filter(Tasks.status=="Проверка").all()
        out_sp = []
        for task in tasks:
            out_sp.append({
                "id": task.id,
                "note": task.note,
            })
        return {
            "Status": "ok",
            "list": out_sp
        }
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200
@app.route('/api/search_tasks_for_volunteer', methods=['GET'])
def search_tasks_for_volunteer():
    try:
        db_sess = db_session.create_session()
        tasks = db_sess.query(Tasks).filter(Tasks.volunteer_id == None).filter(Tasks.ended==False)
        diction = []
        for task in tasks:
            user = db_sess.query(Users).filter(Users.id == task.user_id).first()
            diction.append({
                'id': str(task.id),
                'note': str(task.note),
                'coord_1': str(task.coord_1),
                'coord_2': str(task.coord_2),
                'ended': str(task.ended),
                'created_on': task.created_on.strftime("%d.%m.%Y"),
                'username': str(user.login),
                'contact_info': str(user.contact_information),
                'cost': str(task.cost),
                'formatted_address': json.loads(requests.get(
                            ('https://geocode-maps.yandex.ru/1.x/'
                             f'?apikey={api_key[:-1]}'
                             f'&geocode={task.coord_1}, {task.coord_2}'
                             '&format=json')
                    ).text
                    )[
                        'response'
                    ][
                        'GeoObjectCollection'
                    ][
                        'featureMember'
                    ][
                        0
                    ][
                        'GeoObject'
                    ][
                        'metaDataProperty'
                    ][
                        'GeocoderMetaData'
                    ][
                        'Address'
                    ][
                        'formatted'
                    ]
            })
            db_sess.close()
        return {'Status': 'ok', 'list': diction[::-1]}
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/get_volunteer_task', methods=['GET'])
def get_volunteer_task():
    try:
        uid = int(request.args.get('uid'))
        ended = True if str(request.args.get('ended')) == 'true' else False
        db_sess = db_session.create_session()
        tasks = db_sess.query(Tasks).filter(Tasks.volunteer_id == uid).filter(Tasks.ended==ended)
        diction = []

        for task in tasks:
            user = db_sess.query(Users).filter(
                                            Users.id == task.user_id
                                            ).first()
            diction.append({
                'id': str(task.id),
                'note': str(task.note),
                'coord_1': str(task.coord_1),
                'coord_2': str(task.coord_2),
                'ended': str(task.ended),
                'created_on': task.created_on.strftime("%d.%m.%Y"),
                'username': str(user.login),
                'cost': str(task.cost),
                'contact_info': str(user.contact_information)
            })
        db_sess.close()
        return {'Status': 'ok', 'list': diction}
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/add_task_to_confirmation/<id>/', methods=["POST"])
def add_task_to_confirmation(id):
    try:
        db_sess = db_session.create_session()
        task = db_sess.query(Tasks).filter(Tasks.id == id).first()
        file_after = request.files['file']
        file_after.save(f'static/{task.id}_after.jpg')
        task.picture_after = f'static/{task.id}_after.jpg'
        task.status = 'Проверка'
        db_sess.commit()
        db_sess.close()
        return {"Status": "ok"}
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/get_top_users/<object_ordering>/<uid>')
def get_top_users(object_ordering, uid):
    try:
        uid = int(uid)
        db_sess = db_session.create_session()
        users = db_sess.query(Users)
        if object_ordering == "balance":
            users.order_by(Users.balance.desc())
        elif object_ordering == "count_placed":
            users.order_by(Users.count_order_placed.desc())
        else:
            users.order_by(Users.count_order_completed.desc())
        users = users.all()
        out_sp = []
        counter = 1
        for user in users:
            out_sp.append(
                {
                    "index": str(counter),
                    "id": str(user.id),
                    "name": str(user.login),
                    "balance": str(user.balance),
                    "count_placed": str(user.count_order_placed),
                    "count_completed": str(user.count_order_completed)
                }
            )
            counter += 1
        return {
                    "Status": "ok",
                    "users": out_sp
                }
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/get_image/<time>/<id>')
def get_image(time, id):
    try:
        if os.path.exists("static/" + str(id) + "_" + time + ".jpg"):
            return send_file("../static/" + str(id) + "_" + time + ".jpg")
        return {'Status': 'ok', 'info': 'file is not exists'}
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200

@app.route('/api/get_user_task', methods=['GET'])
def get_user_task():
    try:
        uid = int(request.args.get('uid'))
        ended = True if str(request.args.get('ended')) == 'true' else False
        db_sess = db_session.create_session()
        tasks = db_sess.query(Tasks).filter(
            Tasks.user_id == uid
            ).filter(Tasks.ended == ended)
        diction = []
        for task in tasks:
            user = db_sess.query(Users).filter(
                                            Users.id == task.user_id
                                            ).first()
            diction.append({
                'id': str(task.id),
                'note': task.note,
                'coord_1': task.coord_1,
                'coord_2': task.coord_2,
                'ended': task.ended,
                'created_on': task.created_on.strftime("%d.%m.%Y"),
                'username': user.login,
                'contact_info': user.contact_information,
                'cost': task.cost
            })
        db_sess.close()
        return {'Status': 'ok', 'list': diction}
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/get_count_of_today_tasks', methods=['GET'])
def get_count_of_today_tasks():
    try:
        db_sess = db_session.create_session()
        today_tasks = db_sess.query(Tasks).all()
        out_sp = []
        for elem in today_tasks:
            if elem.created_on.date() == datetime.datetime.today().date():
                out_sp.append(elem)
        db_sess.close()
        return {'Status': 'ok', 'count': str(len(out_sp))}
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


@app.route('/api/get_count_of_user_tasks_and_balance', methods=['GET'])
def get_count_of_user_tasks_and_balance():
    try:
        uid = int(request.args.get('uid'))
        db_sess = db_session.create_session()
        zak_tasks = db_sess.query(Tasks).filter(Tasks.user_id==uid).count()
        vol_tasks = db_sess.query(Tasks).filter(Tasks.volunteer_id==uid).count()
        balance = db_sess.query(Users).filter(Users.id==uid).first().balance
        db_sess.close()
        return {'Status': 'ok', 'zak_count': str(zak_tasks), 'vol_count': str(vol_tasks), 'balance': str(balance)}
    except Exception as e:
        print(str(e))
        return {'Status': 'err', 'Error': 'Something went wrong'}, 200


if __name__ == '__main__':
    api_key = open('api_key.txt', 'r').readline()
    db_session.global_init()
    app.run(host='0.0.0.0', port=5050)
