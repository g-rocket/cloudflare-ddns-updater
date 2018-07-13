#!/usr/bin/env python3

#import dns.resolver
import subprocess
import requests
import os

def get_ip():
	return subprocess.check_output(['dig','+short','myip.opendns.com','@resolver1.opendns.com']).decode('utf-8').strip()
	#ip_resolver = dns.resolver.Resolver()
	#ip_resolver.nameservers = ['208.67.222.222'] # resolver1.opendns.com
	#ip_resolver.query('myip.opendns.com')

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

def main():
	ip = get_ip()
	try:
		with open('old_ip', 'r') as old_ip_file:
			old_ip = old_ip_file.read()
	except FileNotFoundError:
		print('Old IP not found; IP is {}'.format(ip))
		with open('old_ip', 'w') as old_ip_file:
			old_ip_file.write(ip)
		return
	if old_ip == ip:
		#print('IP is still {}; not updating'.format(ip))
		return
	print('IP was {}, now {}; updating!'.format(old_ip, ip))
	with open('old_ip', 'w') as old_ip_file:
		old_ip_file.write(ip)
	update_cloudflare(old_ip, ip)

if __name__ == '__main__':
	main()
