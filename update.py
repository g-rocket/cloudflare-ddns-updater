#!/usr/bin/env python3

import subprocess
import socket
import requests
import os
import json
import ipaddress

def get_ip(v6=False):
	socket_type = socket.AF_INET6 if v6 else socket.AF_INET
	remote_address = '2001:4860:4860::8888' if v6 else '8.8.8.8'
	s = socket.socket(socket_type, socket.SOCK_DGRAM)
	try:
		s.connect((remote_address, 53))
	except OSError as e:
		if e.errno != 101: # 'Network is unreachable'
			raise e
		return False # desired v4/v6 not set up for internet access
	addr = s.getsockname()[0]
	if not ipaddress.ip_address(addr).is_private:
		return addr
	v4v6_flag = '-6' if v6 else '-4'
	return json.loads(subprocess.check_output(
		['dig',v4v6_flag,'+short','TXT','o-o.myaddr.l.google.com','@ns1.google.com'])
		.decode('utf-8'))

def get_var(varname):
	if varname not in globals():
		if varname in os.environ:
			globals()[varname] = os.environ[varname]
		else:
			try:
				mydir = os.path.dirname(os.path.abspath(__file__))
				globals()[varname] = subprocess.check_output(
						['bash', '-c', 'source .env && printf %s "${}"'.format(varname)], 
						cwd=mydir).decode('utf-8')
			except:
				print('{} not available; edit .env'.format(varname))
				globals()[varname] = ''


class CloudflareAuth(requests.auth.AuthBase):
	"""Attaches Cloudflare Authentication to the given Request object."""

	def __init__(self, email, key):
		self.email = email
		self.key = key

	def __eq__(self, other):
		return all([
			self.email == getattr(other, 'email', None),
			self.key == getattr(other, 'key', None)
		])

	def __ne__(self, other):
		return not self == other

	def __call__(self, r):
		r.headers['X-Auth-Email'] = self.email
		r.headers['X-Auth-Key'] = self.key
		return r

def cloudflare_api_get(req_url):
	return requests.get('https://api.cloudflare.com/client/v4/{}'.format(req_url),
		auth=CloudflareAuth(CLOUDFLARE_EMAIL, CLOUDFLARE_KEY)).json()

def cloudflare_api_put(req_url, data):
	return requests.put('https://api.cloudflare.com/client/v4/{}'.format(req_url),
		auth=CloudflareAuth(CLOUDFLARE_EMAIL, CLOUDFLARE_KEY), json=data).json()

def get_zone_id():
	data = cloudflare_api_get('zones')
	for res in data['result']:
		if res['name'] == ZONE_NAME:
			return res['id']

def get_records_to_change(zone_id, old_ip):
	data = cloudflare_api_get('zones/{}/dns_records?type=A'.format(zone_id))
	records = []
	for res in data['result']:
		if res['content'] == old_ip:
			records.append((res['id'], res['name']))
	return records

def update_record(zone_id, record_id, name, ip):
	cloudflare_api_put('zones/{}/dns_records/{}'.format(zone_id, record_id), {
			'type': 'A',
			'name': name,
			'content': ip
		})

def update_cloudflare(old_ip, ip):
	get_var('CLOUDFLARE_EMAIL')
	get_var('CLOUDFLARE_KEY')
	get_var('ZONE_NAME')
	zone_id = get_zone_id()
	records = get_records_to_change(zone_id, old_ip)
	for id, name in records:
		print('updating {} to point to {}'.format(name, ip))
		update_record(zone_id, id, name, ip)

def maybe_update(ipfile, ip):
	if not ip:
		return
	try:
		with open(ipfile, 'r') as old_ip_file:
			old_ip = old_ip_file.read()
	except FileNotFoundError:
		print('Old IP not found; IP is {}'.format(ip))
		with open(ipfile, 'w') as old_ip_file:
			old_ip_file.write(ip)
		return
	if old_ip == ip:
		#print('IP is still {}; not updating'.format(ip))
		return
	print('IP was {}, now {}; updating!'.format(old_ip, ip))
	with open(ipfile, 'w') as old_ip_file:
		old_ip_file.write(ip)
	update_cloudflare(old_ip, ip)

def main():
	maybe_update(os.path.expanduser('~/.ip'), get_ip(v6=False))
	maybe_update(os.path.expanduser('~/.ip6'), get_ip(v6=True))

if __name__ == '__main__':
	main()
