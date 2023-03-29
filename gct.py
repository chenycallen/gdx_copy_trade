
# -*- coding:utf-8 -*-
# ▒███████▒ ▒█████   ███▄ ▄███▓ ▄▄▄▄    ██▓▓█████  ▄████▄   ██▓     █    ██  ▄▄▄▄   
# ▒ ▒ ▒ ▄▀░▒██▒  ██▒▓██▒▀█▀ ██▒▓█████▄ ▓██▒▓█   ▀ ▒██▀ ▀█  ▓██▒     ██  ▓██▒▓█████▄ 
# ░ ▒ ▄▀▒░ ▒██░  ██▒▓██    ▓██░▒██▒ ▄██▒██▒▒███   ▒▓█    ▄ ▒██░    ▓██  ▒██░▒██▒ ▄██
#   ▄▀▒   ░▒██   ██░▒██    ▒██ ▒██░█▀  ░██░▒▓█  ▄ ▒▓▓▄ ▄██▒▒██░    ▓▓█  ░██░▒██░█▀  
# ▒███████▒░ ████▓▒░▒██▒   ░██▒░▓█  ▀█▓░██░░▒████▒▒ ▓███▀ ░░██████▒▒▒█████▓ ░▓█  ▀█▓
# ░▒▒ ▓░▒░▒░ ▒░▒░▒░ ░ ▒░   ░  ░░▒▓███▀▒░▓  ░░ ▒░ ░░ ░▒ ▒  ░░ ▒░▓  ░░▒▓▒ ▒ ▒ ░▒▓███▀▒
# ░░▒ ▒ ░ ▒  ░ ▒ ▒░ ░  ░      ░▒░▒   ░  ▒ ░ ░ ░  ░  ░  ▒   ░ ░ ▒  ░░░▒░ ░ ░ ▒░▒   ░ 
# ░ ░ ░ ░ ░░ ░ ░ ▒  ░      ░    ░    ░  ▒ ░   ░   ░          ░ ░    ░░░ ░ ░  ░    ░ 
#   ░ ░        ░ ░         ░    ░       ░     ░  ░░ ░          ░  ░   ░      ░      
# ░                                  ░            ░                               ░ 
#GDX跟單系統
import web3
from web3 import Web3, logs
from web3.middleware import construct_sign_and_send_raw_middleware

import decimal
import re
import time
import json
import traceback
import requests
import os
import sys
import configparser
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import NoSuchWindowException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import GdxExecutor as d5execu
import ty2 as ty
import near_middle as dpm


SettleMakerOrders = '0x8Eb76679F7eD2a2Ec0145A87fE35d67ff6e19aa6'
token0 = '0x2F27118E3D2332aFb7d165140Cf1bB127eA6975d'
arbscanAip = 'UH5MFQGNHT1NP9V8SF32HS9S3YS5QEAXKX'

myAddress = '0x03d4058Fb4a3bF45b6fD9360363850b2b2c870FD'


# 設定黨讀取
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(base_path, 'setting.ini')
config = configparser.ConfigParser()
with open('setting.ini', 'r', encoding='utf-8') as f:
	config.read_file(f)

path = config.get('setting', 'path')
password = config.get('setting', 'password')
address = config.get('setting', 'address')
followaddress = config.get('setting', 'followaddress')
cd = config.get('setting', 'cd')

path = config.get('sing', 'autoClaim')


global ethUsdPrice
global gdxUsdPrice

private_key = 'e6da14abb734a8e24681534fd1c2b50a1bc58fb6b1285beb0174f023bcb9dc0a'
http_endpoint = 'https://arb-mainnet.g.alchemy.com/v2/YAqC34Nx1yEoTG_6GaWjwkwKPsvLVZTy'


def bel():
	g = d5execu.GDXExecutor(private_key,http_endpoint)
	wethBalance = g.WETH_balance()


	o = ty.T2MakeOTHER(wethBalance,private_key,http_endpoint)
	# a = dpm.DingPkMake(private_key,http_endpoint)
	
	o.run()
	return


bel()
# bel()




def aDay(timestamp): #如果是今天就回傳TRUE
	now = datetime.now()
	start_of_day = datetime.combine(now.date(), time.min)
	end_of_day = datetime.combine(now.date(), time.max)

	start_timestamp = int(start_of_day.timestamp())
	end_timestamp = int(end_of_day.timestamp())

	if start_timestamp <= timestamp <= end_timestamp:
		return True
	else:
		return False

def getAddressCloseOrders(addr, aday=True):
	orders = f'https://api-arbitrum.d5.xyz/v1/orders/close/by_owner?owner={addr}&order_type=close&address=&from=&limit=&direction=next'
	orders = requests.get(orders).json()
	orders = orders['data']['orders']
	buyOrders = 0
	sellOrders = 0
	buyOrderAmount = 0
	sellOrderAmount = 0
	total_oreders = 0
	
	for order in orders:
		status = order['status']
		orderTime = order['settlement_timestamp']
		orderTime = datetime.fromisoformat(orderTime.replace('Z', '+00:00'))
		orderTime = int(orderTime.timestamp())
		orderSide = order['zero']
		if status != "ORDER_STATUS_FILLED":
			total_oreders += 1
			if aDay:
				if orderSide == False: #掛賣GDX=True 掛買GDX=False
					buyOrders += 1
					buyOrderAmount += float(order['maker_amount_in'])
				else:
					sellOrders += 1
					sellOrderAmount += float(order['maker_amount_in'])
	
	totalValue = round((ethUsdPrice*buyOrderAmount)+(gdxUsdPrice*sellOrderAmount),2)

	info = (f'[本日完成訂單]\n'
			f'成交買：{buyOrders} ({round(buyOrderAmount, 4)} E) {round(ethUsdPrice*buyOrderAmount, 2)}U\n'
			f'成交賣：{sellOrders} ({round(sellOrderAmount, 2)} GDX) {round(gdxUsdPrice*sellOrderAmount, 2)}U\n'
			f'總成交價值：{round((ethUsdPrice*buyOrderAmount)+(gdxUsdPrice*sellOrderAmount),2)}U\n'
			f'總成交訂單: {total_oreders}\n'
		)
	return info , totalValue		
		
def convertBoundaryPrice(boundary):
	orderBooks = f'https://api-arbitrum.d5.xyz/v1/market/order_books/0x8Eb76679F7eD2a2Ec0145A87fE35d67ff6e19aa6'
	orderBooks =  requests.get(orderBooks).json()['data']

	orderBooksLows = orderBooks['lows']
	orderBooksHighs = orderBooks['highs']

	price = 0
	lower_price = 0
	upper_price = 0
	
	for orderbook in orderBooksLows:
		origin_boundary = orderbook['origin_boundary']
		if origin_boundary == boundary:
			price = float(orderbook['price'])

	for orderbook in orderBooksHighs:
		origin_boundary = orderbook['origin_boundary']
		if origin_boundary == boundary:
			price = float(orderbook['price'])
	print(price)

	return price



def getAddressOrder(addr):
	getPrice()
	order = f'https://api-arbitrum.d5.xyz/v1/orders/open/by_owner?owner={addr}&order_type=open&address=&from=0&limit=&direction=next'
	respon = requests.get(order).json()
	orders = respon['data']['orders']
	total_oreders = respon['data']['total']

	needClaim = 0 
	maker_amount_swapped = 0
	taker_amount_out = 0
	taker_fee_amount_out = 0

	buyOrders = 0
	sellOrders = 0
	buyOrderAmount = 0
	sellOrderAmount = 0

	allTxhash = []
	gridTxhash = []

	for order in orders:
		orderSide = order['zero']

		if orderSide == False: #掛賣GDX=True 掛買GDX=False
			buyOrders += 1
			buyOrderAmount += float(order['maker_amount_in'])
		else:
			sellOrders += 1
			sellOrderAmount += float(order['maker_amount_in'])

			# print(order['address'])
		if order['status'] == 'ORDER_STATUS_FILLED':
			needClaim += 1


		allTxhash.append(order['tx_hash'])
		# lower = convertBoundaryPrice(order['boundary_lower'])
		# upper = convertBoundaryPrice(order['boundary_upper'])
		# print(lower,upper)

	for item in allTxhash: #判斷哪些是網格
	    if item in gridTxhash:
	        continue
	    print("Processing item:", item, allTxhash.count(item))
	    gridTxhash.append(item)




	# print(gridTxhash)
	


	totalValue = round((ethUsdPrice*buyOrderAmount)+(gdxUsdPrice*sellOrderAmount),2)
	# print(f'網格數量:{len(tx_hash)}')
	info = (	
			f'[即時訂單]\n'
			f'訂單Claim: {needClaim} ({round(maker_amount_swapped, 2)} GDX) \n'
			# f'Taker金額: {round(taker_amount_out, 2)} GDX\n'
			# f'Taker手續費: {round(taker_fee_amount_out, 2)} GDX\n'
			f'買：{buyOrders} ({round(buyOrderAmount, 4)} E) {round(ethUsdPrice*buyOrderAmount, 2)}U\n'
			f'賣：{sellOrders} ({round(sellOrderAmount, 2)} GDX) {round(gdxUsdPrice*sellOrderAmount, 2)}U\n'
			f'總價值：{round((ethUsdPrice*buyOrderAmount)+(gdxUsdPrice*sellOrderAmount),2)}U\n'
			f'總訂單: {total_oreders}\n'
		)

	print(info)
	return info , totalValue



def getPrice(): #取得GDX ETH價格
	global ethUsdPrice
	global gdxUsdPrice
	gdxUsdPrice = f'https://api-arbitrum.d5.xyz/v1/grids/overview/0x8Eb76679F7eD2a2Ec0145A87fE35d67ff6e19aa6'
	gdxUsdPrice = round(float(requests.get(gdxUsdPrice).json()['data']['price_usd']),4)
	ethUsdPrice = f'https://api-arbitrum.d5.xyz/v1/global/eth_price_usd'
	ethUsdPrice = round(float(requests.get(ethUsdPrice).json()['data']['price']),2)

	return gdxUsdPrice, ethUsdPrice


def getLeaderboard(): #取得排行榜
	getPrice()
	leaderboard = f'https://api-arbitrum.d5.xyz/v1/farm/leaderboard?address={myAddress}&grid_address=0x8Eb76679F7eD2a2Ec0145A87fE35d67ff6e19aa6'
	# https://api-arbitrum.d5.xyz/v1/farm/leaderboard/0x94837539246F023138c3089ac378b0Dc2ce7F5c1
	respon = requests.get(leaderboard).json()
	respon = respon['data']['leaderboards']

	for i in respon:

		rank = i['rank']
		address = i['address']
		latest_reward = round(float(i['latest_reward']),2)
		total_reward = round(float(i['total_reward']),2)

		info, totalValue = getAddressOrder(address)
		cinfo, ctotalValue = getAddressCloseOrders(address)

		print(	f"排名：{rank}\n"
		f"地址：{address}\n"
		f"近期獎勵：{latest_reward}\n"
		f"全部獎勵：{total_reward}\n"
		f"{info}\n"
		f"{cinfo}"
		)
		
# getLeaderboard()

# def getRank(addr): #取得分數
# 	leaderboard = f'https://api-arbitrum.d5.xyz/v1/farm/leaderboard?address={addr}&grid_address=0x8Eb76679F7eD2a2Ec0145A87fE35d67ff6e19aa6'
# 	myRank = requests.get(leaderboard).json()
# 	myRank = myRank['data']['my_rank']

# 	lastReward = round(float(myRank['latest_reward']), 2)
# 	totalReward = round(float(myRank['total_reward']), 2)

# 	return lastReward, totalReward



# getAddressOrder('0xdf49A30aD409B7a6D59A008a28689C3b4D0686Cc') #IVEN
# getAddressOrder('0xC9a7C891f2C3dECf022B3B96987E50C8E76fd2BD') #ROERT
# getAddressOrder('0x03d4058Fb4a3bF45b6fD9360363850b2b2c870FD') #ERIC
# getAddressOrder('0x6151ce5aE494292c221938c4647755EaB6b81b34') #ALLEN
# getAddressOrder('0xAA78927Ce4762b5CbA686537d5e60eA0B82DF4EF') #NO1

# getLeaderboard()

# getRank('0x6151ce5aE494292c221938c4647755EaB6b81b34')
# print(getEthPrice())