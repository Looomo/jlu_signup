import requests
from urllib import request
from http import cookiejar
import json
import time
from  sendemail import mail
import re
from urllib.parse import quote , unquote
import random


cfg = [
	{
		'user':'zhangsan20',
		'passwd':'user1_passwd'
	},
	{
		'user':'mzwang20',
		'passwd':'user2_passwd'
	},
	{
		'user':'user3',
		'passwd':'user3_passwd'
	},
	{
		'user':'user4',
		'passwd':'user4_passwd'
	}

]

def check_signed():
	return False

import logging
from logging import handlers


class Logger(object):
    level_relations = {
        'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'crit':logging.CRITICAL
    }

    def __init__(self,filename = 'log.log',level='info',when='D',backCount=3,fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)
        self.logger.setLevel(self.level_relations.get(level))
        sh = logging.StreamHandler()
        sh.setFormatter(format_str) 
        th = handlers.TimedRotatingFileHandler(filename=filename,when=when,backupCount=backCount,encoding='utf-8')
        th.setFormatter(format_str)
        self.logger.addHandler(sh) 
        self.logger.addHandler(th)


from datetime import tzinfo,timedelta

class UTC(tzinfo):
    """UTC"""
    def __init__(self,offset = 0):
        self._offset = offset
    def utcoffset(self, dt):
        return timedelta(hours=self._offset)
    def tzname(self, dt):
        return "UTC +%s" % self._offset
    def dst(self, dt):
        return timedelta(hours=self._offset)


import os
import datetime
import js2py
import ssl

def read_js():
	with open('dec.js' , 'r', encoding='UTF-8') as file:
		res = file.read()
	return res
def cal_rsa(u,p,lt):
	context = js2py.EvalJs()
	context.execute(read_js())
	# encode gonna take time
	rsa = context.strEnc( "{}{}{}".format(u,p,lt) , '1', '2', '3'  )
	return rsa
def report(log , config , restart = 0):
	#ssl._create_default_https_context = ssl._create_unverified_context
	if restart:
		log.Warning("Resarted for {} times. Please check log file for details.".format(restart))
	base = 'https://ehall.jlu.edu.cn'
	with  requests.Session() as r:
		r.headers.update({'Referer': 'https://cas.jlu.edu.cn/'})

		logout = r.get("https://ehall.jlu.edu.cn/taskcenter/logout",verify=False)
		log.info("Logout returned: {}:".format(logout.status_code))

		res = r.get('https://cas.jlu.edu.cn/tpass/login',verify=False)
		lt = re.findall(r'name="lt" value=".+"', res.content.decode())[0].split('"')[-2]
		exec = re.findall(r'name="execution" value=".+"', res.content.decode())[0].split('"')[-2]
		eid = re.findall(r'name="_eventId" value=".+"', res.content.decode())[0].split('"')[-2]
		log.info("Encoding. Gonna take time.")
		rsa = cal_rsa(config['user'], config['passwd'], lt )
		log.info("Encod done.")
		data = {
			'rsa': rsa,
			'ul': len(config['user']),
			'pl': len(config['passwd']),
			'sl': 0,
			'lt':lt,
			'execution':exec,
			'_eventId': eid
		}


		log.info("Trying to login.")
		# 
		url = "https://cas.jlu.edu.cn/tpass/login"
		login = r.post(url, data=data,  allow_redirects = True, verify=False)
		if login.status_code == 403:
			log.warning("Login status {} with auto-redirecting, may got error.".format(login.status_code))

		log.info("Trying to get taskcenter/wechat/index.")
		url = 'https://ehall.jlu.edu.cn/taskcenter/wechat/index'
		res = r.get(url, verify=False)
		if not res.text.__contains__("吉林大学服务大厅"):
			log.error("Unable to access taskcenter/wechat/index, restarting.")

			return False
		
		doen_url = "https://ehall.jlu.edu.cn/taskcenter/api/me/processes/done?limit=50&start=0"
		done_page =  r.get(doen_url,verify=False)
		record = json.loads( done_page.text )
		day_today = datetime.datetime.now()

		# if checktime():
		for rec in record['entities']:
				#rec = record['entities'][i]
				if rec['name'] == '研究生每日健康打卡':
					# if ( datetime.date.fromtimestamp(rec['update']) ) < datetime.date.today():
					if (checktime_(rec['update'])):

						log.info("Last report: {}, reporting.".format( datetime.datetime.fromtimestamp(rec['update']).strftime("%Y-%m-%d %H:%M:%S")  ))
						q_data = {

						}
						res = r.get("https://ehall.jlu.edu.cn/infoplus/form/YJSMRDK/start")
						csrf = re.findall(f'itemscope="csrfToken" content="[a-zA-Z0-9]+"' , res.text)[0].split('"')[-2]
						q_data['idc'] = 'YJSMRDK'
						q_data['csrfToken'] = csrf
						q_data['formData'] = '{"_VAR_URL":"https://ehall.jlu.edu.cn/infoplus/form/YJSMRDK/start","_VAR_URL_Attr":"{}"}'
						q_data['release'] = ''

						res = r.post('https://ehall.jlu.edu.cn/infoplus/interface/start' , data = q_data)

						form_page = res.json()['entities'][0]
						stepid = form_page.split('/')[-2]


						postPayload = {'stepId': stepid, 'csrfToken': csrf}
						render = r.post(url='https://ehall.jlu.edu.cn/infoplus/interface/render', data=postPayload)
						render_info = json.loads(render.content)['entities'][0]['data']

						data = {
							'actionId': 1,
							'formData': json.dumps(render_info),
							'nextUsers': '{}',
							'stepId': stepid,
							'timestamp': int(time.time()),
							'csrfToken': csrf,
							'lang': 'zh'
						}

						res = r.post(url='https://ehall.jlu.edu.cn/infoplus/interface/doAction', data=data)

						mail( subject="Recorder." , context="打卡似乎成功了." , receiver= 'receiver@receiver.com')
					else:
						log.info("Reported today at: {}.".format( datetime.datetime.fromtimestamp(rec['update']).strftime("%Y-%m-%d %H:%M:%S")  ))

					break
		r.close()

	r.close()
	log.info("HeartBeat.")
	return True

def checktime_(timestamp):

	time_list = [[7,12 ] ]
	#time_list = [[7,12 ],[ 20,24 ]   ]

	last_time = datetime.datetime.fromtimestamp(timestamp)
	
	if checktime( time_list[0][0] , time_list[0][1] ):

		return datetime.date.fromtimestamp(timestamp) < datetime.date.today()
	if checktime( time_list[1][0] ,time_list[1][1]  ):
		return last_time.hour < time_list[1][0] or last_time.hour > time_list[1][1]

def checktime(start , end):
	return datetime.datetime.now().hour >= start and datetime.datetime.now().hour < end

def main():
	# os.chdir(f"D:\myProgram\daka")
	log = Logger().logger
	log.info("Inited.")
	report(log,cfg[0])
	mail(receiver='receiver@receiver.com' , context="这是为了提醒你自动打卡挂上了.")
	while True:
		if checktime(7,12): # or checktime(20,24):
			try:
				for config in cfg:
					log.info("\n\n")
					log.info("User:{}".format(config['user']))
					report(log,config)

				log.info("All users reported.")
			except Exception as info: 
				mail(receiver='receiver@receiver.com' , context="出错了，今天的卡可能没打上,正在重试。详情："+str(info))
				log.error("Error occured." + str(info))
				time.sleep(300)
				continue
		else:
			log.info("No need to report now.")
		
		time.sleep(60*60)

if __name__ == '__main__':
	
	requests.packages.urllib3.disable_warnings()
	main()
