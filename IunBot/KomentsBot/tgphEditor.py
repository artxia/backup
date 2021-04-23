from config import TGPH_TOKEN
from telegraph import Telegraph
from data_base import db

class TelegraphEditor(object):
    def __init__(self):
        self.tgph = Telegraph(TGPH_TOKEN)

    def new_comments(self):
        path_top = self.tgph.create_page(
            title = 'Komments | 0', html_content = '-'
        )['path']
        path_new = self.tgph.create_page(
            title = 'Komments | 0', html_content = '-'
        )['path']
        print('CREATED NEW COMMENTS: ', path_top)
        return path_new, path_top


    def update_answers(self, comment_id):
        comnt = db.get_comment(comment_id)
        answers = db.get_answers(comment_id)
        


        body = f'''
        {comnt.text_main}<br/>
         ✉️ {comnt.count_answers}  |  ❤️ {comnt.liked_count}  |  {comnt.date_add.strftime('%H:%M')}<br/>
        <aside><a href=\"https://t.me/KomentsBot?start=1{comnt.id}\">Write answer</a></aside>
        '''

        for answer in answers:
            body += f'''
            <b>{answer.user_name}</b><br/>
            {answer.text_main}<br/>
            ❤️ {comnt.liked_count}  |  {comnt.date_add.strftime('%H:%M')}<br/>
            '''


        title = comnt.user_name

        if comnt.answers_url:
            print('Update answer page')
            r = self.tgph.edit_page(
                path = comnt.answers_url,
                title = title,
                html_content = body
            )
            print(r)

        else:
            print('Create answer page')

            path = self.tgph.create_page(
                title = title,
                html_content = body
            )['path']
            print(path)
            db.set_comment(
                comment_id = comment_id,
                set = 'answers_url',
                value = path
            )
        
        
               

    def update_comments(self, post_id):
        post = db.get_post_info_comments(post_id)

        print(post)
        print(type(post))
        print(post.telegraph_path_new)

        comments_new = db.get_comments(post_id, sort_comnts = 'new', limit_comnts = 25) 
        comments_top = db.get_comments(post_id, sort_comnts = 'top', limit_comnts = 25) 

        path_new = post.telegraph_path_new
        path_top = post.telegraph_path_top

        base = ' <a href="http://t.me/KomentsBot?start=0' + str(post_id) + '"> Add comments</a><br/>'



        body_new = f'Sort <b>New</b> <a href="https://telegra.ph/{path_top}">Top</a> ' + base
        body_top = f'Sort <a href="https://telegra.ph/{path_new}">New</a> <b>Top</b> ' + base


        
    

        for com in comments_new:
            print(com.answers_url, type(com.answers_url))
         
            comment = f'''
            <h4>{com.user_name}</h4>
            {com.text_main}<br/>
            <a href=\"https://t.me/KomentsBot?start=1{com.id}\"> ✉ {com.count_answers}  |  ❤️ {com.liked_count}  |  {com.date_add.strftime('%H:%M')}</a><br/>
            '''

            if com.count_answers > 0:
                answer = db.get_one_answer(com.id)

                comment += f'''
                <b>{answer.user_name}</b><br/>
                <i>{answer.text_main}</i><br/>
                ❤️ {answer.liked_count}  |  {answer.date_add.strftime('%H:%M')}<br/>
                <a href=\"https://telegra.ph/{com.answers_url}\">Open all answers {com.count_answers}</a> <br/>
                '''

            body_new += comment

        for com in comments_top:
            print(com.answers_url, type(com.answers_url))
         
            comment = f'''
            <h4>{com.user_name}</h4>
            {com.text_main}<br/>
            <a href=\"https://t.me/KomentsBot?start=1{com.id}\"> ✉ {com.count_answers}  |  ❤️ {com.liked_count}  |  {com.date_add.strftime('%H:%M')}</a><br/>
            '''

            if com.count_answers > 0:
                answer = db.get_one_answer(com.id)

                comment += f'''
                <b>{answer.user_name}</b><br/>
                <i>{answer.text_main}</i><br/>
                ❤️ {answer.liked_count}  |  {answer.date_add.strftime('%H:%M')}<br/>
                <a href=\"https://telegra.ph/{com.answers_url}\">Open all answers {com.count_answers}</a> <br/>
                '''

            body_top += comment






        title = 'Komments | ' + str(post.all_comments)

        print(post[0], post[1])

        r =self.tgph.edit_page(
            path = post[0],
            title = title,
            html_content = body_new
        )
        self.tgph.edit_page(
            path = post[1],
            title = title,
            html_content = body_top
        )

        print(r)


tgph_editor = TelegraphEditor()



