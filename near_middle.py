# -*- coding:utf-8 -*-
import time
import traceback
import threading
import logging
import web3
from web3 import Web3, logs
import web as d5_web
import GdxExecutor as d5execu
import tool

SLEEP_SEC=5

class DingPkMake(threading.Thread):
    '''一个盯住盘口的挂单撤单策略。逻辑很简单，挂单只追求最中间价位，不是就撤'''
    def __init__(self,
                 private_key,
                 http_endpoint,
                 side='buy',
                 eth_min_amount=0.001,
                 gdx_min_unit=100,
                 min_houdu=50):

        threading.Thread.__init__(self)
        self.side=side
        self.eth_min_amount=eth_min_amount
        self.gdx_min_unit=gdx_min_unit
        self.order_book=None
        self.price_key_dict={}
        self.average_traded_volume=0
        self.min_houdu=min_houdu#eth/gdx
        self.g = d5execu.GDXExecutor(private_key,http_endpoint)

        self.last_maker_time=0
    def run(self) -> None:

        threading.Thread(target=self.update_ob_tsk).start()#no g
        threading.Thread(target=self.update_traded_volume_tsk).start()#no g
        #
        time.sleep(10)
        threading.Thread(target=self.do_opera_tsk).start()

        # threading.Thread(target=self.do_maker_make_tst).start()
    #
    # def do_maker_make_tst(self):
    #
    #     while True:
    #         try:
    #             current_boundary=-73955
    #             make_eth=0.012
    #             logging.info('ToMake Order,current_boundary:%s,amount:%s'%(current_boundary,Web3.to_wei(make_eth, 'ether')))
    #             order_id = self.g.do_maker(int(current_boundary), Web3.to_wei(make_eth, 'ether'), False)
    #             logging.info('Make Order,id:%s'%(order_id))
    #             a, b = self.g.settle_maker(order_id)
    #             logging.info('Settle Order,id:%s'%(order_id))
    #
    #             self.last_maker_time=time.time()
    #         except:
    #             traceback.print_exc()
    #             logging.info('Make maker error.')
    #
    #
    #
    #         time.sleep(10)

    def do_opera_tsk(self):

        while True:
            self.do_maker_cancel()
            if self.side=='buy':
                self.do_maker_make_buy()
                self.do_swap_sell()

            elif self.side=='sell':
                self.do_maker_make_sell()
                self.do_swap_buy()
            time.sleep(SLEEP_SEC)

    def do_maker_make_buy(self):

        try:
            d5c=d5_web.D5()
            order_list=d5c.get_maker_list(self.g.public_key)

            logging.info('do_maker_make,=== Present order_list:%s'%(len(order_list)))
            amount_wei_WETH = self.g.WETH_balance()
            eth_balance = self.g.w3.from_wei(amount_wei_WETH, 'ether')
            logging.info('eth_min_amount:%s,eth_balance:%s'%(self.eth_min_amount,eth_balance))

            if eth_balance>self.eth_min_amount:
                make_eth=float(eth_balance)*0.999
                print(make_eth)
                current_boundary = self.__get_current_boundary()
                current_houdu_list = self.__get_current_boundary_houdu()
                print('current_houdu_list:%s'%(current_houdu_list))

                if current_boundary!=None and current_boundary!=None and float(current_houdu_list[0])>self.min_houdu:
                    try:
                        logging.info('ToMake Order,current_boundary:%s,amount:%s'%(current_boundary,Web3.to_wei(make_eth, 'ether')))
                        order_id = self.g.do_maker(int(current_boundary), Web3.to_wei(make_eth, 'ether'), False)
                        logging.info('Make Buy Order,id:%s'%(order_id))
                        time.sleep(SLEEP_SEC)
                    except:
                        traceback.print_exc()
                        logging.info('Make maker error.')
        except:
            logging.info(traceback.format_exc())


    def do_maker_make_sell(self):

        try:
            d5c=d5_web.D5()
            order_list=d5c.get_maker_list(self.g.public_key)
            logging.info('do_maker_make,=== Present order_list:%s'%(len(order_list)))

            gdx_wei_balance=self.g.GDX_balance()
            gdx_balance=int(self.g.w3.from_wei(gdx_wei_balance,'ether'))

            logging.info('gdx_balance:%s'%(gdx_balance))
            if gdx_balance>self.gdx_min_unit:

                make_gdx=int(float(gdx_balance)*0.999)
                current_boundary = self.__get_current_boundary()
                current_houdu_list=self.__get_current_boundary_houdu()
                print('current_houdu_list:%s'%(current_houdu_list))

                if current_boundary!=None and float(current_houdu_list[1])>self.min_houdu:
                    try:
                        logging.info('ToMake Order,current_boundary:%s,amount:%s'%(current_boundary,make_gdx))
                        order_id = self.g.do_maker(int(current_boundary), Web3.to_wei(make_gdx, 'ether'), True)
                        logging.info('Make Sell Order,id:%s'%(order_id))
                        time.sleep(SLEEP_SEC)
                    except:
                        traceback.print_exc()
                        logging.info('Make maker error.')
        except:
            logging.info(traceback.format_exc())


    def do_maker_cancel(self):

        try:
            d5c=d5_web.D5()
            order_list=d5c.get_maker_list(self.g.public_key)
            # print('order_list:%s'%(order_list))
            ul_tlist=self.__get_middle_pool_ulprice()
            logging.info('present ul_tlist:%s'%(ul_tlist))

            if ul_tlist!=None and order_list!=None:
                for order_item in reversed(order_list):
                    ismid_order=self.__if_the_mid_order(order_item)
                    status=order_item.get('status')
                    if status=='ORDER_STATUS_FILLED' or ismid_order==False:
                        try:
                            order_id = int(order_item.get('order_id'))
                            logging.info('do_maker_cancel_tsk,Settle Order id:%s' % (order_id))
                            a, b = self.g.settle_maker(order_id)
                        except:
                            logging.info('Settle error.')
        except:
            pass


    def do_swap_sell(self):

        try:
            logging.info('do_swap_sell,=== ')

            gdx_wei_balance=self.g.GDX_balance()
            gdx_balance=int(self.g.w3.from_wei(gdx_wei_balance,'ether'))
            if gdx_balance>self.gdx_min_unit:
                do_gdx_swap=gdx_balance*0.99
                amount_ETH = self.g.do_swap(Web3.to_wei(do_gdx_swap, 'ether'), 0, True)
                time.sleep(SLEEP_SEC)
        except:
            traceback.print_exc()

    def do_swap_buy(self):

        try:
            logging.info('do_swap_buy,=== ')

            amount_wei_WETH = self.g.WETH_balance()
            eth_balance = self.g.w3.from_wei(amount_wei_WETH, 'ether')

            if eth_balance>self.eth_min_amount:
                do_eth_swap=eth_balance*0.99
                amount_ETH = self.g.do_swap(Web3.to_wei(do_eth_swap, 'ether'), 0, False)
                time.sleep(SLEEP_SEC)
        except:
            traceback.print_exc()


    def update_traded_volume_tsk(self):

        while True:

            d5c=d5_web.D5()
            volumes=d5c.get_his_volume_data(d5execu.GRID_ADDRESS,candle_count=3,candle_type=60)
            if volumes!=None:
                total=0
                for item in volumes:
                    item_value=float(item)
                    total=total+item_value

                avg_value=total/len(volumes)
                self.average_traded_volume=avg_value

            print(self.average_traded_volume)
            time.sleep(60)


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

    def __get_middle_pool_ulprice(self):
        if self.order_book!=None:
            lows=self.order_book.get('lows')
            highs=self.order_book.get('highs')
            low=lows[0]['upper_price']
            high=highs[0]['lower_price']
            return [low,high]

    def __get_newest_order_by_ul(self,cboundary,order_list):

        timemark=0
        for order in reversed(order_list):
            boundary_upper=order.get('boundary_upper')
            boundary_lower=order.get('boundary_lower')
            block_timestamp=order.get('block_timestamp')
            if cboundary>=boundary_lower and cboundary<=boundary_upper:
                timemark=tool.TimeProcessTool.convert_to_local_timestamp(block_timestamp)

        return timemark

    # def __get_each_eth_amount(self):
    #
    #     each_eth=self.total_eth/float(self.eth_split_count)
    #     return max(each_eth,self.eth_min_amount)

    def __get_current_boundary(self):
        if self.order_book!=None:
            highs=self.order_book.get('highs')
            lows=self.order_book.get('lows')
            # print(highs,lows)
            return int(highs[0].get('origin_boundary')+lows[0].get('origin_boundary'))/2


    def __get_current_boundary_houdu(self):
        if self.order_book!=None:
            current=self.order_book.get('current')
            # print(current)
            return [current.get('amount_quote'),current.get('amount_base')]

    def __if_the_mid_order(self,order):
        if self.order_book!=None:
            boundary_upper = order.get('boundary_upper')
            highs=self.order_book.get('highs')

            if boundary_upper==highs[0].get('origin_boundary'):
                return True
            else:
                return False


    def __if_can_make_by_volume(self,minutes=10,level=3):
        r=False
        if self.order_book!=None:
            current=self.order_book.get('current')
            price=float(current.get('price'))

            lows=self.order_book.get('lows')
            highs=self.order_book.get('highs')
            total_volume,total_count=0,0
            for i in range(level):
                total_volume=total_volume+float(highs[i].get('amount_base'))
                total_count=total_count+1

                total_volume=total_volume+float(lows[i].get('amount_quote'))/price
                total_count=total_count+1

            middle_total=float(current.get('amount_base'))+float(current.get('amount_quote'))/price
            total_volume=total_volume+middle_total
            total_count=total_count+2

            compare_value=minutes*self.average_traded_volume/60
            my_value=total_volume/total_count
            # print('compare_value:%s,my_value:%s'%(compare_value,my_value))
            r= True if my_value>compare_value and middle_total>=my_value else False
        return r





