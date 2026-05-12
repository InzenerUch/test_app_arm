import bcrypt

# Задайте желаемый пароль
my_password = "7314895_="

# Сгенерируйте хеш
hashed = bcrypt.hashpw(my_password.encode('utf-8'), bcrypt.gensalt())

# Выведите результат
print(hashed.decode('utf-8'))