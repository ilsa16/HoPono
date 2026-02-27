from flask import Blueprint, render_template
from app.extensions import db
from app.models.service import Service

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
    return render_template("public/home.html", services=services)


@public_bp.route("/about")
def about():
    return render_template("public/about.html")


@public_bp.route("/services")
def services():
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
    return render_template("public/services.html", services=services)


@public_bp.route("/contact")
def contact():
    return render_template("public/contact.html")


@public_bp.route("/privacy")
def privacy():
    return render_template("public/privacy.html")
