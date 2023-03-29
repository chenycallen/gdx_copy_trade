# -*- coding:utf-8 -*-
import time
import traceback
import threading
import logging
import web3
from web3 import Web3, logs
import web as d5_web
import GdxExecutor as d5execu
import tool as tool_data
GDX_MIN_UNIT=900

SLEEP_SEC=23
MAKE_ORDER_INTERVAL=1*60

UNIT_K=30
COUNT_K=4
class T2MakeOTHER(threading.Thread):

    def __init__(self,total_eth,
                 private_key,http_endpoint,
                 hold_top_ob_count=2,#除current外，盯住几档
                 eth_split_count=1,
                 eth_min_amount=0.001,
                 gdx_min_unit=10,
                 bodong=0.008,
                 whats_like_nofloat=0.003):

        threading.Thread.__init__(self)
        
        self.hold_top_ob_count=hold_top_ob_count
        self.eth_split_count=eth_split_count
        self.eth_min_amount=eth_min_amount
        self.gdx_min_unit=gdx_min_unit
        self.order_book=None
        self.price_key_dict={}
        self.last_unit_float=None
        self.last_smallunit_float=None
        self.whats_like_nofloat=whats_like_nofloat

        self.total_eth=total_eth
        self.bodong=bodong
        self.g = d5execu.GDXExecutor(private_key,http_endpoint)

        self.last_maker_time=0
    def run(self) -> None:

        threading.Thread(target=self.update_ob_tsk).start()#no g
        threading.Thread(target=self.update_traded_float_tsk).start()#no g
        #
        time.sleep(10)

        wethBalance = self.g.WETH_balance()
        ethBalance = self.g.ETH_balance()
        gdxBalance = self.g.GDX_balance()
        print(  f'WETH:{wethBalance/10**18}\n'
                f'ETH:{ethBalance/10**18}\n'
                f'GDX:{gdxBalance/10**18}\n')
        threading.Thread(target=self.do_opera_tsk).start()

    def do_opera_tsk(self):

        while True:
            self.do_maker_make()
            self.do_swap()
            self.do_maker_cancel1()
            time.sleep(SLEEP_SEC)

    def do_maker_make(self):

        try:
            # print('do_maker_make,=== past float:%s,small_float:%s,setting_nofloat:%s'%(self.last_unit_float,self.last_smallunit_float,self.whats_like_nofloat))
            if None not in [self.last_unit_float,self.last_smallunit_float] and self.last_unit_float>self.whats_like_nofloat\
                    and self.last_smallunit_float<self.whats_like_nofloat/2.5:
                return


            d5c=d5_web.D5()
            order_list=d5c.get_maker_list(self.g.public_key)
            # print('do_maker_make,=== Present order_list:%s'%(order_list))
            amount_wei_WETH = self.g.WETH_balance()

            eth_balance = self.g.w3.from_wei(amount_wei_WETH, 'ether')
            ceach_eth=self.__get_each_eth_amount()
            # print(eth_balance)

            if eth_balance>self.eth_min_amount*0.8:
                make_eth=min(float(eth_balance)*0.95,ceach_eth) #*0.95
                # print(make_eth)
                split_scope=self.__get_split_buy_scops()
                # print(split_scope)
                print('eth_min_amount:%s,eth_balance:%s' % (self.eth_min_amount, eth_balance))
                if len(split_scope)>0 and time.time()-self.last_maker_time>MAKE_ORDER_INTERVAL:
                    for sigle_scope in split_scope:
                        ifaready=self.__if_already_in_scope(order_list, sigle_scope)
                        print('ifaready:%s' % (ifaready))
                        # print(ifaready)
                        # print(sigle_scope[0])
                        # print(Web3.to_wei(make_eth, 'ether')/10**18)
                        if ifaready==False:
                            try:
                                print('Make boundaryid:%s'%(sigle_scope[0]))
                                order_id = self.g.do_maker(int(sigle_scope[0]), Web3.to_wei(make_eth, 'ether'), False)
                                print('Make Order,id:%s'%(order_id))

                                time.sleep(SLEEP_SEC)
                                self.last_maker_time=time.time()
                            except:
                                traceback.print_exc()
                                print('Make maker error.')
                            break

        except:
            print(traceback.format_exc())


    def do_maker_cancel1(self):

        try:
            d5c=d5_web.D5()
            order_list=d5c.get_maker_list(self.g.public_key)
            if order_list!=None:
                for order_item in reversed(order_list):
                    status=order_item.get('status')
                    if status=='ORDER_STATUS_FILLED': # and boundary_upper not in top_ids):
                        try:
                            order_id = int(order_item.get('order_id'))
                            print('Claim Order id:%s' % (order_id))
                            a, b = self.g.settle_maker(order_id)
                            # time.sleep(SLEEP_SEC)
                        except:
                            print('Settle error.')
        except:
            pass


    def do_swap(self):

        try:
            # print('do_swap,=== ')

            gdx_wei_balance=self.g.GDX_balance()
            # print(f'{gdx_wei_balance/10**18} swap to ETH')
            gdx_balance=int(self.g.w3.from_wei(gdx_wei_balance,'ether'))
            if gdx_balance>self.gdx_min_unit:
                do_gdx_swap=min(gdx_balance,self.gdx_min_unit)
                amount_ETH = self.g.do_swap(Web3.to_wei(do_gdx_swap, 'ether'), 0, True)

                time.sleep(SLEEP_SEC)
        except:
            traceback.print_exc()


    def update_traded_float_tsk(self):

        while True:

            last_unit_float=self.__get_float(COUNT_K,UNIT_K)
            if last_unit_float!=None:
                print('last_unit_float:%s'%(last_unit_float))
                self.last_unit_float=last_unit_float

            last_smallunit_float=self.__get_float(3,5)
            if last_smallunit_float!=None:
                print('last_smallunit_float:%s'%(last_smallunit_float))
                self.last_smallunit_float=last_smallunit_float

            time.sleep(30)


    def __get_float(self,candle_count,candle_type):

        d5c = d5_web.D5()
        candle_data = d5c.get_his_candal_data(d5execu.GRID_ADDRESS, candle_count=candle_count, candle_type=candle_type)
        if candle_data != None:
            total_l, total_h = 0, 0
            for item in candle_data.get('l'):
                item_value = float(item)
                total_l = total_l + item_value
            for item in candle_data.get('h'):
                item_value = float(item)
                total_h = total_h + item_value

            flot = (total_h - total_l) / total_h
            return flot

    def update_ob_tsk(self):

        while True:
            d5c=d5_web.D5()
            data=d5c.get_ob_data(d5execu.GRID_ADDRESS)
            if data != None:
                current = data.get('current')
                highs = data.get('highs')
                lows = data.get('lows')
                if len(highs)>0 and len(lows)>0:
                    self.__update_self_pdict(highs+lows)

                self.order_book={
                    'current':current,
                    'highs':highs,
                    'lows':lows,
                }
            # print(self.price_key_dict)
            time.sleep(5)


    def __update_self_pdict(self,item_list):

        for item in item_list:
            origin_boundary=item.get('origin_boundary')
            if origin_boundary!=None and origin_boundary not in self.price_key_dict:
                new_p={
                    'price':item['price'],
                    'lower_price':item['lower_price'],
                    'upper_price':item['upper_price']
                }
                self.price_key_dict[origin_boundary]=new_p



    def __get_top_ob_ids(self,count,side='bid'):

        top_ids=[]
        if self.order_book!=None:
            lows=self.order_book.get('lows') if side=='bid' else self.order_book.get('highs')
            for i in range(count):
                item=lows[i]
                top_ids.append(item.get('origin_boundary'))

        return top_ids

    def __get_middle_pool_ul(self):
        if self.order_book!=None:
            lows=self.order_book.get('lows')
            highs=self.order_book.get('highs')
            low=lows[0]['origin_boundary']
            high=highs[0]['origin_boundary']
            return (low,high)

    def __get_newest_order_by_ul(self,cboundary,order_list):

        timemark=0
        for order in reversed(order_list):
            boundary_upper=order.get('boundary_upper')
            boundary_lower=order.get('boundary_lower')
            block_timestamp=order.get('block_timestamp')
            if cboundary>=boundary_lower and cboundary<=boundary_upper:
                timemark=tool_data.TimeProcessTool.convert_to_local_timestamp(block_timestamp)

        return timemark

    def __get_each_eth_amount(self):

        each_eth=self.total_eth/float(self.eth_split_count)
        return max(each_eth,self.eth_min_amount)


    def __get_current_boundary(self):
        if self.order_book!=None:
            highs=self.order_book.get('highs')
            lows=self.order_book.get('lows')
            return int(highs[0].get('origin_boundary')+lows[0].get('origin_boundary'))/2



    def __get_split_buy_scops(self):
        scops = []
        if self.order_book != None:
            current=self.order_book.get('current')
            current_boundary=current.get('origin_boundary')
            cupper_price=float(current.get('upper_price'))
            lows=self.order_book.get('lows')
            price_scope=[cupper_price]
            step=float(self.bodong)/self.eth_split_count
            first_price=cupper_price
            for i in range(self.eth_split_count):
                first_price=first_price*(1-step)
                price_scope.append(first_price)

            # print('price_scope:%s'%(price_scope))
            for i in range(1,len(price_scope)):
                high_price=price_scope[i-1]
                low_price=price_scope[i]
                iscope_sub=[]
                for low_item in lows:
                    price=float(low_item.get('price'))
                    if price <=high_price and price>low_price:
                        iscope_sub.append(low_item.get('origin_boundary'))

                scops.append(iscope_sub)

            if len(scops)>0:
                scops[0]=[lows[0].get('origin_boundary')+5]+scops[0]
        return scops

    def __if_already_in_scope(self,order_list,scope):

        for order in order_list:
            # boundary_upper=order.get('boundary_upper')
            boundary_lower=order.get('boundary_lower')
            if boundary_lower>=min(scope) and boundary_lower<=max(scope):
                return True
        return False