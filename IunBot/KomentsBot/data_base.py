import json
import psycopg2
import psycopg2.extras


from type_s import User, Post, Comment, BTS
import config


class DB(object):
    def __init__(self):
        self.conn = psycopg2.connect(config.DB_URL)
    
    def connect(func):
        def decorator(self, *args, **kwargs):
            with self.conn:
                with self.conn.cursor(cursor_factory = psycopg2.extras.NamedTupleCursor) as self.cur:

                    data = func(self, *args, **kwargs)

            return data
        return decorator

    @connect
    def check_user(self, user_id):
        self.cur.execute("""INSERT INTO Users (id)
                        SELECT %s WHERE 
                            NOT EXISTS (
                                SELECT 1 FROM Users WHERE id = %s 
                                );
                        SELECT * FROM Users WHERE id = %s;
                            """, (user_id, user_id, user_id,))
        

        return User(self.cur.fetchone())

    @connect
    def set_user_param(self, user_id, set, arg):   
        self.cur.execute("UPDATE Users SET {} = %s WHERE id = %s;".format(set), (arg, user_id,))

    @connect
    def user_get(self, user_id, get):
        self.cur.execute("SELECT {} FROM Users WHERE id = %s;".format(get),(user_id,))
        return self.cur.fetchone()[0]
        


    @connect
    def add_channel(self, user_id, ch_id):
        self.cur.execute("""INSERT into chsetting (id, user_id)
                        VALUES (%s, %s)""",(ch_id, user_id,))
            
    @connect
    def get_all_ch(self, user_id):
        self.cur.execute(""" SELECT id FROM chsetting
                        WHERE user_id = %s""",(user_id,))
    
        return list(map(lambda x: x.id, self.cur.fetchall()))

    @connect
    def get_ch_setting(self, ch_id):
       
        self.cur.execute("""SELECT * FROM chsetting
                        WHERE id = %s""",(ch_id,))
        
        return self.cur.fetchone()

    @connect
    def get_arg_channel(self, ch_id, args):
        self.cur.execute("select {} from chsetting where id = %s;".format(', '.join(args)), (ch_id,))
        return self.cur.fetchone()
         

    @connect
    def set_buttons_channel(self, ch_id, buttons, comments_on):
        
        self.cur.execute("""
            UPDATE chsetting 
            SET default_btn_markup = %s, comments_on = %s
            WHERE id = %s;
        """,(buttons.to_json(), comments_on, ch_id,))

    @connect
    def set_buttons_post(self, ch_id, msg_id, buttons):
        self.cur.execute("UPDATE posts SET buttons = %s  WHERE channel_id = %s AND msg_id = %s;",
            (buttons.to_json(), ch_id, msg_id))

    @connect
    def get_buttons_channel(self, ch_id):
        self.cur.execute("SELECT default_btn_markup, comments_on FROM chsetting WHERE id = %s;",(ch_id,))
        data = self.cur.fetchone()

        return BTS(data.default_btn_markup), data.comments_on


    @connect
    def new_post(self, channel_id, buttons, comments_on, user_creator_id = None,
                 telegraph_path_new = None, telegraph_path_top = None):
        
        if comments_on:
            sql = '''insert into posts 
                (comments_on, channel_id, user_creator_id, buttons,
                 telegraph_path_new, telegraph_path_top)
                VALUES (true, %s, %s, %s, %s, %s) RETURNING id;'''

            data = (channel_id, user_creator_id, buttons,
                    telegraph_path_new, telegraph_path_top,)
        else:
            sql = '''insert into posts
                (comments_on, channel_id, user_creator_id, buttons)
                VALUES (false, %s, %s, %s) RETURNING id;'''

            data = (channel_id, user_creator_id, buttons,)

        self.cur.execute(sql, data)
        return self.cur.fetchone().id
        
    @connect
    def get_post_buttons(self, post_id = None, ch_id = None, msg_id = None):
        if post_id:
            self.cur.execute("SELECT buttons FROM posts WHERE id = %s;",(post_id,))

        else:
            self.cur.execute(
                "SELECT buttons FROM posts WHERE channel_id = %s AND msg_id = %s;",
            (ch_id, msg_id,))
        return BTS(self.cur.fetchone().buttons)
    
    
    @connect
    def set_msg_id_post(self, post_id, msg_id):
        self.cur.execute("UPDATE posts SET msg_id = %s WHERE id = %s;",
            (msg_id, post_id,)
        )

    @connect
    def get_post_info_comments(self, post_id):
        self.cur.execute("""
            SELECT telegraph_path_new, telegraph_path_top, all_comments, msg_id, channel_id
            FROM posts
            WHERE id = %s;
        """,(post_id,))
        return self.cur.fetchone()

    @connect
    def get_one_answer(self, comments_id):
        self.cur.execute("SELECT * FROM answers WHERE root_comment_id = %s;", (comments_id,))
        return self.cur.fetchone()

    @connect
    def get_post(self, post_id = None, comment_id = None):
        
        if post_id is None:
            print(comment_id)
            self.cur.execute(
                "select post_id from coments where id = %s",
                (comment_id,)
            )
            post_id = self.cur.fetchone()['post_id']

        self.cur.execute("""select * from posts where id = %s;""",(post_id,))
   
        return self.cur.fetchone()

    @connect
    def get_comments(self, post_id, sort_comnts = 'new', limit_comnts = 3, offset = 0):
        if sort_comnts == 'new':
            self.cur.execute("""
                select * from coments
                where post_id = %s 
                order by date_add desc      
                limit %s offset %s;
                """,(post_id, limit_comnts, offset,)
            )

        elif sort_comnts == 'top':
            self.cur.execute("""
                select * from coments
                where post_id = %s 
                order by liked_count desc
                limit %s offset %s;
            """,(post_id, limit_comnts, offset,))

        return self.cur.fetchall()
         
    
    @connect
    def get_answers(self, root_comment_id):
        self.cur.execute("""
            SELECT * FROM answers
            WHERE root_comment_id = %s;
        """, (root_comment_id,))

        return self.cur.fetchall()
    
    @connect
    def new_comment(self, user_id, text, user_name, post_id, channel_id):
        self.cur.execute("""
            INSERT INTO coments (text_main, post_id, user_creator_id, channel_id, user_name)
            VALUES (%s, %s, %s, %s, %s);

            UPDATE posts SET all_comments = all_comments + 1 where id = %s;""",
            (text, post_id, user_id, channel_id, user_name, post_id,)
        )


    @connect
    def set_comment(self, comment_id, set, value):
        self.cur.execute("UPDATE coments SET {} = %s WHERE id = %s;".format(set), (value, comment_id,))

        
    @connect
    def new_answer(self, user_id, text, user_name, root_comnt_id):
        self.cur.execute("""
            select post_id, channel_id from coments where id = %s;
        """, (root_comnt_id,))

        ids = self.cur.fetchone()
        post_id = ids.post_id
        channel_id = ids.channel_id

        self.cur.execute("""

            INSERT INTO answers (post_id, channel_id, user_name, text_main, user_creator, root_comment_id)
            VALUES (%s, %s, %s, %s, %s, %s);

            update posts set all_comments = all_comments + 1 where id = %s;
            update coments set count_answers = count_answers + 1 where id = %s RETURNING count_answers;

        """,(post_id, channel_id, user_name, text, user_id, root_comnt_id, post_id, root_comnt_id))


        return self.cur.fetchone().count_answers, post_id



    @connect
    def like_comment(self, user_id, comment_id):
        self.cur.execute("""UPDATE coments SET 
                    liked_count = liked_count + 1,
                    users_liked = ARRAY_APPEND(users_liked, %s)
                    WHERE id = %s;""", (user_id, comment_id,))

    @connect
    def dislike_comment(self, user_id, comment_id):
        
        self.cur.execute("""update coments set
                    liked_count = liked_count - 1,
                    users_liked = ARRAY_REMOVE(users_liked, %s) 
                    WHERE id = %s;""", (user_id, comment_id,))

    @connect
    def delete_comment(self, comment_id):
        
        self.cur.execute("""
            SELECT post_id FROM coments WHERE id = %s;
        """, (comment_id,))
        post_id = self.cur.fetchone().post_id


        self.cur.execute("""
            UPDATE posts 
            SET all_comments = all_comments - 1
            WHERE id = %s;
            
            DELETE FROM coments WHERE id = %s;
        """, (post_id, comment_id))

        return post_id
        





    @connect
    def get_comment(self, comment_id):
        
        self.cur.execute("""
                    select * from coments where id = %s
                    """,(comment_id,))
        
        return self.cur.fetchone()
    



db = DB()
