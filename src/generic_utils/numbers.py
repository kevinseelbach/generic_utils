def baseconv(num, alphabet, minimum_characters=0):
    """
    convert base 10 number to custom base w/ alphabet
    :param num: base 10 input
    :param alphabet: alphabet to use for conversion
    :return:
    """
    arr = []
    base = len(alphabet)

    if not num:
        converted_value = alphabet[0]
    else:
        while num:
            rem = num % base
            num //= base
            arr.append(alphabet[rem])

        arr.reverse()
        converted_value = str(''.join(arr))

    # Pad the returned value as needed in the most significant digit
    while len(converted_value) < minimum_characters:
        converted_value = alphabet[0] + converted_value

    return converted_value


def revbaseconv(packet, from_alphabet):
    """
    convert number in custom base w/ alphabet to base 10
    :param packet: string representation of custom number
    :param from_alphabet: alphabet to use for conversion
    :return:
    """
    strlen = len(packet)
    if not strlen:
        raise ValueError("packet is empty")
    num = 0
    idx = 0

    for char in packet:
        try:
            power = (strlen - (idx + 1))
            num += from_alphabet.index(char) * (len(from_alphabet) ** power)
            idx += 1
        except ValueError as e:
            raise ValueError("Invalid encoded packet.  Illegal character '%s' provided in packet." % char)

    # return number as base 10
    return num


def cleanbin(num, minimum_digits=None):
    b = bin(num)
    if b[:2] == '0b':
        b = b[2:]

    if minimum_digits:
        padding = ['0' for a in range(minimum_digits - len(b))]
        b = ''.join(padding) + b

    return b