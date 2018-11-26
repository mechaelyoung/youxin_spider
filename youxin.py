# _*_ coding:utf-8 _*_
import requests
import re
import time
import MySQLdb
import MySQLdb.cursors
from lxml import etree
from urllib import parse
from random import randint

fiter_url = []
url_list = ['https://www.xin.com/guangzhou/i1/']
start_url = 'https://www.xin.com/guangzhou/i1/'
header = {
	'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
}

def start_request(url,header):
	response = requests.get(url=url,headers=header)
	response.enconding = 'utf-8'
	text = response.text
	return text

def get_next_url(url):
	for i in url:
		if i in fiter_url:
			pass
		else:
			fiter_url.append(i)
			time.sleep(randint(1,3))
			content = start_request(i,header)
			return content

def get_car_info_url(text):
	html = etree.HTML(text,etree.HTMLParser())
	next_url = html.xpath('//div[contains(@class,"con-page")]//a/@href')
	for t in next_url:
		next_url = parse.urljoin(start_url,t)
		url_list.append(next_url)
	next_nodes = html.xpath('//div[@class="across"]//a[@class="aimg"]/@href')
	for next_node in next_nodes:
		detail_url = parse.urljoin(start_url,next_node)
		yield detail_url

def get_car_info(detail_url):
	for i in detail_url:
		time.sleep(randint(1,3))
		text = start_request(i,header=header)
		html = etree.HTML(text,etree.HTMLParser())
		data = {}
		data['title'] = html.xpath('//span[@class="cd_m_h_tit"]/text()')[0]
		data['register_time'] = html.xpath('//span[@class="cd_m_desc_key"][1]/text()')[0]
		data['miles'] = html.xpath('//a[@class="cd_m_desc_val"]/text()')[0]
		data['city'] = '广州'
		data['oil_mount'] = html.xpath('//li[contains(@class,"cd_m_desc_line")][4]/span[@class="cd_m_desc_val"]/text()')[0]
		data['price'] = html.xpath('//span[@class="cd_m_info_jg"]/b/text()')[0]
		yield data

def data_clean(datas):
	for data in datas:
		data['miles'] = data['miles'].strip()
		data['title'] = data['title'].strip()

		speed_pattern = r'.*(手动|自动).*'
		m = re.match(speed_pattern,data['title'])
		data['speed_box'] = m.group(1)

		title_pattern = r'(.*\d+款).*'
		t = re.match(title_pattern,data['title'])
		data['title'] = t.group(1)
		
		data['register_time'] = data['register_time'].replace('上牌','')
		yield data

def insert_into_sql(data):
	conn = MySQLdb.connect('localhost','root','9901914846','guazi',charset='utf8',use_unicode=True)
	cursor = conn.cursor()
	insert_sql = """
		insert into youxin_data(title,register_time,miles,city,oil_mount,speed_box,price)
		VALUES(%s,%s,%s,%s,%s,%s,%s)
	"""
	params = (data['title'],data['register_time'],data['miles'],data['city'],data['oil_mount'],data['speed_box'],data['price'])

	cursor.execute(insert_sql,params)
	conn.commit()


if __name__ == '__main__':
	while fiter_url != url_list:
		text = get_next_url(url_list)
		detail_url = get_car_info_url(text)
		datas = get_car_info(detail_url)
		data = data_clean(datas)
		for i in data:
			if i:
				insert_into_sql(i)
				print('插入成功')
			else:
				print('插入失败')

