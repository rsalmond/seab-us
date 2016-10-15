from __future__ import absolute_import

import os
import logging
from datetime import datetime as dt

from seabus.common.database import db
from seabus.common.errors import InvalidBeaconError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log.addHandler(sh)

def safe_get_type(some_dict, some_key, some_type):
   if some_key in some_dict:
        val = some_dict.get(some_key)
        try:
            val = some_type(val)
        except Exception as e:
            return

        return val

class ModelBase(db.Model):
    """ provide some useful common functions for db models """
    __abstract__ = True

    id = db.Column(db.BigInteger, primary_key=True)

    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()

    @classmethod
    def all(cls):
        return db.session.query(cls).all()

    @classmethod
    def count(cls):
        return db.session.query(cls).count()

    def save(self):
        db.session.add(self)
        db.session.commit()

class Boat(ModelBase):
    __tablename__ = 'boats'
    
    telemetry = db.relationship('Telemetry', backref='boat')
    is_seabus = db.Column(db.Boolean, default=False)
    mmsi = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(120), default=None)
    dim_to_bow = db.Column(db.Integer, default=None)
    dim_to_stern = db.Column(db.Integer, default=None)
    dim_to_port = db.Column(db.Integer, default=None)
    dim_to_star = db.Column(db.Integer, default=None)
    type_and_cargo = db.Column(db.Integer, default=None)
    lastseen_on = db.Column(db.DateTime, default = dt.utcnow)

    def __init__(self, mmsi):
        self.mmsi = mmsi
        self.save()

    @classmethod
    def all_seabuses(cls):
        return db.session.query(cls).filter_by(is_seabus=True).all()

    @classmethod
    def from_beacon(cls, beacon):
        """ return existing boat record if present or create and return
        a new one """

        if beacon.get('id') == 4:
            # msg type 4 is a base station, not a boat
            return 

        mmsi = beacon.get('mmsi')
        
        # cant do anything without an mmsi
        if mmsi is None:
            raise InvalidBeaconError

        boat = db.session.query(cls).filter_by(mmsi=mmsi).first()

        if boat is None:
            boat = Boat(mmsi)
        else:
            # if we've seen this boat before update lastseen time
            boat.lastseen_on = dt.utcnow()

        boat._parse_beacon(beacon)
        boat.save()
        return boat

    def _parse_beacon(self, beacon):
        
        name = beacon.get('name')
        if isinstance(name, basestring):
            self.name = name.strip()

        type_and_cargo = beacon.get('type_and_cargo')

        if type_and_cargo is not None:
            try:
                type_and_cargo = int(type_and_cargo)
                self.type_and_cargo = type_and_cargo
            except Exception as e:
                log.exception(e)
                log.info('Bogus type/cargo in beacon {}'.format(beacon))

        d2bow = beacon.get('dim_a')
        d2stern = beacon.get('dim_b')
        d2port = beacon.get('dim_c')
        d2star = beacon.get('dim_d')

        dimensions = (d2bow, d2stern, d2port, d2star)
        
        if None not in dimensions:
            try:
                dimensions = filter(int, (d2bow, d2stern, d2port, d2star))
            except Exception as e:
                log.info('Bogus dimensions in beacon: {}'.format(beacon))
                
            if len(dimensions) == 4:
                self.dim_to_bow = int(d2bow)
                self.dim_to_stern = int(d2stern)
                self.dim_to_port = int(d2port)
                self.dim_to_star = int(d2star)

class Telemetry(ModelBase):
    __tablename__ = 'telemetry'

    boat_id = db.Column(db.Integer, db.ForeignKey('boats.id'))
    nav_status = db.Column(db.Integer)
    pos_accuracy = db.Column(db.Integer)
    lon = db.Column(db.Float)
    lat = db.Column(db.Float)
    speed_over_ground = db.Column(db.Float)
    course_over_ground = db.Column(db.Float)
    true_heading = db.Column(db.Integer)
    rate_of_turn = db.Column(db.Float)
    rate_of_turn_over_range = db.Column(db.Boolean)
    timestamp = db.Column(db.Integer)
    received = db.Column(db.DateTime, default=dt.utcnow)

    def __init__(self):
        pass

    def __repr__(self):
        return '<% {}, {} %>'.format(self.lat, self.lon)

    @classmethod
    def from_beacon(cls, beacon):
        telemetry = Telemetry()
        telemetry._parse_beacon(beacon)
        return telemetry

    def is_valid(self):
        if None in (self.lat, self.lon):
            return False

        if (self.lat < 0) or (self.lat > 90):
            return False

        if (self.lon < -180) or (self.lon > 180):
            return False

        return True

    def _parse_beacon(self, beacon):
        self.nav_status = safe_get_type(beacon, 'nav_status', int)
        self.pos_accuracy = safe_get_type(beacon, 'position_accuracy', int)
        self.lon = safe_get_type(beacon, 'x', float)
        self.lat = safe_get_type(beacon, 'y', float)
        self.speed_over_ground = safe_get_type(beacon, 'sog', float)
        self.course_over_ground = safe_get_type(beacon, 'cog', float)
        self.true_heading = safe_get_type(beacon, 'true_heading', int)
        self.rate_of_turn = safe_get_type(beacon, 'rot', float)
        self.rate_of_turn_over_range = safe_get_type(beacon, 'rot_over_range',bool)
        self.timestamp = safe_get_type(beacon, 'timestamp', int)

    @classmethod
    def latest_for_boat(cls, boat):
        return db.session.query(cls).filter_by(boat_id=boat.id).order_by(cls.id.desc()).first()

    def record_for_boat(self, boat):
        """
        """
        if boat.is_seabus:
            # record every piece of telemetry for each seabus
            if self.is_valid():
                self.boat_id = boat.id
                self.save()
        else:
            # drop all previous telemetry for this boat
            if self.is_valid():
                db.session.query(Telemetry).filter_by(boat_id=boat.id).delete()
                self.boat_id = boat.id
                self.save()