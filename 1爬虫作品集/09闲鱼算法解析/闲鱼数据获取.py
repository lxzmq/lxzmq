import requests
import time
import jsonpath #需要安装  pip install jsonpath
import csv
import hashlib
import json

search = '篮球鞋'
# cookie = 't=7450d5979ca404eb5d7616c083ba83e3; cna=AkEkIpGsQz4CAXZxBQ3NqFXq; tracknick=xy587294431702; xlly_s=1; unb=2214130903783; mtop_partitioned_detect=1; _m_h5_tk=8e838f32eb08152bfeac769c2ce81ade_1785160841329; _m_h5_tk_enc=606e2ada89125575f77e99f0cce53bf2; isg=BLS04tm7YoD3yPZMw213J6GUhXImjdh3fD5Umk4VSj_CuVQDdp4MB2p6PfFhQRDP; cookie2=1774edb8b3ebc40f6787c322bcb2463d; _samesite_flag_=true; _tb_token_=7eb0eeee3b3ae; sgcookie=E100E%2BVXmKDenP9ivurxCbddqjc2zGx5ubOQyczNnltYpMCO5z1zuiuBW1SjeMb9i3vHJOsQtfSNUOF6UpxIiIuoVnBrPNM%2Bwkm13DzPiMOE%2FQI%3D; csg=ee17a538; _m_h5_tk=3f7158eb38b5965faf1a5b22d498ec7c_1785162625854; _m_h5_tk_enc=a27fe63376b321b257dfde35d0332c5a; tfstk=gTKSdps-_7V5PsM-97kqcj1n9ZjBdxoadJ6pIpEzpgI89WpOgQ5P4vmC9Qf24_JP26EBTp-yTH93A9pptYfEEqJkEMjK_fkZbLvoqviDfjSKpKIFdSveP59kEM203W3wkL0B6nIAeMddDZBOIMB8v_HbDOfY29ERpSHfKsIdpMQLkKBFCyCdpBpxh9fA9MQJ9iHfKsCdvMhPtR6IP_vSLBVdQ1ZRTLCbvkK-xa16wyrLvnB5PHpRGLJycT_56wMK-c-JgpKyqZ00uMv25BTptVzcVpLR2OJoVos9eE-C3HkUR_p2cKK5lRrweK8lD3L_pkpfV_dM2aNSG1KkHhjAucH6HnAyEn9UpDB2_spk2MitIgsRwi6DYjqROELp4aj3wf7kpEOfFGIrll56pezQhNqCh1kjhy4H3vI1jLp1egQRnT_qhxNJ-aBchskjh7LhytX5QxMbwef..'
cookie = "t=6fef2309be7192ce1b7f316a0361cc46; cna=Cj3qInp5H3gBASQOA5kOQ5at; tracknick=%E5%AD%99%E9%A2%96suny; unb=667262785; havana_lgc2_77=eyJoaWQiOjY2NzI2Mjc4NSwic2ciOiJlZmZiMjdjNmMzYTQ5YTE3Zjc5ZGE4ZTJmNTk4ZjA2MSIsInNpdGUiOjc3LCJ0b2tlbiI6IjFfZl9sSWpxUXY2UWc5RlhYUHlPMzV3In0; _hvn_lgc_=77; havana_lgc_exp=1787731626538; xlly_s=1; cookie2=1d2da4c8aaf5935edf074d3d973dd557; mtop_partitioned_detect=1; _m_h5_tk=f367c39421be01aa446b45d284ba96b0_1785247373395; _m_h5_tk_enc=32d77ddeaffb43d5d45432644df64088; _samesite_flag_=true; _tb_token_=ee3b68e304353; sgcookie=E100lGsnlSA9077kORioyJWMnzZ2DNcua4kFPfG4ZO9G9rJwwRrNE9ZzAzEvnVrL9Lrd%2BVH1GZyO14QE%2FTKfYtrVJxRNODrNBdp%2BdAsH94JIo2Q%3D; csg=12c31ed3; sdkSilent=1785324774676; _m_h5_tk=bd89c56376dfcf6d97e5132ad1560fd9_1785250554192; _m_h5_tk_enc=db9b12a4085fff72fd406b3a1643dde4; tfstk=gMwodT2RA7l7UWTVIek5gaPf6VCAPYMIMypKJv3FgquXyUp8Ye43uPEJeJEE-y4xlLFRNX3HxYwYwp3RPvqUWvbOWOBTVuGILNQtOny5SvoFp25xaFCnes7OWOBOankhrNELpiqn3Dgq4DJE4iDqVDMeTbzEujoZXUkELySmuDot8Luyam8q2quELvzU0imKu0kELyrVmDGRupugL-wVWMYhBQ0qP-moZVrc1pJHW08t7uuDLpuoqbf84qveL-VQ2zZxz1txRY37404CCLMrt5ZKxzXkUyq_hrm479vtzoZT6bwP9dhin4cLUAxFUoDorfy-s3J87oqU6j2AbOMoU4PKFkKGyo2uyuw0vHRqEYFms8DNCUuLMl2nxJ_CnPq_hrm479bP49R2_NXWdmSL3BOIamimWQNNNHUU-h4OmiA1Nboj2NedmBo-amiRWijD1UGrc0QO."
send_url="https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/"

#伪装请求头
send_h={
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "referer":"https://www.goofish.com/",
    'cookie': cookie
}
# 先将搜索关键词放到字典中
payload = {
    "pageNumber":1,
    "keyword": search,
    "fromFilter":False,
    "rowsPerPage":30,
    "sortValue":"",
    "sortField":"",
    "customDistance":"",
    "gps":"",
    "propValueStr":{},
    "customGps":"",
    "searchReqFromPage":"pcSearch",
    "extraFilterValue":"{}",
    "userPositionJson":"{}"
}
# 将字典数据转为json格式
c_data = json.dumps(payload)

# 获取sign【直接使用或让AI写】
def get_sign(cookie_str, c_data):
    # 1. 提取最后一个 _m_h5_tk token
    pairs = cookie_str.split("; ")
    token_list = []
    for item in pairs:
        if item.startswith("_m_h5_tk="):
            value = item.split("=", 1)[1]
            tk = value.split("_")[0]
            token_list.append(tk)
    if not token_list:
        raise ValueError("Cookie 内未找到 _m_h5_tk 字段！")
    d_token = token_list[-1]

    # 2. 生成13位毫秒时间戳
    t = str(int(time.time() * 1000))
    h = "34839810"

    # 3. 拼接原始串
    raw_sign_str = f"{d_token}&{t}&{h}&{c_data}"

    # 4. MD5加密得到sign
    md5 = hashlib.md5()
    md5.update(raw_sign_str.encode("utf-8"))
    sign = md5.hexdigest()

    return t, sign

t,sign = get_sign(cookie, c_data)

# 【构建查询字符串参数】注意将t 和 sign 改为动态生成的
xy_params={
    'jsv': '2.7.2',
    'appKey': '34839810',
    't': t,#动态生成
    'sign':sign , #动态生成
    'v': '1.0',
    'type': 'originaljson',
    'accountSite': 'xianyu',
    'dataType': 'json',
    'timeout': '20000',
    'api': 'mtop.taobao.idlemtopsearch.pc.search',
    'sessionOption': 'AutoLoginOnly',
    'spm_cnt': 'a21ybx.search.0.0',
    'spm_pre': 'a21ybx.search.searchInput.0'
}


#【构建表单数据】
datas={
    "data": c_data
}

#发起post请求，携带参数
res=requests.post(url=send_url,headers=send_h,params=xy_params,data=datas)
print(res.text)

# 将json数据转换为python数据
resdata=res.json()

# 通过jsonpath---》跨层级找到excontent--->$..
exContent=jsonpath.jsonpath(resdata,'$..exContent')

#定义一个空列表用于存储数据
all_data=[]
for i in exContent:
    #提取地址
    try:
        area=i["area"]
        # 提取价格
        price=i["detailParams"]['soldPrice']
        # 提取标题
        title=i["detailParams"]['title'][:15]
    
        #每循环一次就添加一次
        all_data.append([title,area,price])
    except:
        pass
    
    
"""
【保存数据】
"""
with open('闲鱼数据_篮球鞋.csv', "w", newline="", encoding="utf-8") as f:
    cf = csv.writer(f)
    # 表头
    cf.writerow(["地址","价格"])
    # 要存的数据
    cf.writerows(all_data)


#注意事项：sign里面的token必须和请求头的cookie一致
#注意事项；sign里面用的data必须和请求上面的data一样
