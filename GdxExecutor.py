# -*- coding:utf-8 -*-
import json
import time

import requests
import web3
from web3 import Web3, logs
from web3.middleware import construct_sign_and_send_raw_middleware
import decimal

GRID_ADDRESS = '0x8Eb76679F7eD2a2Ec0145A87fE35d67ff6e19aa6'
SWAP_ROUTER_ADDRESS = '0x426B751AbA5f49914bFbD4A1E45aEE099d757733'
MAKER_ORDER_MANAGER_ADDRESS = '0x36E56CC52d7A0Af506D1656765510cd930fF1595'
GDX_ADDRESS = '0x2F27118E3D2332aFb7d165140Cf1bB127eA6975d'
WETH_ADDRESS = '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
RESOLUSION = 5

def get_token_type(addr):

    if addr==WETH_ADDRESS:
        return 'ETH'
    elif addr==GDX_ADDRESS:
        return 'GDX'


class GDXExecutor:
    def __init__(self, private_key, http_endpoint) -> None:
        self.w3 = Web3(Web3.HTTPProvider(http_endpoint))
        acct = self.w3.eth.account.from_key(private_key)
        self._private_key = private_key
        self.public_key = acct.address
        self._params = {
            'maxFeePerGas': 20000000000,
            'maxPriorityFeePerGas': 10000000000,
        }
        self._maker_list = {}
        self._swap_list = {}

        self.w3.eth.default_account = acct.address
        self.w3.middleware_onion.add(construct_sign_and_send_raw_middleware(self._private_key))

        grid_abi = None
        with open('./abi/Grid.json') as f:
            grid_abi = json.load(f)
        self._grid_contract = self.w3.eth.contract(address=GRID_ADDRESS, abi=grid_abi)

        maker_order_manager_abi = None
        with open('./abi/MakerOrderManager.json') as f:
            maker_order_manager_abi = json.load(f)
        self._maker_order_manager_contract = self.w3.eth.contract(address=MAKER_ORDER_MANAGER_ADDRESS,
                                                                  abi=maker_order_manager_abi)

        swap_router_abi = None
        with open('./abi/SwapRouter.json') as f:
            swap_router_abi = json.load(f)
        self._swap_router_contract = self.w3.eth.contract(address=SWAP_ROUTER_ADDRESS, abi=swap_router_abi)

        GDX_abi = None
        with open('./abi/GDX.json') as f:
            GDX_abi = json.load(f)
        self._GDX_contract = self.w3.eth.contract(address=GDX_ADDRESS, abi=GDX_abi)

        WETH_abi = None
        with open('./abi/WETH.json') as f:
            WETH_abi = json.load(f)
        self._WETH_contract = self.w3.eth.contract(address=WETH_ADDRESS, abi=WETH_abi)

        # self._set_max_allowance()


    def _wrap_eth(self, amount):
        deposit_data = self._WETH_contract.functions.deposit().buildTransaction({
            'value': self.w3.to_wei(amount, 'ether'),
            # 'maxFeePerGas': 20000000000,
            # 'maxPriorityFeePerGas': 10000000000,
        })
        txn_hash = self.w3.eth.send_transaction(deposit_data)
        self.w3.eth.wait_for_transaction_receipt(txn_hash)
        return self.WETH_balance()

    def _grid_token0(self):
        token0 = self._grid_contract.functions.token0().call()
        return token0

    def _grid_token1(self):
        token0 = self._grid_contract.functions.token1().call()
        return token0
    #
    # def _set_allowance(self, token: str, address: str, amount: int):
    #     if token == GDX_ADDRESS:
    #         allowance = self._GDX_contract.functions.allowance(self.public_key, address).call()
    #         print('allowance:%s,amount:%s'%(allowance,amount))
    #
    #         if allowance <= amount:
    #             self._GDX_contract.functions.approve(address, amount).transact()
    #     if token == WETH_ADDRESS:
    #         allowance = self._WETH_contract.functions.allowance(self.public_key, address).call()
    #         print('allowance:%s,amount:%s'%(allowance,amount))
    #
    #         if allowance <= amount:
    #             self._WETH_contract.functions.approve(address, amount).transact()

    def ETH_balance(self):
        balance = self.w3.eth.get_balance(self.public_key)
        return balance

    def WETH_balance(self) -> int:
        '''查WETH余额'''
        balance = self._WETH_contract.functions.balanceOf(self.public_key).call()
        return balance

    def GDX_balance(self) -> int:
        '''查GDX余额'''
        balance = self._GDX_contract.functions.balanceOf(self.public_key).call()
        return balance

    def do_swap(self, amount_in: int, min_amount_out: int, GDX_to_WETH=True,
                expire_time=int(time.time() + 86_400) * 1000) -> int:
        '''下swap单

        Args:
            amount_in: 动用多少本金
            min_amount_out: 期望至少换多少的另一种币
            GDX_to_WETH: 已经持有GDX来换WETH(True), 反之(False), 默认是True, 即帐户已有GDX用swap方式换WETH
            expire_time: 到期时间, 默认是24小时后

        Returns:
            amount_out: 换到多少另一种币
        '''
        try:
            if GDX_to_WETH:
                trx_hash = self._swap_router_contract.functions.exactInputSingle({
                    'tokenIn': GDX_ADDRESS,
                    'tokenOut': WETH_ADDRESS,
                    'resolution': RESOLUSION,
                    'recipient': self.public_key,
                    'deadline': expire_time,
                    'amountIn': amount_in,
                    'amountOutMinimum': min_amount_out,
                    'priceLimitX96': 0
                }).transact()
             
            else:
                trx_hash = self._swap_router_contract.functions.exactInputSingle({
                    'tokenIn': WETH_ADDRESS,
                    'tokenOut': GDX_ADDRESS,
                    'resolution': RESOLUSION,
                    'recipient': self.public_key,
                    'deadline': expire_time,
                    'amountIn': amount_in,
                    'amountOutMinimum': min_amount_out,
                    'priceLimitX96': 0,
                }).transact()
            receipt = self.w3.eth.wait_for_transaction_receipt(trx_hash)
            events = self._grid_contract.events.Swap().process_receipt(receipt, errors=logs.DISCARD)
            if len(events) == 1:
                e = events[0]
                amount_GDX = e.args.amount0
                amount_WETH = e.args.amount1
                self._swap_list[trx_hash] = {
                    'amount_in': amount_in,
                    'amount_out': amount_WETH if GDX_to_WETH else amount_GDX,
                    'GDX_to_WETH': GDX_to_WETH,
                    'timestamp': int(time.time()) * 1000,
                }

        except web3.exceptions.ContractLogicError:
            amount_WETH, amount_GDX = 0, 0

        return abs(amount_WETH) if GDX_to_WETH else abs(amount_GDX)

    def do_maker(self, boundary_lower: int, amount: int, GDX_to_WETH=False,
                 expire_time=int(time.time() + 20*60) * 1000) -> int:
        '''下maker单.

        Args:
            - boundary_lower, 通过orderbook查到的价格区间
            - amount, 下单数量, 注意decimals, 即1个ETH不是输入1, 而是10000000000
            - GDX_to_WETH, 下单方向, 付出WETH挂单买GDX (False), 反之(True). 默认是帐户已有WETH下maker单换GDX
            - expire_time, 设置该maker单的expire_time, 默认是24小时后

        Returns:
            order_id, 合约生成的order id
        '''
        order_id = None

        # slots0_result = self._grid_contract.functions.slot0().call()
        # boundary = slots0_result[1]
        # boundary_lower = boundary - (((boundary % RESOLUSION) + RESOLUSION) % RESOLUSION)
        params={
            'deadline': expire_time,
            'recipient': self.public_key,
            'tokenA': GDX_ADDRESS,
            'tokenB': WETH_ADDRESS,
            'resolution': RESOLUSION,
            'zero': GDX_to_WETH,
            'boundaryLower': boundary_lower,
            'amount': amount
        }
        # print('params:%s'%(params))
        # estimate_gas = self._maker_order_manager_contract.functions.placeMakerOrder(params).estimate_gas()
        # print('myestimate_gas:%s'%(estimate_gas))
        # print('before trx_hash')
        trx_hash = self._maker_order_manager_contract.functions.placeMakerOrder(params).transact()#({'gas':1870671*10})
        # print('trx_hash:%s'%(trx_hash))
        # receipt = self.w3.eth.wait_for_transaction_receipt(trx_hash)
        # print('receipt:%s'%(receipt))
        # print('before txn_dict:%s'%(self.w3.eth.get_transaction_count(self.public_key)))
        # txn_dict = self._maker_order_manager_contract.functions.placeMakerOrder(params).build_transaction()
        #     {
        #     'nonce': self.w3.eth.get_transaction_count(self.public_key),
        #     'gas': 10000000,
        #     # 'gasPrice': self.w3.to_wei('5', 'gwei')
        #     }
        # )
        # signed_txn = self.w3.eth.account.sign_transaction(txn_dict, private_key=self._private_key)
        # trx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(trx_hash)
        # print('after txn_dict:%s'%(receipt))
        events = self._grid_contract.events.PlaceMakerOrder().process_receipt(receipt, errors=logs.DISCARD)
        # print(events)
        if len(events) == 1:
            e = events[0]
            order_id = e.args.orderId
            self._maker_list[trx_hash] = {
                'order_id': order_id,
                'amount_in': amount,
                'amount_remaining': amount,
                'GDX_to_WETH': GDX_to_WETH,
                'timestamp': int(time.time() * 1000)
            }
            self._maker_list[trx_hash] = order_id

        return order_id

    def settle_maker(self, order_id: int):
        '''对于给定的maker, 撤单或确认

        如果没有完全成交, 则撤单; 如果完全成交了, 则确认
        Args:
            - order_id: maker单的order id
        Returns:
            - amount_GDX: 该maker单返还的GDX
            - amount_WETH: 该maker单返还的WETH
        '''
        trx_hash = self._grid_contract.functions.settleMakerOrderAndCollect(self.public_key, order_id,
                                                                            False).transact()
        receipt = self.w3.eth.wait_for_transaction_receipt(trx_hash)
        events = self._grid_contract.events.Collect().process_receipt(receipt, errors=logs.DISCARD)
        if len(events) == 1:
            e = events[0]
            return abs(e.args.amount0), abs(e.args.amount1)
        return 0, 0

    def get_maker_list(self):
        ''' 获取open的maker单子

        Source: https://api-arbitrum.d5.xyz/v1/orders/open/by_owner?owner=0xC895caA68D4d0Ad2c6AC30786DD4A8C1Bbc40D8A&order_type=open&address=&from=0&limit=10&direction=next
        '''
        url = 'https://api-arbitrum.d5.xyz/v1/orders/open/by_owner?owner=' + self.public_key
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('data').get('orders')

    def get_swap_list(self):
        '''获取所有swap'''
        return self._swap_list.values()

    def _set_max_allowance(self):
        amount = 115792089237316195423570985008687907853269984665640564039457584007913129639935
        trx_hash = self._GDX_contract.functions.approve(SWAP_ROUTER_ADDRESS, amount).transact()
        self.w3.eth.wait_for_transaction_receipt(trx_hash)
        trx_hash = self._WETH_contract.functions.approve(SWAP_ROUTER_ADDRESS, amount).transact()
        self.w3.eth.wait_for_transaction_receipt(trx_hash)
        trx_hash = self._GDX_contract.functions.approve(MAKER_ORDER_MANAGER_ADDRESS, amount).transact()
        self.w3.eth.wait_for_transaction_receipt(trx_hash)
        trx_hash = self._WETH_contract.functions.approve(MAKER_ORDER_MANAGER_ADDRESS, amount).transact()
        self.w3.eth.wait_for_transaction_receipt(trx_hash)