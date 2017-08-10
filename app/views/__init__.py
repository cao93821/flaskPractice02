from .. import db, login_manager
from ..models import User
from . import main, auth


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).filter_by(id=user_id).first()
