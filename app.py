import os

from flask import Flask, abort, flash, redirect, render_template, request, url_for

import db

# The only statuses allowed (the database enforces the same list)
STATUSES = ["Saved", "Applied", "Interviewing", "Offer", "Rejected", "Withdrawn"]

app = Flask(__name__)

# Store the database file in the "instance" folder, which Git ignores
app.config["DATABASE"] = os.path.join(app.instance_path, "tracker.sqlite")
os.makedirs(app.instance_path, exist_ok=True)

# Flask needs a secret key to sign the flash messages it stores between pages.
# "dev" is fine on your own computer; a real server must use a long random value.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")

db.init_app(app)


# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------

def parse_salary(value, label, errors):
    """Turn the text from a salary box into a whole number, or None if empty."""
    value = value.strip()
    if value == "":
        return None
    if not value.isdigit():
        errors.append(f"{label} must be a whole number, like 22.")
        return None
    return int(value)


def read_application_form(form):
    """Read and check the add/edit form. Returns (values, errors).

    Both the Add and Edit pages use this, so the rules live in one place.
    """
    errors = []
    values = {
        "company": form.get("company", "").strip(),
        "role": form.get("role", "").strip(),
        "status": form.get("status", "Saved"),
        "date_applied": form.get("date_applied", "").strip() or None,
        "location": form.get("location", "").strip() or None,
        "job_url": form.get("job_url", "").strip() or None,
        "notes": form.get("notes", "").strip() or None,
        "salary_min": parse_salary(form.get("salary_min", ""), "Minimum salary", errors),
        "salary_max": parse_salary(form.get("salary_max", ""), "Maximum salary", errors),
        "salary_period": form.get("salary_period"),
    }

    if not values["company"]:
        errors.append("Company is required.")
    if not values["role"]:
        errors.append("Role is required.")
    if values["status"] not in STATUSES:
        errors.append("Choose a status from the list.")
    if values["job_url"] and not values["job_url"].startswith(("http://", "https://")):
        errors.append("Job posting link must start with http:// or https://.")

    low, high = values["salary_min"], values["salary_max"]
    if low is not None and high is not None and low > high:
        errors.append("Minimum salary can't be more than the maximum.")
    if low is None and high is None:
        values["salary_period"] = None  # no salary entered, so no period either
    elif values["salary_period"] not in ("hour", "year"):
        errors.append("Choose per hour or per year for the salary.")

    return values, errors


def get_application(application_id):
    """Fetch one application, or show a 404 page if it doesn't exist."""
    application = db.get_db().execute(
        "SELECT * FROM applications WHERE id = ?", (application_id,)
    ).fetchone()
    if application is None:
        abort(404)
    return application


# ----------------------------------------------------------
# Pages
# ----------------------------------------------------------

@app.route("/")
def index():
    database = db.get_db()

    # ?status=Interviewing in the URL filters the list
    current_status = request.args.get("status")
    if current_status not in STATUSES:
        current_status = None

    if current_status:
        applications = database.execute(
            "SELECT * FROM applications WHERE status = ? ORDER BY id DESC",
            (current_status,),
        ).fetchall()
    else:
        applications = database.execute(
            "SELECT * FROM applications ORDER BY id DESC"
        ).fetchall()

    # How many applications are in each status, for the filter buttons
    rows = database.execute(
        "SELECT status, COUNT(*) AS total FROM applications GROUP BY status"
    ).fetchall()
    counts = {row["status"]: row["total"] for row in rows}
    total = sum(counts.values())

    return render_template(
        "index.html",
        applications=applications,
        statuses=STATUSES,
        counts=counts,
        total=total,
        current_status=current_status,
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        values, errors = read_application_form(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("form.html", mode="add", statuses=STATUSES, form=request.form), 400

        database = db.get_db()
        database.execute(
            """
            INSERT INTO applications
              (company, role, status, date_applied, location, job_url,
               salary_min, salary_max, salary_period, notes)
            VALUES
              (:company, :role, :status, :date_applied, :location, :job_url,
               :salary_min, :salary_max, :salary_period, :notes)
            """,
            values,
        )
        database.commit()

        flash(f"Added {values['role']} at {values['company']}.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", mode="add", statuses=STATUSES, form={})


@app.route("/edit/<int:application_id>", methods=["GET", "POST"])
def edit(application_id):
    application = get_application(application_id)

    if request.method == "POST":
        values, errors = read_application_form(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "form.html", mode="edit", statuses=STATUSES,
                form=request.form, application=application,
            ), 400

        values["id"] = application_id
        database = db.get_db()
        database.execute(
            """
            UPDATE applications SET
              company = :company, role = :role, status = :status,
              date_applied = :date_applied, location = :location, job_url = :job_url,
              salary_min = :salary_min, salary_max = :salary_max,
              salary_period = :salary_period, notes = :notes
            WHERE id = :id
            """,
            values,
        )
        database.commit()

        flash(f"Updated {values['role']} at {values['company']}.", "success")
        return redirect(url_for("index"))

    # GET: show the form filled in with the saved values.
    # The form expects text, so turn numbers and empty values into strings.
    form = {key: ("" if application[key] is None else str(application[key]))
            for key in application.keys()}
    return render_template(
        "form.html", mode="edit", statuses=STATUSES, form=form, application=application,
    )


@app.route("/delete/<int:application_id>", methods=["POST"])
def delete(application_id):
    application = get_application(application_id)
    database = db.get_db()
    database.execute("DELETE FROM applications WHERE id = ?", (application_id,))
    database.commit()
    flash(f"Deleted {application['role']} at {application['company']}.", "success")
    return redirect(url_for("index"))
