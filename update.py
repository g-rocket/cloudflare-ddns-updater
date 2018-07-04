#!/usr/bin/env python3

#import dns.resolver
import subprocess

def get_ip():
	return subprocess.check_output(['dig','+short','myip.opendns.com','@resolver1.opendns.com']).decode('utf-8').strip()
	#ip_resolver = dns.resolver.Resolver()
	#ip_resolver.nameservers = ['208.67.222.222'] # resolver1.opendns.com
	#ip_resolver.query('myip.opendns.com')

def update_cloudflare(old_ip, ip):
	pass

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
		print('IP is still {}; not updating'.format(ip))
		return
	print('IP was {}, now {}; updating!'.format(old_ip, ip))
	with open('old_ip', 'w') as old_ip_file:
		old_ip_file.write(ip)
	update_cloudflare(old_ip, ip)

if __name__ == '__main__':
	main()
