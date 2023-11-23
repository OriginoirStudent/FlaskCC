from flask import Flask, request, redirect, url_for
from flask import render_template, session
import mysql.connector
import re
from datetime import date


app = Flask(__name__)

app.secret_key = "finalprojectPBD"

db = mysql.connector.connect(
    host="localhost", user="root", password="", database="db_servis"
)


@app.before_request
def count_page_views():
    if "counter" not in session:
        session["counter"] = 1
    else:
        session["counter"] += 1


@app.route("/")
def index():
    counter = session.get("counter")
    return render_template("index.html", counter=counter)


@app.route("/register/", methods=["GET", "POST"])
def register():
    msg = ""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM alamat")
    alamat_list = cursor.fetchall()
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
        and "email" in request.form
        and "alamat" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        alamat = request.form["alamat"]
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM customer WHERE nama=%s or email=%s", (username, email)
        )
        user = cursor.fetchone()
        if user:
            msg = "Username/Email already exists !"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            msg = "Invalid email address !"
        elif not re.match(r"[A-Za-z0-9]+", username):
            msg = "Username must contain only characters and numbers !"
        elif not username or not password or not email or not alamat:
            msg = "Please fill out the form !"
        else:
            cursor.execute(
                "INSERT INTO customer (nama, email, userpass, alamat) VALUES (%s, %s, %s, %s)",
                (username, email, password, alamat),
            )
            db.commit()
            msg = "You have successfully registered !"
    elif request.method == "POST":
        msg = "Please fill out the form !"
    return render_template("register.html", msg=msg, alamat_list=alamat_list)


@app.route("/login/", methods=["GET", "POST"])
def login():
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]

        cursor = db.cursor()
        cursor.execute(
            "SELECT a.admin_id, a.username, a.password, j.nama_jabatan FROM admin a, jabatan j WHERE username = %s AND password = %s AND a.jabatan = j.kode_jabatan",
            (username, password,),
        )
        admin = cursor.fetchone()
        db.commit()

        if admin:
            jabatan = admin[3]
            if jabatan == "Manager":
                session['loggedin'] = True
                session["admin_id"] = admin[0]
                session["username"] = admin[1]
                session["jabatan"] = jabatan
                return redirect(url_for("dashboard"))
            elif jabatan == "Mekanik":
                session['loggedin'] = True
                session["admin_id"] = admin[0]
                session["username"] = admin[1]
                session["jabatan"] = jabatan
                return redirect(url_for("dashboard"))

        else:
            return redirect(url_for("wrong"))

    return render_template("login.html")


@app.route("/login_customer/", methods=["GET", "POST"])
def login_customer():
    if (
        request.method == "POST"
        and "nama" in request.form
        and "userpass" in request.form
    ):
        nama = request.form["nama"]
        userpass = request.form["userpass"]

        cursor = db.cursor()
        cursor.execute(
            "SELECT customer_id FROM customer WHERE nama = %s AND userpass = %s",
            (nama, userpass),
        )
        customer_id = cursor.fetchone()

        if customer_id:
            session['loggedin'] = True
            customer_id = customer_id[0]
            session["customer_id"] = customer_id
            return redirect(url_for("dashboard_customer"))
        
        else:
            return redirect(url_for("wrong"))

    return render_template("login_customer.html")


@app.route("/dashboard/")
def dashboard():
    counter = session["counter"]
    cursor = db.cursor()
    cursor.execute("SELECT SUM(total) FROM proses")
    total_count = cursor.fetchone()[0]
    rupiah = "Rp{0:,}".format(total_count)
    cursor.close()

    if "admin_id" in session:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM proses")
        jumlah_pelanggan = cursor.fetchone()[0]
        if "jabatan" in session and session["jabatan"] == "Manager":
            user_type = "manager"
            cursor = db.cursor()
            cursor.execute(
                "SELECT a.admin_id, a.username, j.nama_jabatan FROM admin a, jabatan j WHERE a.jabatan = j.nama_jabatan"
            )
            admins = cursor.fetchall()
            db.commit()
            cursor.close()

            return render_template(
                "dashboard.html",
                admins=admins,
                user_type=user_type,
                counter=counter,
                jumlah_pelanggan=jumlah_pelanggan,
                rupiah=rupiah,
            )

        elif "jabatan" in session and session["jabatan"] == "Mekanik":
            user_type = "mekanik"
            cursor = db.cursor()
            cursor.execute("""
                SELECT p.kode_proses, c.nama, s.detail_status, a.username, p.tgl_masuk, p.tgl_keluar, p.total
                FROM proses p
                LEFT JOIN admin a ON p.admin = a.admin_id
                JOIN customer c ON p.customer = c.customer_id
                JOIN status s ON p.status = s.kode_status
            """)

            proses = cursor.fetchall()
            
            db.commit() 
            cursor.close()

            return render_template(
                "dashboard.html",
                proses=proses,
                user_type=user_type,
                counter=counter,
                jumlah_pelanggan=jumlah_pelanggan,
                rupiah=rupiah,
            )

    else:
        return redirect(url_for("index"))


@app.route("/dashboard_customer/")
def dashboard_customer():
    cursor = db.cursor()
    cursor.execute("SELECT SUM(total) FROM proses")
    total_count = cursor.fetchone()[0]
    rupiah = "Rp{0:,}".format(total_count)
    cursor.close()

    if "customer_id" in session:
        customer_id = session["customer_id"]
        cursor = db.cursor()
        cursor.execute(
            "SELECT p.kode_proses, a.username, s.detail_status, p.total FROM proses p, admin a, customer c, status s WHERE p.admin = a.admin_id AND p.customer = c.customer_id AND p.status = s.kode_status AND c.customer_id = %s",
            (customer_id,),
        )
        proses = cursor.fetchall()
        cursor.close()

        return render_template(
            "dashboard_customer.html",
            proses=proses,
            rupiah=rupiah,
        )

    else:
        return redirect(url_for("index"))
    

@app.route('/logout/')
def logout():
    session.pop('loggedin', None)
    session.pop('admin_id', None)
    session.pop('username', None)
    session.pop('jabatan', None)
    return redirect(url_for('login'))


@app.route('/logout_customer/')
def logout_customer():
    session.pop('loggedin', None)
    session.pop('customer_id', None)
    return redirect(url_for('login_customer'))


@app.route("/claim/", methods=["POST", "GET"])
def claim_admin():
    if request.method == "POST":
        admin = session["admin_id"]
        kode = request.form["proses_id"]

        cursor = db.cursor()
        cursor.execute(
            "UPDATE proses SET admin = %s WHERE kode_proses = %s", (admin, kode)
        )
        db.commit()

        return redirect(url_for("dashboard"))


@app.route("/wrong/")
def wrong():
    return render_template("wrong.html")


@app.route("/dashboard_pelanggan/")
def dashboard_pelanggan():
    if "username" in session:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM status")
        status = cursor.fetchall()
        cursor.close()
        if "jabatan" in session and session["jabatan"] == "Manager":
            user_type = "manager"
            cursor = db.cursor()
            cursor.execute(
                "SELECT a.username, j.nama_jabatan FROM admin a, jabatan j WHERE a.jabatan = j.nama_jabatan"
            )
            admins = cursor.fetchall()
            cursor.close()

            return render_template(
                "dashboard_pelanggan.html", admins=admins, user_type=user_type
            )

        elif (
            "jabatan" in session
            and "username" in session
            and session["jabatan"] == "Mekanik"
        ):
            user_type = "mekanik"
            cursor = db.cursor()
            username = session["username"]
            cursor.execute(
                "SELECT p.kode_proses, c.nama, s.detail_status, a.username, p.tgl_masuk, p.tgl_keluar, p.total FROM proses p, admin a, customer c, status s WHERE p.admin = a.admin_id AND p.customer = c.customer_id AND p.status = s.kode_status AND username = %s",
                (username,),
            )
            proses = cursor.fetchall()
            cursor.close()

            return render_template(
                "dashboard_pelanggan.html",
                proses=proses,
                user_type=user_type,
                status=status,
            )

    else:
        return redirect(url_for("index"))


@app.route("/update_status/", methods=["POST", "GET"])
def update_status():
    if request.method == "POST":
        proses_id = request.form["proses_id"]
        status = request.form["status"]

        cursor = db.cursor()
        cursor.execute(
            "UPDATE proses SET status = %s WHERE kode_proses = %s", (status, proses_id)
        )
        db.commit()

    return redirect(url_for("dashboard_pelanggan"))


@app.route("/tanggal_keluar/", methods=["POST", "GET"])
def tanggal_keluar():
    if request.method == "POST":
        proses_id = request.form["proses_id"]
        keluar = date.today().strftime("%Y-%m-%d")

        cursor = db.cursor()
        cursor.execute(
            "UPDATE proses SET tgl_keluar = %s WHERE kode_proses = %s", (keluar, proses_id)
        )
        db.commit()

    return redirect(url_for("dashboard_pelanggan"))


@app.route("/delete_proses/", methods=["POST", "GET"])
def delete_proses():
    cursor = db.cursor()
    cursor.execute("SELECT s.detail_status FROM status s, proses p WHERE s.kode_status=p.status")
    kode = cursor.fetchall()
    db.commit()

    if request.method == "POST":
        proses_id = request.form["proses_id"]
        cursor = db.cursor()

        cursor.execute("SELECT status FROM proses WHERE kode_proses = %s", (proses_id,))
        row = cursor.fetchone()
        if row and row[0] == "QUEUE":
            cursor.execute("DELETE FROM proses WHERE kode_proses = %s", (proses_id,))
            db.commit()

    return redirect(url_for("dashboard_customer", kode=kode))


if __name__ == "__main__":
    app.run(debug=True)
