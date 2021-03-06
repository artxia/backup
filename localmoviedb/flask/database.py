# coding: utf-8
import os
from sqlalchemy import Column, INTEGER, TEXT, BOOLEAN, DATETIME, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

realpath = os.path.split(os.path.realpath(__file__))[0]
sql_path = os.path.join(realpath,'movies.db')
engine = create_engine('sqlite:///{}'.format(sql_path),
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool,
                       echo=False)
DBSession = sessionmaker(bind=engine)
Base = declarative_base()


class Config(Base):
    __tablename__ = 'config'

    id = Column(INTEGER, primary_key=True)
    user = Column(TEXT)
    root_dir = Column(TEXT)
    movie_dir_re = Column(TEXT)
    tg_push_on = Column(BOOLEAN)
    tg_chatid = Column(TEXT)
    tg_bot_token= Column(TEXT)
    bark_push_on = Column(BOOLEAN)
    bark_tokens = Column(TEXT)
    server_cyann_on = Column(BOOLEAN)
    server_cyann_token = Column(TEXT)
    proxy_on = Column(BOOLEAN)
    proxy_url = Column(TEXT)


    def __init__(self, user, root_dir, movie_dir_re, tg_push_on, tg_chatid, tg_bot_token, bark_push_on,
                 bark_tokens, server_cyann_on, server_cyann_token, proxy_on, proxy_url):
        self.user = user
        self.root_dir = root_dir
        self.movie_dir_re = movie_dir_re
        self.tg_push_on = tg_push_on
        self.tg_chatid = tg_chatid
        self.tg_bot_token = tg_bot_token
        self.bark_push_on = bark_push_on
        self.bark_tokens = bark_tokens
        self.server_cyann_on = server_cyann_on
        self.server_cyann_token = server_cyann_token
        self.proxy_on = proxy_on
        self.proxy_url = proxy_url
    
    
    def to_json(self):
        if hasattr(self, '__table__'):
            _json = {}
            for i in self.__table__.columns:
                if i.name == 'id':
                    continue
                _json[i.name] = getattr(self, i.name)
            return _json
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class Movie(Base):
    __tablename__ = 'movie'

    id = Column(INTEGER, primary_key=True)
    type = Column(TEXT)  # ??????
    title = Column(TEXT)  # ??????
    original_title = Column(TEXT)  # ?????????
    year = Column(INTEGER)  # ??????
    update_date = Column(DATETIME)  # ????????????
    fanart = Column(TEXT) # ????????????
    trailer = Column(TEXT)  # ?????????
    uri = Column(TEXT)  # ????????????
    douban_url = Column(TEXT)  # ????????????
    thumbnail_url = Column(TEXT)  # ?????????
    douban_rating = Column(TEXT)  # ????????????
    intro = Column(TEXT) #??????
    viedo_files =  Column(TEXT) # ????????????
    desc_html = Column(TEXT) # ??????????????????


    def __init__(self, title, _type, original_title, year, update_date, trailer, fanart, uri, douban_url, thumbnail_url,
                 douban_rating, intro, viedo_files, desc_html):
        self.title = title
        self.type = _type
        self.original_title = original_title
        self.year = year
        self.update_date = update_date
        self.trailer = trailer
        self.fanart = fanart
        self.uri = uri
        self.douban_url = douban_url
        self.thumbnail_url = thumbnail_url
        self.douban_rating = douban_rating
        self.intro = intro
        self.viedo_files = viedo_files
        self.desc_html = desc_html

    def __repr__(self):
        full_title = '{} {} ???{}???'.format(self.title, self.type, self.original_title,
                                         self.year) if self.title != self.original_title \
            else '{} ???{}???'.format(self.title, self.year)

        return 'Movie:{}'.format(full_title)


    def to_json(self):
        if hasattr(self, '__table__'):
            _json = {}
            for i in self.__table__.columns:
                if i.name == 'update_date':
                    _json[i.name] = str(getattr(self, i.name))[:10]
                    continue
                _json[i.name] = getattr(self, i.name)
            return _json
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class MovieTag(Base):
    __tablename__ = 'movie_tag'
    id = Column(INTEGER, primary_key=True)
    movie_id = Column(INTEGER)
    tag_id = Column(INTEGER)

    def __init__(self, movie_id, tag_id):
        self.movie_id = movie_id
        self.tag_id = tag_id


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(INTEGER, primary_key=True)
    text = Column(TEXT)

    def __init__(self, text):
        self.text = text
    
    def to_json(self):
        if hasattr(self, '__table__'):
            _json = {}
            for i in self.__table__.columns:
                _json[i.name] = getattr(self, i.name)
            return _json
        raise AssertionError('<%r> does not have attribute for __table__' % self)


class MovieActor(Base):
    __tablename__ = 'movie_actor'
    id = Column(INTEGER, primary_key=True)
    movie_id = Column(INTEGER)
    actor_id = Column(INTEGER)

    def __init__(self, movie_id, actor_id):
        self.movie_id = movie_id
        self.actor_id = actor_id

class MovieDirector(Base):
    __tablename__ = 'movie_director'
    id = Column(INTEGER, primary_key=True)
    movie_id = Column(INTEGER)
    director_id = Column(INTEGER)

    def __init__(self, movie_id, director_id):
        self.movie_id = movie_id
        self.director_id = director_id


class Role(Base):
    __tablename__ = 'role'
    id = Column(INTEGER, primary_key=True)
    name = Column(TEXT)
    info = Column(TEXT)

    def __init__(self, name, info):
        self.info = info
        self.name = name

    
    def to_json(self):
        if hasattr(self, '__table__'):
            _json = {}
            for i in self.__table__.columns:
                _json[i.name] = getattr(self, i.name)
            return _json
        raise AssertionError('<%r> does not have attribute for __table__' % self)


Base.metadata.create_all(engine)
