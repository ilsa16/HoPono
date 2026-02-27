from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.client import Client
from app.models.note import ClientNote
from app.models.booking import Booking
from app.models.payment import Payment

admin_clients_bp = Blueprint("admin_clients", __name__)


@admin_clients_bp.route("/")
@login_required
def list_clients():
    search = request.args.get("search", "").strip()
    query = Client.query

    if search:
        query = query.filter(
            db.or_(
                Client.name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%"),
                Client.phone.ilike(f"%{search}%"),
            )
        )

    clients = query.order_by(Client.name).all()
    return render_template("admin/clients.html", clients=clients)


@admin_clients_bp.route("/<int:client_id>")
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    bookings = (
        Booking.query.filter_by(client_id=client_id)
        .order_by(Booking.date.desc(), Booking.start_time.desc())
        .all()
    )
    notes = (
        ClientNote.query.filter_by(client_id=client_id)
        .order_by(ClientNote.created_at.desc())
        .all()
    )
    payments = (
        Payment.query.filter_by(client_id=client_id)
        .order_by(Payment.paid_at.desc())
        .all()
    )

    total_paid = sum(p.amount_eur for p in payments)
    visit_count = len([b for b in bookings if b.status == "completed"])

    return render_template(
        "admin/client_detail.html",
        client=client,
        bookings=bookings,
        notes=notes,
        payments=payments,
        total_paid=total_paid,
        visit_count=visit_count,
    )


@admin_clients_bp.route("/<int:client_id>/notes", methods=["POST"])
@login_required
def add_note(client_id):
    client = Client.query.get_or_404(client_id)
    content = request.form.get("content", "").strip()
    booking_id = request.form.get("booking_id", type=int)

    if content:
        note = ClientNote(
            client_id=client_id,
            booking_id=booking_id,
            content=content,
            created_by=current_user.id,
        )
        db.session.add(note)
        db.session.commit()
        flash("Note added.", "success")

    return redirect(url_for("admin_clients.client_detail", client_id=client_id))
