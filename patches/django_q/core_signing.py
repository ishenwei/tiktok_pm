import datetime
import time
import zlib

from django.core.signing import BadSignature, JSONSerializer, SignatureExpired
from django.core.signing import Signer as Sgnr
from django.core.signing import TimestampSigner as TsS
from django.core.signing import b64_decode, dumps
#from django.utils import baseconv
from django.utils.http import base36_to_int, int_to_base36
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_bytes, force_str

# 导入 Django 5.x 兼容的 base36 工具
from django.utils.http import base36_to_int, int_to_base36


# --- Base62 兼容性补丁开始 ---
# 必须手动提供 Base62 解码逻辑，以满足 django-q 的历史代码调用
class Base62:
    """提供 Base62 解码方法"""
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    base = len(alphabet)

    def decode(self, value):
        """将 Base62 字符串解码为整数"""
        base = self.base
        string = self.alphabet
        l = len(value)
        ret = 0
        for i, c in enumerate(value):
            power = l - (i + 1)
            # 确保字符在 Base62 字母表中
            try:
                ret += string.index(c) * (base ** power)
            except ValueError:
                # 如果遇到无效字符，抛出异常或返回 0 (取决于原始逻辑，这里我们返回 0)
                return 0
        return ret


# 创建一个代理类，使得代码可以调用 baseconv.base62
class BaseConvProxy:
    def __init__(self):
        self.base62 = Base62()


# 实例化这个代理对象，作为代码中缺失的 'baseconv'
baseconv = BaseConvProxy()


# --- Base62 兼容性补丁结束 ---


# -----------------------------------------------------------
# 确保文件中的 b36_to_int 和 int_to_b36 函数使用新的导入
# -----------------------------------------------------------

def b36_to_int(s):
    # 使用新的导入：base36_to_int
    return base36_to_int(s)


def int_to_b36(i):
    # 使用新的导入：int_to_base36
    return int_to_base36(i).upper()

dumps = dumps

"""
The loads function is the same as the `django.core.signing.loads` function
The difference is that `this` loads function calls `TimestampSigner` and `Signer`
"""


def loads(
    s,
    key=None,
    salt: str = "django.core.signing",
    serializer=JSONSerializer,
    max_age=None,
):
    """
    Reverse of dumps(), raise BadSignature if signature fails.

    The serializer is expected to accept a bytestring.
    """
    # TimestampSigner.unsign() returns str but base64 and zlib compression
    # operate on bytes.
    #base64d = force_bytes(TimestampSigner(key, salt=salt).unsign(s, max_age=max_age))
    #base64e = force_str(TimestampSigner(key=key, salt=salt).sign(base64e))
    base64d = force_bytes(TimestampSigner(key=key, salt=salt).unsign(s, max_age=max_age))
    decompress = False
    if base64d[:1] == b".":
        # It's compressed; uncompress it first
        base64d = base64d[1:]
        decompress = True
    data = b64_decode(base64d)
    if decompress:
        data = zlib.decompress(data)
    return serializer().loads(data)


class Signer(Sgnr):
    def unsign(self, signed_value):
        signed_value = force_str(signed_value)
        if self.sep not in signed_value:
            raise BadSignature('No "%s" found in value' % self.sep)
        value, sig = signed_value.rsplit(self.sep, 1)
        if constant_time_compare(sig, self.signature(value)):
            return force_str(value)
        raise BadSignature('Signature "%s" does not match' % sig)


"""
TimestampSigner is also the same as `django.core.signing.TimestampSigner` but is
calling `this` Signer.
"""


class TimestampSigner(Signer, TsS):
    def unsign(self, value, max_age=None):
        """
        Retrieve original value and check it wasn't signed more
        than max_age seconds ago.
        """
        result = super(TimestampSigner, self).unsign(value)
        value, timestamp = result.rsplit(self.sep, 1)
        timestamp = baseconv.base62.decode(timestamp)
        if max_age is not None:
            if isinstance(max_age, datetime.timedelta):
                max_age = max_age.total_seconds()
            # Check timestamp is not older than max_age
            age = time.time() - timestamp
            if age > max_age:
                raise SignatureExpired("Signature age %s > %s seconds" % (age, max_age))
        return value
