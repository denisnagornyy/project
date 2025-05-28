from .database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Region(db.Model):
    __tablename__ = 'region'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    organizations = db.relationship('EducationalOrganization', backref='region', lazy='dynamic')

    def __repr__(self):
        return f'<Region {self.name}>'

class SpecialtyGroup(db.Model):
    __tablename__ = 'specialty_group'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    specialties = db.relationship('Specialty', backref='group', lazy='dynamic')

    def __repr__(self):
        return f'<SpecialtyGroup {self.code} {self.name}>'

class Specialty(db.Model):
    __tablename__ = 'specialty'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('specialty_group.id'), nullable=False)
    programs = db.relationship('EducationalProgram', backref='specialty', lazy='dynamic')

    def __repr__(self):
        return f'<Specialty {self.code} {self.name}>'

class EducationalOrganization(db.Model):
    __tablename__ = 'educational_organization'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(1000), nullable=False)
    short_name = db.Column(db.String(500))
    ogrn = db.Column(db.String(15), unique=True, index=True)
    inn = db.Column(db.String(12), unique=True, index=True)
    kpp = db.Column(db.String(9), index=True)
    address = db.Column(db.String(1000))
    phone = db.Column(db.String(100))
    fax = db.Column(db.String(100))
    email = db.Column(db.String(255))
    website = db.Column(db.String(255))
    head_post = db.Column(db.String(255))
    head_name = db.Column(db.String(255))
    form_name = db.Column(db.String(255))
    form_code = db.Column(db.String(50))
    kind_name = db.Column(db.String(255))
    kind_code = db.Column(db.String(50))
    type_name = db.Column(db.String(255))
    type_code = db.Column(db.String(50))
    region_id = db.Column(db.Integer, db.ForeignKey('region.id'))
    federal_district_code = db.Column(db.String(50))
    federal_district_short_name = db.Column(db.String(50))
    federal_district_name = db.Column(db.String(255))
    parent_id = db.Column(db.Integer, db.ForeignKey('educational_organization.id'), nullable=True)
    programs = db.relationship('EducationalProgram', backref='organization', lazy='dynamic')

    def __repr__(self):
        return f'<EducationalOrganization {self.short_name or self.full_name}>'

class EducationalProgram(db.Model):
    __tablename__ = 'educational_program'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('educational_organization.id'), nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'), nullable=False)

    def __repr__(self):
        return f'<EducationalProgram id={self.id} org_id={self.organization_id} spec_id={self.specialty_id}>'

class IndividualEntrepreneur(db.Model):
    __tablename__ = 'individual_entrepreneur'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(1000), nullable=False)
    ogrnip = db.Column(db.String(15), unique=True, index=True)
    inn = db.Column(db.String(12), unique=True, index=True)
    address = db.Column(db.String(1000))
    phone = db.Column(db.String(100))
    email = db.Column(db.String(255))
    website = db.Column(db.String(255))

    def __repr__(self):
        return f'<IndividualEntrepreneur {self.full_name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
