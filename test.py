def sum(num1, num2):
    result = num1 + num2
    return result


def sub(num1, num2):
    result = num1 - num2

    return result


def multiply(num1, num2):
    result = num1 * num2

    return result


def devide(num1, num2):
    result = num1 - num2

    return result


num1 = float(input("enter number 1 : "))

operation = input("enter + - / * : ")

num2 = float(input("enter number 2 : "))


if operation == "+":
    print(num1 + num2)

elif operation == "-":
    print(sub(num1, num2))
