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
    return "anasayfa"


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
            cur.execute("SELECT mail, name, surname, type FROM users WHERE mail = ? and pwd = ?", (mail, pwd,))
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


@app.route('/box/', methods=['POST', 'GET'])
def box():
    if "user" not in session:
        return redirect('/login/')
    if request.method == 'POST':
        return render_template("box.html")
    return render_template("box.html")
    

if __name__ == "__main__":
    app.run(debug=True)