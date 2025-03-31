import hashlib

num = 0
text = str(num)

hash_object = hashlib.md5(text.encode())
print(hash_object.hexdigest())