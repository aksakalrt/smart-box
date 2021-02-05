from flask import Flask, render_template, request, redirect, session
from datetime import timedelta
import sqlite3
import hashlib
import re
import time


app = Flask(__name__)

app.secret_key = "hello"
app.permanent_session_lifetime = timedelta(minutes=5)


@app.route('/')
def main():
    return redirect('login')


@app.route('/register/', methods=['GET','POST'])
def register():
    if "user" in session:
        return redirect('/box/')
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        mail = request.form['mail']
        pwd = request.form['pwd']
        pwd2 = request.form['pwd_again']
        name = request.form['name']
        surname = request.form['surname']
        if mail == "" or pwd == "" or pwd2 == "" or name == "" or surname == "":
            return "Lütfen Tüm Alanları Eksiksiz Doldurunuz!"
        pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)") 
        if not re.fullmatch(pattern, mail):
            return "Mail Adresi Geçersiz!"
        if pwd != pwd2:
            return "Şifreler Aynı Değil!"
        date = str(time.time()+10800).split('.')[0]
        pwd = hashlib.md5(pwd.encode()).hexdigest()
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT id FROM users WHERE mail=?", (mail,))
            res = cur.fetchall()
            if(res != []):
                return "Mail Adresi Zaten Kullanılıyor!"
            cur.execute("INSERT INTO users (mail, pwd, name, surname, date) VALUES (?, ?, ?, ?, ?)", (mail, pwd, name, surname, date))
            con.commit()
        except:
            return "Veritabanı hatası"
        finally:
            con.close()
        return redirect('/login/')


@app.route("/login/", methods=['GET','POST'])
def login():
    if "user" in session:
        return redirect('/box/')
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        mail = request.form['mail']
        pwd = request.form['pwd']
        pwd = hashlib.md5(pwd.encode()).hexdigest()
        try:
            con = sqlite3.connect('database.db')
            cur = con.cursor()
            cur.execute("SELECT id, mail, name, surname, type FROM users WHERE mail = ? and pwd = ?", (mail, pwd,))
            res = cur.fetchall()
        except:
            return "Veritabanı hatası"
        finally:
            con.close()
        if res == []:
            return "Kullanıcı Adı veya Şifre Yanlış!"
        else:
            res = list(res[0])
            session["user"] = res
            return redirect('/box/')


@app.route('/logout/')
def logout():
    session.pop("user", None)
    return redirect('/')


@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    if "user" not in session:
        return redirect('/login/')
    if session["user"][4] == 1:
        if request.method == 'POST':
            box_code = request.form['box_code'].lower()
            capacity = request.form['capacity']
            timestamp = str(time.time()+10800).split('.')[0]
            con = sqlite3.connect('database.db')
            cur = con.cursor()
            try:
                cur.execute("SELECT id FROM boxes WHERE box_code = ?", (box_code,))
                res = cur.fetchall()
            except:
                return "Veritabanı Hatası1"
            if res != []:
                return "Kutu Zaten Mevcut!"
            try:
                cur.execute("INSERT INTO boxes (box_code, max_limit, date) VALUES (?, ?, ?)", (box_code, capacity, timestamp))
                con.commit()
            except:
                return "Veritabanı Hatası"
            finally:
                con.close()
            return "Kutu Eklendi"
        elif request.method == 'GET':
            return render_template('admin.html')
    else:
        return redirect('/box/')


@app.route('/box/', methods=['POST', 'GET'])
def box():
    if "user" not in session:
        return redirect('/login/')
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    try:
        cur.execute("SELECT id, box_code FROM boxes WHERE user_id = ?", (session["user"][0],))
        boxes = cur.fetchall()
    except:
        return "Veritabanı hatası"
    box_settings = []
    try:
        for box in boxes:
            cur.execute("SELECT name, expiration, trig_limit FROM box_settings WHERE box_id = ?", (box[0],))
            res = cur.fetchall()
            res = list(res[0])
            res.insert(0, box[1])
            box_settings.append(res)
    except:
        return "Veritabanı hatası"
    finally:
        con.close()
    
    return render_template('box.html', bs = box_settings)
    
@app.route('/box/<path>/', methods=['POST', 'GET'])
def crud_box(path):
    if request.method == 'POST':
        if path.lower() == 'create':
            box_code = request.form['box_code'].lower()
            con = sqlite3.connect('database.db')
            cur = con.cursor()
            try:
                cur.execute("SELECT id, user_id FROM boxes WHERE box_code = ?", (box_code,))
                res = cur.fetchall()
            except:
                return "Veritabanı hatası"
            if res == []:
                return "Kutu Mevcut Değil!"
            elif res[0][1] != None:
                return "Kutu Zaten Tanımlı"
            try:
                cur.execute("UPDATE boxes SET user_id = ? WHERE id = ?", (session["user"][0], res[0][0],))
                con.commit()
            except:
                return "Update hata"
            try:
                timestamp = str(time.time()+10800).split('.')[0]
                cur.execute("INSERT INTO box_settings (box_id, name, expiration, trig_limit, date) VALUES (?, ?, ?, ?, ?)", (res[0][0], "Belirtilmemiş", timestamp, 0, timestamp))
                con.commit()
            except:
                return "Box Settings Hata"
            finally:
                con.close()

            return "create"
        elif path.lower() == 'update':
            return "up"
        else:
            return "404"
    else:
        return "get "+path

if __name__ == "__main__":
    app.run(debug=True)