#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili WBI 签名工具
用于生成B站API请求所需的WBI签名

基于官方文档: https://socialsisteryi.github.io/bilibili-API-collect/docs/misc/sign/wbi.html
更新时间: 2025-11
"""

from functools import reduce
from hashlib import md5
import urllib.parse
import time
import requests
from typing import Dict, Tuple, Optional


class WBISigner:
    """WBI签名生成器"""

    # 重排映射表
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52
    ]

    def __init__(self, cookies: Optional[Dict] = None):
        self.img_key: Optional[str] = None
        self.sub_key: Optional[str] = None
        self.key_timestamp: float = 0
        self.key_expire_time = 3600  # 密钥缓存1小时
        self.cookies = cookies or {}

    def _get_mixin_key(self, orig: str) -> str:
        """
        生成混合密钥

        Args:
            orig: 原始密钥字符串

        Returns:
            混合后的密钥（取前32位）
        """
        return reduce(lambda s, i: s + orig[i], self.MIXIN_KEY_ENC_TAB, '')[:32]

    def get_wbi_keys(self, force_refresh: bool = False) -> Tuple[str, str]:
        """
        从nav接口获取img_key和sub_key

        Args:
            force_refresh: 是否强制刷新密钥

        Returns:
            (img_key, sub_key) 元组
        """
        # 检查缓存是否有效
        if not force_refresh and self.img_key and self.sub_key:
            if time.time() - self.key_timestamp < self.key_expire_time:
                return self.img_key, self.sub_key

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/'
        }

        try:
            resp = requests.get('https://api.bilibili.com/x/web-interface/nav',
                              headers=headers, cookies=self.cookies, timeout=10)
            json_content = resp.json()

            data = json_content.get('data', {})

            # 注意：即使未登录（code=-101），wbi_img密钥依然会返回
            # WBI密钥是公开的，不需要登录
            wbi_img = data.get('wbi_img', {})

            img_url = wbi_img.get('img_url', '')
            sub_url = wbi_img.get('sub_url', '')

            if not img_url or not sub_url:
                raise Exception("WBI密钥URL为空")

            # 提取密钥
            self.img_key = img_url.rsplit('/', 1)[1].split('.')[0]
            self.sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
            self.key_timestamp = time.time()

            return self.img_key, self.sub_key

        except Exception as e:
            print(f"[ERROR] 获取WBI密钥失败: {str(e)}")
            # 返回空密钥，让调用者决定如何处理
            return "", ""

    def sign_params(self, params: Dict, img_key: Optional[str] = None, sub_key: Optional[str] = None) -> Dict:
        """
        为请求参数进行WBI签名

        Args:
            params: 原始请求参数
            img_key: 可选，直接提供img_key（否则自动获取）
            sub_key: 可选，直接提供sub_key（否则自动获取）

        Returns:
            包含w_rid和wts的签名后参数
        """
        # 获取密钥
        if img_key and sub_key:
            _img_key, _sub_key = img_key, sub_key
        else:
            _img_key, _sub_key = self.get_wbi_keys()

        if not _img_key or not _sub_key:
            print("[WARN] WBI密钥为空，返回未签名参数")
            return params

        # 生成混合密钥
        mixin_key = self._get_mixin_key(_img_key + _sub_key)

        # 添加时间戳
        curr_time = round(time.time())
        params['wts'] = curr_time

        # 排序参数
        params = dict(sorted(params.items()))

        # 过滤特殊字符 !'()*
        params = {
            k: ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
            for k, v in params.items()
        }

        # URL编码
        query = urllib.parse.urlencode(params)

        # 计算签名
        wbi_sign = md5((query + mixin_key).encode()).hexdigest()
        params['w_rid'] = wbi_sign

        return params


# 全局单例
_wbi_signer_instance: Optional[WBISigner] = None


def get_wbi_signer() -> WBISigner:
    """获取WBI签名器单例"""
    global _wbi_signer_instance
    if _wbi_signer_instance is None:
        _wbi_signer_instance = WBISigner()
    return _wbi_signer_instance


def sign_wbi_params(params: Dict) -> Dict:
    """
    便捷函数：为参数添加WBI签名

    Args:
        params: 原始参数

    Returns:
        签名后的参数
    """
    signer = get_wbi_signer()
    return signer.sign_params(params)


# 测试代码
if __name__ == '__main__':
    print("测试WBI签名...")

    # 测试获取密钥
    signer = WBISigner()
    img_key, sub_key = signer.get_wbi_keys()
    print(f"[OK] 获取密钥成功:")
    print(f"    img_key: {img_key}")
    print(f"    sub_key: {sub_key}")

    # 测试签名
    test_params = {
        'foo': '114',
        'bar': '514',
        'baz': 1919810
    }
    signed = signer.sign_params(test_params.copy())
    print(f"\n[OK] 签名测试:")
    print(f"    原始参数: {test_params}")
    print(f"    签名参数: {signed}")
    print(f"    w_rid: {signed.get('w_rid')}")
    print(f"    wts: {signed.get('wts')}")

    # 测试URL
    query = urllib.parse.urlencode(signed)
    print(f"\n[OK] 完整URL参数:")
    print(f"    {query}")
