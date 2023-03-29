# -*- coding: utf-8 -*-
import requests
import time

class D5:

    def get_his_volume_data(self,add,
                            candle_count=3,
                            candle_type=15
                            ):
        '''
            {
                s: "ok",
                t: [
                1679383800,
                1679384700
                ],
                c: [
                "0.0006617437778333914933749327",
                "0.0006617613809335494229151629"
                ],
                o: [
                "0.0006611482909166340437370220",
                "0.0006617436683946330529306027"
                ],
                h: [
                "0.0006617437778333914933749327",
                "0.0006618069155628415755526682"
                ],
                l: [
                "0.0006611482909166340437370220",
                "0.0006615716827380949982740973"
                ],
                v: [
                "415605.858136278240387213",
                "392387.359971520282910864"
                ]
            }
        '''
        to_time=int(time.time())-5
        from_time=to_time-(candle_count+1)*candle_type*60
        crawl_url='https://api-arbitrum.d5.xyz/v1/udf/history?symbol=GRID-%s&resolution=%s&from=%s&to=%s&countback=%s'%(add,candle_type,from_time,to_time,candle_count)
        try:
            with requests.get(url=crawl_url, timeout=10, stream=True) as req:
                res_data=req.json()
                if res_data.get('s')=='ok':
                    volumes=res_data.get('v')
                    return volumes
        except Exception:
            print('get_his_volume_data Error happened')

    def get_his_candal_data(self,add,
                            candle_count=3,
                            candle_type=15
                            ):
        '''
            {
                s: "ok",
                t: [
                1679383800,
                1679384700
                ],
                c: [
                "0.0006617437778333914933749327",
                "0.0006617613809335494229151629"
                ],
                o: [
                "0.0006611482909166340437370220",
                "0.0006617436683946330529306027"
                ],
                h: [
                "0.0006617437778333914933749327",
                "0.0006618069155628415755526682"
                ],
                l: [
                "0.0006611482909166340437370220",
                "0.0006615716827380949982740973"
                ],
                v: [
                "415605.858136278240387213",
                "392387.359971520282910864"
                ]
            }
        '''
        to_time=int(time.time())-5
        from_time=to_time-(candle_count+1)*candle_type*60
        crawl_url='https://api-arbitrum.d5.xyz/v1/udf/history?symbol=GRID-%s&resolution=%s&from=%s&to=%s&countback=%s'%(add,candle_type,from_time,to_time,candle_count)
        try:
            with requests.get(url=crawl_url, timeout=10, stream=True) as req:
                res_data=req.json()
                if res_data.get('s')=='ok':
                    return res_data
        except Exception:
            print('get_his_candal_data Error happened')
#https://api-arbitrum.d5.xyz/v1/udf/history?symbol=GRID-0x8Eb76679F7eD2a2Ec0145A87fE35d67ff6e19aa6&resolution=30&from=1679762483&to=1679798483&countback=2
#https://api-arbitrum.d5.xyz/v1/udf/history?symbol=GRID-0x7c063BA4799A7479a8104a41aef1e0A6bD0ff186&resolution=30&from=1679794814&to=1679800214&countback=2
    def get_ob_data(self,add):
        '''
        https://api-arbitrum.d5.xyz/v1/market/order_books/0x8Eb76679F7eD2a2Ec0145A87fE35d67ff6e19aa6
        {
            code: 200,
            message: "success",
            data: {
            current: {
            origin_boundary: -73214,
            price: "0.0006615353188800410226988051",#池子中间价
            amount_base: "6181.121512898852568175",#买单的话，这个就是eth，卖单的话，这个就是gdx
            amount_quote: "5.281668140970393696",
            lower_price: "0.0006614117783249446199372370",#池子低价
            upper_price: "0.0006617425503618993732374203",#池子高价
            price_on_border: false
            },
            highs: [],#asks报单
            lows: []，#bids报单
            }
            }
        '''
        crawl_url='https://api-arbitrum.d5.xyz/v1/market/order_books/%s'%(add)
        try:
            with requests.get(url=crawl_url, timeout=10, stream=True) as req:
                res_data=req.json()
                if res_data.get('code')==200:
                    data=res_data.get('data')
                    return data
        except Exception:
            print('Error happened')

    def get_maker_list(self,_public_key):
        ''' 获取open的maker单子

        Source: https://api-arbitrum.d5.xyz/v1/orders/open/by_owner?owner=0xC895caA68D4d0Ad2c6AC3786DD4A8C1Bbc40D8A&order_type=open&address=&from=0&limit=10&direction=next
        '''
        url = 'https://api-arbitrum.d5.xyz/v1/orders/open/by_owner?owner=' + _public_key
        try:
            with requests.get(url=url, timeout=10, stream=True) as response:
                if response.status_code == 200:
                    return response.json().get('data').get('orders')
        except Exception as ex:
            print('get_maker_list Error happened')

