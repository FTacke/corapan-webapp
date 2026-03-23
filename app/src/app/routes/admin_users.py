"""Admin user management API endpoints.

All endpoints require JWT auth and admin role.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, current_app, url_for
from flask_jwt_extended import jwt_required

from ..auth import Role
from ..auth.decorators import require_role
from ..auth import services as auth_services
from ..auth.models import User as UserModel, ResetToken as ResetTokenModel
import secrets
from sqlalchemy import select

bp = Blueprint("admin_users", __name__, url_prefix="/admin/users")


@bp.get("")
@jwt_required()
@require_role(Role.ADMIN)
def list_users():
    # DB-backed auth is required for admin user management

    q = request.args.get("q")
    role = request.args.get("role")
    status = request.args.get("status")
    include_inactive = request.args.get("include_inactive", "0") == "1"
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 50))

    # naive query using session
    with auth_services.get_session() as session:
        sel = select(UserModel)
        # apply filters
        if q:
            sel = sel.where(
                (UserModel.username.ilike(f"%{q}%")) | (UserModel.email.ilike(f"%{q}%"))
            )
        if role:
            sel = sel.where(UserModel.role == role)

        # Status filter: if include_inactive is False (default), show only active users
        if status:
            if status == "active":
                sel = sel.where(UserModel.is_active)
            elif status == "inactive":
                sel = sel.where(not UserModel.is_active)
            elif status == "deleted":
                sel = sel.where(UserModel.deleted_at is not None)
            elif status == "locked":
                sel = sel.where(UserModel.locked_until is not None)
            elif status == "all":
                pass  # No filter - show all
        elif not include_inactive:
            # Default: only active users
            sel = sel.where(UserModel.is_active)

        # Sort: active users first, then inactive
        sel = sel.order_by(UserModel.is_active.desc(), UserModel.username)

        offset = (page - 1) * size
        res = session.execute(sel.offset(offset).limit(size)).scalars().all()

        items = [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "is_active": bool(u.is_active),
                "last_login_at": u.last_login_at.isoformat()
                if u.last_login_at
                else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in res
        ]

    return jsonify({"items": items, "meta": {"page": page, "size": size}})


@bp.get("/<id>")
@jwt_required()
@require_role(Role.ADMIN)
def get_user(id):
    # DB-backed auth is required for admin user management
    user = auth_services.get_user_by_id(id)
    if not user:
        return jsonify({"error": "not_found"}), 404
    obj = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": bool(user.is_active),
        "must_reset_password": bool(user.must_reset_password),
        "valid_from": user.valid_from.isoformat() if user.valid_from else None,
        "access_expires_at": user.access_expires_at.isoformat()
        if user.access_expires_at
        else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "login_failed_count": user.login_failed_count,
        "locked_until": user.locked_until.isoformat() if user.locked_until else None,
    }
    # Attach recent reset token metadata (non-sensitive: no raw token)
    with auth_services.get_session() as session:
        stmt = (
            select(ResetTokenModel)
            .where(ResetTokenModel.user_id == id)
            .order_by(ResetTokenModel.created_at.desc())
            .limit(5)
        )
        tokens = session.execute(stmt).scalars().all()
        obj["resetTokens"] = [
            {
                "id": t.id,
                "created_at": t.created_at.isoformat(),
                "expires_at": t.expires_at.isoformat(),
                "used_at": t.used_at.isoformat() if t.used_at else None,
            }
            for t in tokens
        ]

    return jsonify(obj)


@bp.post("")
@jwt_required()
@require_role(Role.ADMIN)
def create_user():
    # Invite flow: do not store plaintext password; create a user with must_reset_password true and generate reset token
    # DB-backed auth is required for admin user management

    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    role = data.get("role", "user")
    must_reset_password = bool(data.get("must_reset_password", True))

    if not username and not email:
        return jsonify({"error": "username_or_email_required"}), 400

    # create user
    from uuid import uuid4
    from datetime import datetime, timezone

    uid = str(uuid4())
    hashed = auth_services.hash_password(secrets.token_urlsafe(12))
    with auth_services.get_session() as session:
        u = auth_services.User(
            id=uid,
            username=(username or email).lower(),
            email=(email or None),
            password_hash=hashed,
            role=role,
            is_active=True,
            must_reset_password=must_reset_password,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(u)

    # generate invite/reset token and log
    raw, tokenrow = auth_services.create_reset_token_for_user(u)
    current_app.logger.info(f"Invite created for {u.username}: token={raw}")

    # Return the token so the admin can copy it (since we don't have email sending set up yet)
    # Use password_reset_page instead of login page to ensure the token is handled correctly
    invite_link = url_for("auth.password_reset_page", token=raw, _external=True)

    # Include token metadata so the admin UI can show expiry and the token id
    return (
        jsonify(
            {
                "ok": True,
                "userId": uid,
                "inviteSent": True,
                "inviteLink": invite_link,
                "inviteId": tokenrow.id,
                "inviteExpiresAt": tokenrow.expires_at.isoformat(),
            }
        ),
        201,
    )


@bp.patch("/<id>")
@jwt_required()
@require_role(Role.ADMIN)
def patch_user(id):
    # DB-backed auth is required for admin user management
    data = request.get_json() or {}
    # allowed: role, is_active, email, must_reset_password, valid_from, access_expires_at

    # Validate email format if provided
    if "email" in data and data["email"]:
        import re

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, data["email"]):
            return jsonify(
                {"error": "invalid_email", "message": "Ungültiges E-Mail-Format"}
            ), 400

    # Validate role if provided
    if "role" in data and data["role"] not in ("admin", "editor", "user"):
        return jsonify(
            {
                "error": "invalid_role",
                "message": "Rolle muss admin, editor oder user sein",
            }
        ), 400

    with auth_services.get_session() as session:
        stmt = select(UserModel).where(UserModel.id == id)
        user = session.execute(stmt).scalars().first()
        if not user:
            return jsonify({"error": "not_found"}), 404

        # Last-admin protection: prevent demoting or deactivating the last active admin
        is_demoting_from_admin = (
            "role" in data and user.role == "admin" and data["role"] != "admin"
        )
        is_deactivating = "is_active" in data and not bool(data["is_active"])

        if user.role == "admin" and (is_demoting_from_admin or is_deactivating):
            # Count active admins
            admin_count_stmt = select(UserModel).where(
                UserModel.role == "admin",
                UserModel.is_active,
                UserModel.deleted_at is None,
            )
            active_admins = session.execute(admin_count_stmt).scalars().all()
            if len(active_admins) <= 1:
                return jsonify(
                    {
                        "error": "last_admin",
                        "message": "Der letzte aktive Administrator kann nicht herabgestuft oder deaktiviert werden.",
                    }
                ), 400

        if "role" in data:
            user.role = data["role"]
        if "is_active" in data:
            user.is_active = bool(data["is_active"])
        if "email" in data:
            user.email = data["email"] if data["email"] else None
        if "must_reset_password" in data:
            user.must_reset_password = bool(data["must_reset_password"])
        if "valid_from" in data:
            user.valid_from = data["valid_from"]
        if "access_expires_at" in data:
            user.access_expires_at = data["access_expires_at"]

        user.updated_at = datetime.now(timezone.utc)

    return jsonify({"ok": True})


@bp.post("/<id>/reset-password")
@jwt_required()
@require_role(Role.ADMIN)
def admin_reset_password(id):
    # DB-backed auth is required for admin user management
    # create reset token for user
    user = auth_services.get_user_by_id(id)
    if not user:
        return jsonify({"error": "not_found"}), 404
    raw, tokenrow = auth_services.create_reset_token_for_user(user)
    current_app.logger.info(f"Admin-reset for {user.username}: token={raw}")

    invite_link = url_for("auth.password_reset_page", token=raw, _external=True)

    # Return link and meta so UI can surface the invite link for the admin
    return jsonify(
        {
            "ok": True,
            "inviteLink": invite_link,
            "inviteId": tokenrow.id,
            "inviteExpiresAt": tokenrow.expires_at.isoformat(),
        }
    )


@bp.post("/<id>/lock")
@jwt_required()
@require_role(Role.ADMIN)
def admin_lock_user(id):
    # DB-backed auth is required for admin user management
    data = request.get_json() or {}
    until = data.get("until")
    from datetime import datetime

    with auth_services.get_session() as session:
        stmt = select(UserModel).where(UserModel.id == id)
        user = session.execute(stmt).scalars().first()
        if not user:
            return jsonify({"error": "not_found"}), 404
        user.locked_until = datetime.fromisoformat(until) if until else None
    return jsonify({"ok": True})


@bp.post("/<id>/unlock")
@jwt_required()
@require_role(Role.ADMIN)
def admin_unlock_user(id):
    # DB-backed auth is required for admin user management
    with auth_services.get_session() as session:
        stmt = select(UserModel).where(UserModel.id == id)
        user = session.execute(stmt).scalars().first()
        if not user:
            return jsonify({"error": "not_found"}), 404
        user.locked_until = None
    return jsonify({"ok": True})


@bp.post("/<id>/invalidate-sessions")
@jwt_required()
@require_role(Role.ADMIN)
def admin_invalidate_sessions(id):
    # DB-backed auth is required for admin operations
    auth_services.revoke_all_refresh_tokens_for_user(id)
    return jsonify({"ok": True})


@bp.delete("/<id>")
@jwt_required()
@require_role(Role.ADMIN)
def admin_delete_user(id):
    # DB-backed auth is required for admin operations
    auth_services.mark_user_deleted(id)
    auth_services.revoke_all_refresh_tokens_for_user(id)
    current_app.logger.info(f"Admin deleted user {id}")
    return jsonify({"ok": True})
