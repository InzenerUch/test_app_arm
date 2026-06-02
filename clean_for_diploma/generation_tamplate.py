import bcrypt
my_password = "7314895_="
hashed = bcrypt.hashpw(my_password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))