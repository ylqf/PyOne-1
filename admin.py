#-*- coding=utf-8 -*-
from flask import Blueprint,redirect,url_for,request,render_template,flash,session,jsonify,Response,make_response
from flask_sqlalchemy import Pagination
from function import *
from config import *
from run import FetchData,path_list,GetName,CodeType,_remote_content,rd
import os
import io
import re
import subprocess
import random
import urllib
from shelljob import proc
import eventlet

eventlet.monkey_patch()


admin = Blueprint('admin', __name__,url_prefix='/admin')

############功能函数
def set(key,value):
    allow_key=['title','share_path','downloadUrl_timeout','allow_site','password']
    if key not in allow_key:
        return u'禁止修改'
    print 'set {}:{}'.format(key,value)
    config_path=os.path.join(config_dir,'config.py')
    with open(config_path,'r') as f:
        old_text=f.read()
    with open(config_path,'w') as f:
        if key=='allow_site':
            value=value.split(',')
            new_text=re.sub('{}=.*'.format(key),'{}={}'.format(key,value),old_text)
        else:
            new_text=re.sub('{}=.*'.format(key),'{}="{}"'.format(key,value),old_text)
        f.write(new_text)


############视图函数
@admin.before_request
def before_request():
    if request.endpoint.startswith('admin') and request.endpoint!='admin.login' and session.get('login') is None:
        return redirect(url_for('admin.login'))


########web console
@admin.route('/web_console')
def web_console():
    g = proc.Group()
    action=request.args.get('action')
    allow_action=['UpdateFile','UploadDir','Upload']
    if action not in allow_action:
        return make_response('error')
    if action in ['UploadDir','Upload']:
        local=urllib.unquote(request.args.get('local'))
        remote=urllib.unquote(request.args.get('remote'))
        cmd=["python","-u",os.path.join(config_dir,'function.py'),action,local,remote]
    elif action=='UpdateFile':
        dir_=request.args.get('dir')
        if dir_=='/':
            cmd=["python","-u",os.path.join(config_dir,'function.py'),action]
        else:
            cmd=["python","-u",os.path.join(config_dir,'function.py'),'Dir',dir_]
    else:
        cmd=["python","-u",os.path.join(config_dir,'function.py'),action]
    p = g.run(cmd)
    def read_process():
        while g.is_pending():
            lines = g.readlines()
            for proc, line in lines:
                yield "data:" + line + "\n\n"
        yield "data:end\n\n"
    return Response(read_process(), mimetype= 'text/event-stream')

########admin
@admin.route('/',methods=['GET','POST'])
@admin.route('/setting',methods=['GET','POST'])
def setting():
    if request.method=='POST':
        title=request.form.get('title','PyOne')
        share_path=request.form.get('share_path','/')
        downloadUrl_timeout=request.form.get('downloadUrl_timeout',5*60)
        allow_site=request.form.get('allow_site','no-referrer')
        password1=request.form.get('password1')
        password2=request.form.get('password2')
        password_s=request.form.get('password')
        if password_s is None:
            flash(u'请输入原密码')
        else:
            new_password=password
            if ((password1 is not None and password2 is None) or (password1 is None and password2 is not None)):
                flash(u'请输入新密码或者二次确认新密码')
            elif password1 is not None and password2 is not None and password1!=password2:
                flash(u'两次输入密码不相同')
            elif password1 is not None and password2 is not None and password1==password2:
                new_password=password1
            if password_s==password:
                set('title',title)
                set('downloadUrl_timeout',downloadUrl_timeout)
                set('share_path',share_path)
                set('allow_site',allow_site)
                set('password',new_password)
            else:
                flash(u'原密码错误')
        return render_template('admin/setting.html')
    return render_template('admin/setting.html')



@admin.route('/upload',methods=["POST","GET"])
def upload():
    if request.method=='POST':
        local=request.form.get('local')
        remote=request.form.get('remote')
        if not os.path.exists(local):
            flash('本地目录/文件不存在')
            return redirect(url_for('admin.upload'))
        return render_template('admin/upload.html',remote=remote,local=local,action='UploadDir')
    return render_template('admin/upload.html')



@admin.route('/cache',methods=["POST","GET"])
def cache():
    if request.method=='POST':
        dir_=request.form.get('dir')
        return render_template('admin/cache.html',dir=dir_,action='UpdateFile')
    return render_template('admin/cache.html')


@admin.route('/manage',methods=["POST","GET"])
def manage():
    if request.method=='POST':
        pass
    path=urllib.unquote(request.args.get('path','/'))
    if path=='':
        path='/'
    if path!='/' and path.startswith('/'):
        path=re.sub('^/+','',path)
    page=request.args.get('page',1,type=int)
    image_mode=request.args.get('image_mode')
    sortby=request.args.get('sortby')
    order=request.args.get('order')
    if sortby:
        sortby=request.args.get('sortby')
    else:
        sortby=request.cookies.get('sortby') if request.cookies.get('sortby') is not None else 'lastModtime'
        sortby=sortby
    if order:
        order=request.args.get('order')
    else:
        order=request.cookies.get('order') if request.cookies.get('order') is not None else 'desc'
        order=order
    resp,total = FetchData(path=path,page=page,per_page=50,sortby=sortby,order=order)
    pagination=Pagination(query=None,page=page, per_page=50, total=total, items=None)
    resp=make_response(render_template('admin/manage.html',pagination=pagination,items=resp,path=path,sortby=sortby,order=order,endpoint='admin.manage'))
    resp.set_cookie('admin_sortby',str(sortby))
    resp.set_cookie('admin_order',str(order))
    return resp


@admin.route('/edit',methods=["GET","POST"])
def edit():
    if request.method=='POST':
        fileid=request.form.get('fileid')
        content=request.form.get('content').encode('utf-8')
        info={}
        token=GetToken()
        app_url=GetAppUrl()
        headers={'Authorization':'bearer {}'.format(token)}
        url=app_url+'_api/v2.0/me/drive/items/{}/content'.format(fileid)
        print url
        try:
            r=requests.put(url,headers=headers,data=content,timeout=10)
            data=json.loads(r.content)
            if data.get('@content.downloadUrl'):
                info['status']=0
                info['msg']='修改成功'
                rd.delete('{}:content'.format(fileid))
            else:
                info['status']=0
                info['msg']=data.get('error').get('message')
        except:
            info['status']=0
            info['msg']='修改超时'
        return jsonify(info)
    fileid=request.args.get('fileid')
    name=GetName(fileid)
    ext=name.split('.')[-1]
    language=CodeType(ext)
    if language is None:
        language='Text'
    content=_remote_content(fileid)
    return render_template('admin/edit.html',content=content,fileid=fileid,language=language)




@admin.route('/delete',methods=["POST"])
def delete():
    ids=request.form.get('id')
    if ids is None:
        return jsonify({'msg':u'请选择要删除的文件','status':0})
    ids=ids.split('##')
    infos={}
    infos['status']=1
    infos['delete']=0
    infos['fail']=0
    for id in ids:
        status=DeleteRemoteFile(id)
        if status:
            infos['delete']+=1
        else:
            infos['fail']+=1
    return jsonify(infos)







@admin.route('/login',methods=["POST","GET"])
def login():
    if request.method=='POST':
        password1=request.form.get('password')
        if password1==password:
            session['login']='true'
            return redirect(url_for('admin.setting'))
        else:
            return render_template('admin/login.html')
    return render_template('admin/login.html')


@admin.route('/logout',methods=['GET','POST'])
def logout():
    session.pop('login',None)
    return redirect('/')

@admin.route('/reload',methods=['GET','POST'])
def reload():
    cmd='supervisorctl -c {} restart pyone'.format(os.path.join(config_dir,'supervisord.conf'))
    subprocess.Popen(cmd,shell=True)
    flash('正在重启网站...')
    return redirect(url_for('admin.setting'))


