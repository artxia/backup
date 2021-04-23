import json
from pprint import pprint

from telegram import InlineKeyboardButton as Button
from telegram import InlineKeyboardMarkup as Markup
  

class User(object):
    def __init__(self, data):
        self.id = data.id
        self.mode_write = data.mode_write

class Comment(object):
    def __init__(self, comment):
        self.id          = comment.id
        self.post_id     = comment.post_id
        self.user_name   = comment.user_name
        self.channel_id  = comment.channel_id
        self.text        = comment.text_main
        self.date_add    = comment.date_add.strftime('%H:%M') 
        self.user_creator= comment.user_creator_id
        self.liked_count = comment.liked_count
        self.users_liked = comment.users_liked
        self.count_subcomnt = comment.count_subcomments

    def __repr__(self):
        return f'<{self.text} {self.date_add} {self.liked_count}>'


class BTS(object):
    def __init__(self, bts_json):
        print(bts_json)
        self.bts = []
        if bts_json:
            data = json.loads(bts_json)
            pprint(data)
            
            if data:
                for i, line in enumerate(data):
                    self.bts.append([])
                    for btn_dict in line:
                        self.bts[i].append(BTN().from_dict(btn_dict))
                        
    
    def add(self, type, text, url = None):
        id = len(self.bts)
        self.bts.append([BTN(id, type, text, url)])

    def check_comments(self):
        for line in self.bts:
            for btn in line:
                if btn.type == 'comments':
                    return True

        return False

    def upcount(self, btn_id, from_user):
        up = False
        for line in self.bts:
            for btn in line:
                if btn.id == btn_id:
                    btn.upcount(from_user)
                    up = True
        if not up:
            raise Exception('Not found button')
                

        

    def get_tg_bts(self, markup = True, config = False, ch_id = None):

        if self.bts is None:
            return []

        print(self.bts)
        bts = []
        for i, line in enumerate(self.bts):
            bts.append([])
            for btn in line:
                bts[i].append(btn.get_tg(config, ch_id))

        if markup:
            return Markup(bts)
        else:
            return bts

    def to_json(self):
        bts_json = []
        for i, line in enumerate(self.bts):
            bts_json.append([])
            for btn in line:
                bts_json[i].append(btn.to_dict())

        return json.dumps(bts_json)

    def __repr__(self):
        bts_info = []
        for i, line in enumerate(self.bts): 
            bts_info.append([])
            for btn in line:
                bts_info[i].append(btn.__repr__())

        return str(bts_info)

        



class BTN(object):
    
    def __init__(self, id = None, type = None, text =None , url = None, users_liked = [], data = None, count = 0):
        self.id = id
        self.type = type
        self.text = text
        self.url = url 
        self.users_liked = users_liked
        self.count = count
        self.data = data or 'upcount ' + str(id) 

    def upcount(self, from_user):
        if from_user in self.users_liked:
            self.users_liked.remove(from_user)
            self.count -= 1
        else:
            self.users_liked.append(from_user)
            self.count += 1

    @classmethod
    def from_dict(cls, btn_dict):
        return cls(
            id =   btn_dict['id'],
            type = btn_dict['type'],
            text = btn_dict['text'],
            data = btn_dict['data'],
            users_liked = btn_dict['users_liked'],
            url = btn_dict['url'],
            count = btn_dict['count']   
        )
       




    def to_dict(self):
        return {
            'id':   self.id,
            'type': self.type,
            'text': self.text,
            'data': self.data,
            'users_liked': self.users_liked,
            'url': self.url,
            'count':self.count
        }
        
    
    def __repr__(self):
        return f'<BTN object id: {self.id} text: {self.text} type: {self.type} count:{self.count}>'

    def get_tg(self, config, ch_id):
        if config:
            return Button(
                str(self.id + 1) +') '+ self.text,
                callback_data = f'open del_btn ?btn_id={self.id}&ch_id={ch_id}'
            )

        if self.type == 'url':
            return Button(self.text, url = self.url)
        elif self.type == 'reaction':
            return Button(self.text.format(count = self.count), callback_data = self.data)
        elif self.type == 'comments':
            return Button(self.text.format(count = self.count), url = self.url)
        else:
            raise Exception('Invalid type \'' + self.type + '\'of btn')
        

class Post(object):
    def __init__(self, user_id = None, type = None,
                 text = None,data = None, photo = None, photo_url = None, from_db = False):
        if from_db:
            self.id = data.id
            self.channel_id = data.channel_id
            self.msg_id = data.msg_id
            self.buttons = data.buttons
            self.all_comments = data.all_comments
            self.telegraph_path_top = data.telegraph_path_top
            self.telegraph_path_new = data.telegraph_path_new
        else:
            self.user_id = user_id
            self.text = text
            self.chennel_id = None
            self.photo = photo
            self.buttons = BTS()
            self.comments_on = False
            self.type = type
            self.photo_url = '&#8203;'
        
    

    def __repr__(self):
        return str(self.id)



        

# Comments      
# id          
# post_id     
# user_name   
# channel_id  
# text        
# date_add    
# user_creator 
# liked_count  
# users_liked 
# count_answers   re:name

# answers_url     +


# Answers
# id
# post_id
# user_name
# channel_id
# text
# date_add
# user_creator
# liked_count
# users_liked
# root_comment_id

# create table answers(
# id        serial not null,
# post_id    bigint,
# user_name    text,
# channel_id  bigint,
# text_main text,
# date_add    timestamp default now(),
# user_creator int,
# liked_count int,
# users_liked int[],
# root_comment_id int,
# )
