#-*- coding=utf-8 -*-
import os

#限制调用域名
allow_site=['no-referrer'] #如果不限制，则添加：no-referrer

#######源码目录
config_dir='/root/PyOne'
data_dir=os.path.join(config_dir,'data')

#######分享目录
share_path='/'

#onedrive类型设置
od_type='business_21v' #国际版：bussiness; 世纪互联版：bussiness_21v

#onedrive api设置
redirect_uri='https://auth.3pp.me/'
base_dict={
    'business':{
        'BaseAuthUrl':'https://login.microsoftonline.com',
        'ResourceID':'https://api.office.com/discovery/',
        'client_id':'7f41584d-b8a9-4362-b79e-cd1af45e19a3',
        'client_secret':' 3CXqrraR8Bvykx7og3sT7EkA8T1QgmAp79P/fHGIjhM=',
    },
    'business_21v':{
        'BaseAuthUrl':'https://login.partner.microsoftonline.cn',
        'ResourceID':'00000003-0000-0ff1-ce00-000000000000',
        'client_id':'3102ff3c-ed3f-4056-9c97-3ab67f305344',
        'client_secret':'2GFqeJoNgyKu2Nc95Lv8r73YJ5IgHdaFrdqBM1EGAI0=',
        }
    }


#下载链接过期时间
downloadUrl_timeout=5*60 #默认10分钟过期

#onedrive个人页的域名。国际版为com结尾，世纪互联版为cn结尾，最后面一定要带/
app_url=u'https://yourname-my.sharepoint.cn/'


