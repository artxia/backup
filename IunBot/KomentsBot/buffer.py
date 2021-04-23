class Buffer(object):
    def __init__(self):
        self.bildposts = {}

    def add_bildpost(self, user_id,  post):
        self.bildposts[user_id] = post
    
    def get_bildpost(self, user_id):
        return self.bildposts.get(user_id)

    def set_arg_post(self, user_id, key, value):
        setattr(self.bildposts[user_id], key, value)
    
    def get_arg_post(self, user_id, key):
        return getattr(self.bildposts[user_id], key)
        
        

buffer = Buffer()

